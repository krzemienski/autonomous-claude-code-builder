"""
Prompt Routing Module
=====================

Classifies user prompts into workflow types and configurations.
"""

from .router import PromptRouter
from .workflows import WorkflowConfig, WorkflowType

__all__ = [
    "PromptRouter",
    "WorkflowConfig",
    "WorkflowType",
]
