"""In-session practice history helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .scoring import CoachingResult
from .topics import FocusSkill


DIMENSION_LABELS = {
    "clarity": "Clarity",
    "structure": "Structure",
    "pace_and_fillers": "Pace / fillers",
    "topic_connection": "On topic",
    "focus_skill": "Focus skill",
}

IMPROVEMENT_THEMES = {
    "Pace and filler control": ("filler", "pace", "pause", "silence", "rushing"),
    "Clear structure": ("structure", "signpost", "opening", "close", "first/second"),
    "Clarity and concise sentences": ("clarity", "sentence", "one idea", "shorten"),
    "Staying on topic": ("topic", "prompt", "directly", "key words"),
    "Audience connection": ("listener", "audience", "address", "shared example"),
    "Storytelling": ("story", "moment of change", "setup", "tension"),
    "Speaking with conviction": ("hedge", "conviction", "stronger verbs", "maybe"),
}

PRACTICE_ACTIONS = {
    "clarity": "Use one idea per sentence and aim for sentences of roughly 10–18 words.",
    "structure": "Before speaking, note a one-line opening, two main points, and one closing takeaway.",
    "pace_and_fillers": "Replace filler words with a deliberate one-second pause.",
    "topic_connection": "Answer the exact question in your first two sentences, then support that answer.",
    "focus_skill": "Repeat the round's focus cue before recording and demonstrate it at least twice.",
}


def make_history_entry(
    topic: str,
    skill: FocusSkill,
    result: CoachingResult,
    transcript_preview: str,
) -> dict[str, Any]:
    preview = " ".join(transcript_preview.split())
    if len(preview) > 120:
        preview = preview[:117] + "..."
    return {
        "time": datetime.now(timezone.utc).strftime("%H:%M"),
        "topic": topic,
        "skill": skill.name,
        "overall": result.overall,
        "source": result.source,
        "preview": preview,
        "improvements": result.improvements,
        "dimensions": {
            "clarity": result.dimensions.clarity,
            "structure": result.dimensions.structure,
            "pace_and_fillers": result.dimensions.pace_and_fillers,
            "topic_connection": result.dimensions.topic_connection,
            "focus_skill": result.dimensions.focus_skill,
        },
    }


def _recurring_improvement_areas(history: list[dict[str, Any]]) -> list[str]:
    theme_counts = {theme: 0 for theme in IMPROVEMENT_THEMES}
    for entry in history:
        improvement_text = " ".join(entry.get("improvements", [])).lower()
        for theme, keywords in IMPROVEMENT_THEMES.items():
            if any(keyword in improvement_text for keyword in keywords):
                theme_counts[theme] += 1

    recurring = [
        theme
        for theme, count in sorted(
            theme_counts.items(), key=lambda item: item[1], reverse=True
        )
        if count > 0
    ]
    return recurring[:3]


def build_session_summary(history: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate completed practice rounds into an actionable session review."""
    if not history:
        raise ValueError("At least one completed practice is required.")

    average_score = sum(float(entry["overall"]) for entry in history) / len(history)
    if average_score >= 8:
        assessment = (
            "A strong session: your communication was consistently effective. "
            "Refine the priority area below to make your delivery more polished."
        )
    elif average_score >= 6:
        assessment = (
            "A developing session: your core message usually came through, with clear "
            "opportunities to become more consistent and confident."
        )
    else:
        assessment = (
            "A useful foundation session: focus on one improvement at a time rather "
            "than trying to change every part of your delivery at once."
        )
    dimension_values: dict[str, list[float]] = {
        key: [] for key in DIMENSION_LABELS
    }
    for entry in history:
        for key, value in entry.get("dimensions", {}).items():
            if key in dimension_values:
                dimension_values[key].append(float(value))

    dimension_averages = {
        key: sum(values) / len(values)
        for key, values in dimension_values.items()
        if values
    }
    if dimension_averages:
        strongest_key = max(dimension_averages, key=dimension_averages.get)
        priority_key = min(dimension_averages, key=dimension_averages.get)
        strongest = {
            "label": DIMENSION_LABELS[strongest_key],
            "score": dimension_averages[strongest_key],
        }
        priority = {
            "label": DIMENSION_LABELS[priority_key],
            "score": dimension_averages[priority_key],
        }
        take_home = PRACTICE_ACTIONS[priority_key]
    else:
        strongest = None
        priority = None
        take_home = (
            "In your next session, use a clear opening, two supporting points, "
            "and a short closing takeaway."
        )

    return {
        "rounds": len(history),
        "average_score": average_score,
        "assessment": assessment,
        "dimension_averages": dimension_averages,
        "strongest": strongest,
        "priority": priority,
        "improvement_areas": _recurring_improvement_areas(history),
        "take_home": take_home,
    }
