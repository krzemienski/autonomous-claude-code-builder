"""Agent type definitions and pre-configured agent configs.

Each AgentType maps to a specific model, tool set, and prompt template.
Use AgentDefinition.for_type() to get a ready-to-use definition with
optional context, skills, and memory injection.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AgentType(StrEnum):
    """Enumeration of all agent roles in the orchestration pipeline."""

    ROUTER = "router"
    ANALYST = "analyst"
    PLANNER = "planner"
    IMPLEMENTER = "implementer"
    VALIDATOR = "validator"
    CONTEXT_MANAGER = "context_manager"
    REPORTER = "reporter"


AGENT_CONFIGS: dict[AgentType, dict[str, Any]] = {
    AgentType.ROUTER: {
        "model": "claude-sonnet-4-6",
        "max_turns": 10,
        "thinking": {"type": "adaptive"},
        "effort": None,
        "output_budget": 4096,
        "allowed_tools": ["Read", "Glob", "Grep"],
        "prompt_template": (
            "You are a routing agent. Classify the user's prompt into one "
            "of the available workflow types: greenfield, brownfield, spec_enhance, "
            "or monitoring. Respond with a JSON object containing the workflow "
            "type and a brief justification."
        ),
    },
    AgentType.ANALYST: {
        "model": "claude-opus-4-6",
        "max_turns": 50,
        "thinking": {"type": "adaptive"},
        "effort": "high",
        "output_budget": 16384,
        "allowed_tools": ["Read", "Glob", "Grep", "Bash"],
        "prompt_template": (
            "You are a codebase analyst. Examine the project structure, "
            "identify the tech stack, architecture patterns, coding conventions, "
            "and key dependencies. Produce a structured analysis report."
        ),
    },
    AgentType.PLANNER: {
        "model": "claude-opus-4-6",
        "max_turns": 50,
        "thinking": {"type": "adaptive"},
        "effort": "high",
        "output_budget": 32768,
        "allowed_tools": ["Read", "Write", "Glob", "Grep"],
        "prompt_template": (
            "You are a technical planner. Given a codebase analysis and a set "
            "of requirements, produce a detailed implementation plan with phases, "
            "tasks, dependencies, and risk assessment."
        ),
    },
    AgentType.IMPLEMENTER: {
        "model": "claude-sonnet-4-6",
        "max_turns": 200,
        "thinking": {"type": "adaptive"},
        "effort": None,
        "output_budget": 65536,
        "allowed_tools": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
        "prompt_template": (
            "You are an expert implementer. Execute the assigned task from the "
            "implementation plan. Write clean, tested, production-ready code "
            "following the project conventions."
        ),
    },
    AgentType.VALIDATOR: {
        "model": "claude-sonnet-4-6",
        "max_turns": 30,
        "thinking": {"type": "adaptive"},
        "effort": None,
        "output_budget": 8192,
        "allowed_tools": ["Read", "Bash", "Glob", "Grep"],
        "prompt_template": (
            "You are a functional validator. Run the real application, execute "
            "functional tests, and verify that the implementation meets the "
            "acceptance criteria. No mocks or stubs."
        ),
    },
    AgentType.CONTEXT_MANAGER: {
        "model": "claude-sonnet-4-6",
        "max_turns": 20,
        "thinking": {"type": "adaptive"},
        "effort": None,
        "output_budget": 8192,
        "allowed_tools": ["Read", "Write", "Glob", "Grep"],
        "prompt_template": (
            "You are a context manager. Maintain project knowledge across "
            "sessions by reading codebase state, updating memory facts, and "
            "summarizing context for other agents."
        ),
    },
    AgentType.REPORTER: {
        "model": "claude-sonnet-4-6",
        "max_turns": 10,
        "thinking": {"type": "adaptive"},
        "effort": None,
        "output_budget": 8192,
        "allowed_tools": ["Read", "Write"],
        "prompt_template": (
            "You are a reporting agent. Summarize the results of the current "
            "session including completed tasks, validation results, and any "
            "issues encountered."
        ),
    },
}


@dataclass
class AgentDefinition:
    """Complete definition for creating and running an agent.

    Holds model selection, tool permissions, prompt template, and
    configuration for thinking and output budgets.

    Attributes:
        agent_type: The role this agent fulfills.
        model: Claude model identifier to use.
        system_prompt_template: Full system prompt (may include injected context).
        allowed_tools: List of tool names the agent can invoke.
        max_turns: Maximum conversation turns before stopping.
        thinking_config: Configuration for extended thinking.
        effort: Effort level hint (None, "low", "medium", "high").
        output_budget: Maximum output tokens.
    """

    agent_type: AgentType
    model: str
    system_prompt_template: str
    allowed_tools: list[str] = field(default_factory=list)
    max_turns: int = 100
    thinking_config: dict[str, Any] = field(default_factory=dict)
    effort: str | None = None
    output_budget: int = 8192

    @classmethod
    def for_type(
        cls,
        agent_type: AgentType,
        context: str = "",
        skills: str = "",
        memory: str = "",
    ) -> "AgentDefinition":
        """Create a pre-configured definition for the given agent type.

        Optionally injects project context, available skills, and memory
        into the system prompt template.

        Args:
            agent_type: Which agent role to configure.
            context: Project context summary to inject.
            skills: Available skills description to inject.
            memory: Accumulated memory/facts to inject.

        Returns:
            Fully configured AgentDefinition ready for use.
        """
        config = AGENT_CONFIGS[agent_type]
        template = config["prompt_template"]

        if context:
            template += f"\n\n## Project Context\n{context}"
        if skills:
            template += f"\n\n## Available Skills\n{skills}"
        if memory:
            template += f"\n\n## Memory\n{memory}"

        return cls(
            agent_type=agent_type,
            model=config["model"],
            system_prompt_template=template,
            allowed_tools=list(config["allowed_tools"]),
            max_turns=config["max_turns"],
            thinking_config=dict(config["thinking"]),
            effort=config.get("effort"),
            output_budget=config["output_budget"],
        )
