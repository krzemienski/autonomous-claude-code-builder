"""Workflow type definitions and configuration."""

from dataclasses import dataclass, field
from enum import StrEnum


class WorkflowType(StrEnum):
    """Classification of user prompts into workflow categories."""

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
    """Configuration produced by prompt classification."""

    workflow_type: WorkflowType
    requires_onboarding: bool
    agent_sequence: list[str] = field(default_factory=list)
    model_tier: str = "sonnet"
    platform: str = "generic"
