"""
Agent Factory
=============

Creates configured SDK clients for each agent type with context injection.
"""

from pathlib import Path

from ..context.memory import MemoryManager
from ..context.store import ContextStore
from ..core.client import create_sdk_client
from .definitions import AgentDefinition, AgentType

try:
    from claude_agent_sdk import ClaudeSDKClient
except ImportError:
    ClaudeSDKClient = None  # type: ignore[assignment, misc]


class AgentFactory:
    """
    Creates configured SDK clients for each agent type.

    Injects:
    - Context from ContextStore (codebase knowledge)
    - Memory from MemoryManager (cross-session facts)
    - Skills from SkillEngine (auto-detected)
    - Security hooks (bash validation + mock detection)
    """

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
        self, agent_type: AgentType, task_context: str = ""
    ) -> "ClaudeSDKClient":
        """Create a fully configured agent client."""
        definition = AgentDefinition.for_type(agent_type)
        system_prompt = self._build_system_prompt(definition, task_context)

        return create_sdk_client(
            project_dir=self.project_dir,
            model=definition.model,
            system_prompt=system_prompt,
        )

    def _build_system_prompt(
        self, definition: AgentDefinition, task_context: str
    ) -> str:
        """Build system prompt with context, memory, and skill injection."""
        context_summary = self.context_store.get_context_summary()
        memory_injection = self.memory_manager.get_injection_prompt()

        # Format template with available data
        prompt = definition.system_prompt_template.format(
            context=context_summary,
            memory=memory_injection,
            skills="",
        )

        if task_context:
            prompt += f"\n\n## Current Task\n{task_context}"

        return prompt
