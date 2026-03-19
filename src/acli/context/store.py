"""
Context Store
=============

Persistent codebase knowledge store.
Reads/writes to .acli/context/ directory.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ContextStore:
    """
    Persistent codebase knowledge store.

    Reads/writes to .acli/context/ directory:
    - codebase_analysis.json: Full architecture map
    - dependency_graph.json: Import relationships
    - conventions.json: Code patterns and style
    - tech_stack.json: Detected technology stack
    - decisions.jsonl: Append-only decision log
    """

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self._context_dir = project_dir / ".acli" / "context"

    def initialize(self) -> None:
        """Create .acli/context/ structure."""
        self._context_dir.mkdir(parents=True, exist_ok=True)

    def store_analysis(self, analysis: dict[str, Any]) -> None:
        """Store codebase analysis."""
        self._write_json("codebase_analysis.json", analysis)

    def store_tech_stack(self, tech_stack: dict[str, Any]) -> None:
        """Store detected tech stack."""
        self._write_json("tech_stack.json", tech_stack)

    def store_conventions(self, conventions: dict[str, Any]) -> None:
        """Store detected code conventions."""
        self._write_json("conventions.json", conventions)

    def log_decision(self, key: str, value: str, confidence: float) -> None:
        """Append a decision to the decision log."""
        self._context_dir.mkdir(parents=True, exist_ok=True)
        decision = {
            "key": key,
            "value": value,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        decisions_file = self._context_dir / "decisions.jsonl"
        with open(decisions_file, "a") as f:
            f.write(json.dumps(decision) + "\n")

    def get_analysis(self) -> dict[str, Any] | None:
        """Get stored codebase analysis."""
        return self._read_json("codebase_analysis.json")

    def get_tech_stack(self) -> dict[str, Any] | None:
        """Get stored tech stack."""
        return self._read_json("tech_stack.json")

    def get_conventions(self) -> dict[str, Any] | None:
        """Get stored conventions."""
        return self._read_json("conventions.json")

    def get_context_summary(self) -> str:
        """Human-readable summary for agent prompt injection."""
        parts: list[str] = []

        tech_stack = self.get_tech_stack()
        if tech_stack:
            parts.append("Tech Stack:")
            for k, v in tech_stack.items():
                parts.append(f"  - {k}: {v}")

        analysis = self.get_analysis()
        if analysis:
            parts.append("Architecture:")
            for k, v in analysis.items():
                parts.append(f"  - {k}: {v}")

        conventions = self.get_conventions()
        if conventions:
            parts.append("Conventions:")
            for k, v in conventions.items():
                parts.append(f"  - {k}: {v}")

        if not parts:
            return "No context available yet."

        return "\n".join(parts)

    def is_onboarded(self) -> bool:
        """True if codebase_analysis.json exists and non-empty."""
        analysis_file = self._context_dir / "codebase_analysis.json"
        if not analysis_file.exists():
            return False
        try:
            data = json.loads(analysis_file.read_text())
            return bool(data)
        except (json.JSONDecodeError, OSError):
            return False

    def _write_json(self, filename: str, data: dict[str, Any]) -> None:
        """Write JSON to context directory."""
        self._context_dir.mkdir(parents=True, exist_ok=True)
        filepath = self._context_dir / filename
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def _read_json(self, filename: str) -> dict[str, Any] | None:
        """Read JSON from context directory."""
        filepath = self._context_dir / filename
        if not filepath.exists():
            return None
        try:
            with open(filepath) as f:
                return json.load(f)  # type: ignore[no-any-return]
        except (json.JSONDecodeError, OSError):
            return None
