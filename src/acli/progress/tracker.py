"""
Progress Tracker
================

High-level progress tracking with events and history.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .feature_list import FeatureList, Feature, load_feature_list


@dataclass
class ProgressEvent:
    """A progress change event."""
    timestamp: datetime
    event_type: str  # "feature_complete", "session_start", "session_end", "milestone"
    feature_id: int | None = None
    session_id: int | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Milestone:
    """A progress milestone."""
    name: str
    threshold: float  # percentage
    reached: bool = False
    reached_at: datetime | None = None


class ProgressTracker:
    """
    Tracks progress with events, milestones, and callbacks.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.feature_list_path = project_dir / "feature_list.json"
        self._feature_list: FeatureList | None = None
        self._events: list[ProgressEvent] = []
        self._callbacks: list[Callable[[ProgressEvent], Any]] = []

        # Standard milestones
        self.milestones = [
            Milestone("Started", 0),
            Milestone("10% Complete", 10),
            Milestone("25% Complete", 25),
            Milestone("50% Complete", 50),
            Milestone("75% Complete", 75),
            Milestone("90% Complete", 90),
            Milestone("Complete", 100),
        ]

    @property
    def feature_list(self) -> FeatureList:
        """Get or load feature list."""
        if self._feature_list is None:
            self._feature_list = load_feature_list(self.feature_list_path)
        return self._feature_list

    def reload(self) -> None:
        """Reload feature list from disk."""
        self._feature_list = None

    def is_first_run(self) -> bool:
        """Check if this is the first run (no feature_list.json exists)."""
        return not self.feature_list_path.exists()

    def get_total_count(self) -> int:
        """Get total number of features."""
        return self.feature_list.total

    def get_completed_count(self) -> int:
        """Get number of completed features."""
        return self.feature_list.passing

    def get_incomplete_count(self) -> int:
        """Get number of incomplete features."""
        return self.feature_list.remaining

    def get_progress_percentage(self) -> float:
        """Get progress percentage."""
        return self.feature_list.percentage

    def on_progress(self, callback: Callable[[ProgressEvent], Any]) -> None:
        """Register progress callback."""
        self._callbacks.append(callback)

    def _emit(self, event: ProgressEvent) -> None:
        """Emit progress event."""
        self._events.append(event)
        for callback in self._callbacks:
            callback(event)

        # Check milestones
        self._check_milestones()

    def _check_milestones(self) -> None:
        """Check and trigger milestone events."""
        percentage = self.feature_list.percentage

        for milestone in self.milestones:
            if not milestone.reached and percentage >= milestone.threshold:
                milestone.reached = True
                milestone.reached_at = datetime.now()

                self._emit(ProgressEvent(
                    timestamp=datetime.now(),
                    event_type="milestone",
                    details={"name": milestone.name, "percentage": percentage},
                ))

    def record_feature_complete(
        self,
        feature_id: int,
        notes: str = "",
    ) -> bool:
        """Record feature completion."""
        success = self.feature_list.mark_passing(feature_id, notes)

        if success:
            self._emit(ProgressEvent(
                timestamp=datetime.now(),
                event_type="feature_complete",
                feature_id=feature_id,
                details={"notes": notes},
            ))
            self.feature_list.save()

        return success

    def record_feature_attempt(
        self,
        feature_id: int,
        notes: str = "",
    ) -> bool:
        """Record failed feature attempt."""
        success = self.feature_list.mark_failed(feature_id, notes)

        if success:
            self._emit(ProgressEvent(
                timestamp=datetime.now(),
                event_type="feature_attempt",
                feature_id=feature_id,
                details={"notes": notes},
            ))
            self.feature_list.save()

        return success

    def record_session_start(self, session_id: int) -> None:
        """Record session start."""
        self._emit(ProgressEvent(
            timestamp=datetime.now(),
            event_type="session_start",
            session_id=session_id,
        ))

    def record_session_end(self, session_id: int, features_completed: int = 0) -> None:
        """Record session end."""
        self._emit(ProgressEvent(
            timestamp=datetime.now(),
            event_type="session_end",
            session_id=session_id,
            details={"features_completed": features_completed},
        ))

    def get_next_feature(self) -> Feature | None:
        """Get next feature to work on."""
        return self.feature_list.get_next_incomplete()

    def get_status(self) -> dict[str, Any]:
        """Get current progress status."""
        fl = self.feature_list

        return {
            "total": fl.total,
            "passing": fl.passing,
            "remaining": fl.remaining,
            "percentage": fl.percentage,
            "milestones": [
                {
                    "name": m.name,
                    "threshold": m.threshold,
                    "reached": m.reached,
                    "reached_at": m.reached_at.isoformat() if m.reached_at else None,
                }
                for m in self.milestones
            ],
            "next_feature": (nf.to_dict() if (nf := self.get_next_feature()) else None),
        }

    def get_summary_text(self) -> str:
        """Get human-readable summary."""
        fl = self.feature_list

        lines = [
            f"Progress: {fl.passing}/{fl.total} ({fl.percentage:.1f}%)",
            f"Remaining: {fl.remaining} features",
        ]

        # Add recent milestones
        recent = [m for m in self.milestones if m.reached][-3:]
        if recent:
            lines.append("Recent milestones:")
            for m in recent:
                lines.append(f"  - {m.name}")

        # Next feature
        next_feat = self.get_next_feature()
        if next_feat:
            lines.append(f"Next: {next_feat.description[:50]}...")

        return "\n".join(lines)

    def export_history(self, path: Path | None = None) -> str:
        """Export event history to JSON."""
        data = [
            {
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "feature_id": e.feature_id,
                "session_id": e.session_id,
                "details": e.details,
            }
            for e in self._events
        ]

        json_str = json.dumps(data, indent=2)

        if path:
            path.write_text(json_str)

        return json_str
