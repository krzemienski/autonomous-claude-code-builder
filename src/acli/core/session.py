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
        """Check if this is the first run."""
        feature_file = self.project_dir / "feature_list.json"
        return not feature_file.exists()

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
