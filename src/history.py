"""In-session practice history helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .scoring import CoachingResult
from .topics import FocusSkill


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
    }
