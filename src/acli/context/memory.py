"""Cross-session memory manager."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class MemoryManager:
    """Stores and retrieves cross-session facts."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.memory_dir = project_dir / ".acli" / "memory"
        self.memory_file = self.memory_dir / "project_memory.json"
        self._facts: list[dict[str, Any]] = self._load()

    def add_fact(self, category: str, fact: str) -> None:
        """Add a fact to memory."""
        entry = {
            "category": category,
            "fact": fact,
            "timestamp": datetime.now().isoformat(),
        }
        self._facts.append(entry)
        self._save()

    def get_facts(self, category: str | None = None) -> list[dict[str, Any]]:
        """Get facts, optionally filtered by category."""
        if category is None:
            return list(self._facts)
        return [f for f in self._facts if f["category"] == category]

    def get_injection_prompt(self) -> str:
        """Format facts for system prompt injection."""
        if not self._facts:
            return "No project memory yet."
        lines = ["## Project Memory"]
        by_category: dict[str, list[str]] = {}
        for f in self._facts:
            cat = f["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f["fact"])
        for cat, facts in by_category.items():
            lines.append(f"\n### {cat}")
            for fact in facts:
                lines.append(f"- {fact}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all facts."""
        self._facts = []
        self._save()

    @property
    def fact_count(self) -> int:
        """Number of facts stored."""
        return len(self._facts)

    def _load(self) -> list[dict[str, Any]]:
        if not self.memory_file.exists():
            return []
        with open(self.memory_file) as f:
            return json.load(f)

    def _save(self) -> None:
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, "w") as f:
            json.dump(self._facts, f, indent=2)
