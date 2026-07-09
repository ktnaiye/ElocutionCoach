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


DIMENSION_LABELS = {
    "clarity": "Clarity",
    "structure": "Structure",
    "pace_and_fillers": "Pace / fillers",
    "topic_connection": "On topic",
    "focus_skill": "Focus skill",
}


@dataclass
class DimensionScores:
    clarity: int
    structure: int
    pace_and_fillers: int
    topic_connection: int
    focus_skill: int


@dataclass
class DimensionBreakdown:
    """Score plus a short explanation for one rating dimension."""

    key: str
    label: str
    score: int
    reason: str


@dataclass
class CoachingResult:
    overall: int
    dimensions: DimensionScores
    improvements: list[str]
    rewrite_tip: str
    source: str = "heuristic"
    notes: list[str] = field(default_factory=list)
    dimension_breakdown: list[DimensionBreakdown] = field(default_factory=list)
    overall_reason: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        return data


def build_breakdown(
    dims: DimensionScores,
    reasons: dict[str, str],
) -> list[DimensionBreakdown]:
    """Attach human-readable reasons to each dimension score."""
    order = (
        "clarity",
        "structure",
        "pace_and_fillers",
        "topic_connection",
        "focus_skill",
    )
    breakdown: list[DimensionBreakdown] = []
    for key in order:
        breakdown.append(
            DimensionBreakdown(
                key=key,
                label=DIMENSION_LABELS[key],
                score=int(getattr(dims, key)),
                reason=reasons.get(key, "No detailed reason provided for this score."),
            )
        )
    return breakdown


