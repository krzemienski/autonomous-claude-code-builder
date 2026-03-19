"""Agent type definitions and system prompt templates."""

from dataclasses import dataclass, field
from enum import Enum

from ..core.client import MODEL_OPUS, MODEL_SONNET


class AgentType(str, Enum):
    """Available agent types in the ACLI v2 orchestration pipeline."""

    ROUTER = "router"
    ANALYST = "analyst"
    PLANNER = "planner"
    IMPLEMENTER = "implementer"
    VALIDATOR = "validator"
    CONTEXT_MANAGER = "context_manager"
    REPORTER = "reporter"


# Model assignments per agent type
_MODEL_MAP: dict[AgentType, str] = {
    AgentType.ROUTER: MODEL_SONNET,
    AgentType.ANALYST: MODEL_OPUS,
    AgentType.PLANNER: MODEL_OPUS,
    AgentType.IMPLEMENTER: MODEL_SONNET,
    AgentType.VALIDATOR: MODEL_SONNET,
    AgentType.CONTEXT_MANAGER: MODEL_SONNET,
    AgentType.REPORTER: MODEL_SONNET,
}

# Effort config per agent type
_EFFORT_MAP: dict[AgentType, str | None] = {
    AgentType.ROUTER: None,
    AgentType.ANALYST: "high",
    AgentType.PLANNER: "high",
    AgentType.IMPLEMENTER: None,
    AgentType.VALIDATOR: None,
    AgentType.CONTEXT_MANAGER: None,
    AgentType.REPORTER: None,
}

# System prompt templates per agent type
_PROMPT_TEMPLATES: dict[AgentType, str] = {
    AgentType.ROUTER: (
        "<role>You are a prompt router. Classify the user's request into a workflow type.</role>\n"
        "<context>{context}</context>\n"
        "<task>{task}</task>\n"
    ),
    AgentType.ANALYST: (
        "<role>You are an expert code analyst. Analyze the codebase thoroughly.</role>\n"
        "<context>{context}</context>\n"
        "<skills>{skills}</skills>\n"
        "<memory>{memory}</memory>\n"
        "<iron_rule>NEVER create mocks, stubs, or test files. Analyze the REAL codebase.</iron_rule>\n"
        "<task>{task}</task>\n"
        "<validation_criteria>Produce actionable findings with file paths and line numbers.</validation_criteria>\n"
    ),
    AgentType.PLANNER: (
        "<role>You are an expert software architect and planner.</role>\n"
        "<context>{context}</context>\n"
        "<skills>{skills}</skills>\n"
        "<memory>{memory}</memory>\n"
        "<iron_rule>Every plan MUST include functional validation gates. NO mock-based testing.</iron_rule>\n"
        "<task>{task}</task>\n"
        "<constraints>Plans must be executable by a single coding agent session.</constraints>\n"
    ),
    AgentType.IMPLEMENTER: (
        "<role>You are an expert full-stack developer.</role>\n"
        "<context>{context}</context>\n"
        "<skills>{skills}</skills>\n"
        "<memory>{memory}</memory>\n"
        "<iron_rule>Write production code. NEVER create test files, mocks, or stubs.</iron_rule>\n"
        "<task>{task}</task>\n"
        "<validation_criteria>Code compiles, runs, and passes functional validation.</validation_criteria>\n"
    ),
    AgentType.VALIDATOR: (
        "<role>You are a functional validation expert.</role>\n"
        "<context>{context}</context>\n"
        "<skills>{skills}</skills>\n"
        "<iron_rule>Validate through REAL system execution only. NO mocks, NO unit tests.</iron_rule>\n"
        "<task>{task}</task>\n"
        "<validation_criteria>Capture real CLI output, screenshots, or logs as evidence.</validation_criteria>\n"
    ),
    AgentType.CONTEXT_MANAGER: (
        "<role>You are a codebase context analyst.</role>\n"
        "<context>{context}</context>\n"
        "<task>{task}</task>\n"
    ),
    AgentType.REPORTER: (
        "<role>You are a concise technical reporter.</role>\n"
        "<context>{context}</context>\n"
        "<task>{task}</task>\n"
        "<constraints>Reports must be under 200 lines. Sacrifice grammar for concision.</constraints>\n"
    ),
}

# Default tool allowlists per agent type
_TOOLS_MAP: dict[AgentType, list[str]] = {
    AgentType.ROUTER: ["Read", "Glob", "Grep"],
    AgentType.ANALYST: ["Read", "Glob", "Grep", "Bash"],
    AgentType.PLANNER: ["Read", "Glob", "Grep", "Write"],
    AgentType.IMPLEMENTER: ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    AgentType.VALIDATOR: ["Read", "Glob", "Grep", "Bash"],
    AgentType.CONTEXT_MANAGER: ["Read", "Glob", "Grep"],
    AgentType.REPORTER: ["Read", "Glob", "Grep", "Write"],
}


@dataclass
class AgentDefinition:
    """Complete definition for an agent instance."""

    agent_type: AgentType
    model: str
    system_prompt_template: str
    allowed_tools: list[str] = field(default_factory=list)
    max_turns: int = 200
    thinking_config: dict[str, str] = field(default_factory=lambda: {"type": "adaptive"})
    effort: str | None = None

    @classmethod
    def for_type(
        cls,
        agent_type: AgentType,
        context: str = "",
        skills: str = "",
        memory: str = "",
    ) -> "AgentDefinition":
        """Factory method to create a definition for a given agent type."""
        return cls(
            agent_type=agent_type,
            model=_MODEL_MAP[agent_type],
            system_prompt_template=_PROMPT_TEMPLATES[agent_type],
            allowed_tools=list(_TOOLS_MAP[agent_type]),
            effort=_EFFORT_MAP[agent_type],
        )
