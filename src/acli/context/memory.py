"""
Memory Manager
==============

Cross-session memory — facts that persist across agent sessions.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class MemoryManager:
    """
    Cross-session memory — facts that persist across agent sessions.

    Stores to .acli/memory/project_memory.json
    """

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self._memory_dir = project_dir / ".acli" / "memory"
        self._memory_file = self._memory_dir / "project_memory.json"
        self._facts: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        """Load existing facts from disk."""
        if self._memory_file.exists():
            try:
                with open(self._memory_file) as f:
                    data = json.load(f)
                self._facts = data.get("facts", [])
            except (json.JSONDecodeError, OSError):
                self._facts = []

    def _save(self) -> None:
        """Save facts to disk."""
        self._memory_dir.mkdir(parents=True, exist_ok=True)
        data = {"facts": self._facts}
        with open(self._memory_file, "w") as f:
            json.dump(data, f, indent=2)

    def add_fact(self, category: str, fact: str) -> None:
        """Add a new fact to memory."""
        entry = {
            "category": category,
            "fact": fact,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._facts.append(entry)
        self._save()

    def get_facts(self, category: str | None = None) -> list[dict[str, Any]]:
        """Get facts, optionally filtered by category."""
        if category is None:
            return list(self._facts)
        return [f for f in self._facts if f.get("category") == category]

    def get_injection_prompt(self) -> str:
        """Formatted text for system prompt injection."""
        if not self._facts:
            return ""

        lines = ["## Project Memory (cross-session facts)", ""]
        categories: dict[str, list[str]] = {}
        for entry in self._facts:
            cat = entry.get("category", "general")
            categories.setdefault(cat, []).append(entry.get("fact", ""))

        for cat, facts in categories.items():
            lines.append(f"### {cat}")
            for fact in facts:
                lines.append(f"- {fact}")
            lines.append("")

        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all memory facts."""
        self._facts = []
        self._save()

    @property
    def fact_count(self) -> int:
        """Total number of stored facts."""
        return len(self._facts)