def _default_short_reasons() -> dict[str, str]:
    return {
        "clarity": "Not enough speech to judge how clearly ideas were expressed.",
        "structure": "Not enough speech to judge opening, body, and close.",
        "pace_and_fillers": "Not enough speech to judge pace or filler words.",
        "topic_connection": "Not enough speech to judge how closely you answered the topic.",
        "focus_skill": "Not enough speech to judge the focus skill for this round.",
    }


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
        dims = DimensionScores(2, 2, 2, 2, 2)
        reasons = _default_short_reasons()
        return CoachingResult(
            overall=2,
            dimensions=dims,
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
            dimension_breakdown=build_breakdown(dims, reasons),
            overall_reason=(
                "Overall is low because the sample was too short to assess clarity, "
                "structure, pace, topic focus, or the round's skill."
            ),
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
        clarity_reason = (
            f"Average sentence length was {avg_sentence_len:.1f} words — "
            "a clear, easy-to-follow range (about 8–22 words)."
        )
    elif avg_sentence_len < 8:
        clarity = 6
        clarity_reason = (
            f"Sentences averaged only {avg_sentence_len:.1f} words, which can sound choppy. "
            "Join related ideas into fuller sentences of about 10–18 words."
        )
    else:
        clarity = 5
        clarity_reason = (
            f"Sentences averaged {avg_sentence_len:.1f} words, which is long for spoken English. "
            "Split dense sentences so each carries one idea."
        )
    if word_count >= 80:
        clarity += 1
        clarity_reason += f" You also gave enough content ({word_count} words) to develop the idea."
    else:
        clarity_reason += f" The sample was fairly short ({word_count} words); a bit more detail would help."
    clarity = _clamp(clarity)

    # Structure: openings, closings, signposts
    lower = text.lower()
    structure = 5
    structure_bits: list[str] = []
    if re.search(r"\b(first|second|finally|to begin|in conclusion|overall)\b", lower):
        structure += 2
        structure_bits.append("you used clear signposts (e.g. first/second/finally)")
    else:
        structure_bits.append("few signposts like 'first', 'second', or 'finally' were heard")
    if sentences and len(sentences[0].split()) <= 20:
        structure += 1
        structure_bits.append("the opening sentence was concise")
    else:
        structure_bits.append("the opening could be shorter and more purposeful")
    if len(sentences) >= 3:
        structure += 1
        structure_bits.append(f"you built {len(sentences)} sentences, enough for open/body/close")
    else:
        structure_bits.append("there were fewer than three sentences, so the arc felt thin")
    structure = _clamp(structure)
    structure_reason = (
        f"Structure scored {structure}/10 because " + "; ".join(structure_bits) + "."
    )

    # Pace / fillers
    filler_rate = filler_count / max(word_count, 1)
    if filler_rate <= 0.01:
        pace = 9
        pace_reason = (
            f"Only about {filler_count} filler(s) in {word_count} words — "
            "pace sounded controlled, with little padding (um, like, you know)."
        )
    elif filler_rate <= 0.03:
        pace = 7
        pace_reason = (
            f"About {filler_count} filler(s) in {word_count} words — "
            "mostly steady, but a few fillers still interrupt flow. Pause instead of filling silence."
        )
    elif filler_rate <= 0.06:
        pace = 5
        pace_reason = (
            f"About {filler_count} filler(s) in {word_count} words — "
            "fillers are noticeable. Practise a silent beat when you need thinking time."
        )
    else:
        pace = 3
        pace_reason = (
            f"About {filler_count} filler(s) in {word_count} words — "
            "fillers are frequent and weaken authority. Slow down and replace them with pauses."
        )
    pace = _clamp(pace)

    # Topic connection
    if topic_ratio >= 0.35:
        topic_score = 8
        topic_reason = (
            "You echoed several key words from the prompt and stayed close to the question asked."
        )
    elif topic_ratio >= 0.15:
        topic_score = 6
        topic_reason = (
            "You touched the topic, but only partly. Name the question early and answer it directly "
            "before adding side points."
        )
    else:
        topic_score = 4
        topic_reason = (
            "Little overlap with the prompt's key words. Restate the topic in your opening "
            "so the listener knows you are answering it."
        )
    topic_score = _clamp(topic_score)

    # Focus skill heuristics
    focus = 6
    skill_notes: list[str] = []
    if skill.name == "Simplicity":
        if avg_sentence_len <= 18:
            focus += 2
            focus_reason = (
                f"Focus skill ({skill.name}): sentences stayed fairly short "
                f"({avg_sentence_len:.1f} words on average), which supports one clear idea."
            )
        else:
            focus -= 1
            focus_reason = (
                f"Focus skill ({skill.name}): sentences ran long "
                f"({avg_sentence_len:.1f} words). Shorten them so each carries one idea."
            )
            skill_notes.append("Shorten sentences so each carries one idea.")
    elif skill.name == "Connecting":
        you_count = len(re.findall(r"\byou\b", lower))
        if you_count >= 2:
            focus += 2
            focus_reason = (
                f"Focus skill ({skill.name}): you addressed the listener "
                f"({you_count} uses of 'you'), which helps the talk feel audience-first."
            )
        else:
            focus -= 1
            focus_reason = (
                f"Focus skill ({skill.name}): little direct address to the listener. "
                "Use 'you' and a shared example at least twice."
            )
            skill_notes.append("Address the listener with 'you' and a shared example.")
    elif skill.name == "Storytelling":
        if re.search(r"\b(when|then|suddenly|realised|realized|happened)\b", lower):
            focus += 2
            focus_reason = (
                f"Focus skill ({skill.name}): narrative cues (when/then/happened) suggest "
                "a short story arc with a moment of change."
            )
        else:
            focus -= 1
            focus_reason = (
                f"Focus skill ({skill.name}): few story markers were heard. "
                "Add a brief setup → tension → point."
            )
            skill_notes.append("Add a short story with a moment of change.")
    elif skill.name == "Conviction":
        if hedge_count <= 2:
            focus += 2
            focus_reason = (
                f"Focus skill ({skill.name}): only about {hedge_count} hedge(s) "
                "(maybe / I think / sort of) — your stance sounded clearer."
            )
        else:
            focus -= 2
            focus_reason = (
                f"Focus skill ({skill.name}): about {hedge_count} hedge(s) softened your message. "
                "Replace them with stronger verbs and a clear claim."
            )
            skill_notes.append("Cut hedges like 'maybe', 'I think', and 'sort of'.")
    elif skill.name == "Preparation":
        if len(sentences) >= 4 and structure >= 7:
            focus += 2
            focus_reason = (
                f"Focus skill ({skill.name}): enough sentences and signposts to suggest "
                "a prepared open / body / close."
            )
        else:
            focus -= 1
            focus_reason = (
                f"Focus skill ({skill.name}): the talk needed a clearer prepared shape — "
                "open with purpose, two points, then a takeaway."
            )
            skill_notes.append("Use a clear open, two points, and a close.")
    else:
        focus_reason = f"Focus skill ({skill.name}): scored from how clearly the skill tip showed up in your talk."
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
    reasons = {
        "clarity": clarity_reason,
        "structure": structure_reason,
        "pace_and_fillers": pace_reason,
        "topic_connection": topic_reason,
        "focus_skill": focus_reason,
    }
    overall_reason = (
        f"Overall {overall}/10 is the average of Clarity ({clarity}), Structure ({structure}), "
        f"Pace/fillers ({pace}), On topic ({topic_score}), and Focus skill ({focus}). "
        "Improve the lowest dimensions first for the biggest gain."
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
        dimension_breakdown=build_breakdown(dims, reasons),
        overall_reason=overall_reason,
    )
