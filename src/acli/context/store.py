"""Persistent codebase knowledge store."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ContextStore:
    """Reads/writes codebase knowledge to .acli/context/ directory."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.context_dir = project_dir / ".acli" / "context"

    def initialize(self) -> None:
        """Create .acli/context/ directory structure."""
        self.context_dir.mkdir(parents=True, exist_ok=True)
        (self.context_dir / "knowledge_chunks").mkdir(exist_ok=True)

    def store_analysis(self, analysis: dict[str, Any]) -> None:
        """Save full codebase analysis."""
        self._write_json("codebase_analysis.json", analysis)

    def store_tech_stack(self, tech_stack: dict[str, Any]) -> None:
        """Save detected technology stack."""
        self._write_json("tech_stack.json", tech_stack)

    def store_conventions(self, conventions: dict[str, Any]) -> None:
        """Save detected code conventions."""
        self._write_json("conventions.json", conventions)

    def log_decision(self, key: str, value: str, confidence: float) -> None:
        """Append decision to JSONL log."""
        entry = {
            "key": key,
            "value": value,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }
        decisions_file = self.context_dir / "decisions.jsonl"
        with open(decisions_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_analysis(self) -> dict[str, Any] | None:
        """Retrieve codebase analysis."""
        return self._read_json("codebase_analysis.json")

    def get_tech_stack(self) -> dict[str, Any] | None:
        """Retrieve tech stack."""
        return self._read_json("tech_stack.json")

    def get_context_summary(self) -> str:
        """Human-readable summary for agent system prompts."""
        parts: list[str] = []
        tech = self.get_tech_stack()
        if tech:
            parts.append(f"Tech Stack: {json.dumps(tech)}")
        analysis = self.get_analysis()
        if analysis:
            parts.append(f"Architecture: {json.dumps(analysis)}")
        decisions = self._read_decisions()
        if decisions:
            parts.append(f"Decisions: {len(decisions)} logged")
            for d in decisions[-5:]:
                parts.append(f"  - {d['key']}: {d['value']} (conf: {d['confidence']})")
        return "\n".join(parts) if parts else "No context available yet."

    def is_onboarded(self) -> bool:
        """True if codebase_analysis.json exists and is non-empty."""
        analysis_file = self.context_dir / "codebase_analysis.json"
        if not analysis_file.exists():
            return False
        content = analysis_file.read_text().strip()
        return content not in ("", "{}", "null")

    def _write_json(self, filename: str, data: dict[str, Any]) -> None:
        self.context_dir.mkdir(parents=True, exist_ok=True)
        with open(self.context_dir / filename, "w") as f:
            json.dump(data, f, indent=2)

    def _read_json(self, filename: str) -> dict[str, Any] | None:
        path = self.context_dir / filename
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def _read_decisions(self) -> list[dict[str, Any]]:
        path = self.context_dir / "decisions.jsonl"
        if not path.exists():
            return []
        decisions: list[dict[str, Any]] = []
        with open(path) as f:
            for line in f:
                if line.strip():
                    decisions.append(json.loads(line))
        return decisions
