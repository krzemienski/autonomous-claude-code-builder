"""
Workflow Type Definitions
=========================

Defines the workflow types and configurations for prompt routing.
"""

from dataclasses import dataclass, field
from enum import Enum


class WorkflowType(str, Enum):
    """Types of workflows that can be routed to."""

    GREENFIELD_APP = "greenfield_app"
    BROWNFIELD_ONBOARD = "brownfield_onboard"
    BROWNFIELD_TASK = "brownfield_task"
    REFACTOR = "refactor"
    DEBUG = "debug"
    CLI_TOOL = "cli_tool"
    IOS_APP = "ios_app"
    FREE_TASK = "free_task"


@dataclass
class WorkflowConfig:
    """Configuration for a classified workflow."""

    workflow_type: WorkflowType
    requires_onboarding: bool
    agent_sequence: list[str] = field(default_factory=list)
    model_tier: str = "sonnet"
    platform: str = "generic"
