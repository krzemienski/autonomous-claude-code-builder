"""Memory manager for accumulating project knowledge across sessions.

Stores facts with categories and timestamps in a single JSON file
under `.acli/memory/project_memory.json`.
"""

import json
from datetime import UTC, datetime
from pathlib import Path


class MemoryManager:
    """Manages categorized project facts for system prompt injection.

    Facts are stored as a flat list with category, content, and timestamp.
    The manager supports filtering by category and producing a formatted
    prompt string suitable for LLM context injection.

    Args:
        project_dir: Root directory of the target project.
    """

    def __init__(self, project_dir: Path) -> None:
        """Initialize memory manager.

        Args:
            project_dir: Root directory of the target project.
        """
        self._memory_path = project_dir / ".acli" / "memory" / "project_memory.json"
        self._data: dict[str, list[dict[str, str]]] = {"facts": []}
        self._load()

    def _load(self) -> None:
        """Load existing memory from disk if available."""
        if self._memory_path.exists():
            content = self._memory_path.read_text(encoding="utf-8").strip()
            if content:
                self._data = json.loads(content)

    def _save(self) -> None:
        """Persist current memory state to disk."""
        self._memory_path.parent.mkdir(parents=True, exist_ok=True)
        self._memory_path.write_text(
            json.dumps(self._data, indent=2, default=str), encoding="utf-8"
        )

    def add_fact(self, category: str, fact: str) -> None:
        """Append a categorized fact with a timestamp.

        Args:
            category: Grouping label (e.g., 'architecture', 'gotcha').
            fact: The knowledge to store.
        """
        entry: dict[str, str] = {
            "category": category,
            "fact": fact,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._data["facts"].append(entry)
        self._save()

    def get_facts(self, category: str | None = None) -> list[dict[str, str]]:
        """Retrieve stored facts, optionally filtered by category.

        Args:
            category: If provided, only return facts in this category.

        Returns:
            List of fact dictionaries with category, fact, and timestamp.
        """
        facts = self._data["facts"]
        if category is not None:
            return [f for f in facts if f["category"] == category]
        return list(facts)

    def get_injection_prompt(self) -> str:
        """Format all stored facts for system prompt injection.

        Returns:
            A formatted string grouping facts by category, suitable
            for inclusion in an LLM system prompt.
        """
        if not self._data["facts"]:
            return ""

        grouped: dict[str, list[str]] = {}
        for entry in self._data["facts"]:
            cat = entry["category"]
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(entry["fact"])

        lines: list[str] = ["# Project Memory"]
        for cat, facts in grouped.items():
            lines.append(f"\n## {cat}")
            for fact in facts:
                lines.append(f"- {fact}")

        return "\n".join(lines)

    def clear(self) -> None:
        """Reset all stored memory."""
        self._data = {"facts": []}
        self._save()

    @property
    def fact_count(self) -> int:
        """Total number of stored facts."""
        return len(self._data["facts"])
