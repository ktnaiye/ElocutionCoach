"""OpenAI-powered transcription and elocution coaching."""

from __future__ import annotations

import io
import json
import os
import re
from typing import Any

from .scoring import (
    CoachingResult,
    DimensionScores,
    build_breakdown,
    score_transcript,
)
from .topics import FocusSkill

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore


def get_api_key() -> str | None:
    """Read API key from environment or Streamlit secrets if available."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        return key
    try:
        import streamlit as st

        key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()
        return key or None
    except Exception:
        return None


def has_openai() -> bool:
    return bool(get_api_key() and OpenAI is not None)


def _client() -> Any:
    if OpenAI is None:
        raise RuntimeError("openai package is not installed")
    key = get_api_key()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=key)


def transcribe_audio(audio_bytes: bytes, filename: str = "recording.wav") -> str:
    """Transcribe recorded audio with Whisper."""
    client = _client()
    bio = io.BytesIO(audio_bytes)
    bio.name = filename
    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=bio,
        language="en",
    )
    return (result.text or "").strip()


def _extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _reason_map(data: dict, dims: DimensionScores, skill: FocusSkill) -> dict[str, str]:
    raw = data.get("dimension_reasons") or data.get("reasons") or {}
    defaults = {
        "clarity": (
            f"Clarity {dims.clarity}/10 — based on how easy the ideas were to follow "
            "in spoken English (sentence length, one idea at a time)."
        ),
        "structure": (
            f"Structure {dims.structure}/10 — based on whether there was a clear open, "
            "developed middle, and memorable close."
        ),
        "pace_and_fillers": (
            f"Pace/fillers {dims.pace_and_fillers}/10 — based on filler words, hedges, "
            "and whether pauses replaced padding."
        ),
        "topic_connection": (
            f"On topic {dims.topic_connection}/10 — based on how directly the talk "
            "answered the practice prompt."
        ),
        "focus_skill": (
            f"Focus skill ({skill.name}) {dims.focus_skill}/10 — based on how clearly "
            f"the tip for {skill.name.lower()} showed up in the talk."
        ),
    }
    reasons: dict[str, str] = {}
    for key, fallback in defaults.items():
        value = raw.get(key) if isinstance(raw, dict) else None
        reasons[key] = str(value).strip() if value else fallback
    return reasons


def _parse_ai_result(data: dict, skill: FocusSkill) -> CoachingResult:
    dims_raw = data.get("dimensions") or {}
    dims = DimensionScores(
        clarity=int(dims_raw.get("clarity", 5)),
        structure=int(dims_raw.get("structure", 5)),
        pace_and_fillers=int(dims_raw.get("pace_and_fillers", 5)),
        topic_connection=int(dims_raw.get("topic_connection", 5)),
        focus_skill=int(dims_raw.get("focus_skill", 5)),
    )
    improvements = data.get("improvements") or []
    if isinstance(improvements, str):
        improvements = [improvements]
    improvements = [str(i).strip() for i in improvements if str(i).strip()][:3]
    while len(improvements) < 2:
        improvements.append(f"Practise {skill.name.lower()} with a clearer example next round.")

    overall = data.get("overall")
    if overall is None:
        overall = round(
            (
                dims.clarity
                + dims.structure
                + dims.pace_and_fillers
                + dims.topic_connection
                + dims.focus_skill
            )
            / 5
        )
    overall = max(1, min(10, int(overall)))
    reasons = _reason_map(data, dims, skill)
    overall_reason = str(data.get("overall_reason") or "").strip() or (
        f"Overall {overall}/10 averages the five dimensions. "
        "Raise the lowest scores first for the fastest improvement."
    )

    return CoachingResult(
        overall=overall,
        dimensions=dims,
        improvements=improvements,
        rewrite_tip=str(data.get("rewrite_tip") or "Open with your main point in one crisp sentence."),
        source="openai",
        notes=[str(n) for n in (data.get("notes") or [])][:5],
        dimension_breakdown=build_breakdown(dims, reasons),
        overall_reason=overall_reason,
    )


SYSTEM_PROMPT = """You are an encouraging elocution and communication coach for a non-native English speaker living in the UK.
Score spoken English practice for clarity, structure, pace/filler awareness, connection to the topic, and application of a focus skill.
Draw on well-known public communication principles (e.g. simplicity, connecting with the audience, storytelling, conviction, preparation) — paraphrase; do not quote copyrighted books.
Be constructive, specific, and kind. Do not shame accents. Suggest British English phrasing only when it improves clarity or naturalness.
For every dimension score, explain WHY in one or two concrete sentences that cite what you heard (or did not hear) in the transcript. Mention examples from the speaker's words when useful.
Return ONLY valid JSON with this shape:
{
  "overall": 1-10,
  "overall_reason": "One or two sentences explaining how the overall score was formed and what to prioritise.",
  "dimensions": {
    "clarity": 1-10,
    "structure": 1-10,
    "pace_and_fillers": 1-10,
    "topic_connection": 1-10,
    "focus_skill": 1-10
  },
  "dimension_reasons": {
    "clarity": "Why this clarity score — cite sentence length, density, or wording.",
    "structure": "Why this structure score — cite open/body/close or signposts.",
    "pace_and_fillers": "Why this pace score — cite fillers, hedges, or rushing.",
    "topic_connection": "Why this topic score — cite how directly the prompt was answered.",
    "focus_skill": "Why this focus-skill score — cite evidence of the named skill."
  },
  "improvements": ["...", "...", "..."],
  "rewrite_tip": "One stronger opening or closing line the speaker could try.",
  "notes": ["optional short observations"]
}
"""


def rate_with_openai(
    transcript: str,
    topic: str,
    skill: FocusSkill,
) -> CoachingResult:
    client = _client()
    user_prompt = f"""Topic: {topic}
Focus skill: {skill.name}
Skill tip: {skill.tip}
Skill cue: {skill.cue}

Transcript:
\"\"\"{transcript}\"\"\"
"""
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.4,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    data = _extract_json(content)
    return _parse_ai_result(data, skill)


def coach_transcript(
    transcript: str,
    topic: str,
    skill: FocusSkill,
) -> CoachingResult:
    """Rate a transcript with OpenAI when available, else heuristics."""
    text = (transcript or "").strip()
    if not text:
        return score_transcript(text, topic, skill)
    if has_openai():
        try:
            return rate_with_openai(text, topic, skill)
        except Exception as exc:  # noqa: BLE001 — fall back gracefully
            result = score_transcript(text, topic, skill)
            result.notes = [f"AI coaching unavailable ({exc}); used heuristic scoring."] + list(
                result.notes
            )
            return result
    return score_transcript(text, topic, skill)
