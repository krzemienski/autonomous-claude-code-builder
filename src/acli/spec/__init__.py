"""Specification enhancement module exports."""

from .schemas import (
    ProjectSpec,
    FeatureSpec,
    Requirement,
    TechStack,
    Priority,
    EnhancementResult,
    ClarificationQuestion,
)
from .enhancer import enhance_spec, refine_spec_with_answers
from .validator import validate_spec, is_spec_complete
from .refinement import (
    interactive_enhancement,
    save_spec_to_file,
    save_feature_list,
)

__all__ = [
    # Schemas
    "ProjectSpec",
    "FeatureSpec",
    "Requirement",
    "TechStack",
    "Priority",
    "EnhancementResult",
    "ClarificationQuestion",
    # Enhancement
    "enhance_spec",
    "refine_spec_with_answers",
    # Validation
    "validate_spec",
    "is_spec_complete",
    # Refinement
    "interactive_enhancement",
    "save_spec_to_file",
    "save_feature_list",
]