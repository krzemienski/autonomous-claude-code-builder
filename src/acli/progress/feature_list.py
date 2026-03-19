"""
Feature List Handler
====================

Manages feature_list.json - the source of truth for progress.
"""

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Feature:
    """A single feature/test case."""
    id: int
    component: str
    description: str
    passes: bool = False
    priority: str = "medium"
    attempts: int = 0
    last_attempt: str | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "component": self.component,
            "description": self.description,
            "passes": self.passes,
            "priority": self.priority,
            "attempts": self.attempts,
            "last_attempt": self.last_attempt,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Feature":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            component=data.get("component", "Unknown"),
            description=data.get("description", ""),
            passes=data.get("passes", False),
            priority=data.get("priority", "medium"),
            attempts=data.get("attempts", 0),
            last_attempt=data.get("last_attempt"),
            notes=data.get("notes", ""),
        )


class FeatureList:
    """
    Manager for feature_list.json.

    Provides CRUD operations and progress queries.
    """

    def __init__(self, path: Path):
        self.path = path
        self._features: list[Feature] = []
        self._dirty = False

    @property
    def total(self) -> int:
        """Total number of features."""
        return len(self._features)

    @property
    def passing(self) -> int:
        """Number of passing features."""
        return sum(1 for f in self._features if f.passes)

    @property
    def remaining(self) -> int:
        """Number of remaining features."""
        return self.total - self.passing

    @property
    def percentage(self) -> float:
        """Completion percentage."""
        if self.total == 0:
            return 0.0
        return (self.passing / self.total) * 100

    def load(self) -> None:
        """Load features from file."""
        if not self.path.exists():
            self._features = []
            return

        with open(self.path) as f:
            data = json.load(f)

        # Handle both list and dict formats
        if isinstance(data, list):
            features_data = data
        elif isinstance(data, dict) and "features" in data:
            features_data = data["features"]
        else:
            features_data = []

        self._features = [Feature.from_dict(f) for f in features_data]
        self._dirty = False

    def save(self) -> None:
        """Save features to file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

        data = [f.to_dict() for f in self._features]

        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

        self._dirty = False

    def save_if_dirty(self) -> None:
        """Save only if changes were made."""
        if self._dirty:
            self.save()

    def get(self, feature_id: int) -> Feature | None:
        """Get feature by ID."""
        for f in self._features:
            if f.id == feature_id:
                return f
        return None

    def get_next_incomplete(self) -> Feature | None:
        """Get next incomplete feature (by priority, then ID)."""
        priority_order = {"high": 0, "medium": 1, "low": 2}

        incomplete = [f for f in self._features if not f.passes]
        if not incomplete:
            return None

        # Sort by priority, then by ID
        incomplete.sort(key=lambda f: (priority_order.get(f.priority, 1), f.id))
        return incomplete[0]

    def mark_passing(self, feature_id: int, notes: str = "") -> bool:
        """Mark feature as passing."""
        feature = self.get(feature_id)
        if feature:
            feature.passes = True
            feature.notes = notes
            self._dirty = True
            return True
        return False

    def mark_failed(self, feature_id: int, notes: str = "") -> bool:
        """Mark feature as attempted but not passing."""
        feature = self.get(feature_id)
        if feature:
            feature.attempts += 1
            feature.notes = notes
            from datetime import datetime
            feature.last_attempt = datetime.now().isoformat()
            self._dirty = True
            return True
        return False

    def add(self, feature: Feature) -> None:
        """Add new feature."""
        self._features.append(feature)
        self._dirty = True

    def add_many(self, features: list[Feature]) -> None:
        """Add multiple features."""
        self._features.extend(features)
        self._dirty = True

    def iter_incomplete(self) -> Iterator[Feature]:
        """Iterate over incomplete features."""
        for f in self._features:
            if not f.passes:
                yield f

    def iter_by_component(self, component: str) -> Iterator[Feature]:
        """Iterate features by component."""
        for f in self._features:
            if f.component == component:
                yield f

    def get_components(self) -> list[str]:
        """Get list of unique components."""
        return list(set(f.component for f in self._features))

    def get_summary(self) -> dict[str, Any]:
        """Get progress summary."""
        by_component = {}
        for f in self._features:
            if f.component not in by_component:
                by_component[f.component] = {"total": 0, "passing": 0}
            by_component[f.component]["total"] += 1
            if f.passes:
                by_component[f.component]["passing"] += 1

        return {
            "total": self.total,
            "passing": self.passing,
            "remaining": self.remaining,
            "percentage": self.percentage,
            "by_component": by_component,
        }


def load_feature_list(path: Path | str) -> FeatureList:
    """Load feature list from path."""
    fl = FeatureList(Path(path))
    fl.load()
    return fl


def create_feature_list(path: Path | str, features: list[dict[str, Any]]) -> FeatureList:
    """Create new feature list from data."""
    fl = FeatureList(Path(path))
    fl.add_many([Feature.from_dict(f) for f in features])
    fl.save()
    return fl
