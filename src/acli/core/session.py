"""
Session State Management
========================

Tracks state across agent sessions.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class SessionState:
    """State for a single agent session."""

    session_id: int
    session_type: str  # "initializer" or "coding"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    status: str = "running"  # running, completed, error
    features_completed: list[int] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    tool_calls: int = 0
    tokens_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "session_type": self.session_type,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "features_completed": self.features_completed,
            "errors": self.errors,
            "tool_calls": self.tool_calls,
            "tokens_used": self.tokens_used,
        }


@dataclass
class ProjectState:
    """Overall project state across all sessions."""

    project_dir: Path
    created_at: datetime = field(default_factory=datetime.now)
    sessions: list[SessionState] = field(default_factory=list)
    current_session: SessionState | None = None

    @property
    def state_file(self) -> Path:
        """Path to state persistence file."""
        return self.project_dir / ".acli_state.json"

    @property
    def session_count(self) -> int:
        """Total number of sessions."""
        return len(self.sessions)

    @property
    def is_first_run(self) -> bool:
        """Check if this is the first run (no populated feature list)."""
        feature_file = self.project_dir / "feature_list.json"
        if not feature_file.exists():
            return True
        try:
            import json as _json
            data = _json.loads(feature_file.read_text())
            if isinstance(data, list):
                return len(data) == 0
            if isinstance(data, dict):
                return len(data.get("features", [])) == 0
            return True
        except Exception:
            return True

    def start_session(self) -> SessionState:
        """Start a new session."""
        session_type = "initializer" if self.is_first_run else "coding"
        session = SessionState(
            session_id=self.session_count + 1,
            session_type=session_type,
        )
        self.current_session = session
        return session

    def end_session(
        self,
        status: str = "completed",
        features_completed: list[int] | None = None,
        errors: list[str] | None = None,
    ) -> None:
        """End current session."""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.current_session.status = status
            if features_completed:
                self.current_session.features_completed = features_completed
            if errors:
                self.current_session.errors = errors
            self.sessions.append(self.current_session)
            self.current_session = None

    def save(self) -> None:
        """Save state to file."""
        data = {
            "project_dir": str(self.project_dir),
            "created_at": self.created_at.isoformat(),
            "sessions": [s.to_dict() for s in self.sessions],
        }
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, project_dir: Path) -> "ProjectState":
        """Load state from file or create new."""
        state_file = project_dir / ".acli_state.json"

        if state_file.exists():
            with open(state_file) as f:
                data = json.load(f)

            state = cls(
                project_dir=project_dir,
                created_at=datetime.fromisoformat(data["created_at"]),
            )

            for session_data in data.get("sessions", []):
                session = SessionState(
                    session_id=session_data["session_id"],
                    session_type=session_data["session_type"],
                    start_time=datetime.fromisoformat(session_data["start_time"]),
                    end_time=(
                        datetime.fromisoformat(session_data["end_time"])
                        if session_data["end_time"]
                        else None
                    ),
                    status=session_data["status"],
                    features_completed=session_data.get("features_completed", []),
                    errors=session_data.get("errors", []),
                    tool_calls=session_data.get("tool_calls", 0),
                    tokens_used=session_data.get("tokens_used", 0),
                )
                state.sessions.append(session)

            return state

        return cls(project_dir=project_dir)


def get_project_state(project_dir: Path) -> ProjectState:
    """Get or create project state."""
    return ProjectState.load(project_dir)


class SessionLogger:
    """Writes agent session events to JSONL files."""

    def __init__(self, project_dir: Path, session_id: str) -> None:
        self.session_id = session_id
        self.sessions_dir = project_dir / ".acli" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.sessions_dir / f"{session_id}.jsonl"
        self._file = open(self.log_file, "a")

    def log_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Write a single event to the JSONL log."""
        entry = {
            "type": event_type,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            **data,
        }
        self._file.write(json.dumps(entry) + "\n")
        self._file.flush()

    def close(self) -> None:
        """Close the log file."""
        self._file.close()

    @staticmethod
    def list_sessions(project_dir: Path) -> list[dict[str, Any]]:
        """List all JSONL session logs for a project."""
        sessions_dir = project_dir / ".acli" / "sessions"
        if not sessions_dir.exists():
            return []
        return [
            {"session_id": f.stem, "path": str(f), "size": f.stat().st_size}
            for f in sorted(sessions_dir.glob("*.jsonl"))
        ]

    @staticmethod
    def load_session(project_dir: Path, session_id: str) -> list[dict[str, Any]]:
        """Load all events from a session log."""
        path = project_dir / ".acli" / "sessions" / f"{session_id}.jsonl"
        if not path.exists():
            return []
        events: list[dict[str, Any]] = []
        with open(path) as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        return events
