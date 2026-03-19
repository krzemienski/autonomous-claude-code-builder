"""Agent factory — creates configured SDK clients from agent definitions."""

from pathlib import Path

from ..context.memory import MemoryManager
from ..context.store import ContextStore
from ..core.client import create_sdk_client
from .definitions import AgentDefinition, AgentType


class AgentFactory:
    """Creates configured ClaudeSDKClient instances for each agent type."""

    def __init__(
        self,
        project_dir: Path,
        context_store: ContextStore,
        memory_manager: MemoryManager,
    ) -> None:
        self.project_dir = project_dir
        self.context_store = context_store
        self.memory_manager = memory_manager

    def create_agent(
        self,
        agent_type: AgentType,
        task_context: str = "",
    ) -> "ClaudeSDKClient":
        """Create a configured SDK client for the given agent type.

        Returns a ClaudeSDKClient ready for use in an async context manager.
        """
        definition = AgentDefinition.for_type(agent_type)
        system_prompt = self._build_system_prompt(definition, task_context)

        model_tier = "opus" if "opus" in definition.model else "sonnet"

        return create_sdk_client(
            project_dir=self.project_dir,
            model=definition.model,
            system_prompt=system_prompt,
            model_tier=model_tier,
        )

    def _build_system_prompt(
        self,
        definition: AgentDefinition,
        task_context: str = "",
    ) -> str:
        """Build full system prompt by injecting context, memory, and task."""
        context_summary = self.context_store.get_context_summary()
        memory_prompt = self.memory_manager.get_injection_prompt()

        prompt = definition.system_prompt_template
        prompt = prompt.replace("{context}", context_summary)
        prompt = prompt.replace("{memory}", memory_prompt)
        prompt = prompt.replace("{skills}", "")  # Skills injected by skill engine
        prompt = prompt.replace("{task}", task_context)

        return prompt


# Re-export for type checking
from claude_agent_sdk import ClaudeSDKClient as ClaudeSDKClient  # noqa: E402, F811
