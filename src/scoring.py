"""Heuristic elocution scoring when no OpenAI API key is available."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .topics import FocusSkill

FILLERS = {
    "um",
    "uh",
    "erm",
    "er",
    "ah",
    "like",
    "basically",
    "literally",
    "you know",
    "i mean",
    "sort of",
    "kind of",
    "right",
}

HEDGES = {
    "maybe",
    "perhaps",
    "i think",
    "i guess",
    "i feel like",
    "probably",
    "somewhat",
    "a bit",
    "just",
}


@dataclass
class DimensionScores:
    clarity: int
    structure: int
    pace_and_fillers: int
    topic_connection: int
    focus_skill: int


@dataclass
class CoachingResult:
    overall: int
    dimensions: DimensionScores
    improvements: list[str]
    rewrite_tip: str
    source: str = "heuristic"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        return data


def _words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def _sentences(text: str) -> list[str]:
    parts = re.split(r"[.!?]+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _count_phrases(text: str, phrases: set[str]) -> int:
    lower = f" {text.lower()} "
    count = 0
    for phrase in phrases:
        if " " in phrase:
            count += lower.count(f" {phrase} ")
        else:
            count += len(re.findall(rf"\b{re.escape(phrase)}\b", lower))
    return count


def _clamp(score: float) -> int:
    return max(1, min(10, int(round(score))))


def score_transcript(
    transcript: str,
    topic: str,
    skill: FocusSkill,
) -> CoachingResult:
    """Score a transcript with simple linguistic heuristics."""
    text = (transcript or "").strip()
    words = _words(text)
    sentences = _sentences(text)
    word_count = len(words)

    if word_count < 8:
        return CoachingResult(
            overall=2,
            dimensions=DimensionScores(2, 2, 2, 2, 2),
            improvements=[
                "Speak for longer — aim for at least 45–90 seconds so there is enough to coach.",
                "State your main point in the first two sentences.",
                "End with one clear takeaway the listener can remember.",
            ],
            rewrite_tip=(
                f'Try opening with: "Today I want to talk about {topic.lower().rstrip("?")} — '
                f'and my view is simple."'
            ),
            notes=["Transcript too short for a full assessment."],
        )

    filler_count = _count_phrases(text, FILLERS)
    hedge_count = _count_phrases(text, HEDGES)
    avg_sentence_len = word_count / max(len(sentences), 1)
    topic_tokens = {w for w in _words(topic) if len(w) > 3}
    overlap = len(topic_tokens & set(words))
    topic_ratio = overlap / max(len(topic_tokens), 1)

    # Clarity: prefer moderate sentence length and enough content
    if 8 <= avg_sentence_len <= 22:
        clarity = 8
    elif avg_sentence_len < 8:
        clarity = 6
    else:
        clarity = 5
    if word_count >= 80:
        clarity += 1
    clarity = _clamp(clarity)

    # Structure: openings, closings, signposts
    lower = text.lower()
    structure = 5
    if re.search(r"\b(first|second|finally|to begin|in conclusion|overall)\b", lower):
        structure += 2
    if sentences and len(sentences[0].split()) <= 20:
        structure += 1
    if len(sentences) >= 3:
        structure += 1
    structure = _clamp(structure)

    # Pace / fillers
    filler_rate = filler_count / max(word_count, 1)
    if filler_rate <= 0.01:
        pace = 9
    elif filler_rate <= 0.03:
        pace = 7
    elif filler_rate <= 0.06:
        pace = 5
    else:
        pace = 3
    pace = _clamp(pace)

    # Topic connection
    if topic_ratio >= 0.35:
        topic_score = 8
    elif topic_ratio >= 0.15:
        topic_score = 6
    else:
        topic_score = 4
    topic_score = _clamp(topic_score)

    # Focus skill heuristics
    focus = 6
    skill_notes: list[str] = []
    if skill.name == "Simplicity":
        if avg_sentence_len <= 18:
            focus += 2
        else:
            focus -= 1
            skill_notes.append("Shorten sentences so each carries one idea.")
    elif skill.name == "Connecting":
        you_count = len(re.findall(r"\byou\b", lower))
        if you_count >= 2:
            focus += 2
        else:
            focus -= 1
            skill_notes.append("Address the listener with 'you' and a shared example.")
    elif skill.name == "Storytelling":
        if re.search(r"\b(when|then|suddenly|realised|realized|happened)\b", lower):
            focus += 2
        else:
            focus -= 1
            skill_notes.append("Add a short story with a moment of change.")
    elif skill.name == "Conviction":
        if hedge_count <= 2:
            focus += 2
        else:
            focus -= 2
            skill_notes.append("Cut hedges like 'maybe', 'I think', and 'sort of'.")
    elif skill.name == "Preparation":
        if len(sentences) >= 4 and structure >= 7:
            focus += 2
        else:
            focus -= 1
            skill_notes.append("Use a clear open, two points, and a close.")
    focus = _clamp(focus)

    dims = DimensionScores(
        clarity=clarity,
        structure=structure,
        pace_and_fillers=pace,
        topic_connection=topic_score,
        focus_skill=focus,
    )
    overall = _clamp(
        (clarity + structure + pace + topic_score + focus) / 5
    )

    improvements: list[str] = []
    if pace <= 6:
        improvements.append(
            f"Reduce filler words — found about {filler_count} "
            "(um, like, you know, etc.). Pause instead of filling silence."
        )
    if structure <= 6:
        improvements.append(
            "Signpost your structure: open with your point, use 'first/second', close with a takeaway."
        )
    if clarity <= 6:
        improvements.append(
            "Aim for sentences of roughly 10–18 words. One idea per sentence improves clarity."
        )
    if topic_score <= 6:
        improvements.append(
            "Stay closer to the topic — echo key words from the prompt and answer it directly."
        )
    improvements.extend(skill_notes)
    if not improvements:
        improvements.append(
            f"Strong round. Stretch yourself next time by emphasising {skill.name.lower()} even more."
        )
    improvements = improvements[:3]

    first_sentence = sentences[0] if sentences else topic
    rewrite_tip = (
        f'Stronger opening: "Here is my view on this: {first_sentence.rstrip(".")}. '
        f'That matters because…" — then deliver one concrete example.'
    )

    notes = [
        f"Words: {word_count}",
        f"Sentences: {len(sentences)}",
        f"Avg sentence length: {avg_sentence_len:.1f}",
        f"Fillers: {filler_count}",
        f"Hedges: {hedge_count}",
        f"Focus skill: {skill.name}",
    ]

    return CoachingResult(
        overall=overall,
        dimensions=dims,
        improvements=improvements,
        rewrite_tip=rewrite_tip,
        source="heuristic",
        notes=notes,
    )
