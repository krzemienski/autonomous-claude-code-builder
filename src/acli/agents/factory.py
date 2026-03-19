"""Agent factory for creating configured agent definitions.

Creates agents with injected project context, accumulated memory,
and skill metadata. Serves as the single entry point for agent
creation in the orchestrator.
"""

from pathlib import Path

from ..context.memory import MemoryManager
from ..context.store import ContextStore
from .definitions import AgentDefinition, AgentType


class AgentFactory:
    """Creates configured agents with context, memory, and skill injection.

    The factory reads project state from ContextStore and MemoryManager
    to produce AgentDefinitions whose system prompts include relevant
    project knowledge.

    Args:
        project_dir: Root directory of the target project.
        context_store: Persistent store for codebase analysis data.
        memory_manager: Manager for accumulated project facts.
    """

    def __init__(
        self,
        project_dir: Path,
        context_store: ContextStore,
        memory_manager: MemoryManager,
    ) -> None:
        """Initialize factory with project dependencies.

        Args:
            project_dir: Root directory of the target project.
            context_store: Persistent store for codebase analysis data.
            memory_manager: Manager for accumulated project facts.
        """
        self.project_dir = project_dir
        self.context_store = context_store
        self.memory_manager = memory_manager

    def create_definition(
        self,
        agent_type: AgentType,
        task_context: str = "",
    ) -> AgentDefinition:
        """Create a fully configured agent definition with injected context.

        Reads current project context and memory, then produces an
        AgentDefinition with everything baked into the system prompt.

        Args:
            agent_type: Which agent role to create.
            task_context: Optional task-specific context to append.

        Returns:
            AgentDefinition with context, memory, and prompt assembled.
        """
        context = self.context_store.get_context_summary()
        memory = self.memory_manager.get_injection_prompt()

        definition = AgentDefinition.for_type(
            agent_type,
            context=context,
            skills="",
            memory=memory,
        )

        if task_context:
            definition = AgentDefinition(
                agent_type=definition.agent_type,
                model=definition.model,
                system_prompt_template=(
                    definition.system_prompt_template
                    + f"\n\n## Current Task\n{task_context}"
                ),
                allowed_tools=list(definition.allowed_tools),
                max_turns=definition.max_turns,
                thinking_config=dict(definition.thinking_config),
                effort=definition.effort,
                output_budget=definition.output_budget,
            )

        return definition

    def _build_system_prompt(
        self,
        definition: AgentDefinition,
        task_context: str = "",
    ) -> str:
        """Build final system prompt with optional task context appended.

        Args:
            definition: The agent definition containing the base prompt.
            task_context: Optional task-specific context to append.

        Returns:
            Complete system prompt string ready for the LLM.
        """
        prompt = definition.system_prompt_template
        if task_context:
            prompt += f"\n\n## Current Task\n{task_context}"
        return prompt
