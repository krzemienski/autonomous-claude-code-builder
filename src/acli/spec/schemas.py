"""
Specification Schemas
=====================

Pydantic models for structured specification output.
Used with Claude structured outputs for guaranteed schema compliance.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Priority(StrEnum):
    """Feature priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Requirement(BaseModel):
    """A single functional requirement."""

    id: int = Field(..., description="Unique requirement ID")
    description: str = Field(..., min_length=10, max_length=500)
    priority: Priority = Field(default=Priority.MEDIUM)
    acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Testable conditions for this requirement"
    )
    dependencies: list[int] = Field(
        default_factory=list,
        description="IDs of requirements this depends on"
    )


class NonFunctionalConstraint(BaseModel):
    """Non-functional requirement or constraint."""

    category: str = Field(..., description="e.g., performance, security, scalability")
    description: str
    target: str | None = Field(None, description="Measurable target if applicable")


class TechStack(BaseModel):
    """Technology stack specification."""

    language: str = Field(..., description="Primary programming language")
    framework: str | None = Field(None, description="Web/app framework")
    database: str | None = Field(None)
    ui_library: str | None = Field(None)
    testing: str | None = Field(None, description="Testing framework")
    additional: list[str] = Field(default_factory=list)


class FeatureSpec(BaseModel):
    """Enhanced feature specification."""

    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=20)
    user_story: str = Field(
        ...,
        description="As a [WHO], I want [WHAT] so that [WHY]"
    )
    requirements: list[Requirement] = Field(default_factory=list)
    constraints: list[NonFunctionalConstraint] = Field(default_factory=list)
    estimated_hours: float | None = Field(None, ge=0, le=1000)


class ProjectSpec(BaseModel):
    """Complete project specification."""

    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=20)
    tech_stack: TechStack
    features: list[FeatureSpec] = Field(default_factory=list)
    constraints: list[NonFunctionalConstraint] = Field(default_factory=list)

    # Metadata
    version: str = Field(default="1.0.0")
    estimated_total_hours: float | None = None

    def to_feature_list(self) -> list[dict[str, Any]]:
        """Convert to feature_list.json format for agent consumption."""
        features = []
        feature_id = 1

        for feat in self.features:
            for req in feat.requirements:
                for ac in req.acceptance_criteria:
                    features.append({
                        "id": feature_id,
                        "component": feat.name,
                        "description": ac,
                        "passes": False,
                        "priority": req.priority.value,
                    })
                    feature_id += 1

        return features


class ClarificationQuestion(BaseModel):
    """A question to clarify ambiguous spec elements."""

    field: str = Field(..., description="Which field this clarifies")
    question: str
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested answers"
    )
    required: bool = Field(default=False)


class EnhancementResult(BaseModel):
    """Result of spec enhancement pass."""

    spec: ProjectSpec
    completeness_score: float = Field(..., ge=0, le=100)
    clarifications_needed: list[ClarificationQuestion] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
