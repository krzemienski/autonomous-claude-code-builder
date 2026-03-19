"""
Agent Type Definitions
======================

Defines the 7 agent types with model assignments, prompt templates,
tool permissions, and thinking configurations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..core.client import MODEL_OPUS, MODEL_SONNET, THINKING_OPUS, THINKING_SONNET


class AgentType(str, Enum):
    """Types of agents in the v2 orchestrator."""

    ROUTER = "router"
    ANALYST = "analyst"
    PLANNER = "planner"
    IMPLEMENTER = "implementer"
    VALIDATOR = "validator"
    CONTEXT_MANAGER = "context_manager"
    REPORTER = "reporter"


# Model assignments per agent type
_AGENT_MODELS: dict[AgentType, str] = {
    AgentType.ROUTER: MODEL_SONNET,
    AgentType.ANALYST: MODEL_OPUS,
    AgentType.PLANNER: MODEL_OPUS,
    AgentType.IMPLEMENTER: MODEL_SONNET,
    AgentType.VALIDATOR: MODEL_SONNET,
    AgentType.CONTEXT_MANAGER: MODEL_OPUS,
    AgentType.REPORTER: MODEL_SONNET,
}

# Max turns per agent type
_AGENT_MAX_TURNS: dict[AgentType, int] = {
    AgentType.ROUTER: 10,
    AgentType.ANALYST: 50,
    AgentType.PLANNER: 30,
    AgentType.IMPLEMENTER: 200,
    AgentType.VALIDATOR: 50,
    AgentType.CONTEXT_MANAGER: 30,
    AgentType.REPORTER: 20,
}

# Allowed tools per agent type
_AGENT_TOOLS: dict[AgentType, list[str]] = {
    AgentType.ROUTER: ["Read", "Glob"],
    AgentType.ANALYST: ["Read", "Glob", "Grep", "Bash"],
    AgentType.PLANNER: ["Read", "Glob", "Grep", "Write"],
    AgentType.IMPLEMENTER: ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    AgentType.VALIDATOR: ["Read", "Glob", "Grep", "Bash"],
    AgentType.CONTEXT_MANAGER: ["Read", "Glob", "Grep", "Write"],
    AgentType.REPORTER: ["Read", "Glob", "Write"],
}

# System prompt templates
_SYSTEM_PROMPTS: dict[AgentType, str] = {
    AgentType.ROUTER: (
        "You are a prompt router. Classify the user's request into a workflow type "
        "and determine the best agent sequence to handle it."
    ),
    AgentType.ANALYST: (
        "You are an expert code analyst. Analyze the codebase deeply — understand "
        "architecture, patterns, dependencies, and constraints.\n\n{context}\n\n{memory}"
    ),
    AgentType.PLANNER: (
        "You are an expert software architect. Create detailed implementation plans "
        "with validation gates for each task.\n\n{context}\n\n{memory}\n\n{skills}"
    ),
    AgentType.IMPLEMENTER: (
        "You are an expert full-stack developer. Implement features according to the "
        "plan. Write clean, production-quality code. Never write tests or mocks.\n\n"
        "{context}\n\n{memory}\n\n{skills}"
    ),
    AgentType.VALIDATOR: (
        "You are a validation engineer. Verify implementations by running real commands "
        "and collecting evidence. Never use mocks or test frameworks.\n\n{context}\n\n{skills}"
    ),
    AgentType.CONTEXT_MANAGER: (
        "You are a codebase context manager. Analyze the project structure, detect "
        "tech stack, conventions, and architecture patterns.\n\n{context}"
    ),
    AgentType.REPORTER: (
        "You are a build reporter. Summarize completed work, validation results, "
        "and remaining tasks.\n\n{context}\n\n{memory}"
    ),
}


@dataclass
class AgentDefinition:
    """Complete definition for creating an agent."""

    agent_type: AgentType
    model: str
    system_prompt_template: str
    allowed_tools: list[str] = field(default_factory=list)
    max_turns: int = 100
    thinking_config: dict[str, Any] = field(default_factory=dict)
    output_budget: int = 16000

    @classmethod
    def for_type(
        cls,
        agent_type: AgentType,
        context: str = "",
        skills: str = "",
        memory: str = "",
    ) -> "AgentDefinition":
        """Factory method returning pre-configured definition for agent type."""
        model = _AGENT_MODELS.get(agent_type, MODEL_SONNET)
        thinking = THINKING_OPUS if "opus" in model else THINKING_SONNET

        template = _SYSTEM_PROMPTS.get(agent_type, "You are an AI assistant.")

        return cls(
            agent_type=agent_type,
            model=model,
            system_prompt_template=template,
            allowed_tools=_AGENT_TOOLS.get(agent_type, []),
            max_turns=_AGENT_MAX_TURNS.get(agent_type, 100),
            thinking_config=dict(thinking),
            output_budget=32000 if "opus" in model else 16000,
        )
