"""
Progress Persistence
====================

File-based persistence for progress state across sessions.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ProgressSnapshot:
    """Snapshot of progress at a point in time."""
    timestamp: str
    total_features: int
    passing_features: int
    session_count: int
    last_feature_id: int | None
    elapsed_seconds: float


class ProgressPersistence:
    """
    Persists progress state to disk.

    Files:
    - .acli_progress.json: Current progress snapshot
    - .acli_history.jsonl: Append-only history log
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.snapshot_path = project_dir / ".acli_progress.json"
        self.history_path = project_dir / ".acli_history.jsonl"

    def save_snapshot(self, snapshot: ProgressSnapshot) -> None:
        """Save current progress snapshot."""
        with open(self.snapshot_path, "w") as f:
            json.dump(asdict(snapshot), f, indent=2)

    def load_snapshot(self) -> ProgressSnapshot | None:
        """Load last progress snapshot."""
        if not self.snapshot_path.exists():
            return None

        with open(self.snapshot_path) as f:
            data = json.load(f)

        return ProgressSnapshot(**data)

    def append_history(self, event: dict[str, Any]) -> None:
        """Append event to history log."""
        event["timestamp"] = datetime.now().isoformat()

        with open(self.history_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def read_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Read recent history entries."""
        if not self.history_path.exists():
            return []

        events = []
        with open(self.history_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))

        return events[-limit:]

    def clear_history(self) -> None:
        """Clear history log."""
        if self.history_path.exists():
            self.history_path.unlink()

    def get_stats(self) -> dict[str, Any]:
        """Get persistence statistics."""
        history = self.read_history(1000)

        sessions = [e for e in history if e.get("event_type") == "session_end"]
        features = [e for e in history if e.get("event_type") == "feature_complete"]

        return {
            "total_sessions": len(sessions),
            "total_features_completed": len(features),
            "history_entries": len(history),
        }


def create_snapshot(
    total: int,
    passing: int,
    session_count: int,
    last_feature: int | None,
    elapsed: float,
) -> ProgressSnapshot:
    """Create progress snapshot."""
    return ProgressSnapshot(
        timestamp=datetime.now().isoformat(),
        total_features=total,
        passing_features=passing,
        session_count=session_count,
        last_feature_id=last_feature,
        elapsed_seconds=elapsed,
    )
