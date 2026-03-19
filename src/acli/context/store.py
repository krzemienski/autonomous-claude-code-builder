"""Context store for persisting brownfield project analysis results.

Stores codebase analysis, tech stack, conventions, and decisions
under `.acli/context/` in the project directory.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ContextStore:
    """Persistent storage for project context data.

    All data is stored as JSON files under `.acli/context/` in the
    project directory. Provides read/write access to codebase analysis,
    tech stack info, coding conventions, and architectural decisions.

    Args:
        project_dir: Root directory of the target project.
    """

    def __init__(self, project_dir: Path) -> None:
        """Initialize context store paths.

        Args:
            project_dir: Root directory of the target project.
        """
        self._context_dir = project_dir / ".acli" / "context"
        self._analysis_path = self._context_dir / "codebase_analysis.json"
        self._tech_stack_path = self._context_dir / "tech_stack.json"
        self._conventions_path = self._context_dir / "conventions.json"
        self._decisions_path = self._context_dir / "decisions.jsonl"

    def initialize(self) -> None:
        """Create the `.acli/context/` directory structure."""
        self._context_dir.mkdir(parents=True, exist_ok=True)

    def store_analysis(self, analysis: dict[str, Any]) -> None:
        """Write codebase analysis results to disk.

        Args:
            analysis: Dictionary containing analysis data (file counts,
                architecture style, directory layout, etc.).
        """
        self._context_dir.mkdir(parents=True, exist_ok=True)
        self._analysis_path.write_text(
            json.dumps(analysis, indent=2, default=str), encoding="utf-8"
        )

    def store_tech_stack(self, tech_stack: dict[str, Any]) -> None:
        """Write detected tech stack to disk.

        Args:
            tech_stack: Dictionary with language, framework, database, etc.
        """
        self._context_dir.mkdir(parents=True, exist_ok=True)
        self._tech_stack_path.write_text(
            json.dumps(tech_stack, indent=2, default=str), encoding="utf-8"
        )

    def store_conventions(self, conventions: dict[str, Any]) -> None:
        """Write detected coding conventions to disk.

        Args:
            conventions: Dictionary with linter, formatter, style settings.
        """
        self._context_dir.mkdir(parents=True, exist_ok=True)
        self._conventions_path.write_text(
            json.dumps(conventions, indent=2, default=str), encoding="utf-8"
        )

    def log_decision(self, key: str, value: str, confidence: float) -> None:
        """Append an architectural decision to the decisions log.

        Args:
            key: Decision identifier (e.g., 'auth_strategy').
            value: Chosen approach description.
            confidence: Confidence score between 0.0 and 1.0.
        """
        self._context_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "key": key,
            "value": value,
            "confidence": confidence,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        with open(self._decisions_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def get_analysis(self) -> dict[str, Any] | None:
        """Read codebase analysis from disk.

        Returns:
            Analysis dictionary, or None if not yet stored.
        """
        if not self._analysis_path.exists():
            return None
        content = self._analysis_path.read_text(encoding="utf-8").strip()
        if not content:
            return None
        data: dict[str, Any] = json.loads(content)
        return data

    def get_tech_stack(self) -> dict[str, Any] | None:
        """Read tech stack from disk.

        Returns:
            Tech stack dictionary, or None if not yet stored.
        """
        if not self._tech_stack_path.exists():
            return None
        content = self._tech_stack_path.read_text(encoding="utf-8").strip()
        if not content:
            return None
        data: dict[str, Any] = json.loads(content)
        return data

    def get_context_summary(self) -> str:
        """Build a human-readable summary of all stored context.

        Returns:
            Formatted string combining analysis, tech stack,
            conventions, and recent decisions.
        """
        sections: list[str] = []

        analysis = self.get_analysis()
        if analysis:
            sections.append("## Codebase Analysis")
            for k, v in analysis.items():
                sections.append(f"  {k}: {v}")

        tech_stack = self.get_tech_stack()
        if tech_stack:
            sections.append("## Tech Stack")
            for k, v in tech_stack.items():
                sections.append(f"  {k}: {v}")

        if self._conventions_path.exists():
            content = self._conventions_path.read_text(encoding="utf-8").strip()
            if content:
                conventions = json.loads(content)
                sections.append("## Conventions")
                for k, v in conventions.items():
                    sections.append(f"  {k}: {v}")

        if self._decisions_path.exists():
            lines = self._decisions_path.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                sections.append("## Decisions")
                for line in lines[-10:]:  # last 10 decisions
                    entry = json.loads(line)
                    sections.append(
                        f"  [{entry['confidence']:.0%}] {entry['key']}: {entry['value']}"
                    )

        if not sections:
            return "No context data stored yet."

        return "\n".join(sections)

    def is_onboarded(self) -> bool:
        """Check whether onboarding has been completed.

        Returns:
            True if codebase_analysis.json exists and is non-empty.
        """
        if not self._analysis_path.exists():
            return False
        content = self._analysis_path.read_text(encoding="utf-8").strip()
        return len(content) > 2  # more than empty "{}"
