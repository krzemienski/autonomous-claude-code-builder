"""
Enhanced Multi-Agent Orchestrator (v2)
======================================

Accepts any prompt, routes to appropriate workflow,
spawns typed agents via AgentFactory.
"""

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..agents.definitions import AgentType
from ..agents.factory import AgentFactory
from ..context.memory import MemoryManager
from ..context.store import ContextStore
from ..routing.router import PromptRouter
from ..routing.workflows import WorkflowConfig
from ..utils import logger
from .session import get_project_state
from .streaming import StreamBuffer, StreamingHandler


class EnhancedOrchestrator:
    """
    v2 orchestrator: accepts any prompt, routes to workflow, spawns agents.

    Backwards-compatible with v1 via run_loop().
    """

    def __init__(
        self,
        project_dir: Path,
        model: str = "claude-sonnet-4-6",
        max_iterations: int | None = None,
    ):
        """Initialize enhanced orchestrator with project directory and model."""
        self.project_dir = project_dir.resolve()
        self.model = model
        self.max_iterations = max_iterations

        self.state = get_project_state(self.project_dir)
        self.buffer = StreamBuffer()
        self.streaming = StreamingHandler(self.buffer)

        # v2 components
        self.router = PromptRouter()
        self.context_store = ContextStore(self.project_dir)
        self.memory_manager = MemoryManager(self.project_dir)
        self.factory = AgentFactory(
            self.project_dir, self.context_store, self.memory_manager
        )

        self._running = False
        self._pause_requested = False
        self._stop_requested = False
        self._current_workflow: WorkflowConfig | None = None
        self._prompt: str = ""

    @property
    def is_running(self) -> bool:
        """Whether the orchestrator is currently running."""
        return self._running

    async def run(self, prompt: str) -> None:
        """Execute full workflow for any prompt."""
        self._running = True
        self._stop_requested = False
        self._prompt = prompt

        try:
            # Route prompt
            self._current_workflow = await self.route_prompt(prompt)
            await self.streaming.handle_phase_start("routing", "Prompt Classification")

            logger.info(f"Workflow: {self._current_workflow.workflow_type.value}")
            logger.info(f"Agent sequence: {self._current_workflow.agent_sequence}")

            await self.streaming.handle_phase_end("routing", "completed")

            # Initialize context store
            self.context_store.initialize()

            # Execute agent sequence (placeholder -- actual SDK calls in future)
            for agent_name in self._current_workflow.agent_sequence:
                if self._stop_requested:
                    break
                while self._pause_requested and not self._stop_requested:
                    await asyncio.sleep(0.5)

                agent_type = self._resolve_agent_type(agent_name)
                if agent_type:
                    await self.streaming.handle_agent_spawn(
                        agent_id=f"{agent_name}_001",
                        agent_type=agent_name,
                        model=self.model,
                    )
                    # Actual agent execution will be wired in Phase 6
                    await self.streaming.handle_agent_complete(
                        agent_id=f"{agent_name}_001",
                        status="completed",
                    )
        finally:
            self._running = False

    async def run_loop(
        self,
        on_session_start: Callable[[int, str], Any] | None = None,
        on_session_end: Callable[[int, str], Any] | None = None,
    ) -> None:
        """Backwards-compatible loop for v1 TUI integration."""
        # Delegate to v1 behavior if no prompt set
        if not self._prompt:
            from .orchestrator_v1 import AgentOrchestrator

            v1 = AgentOrchestrator(
                project_dir=self.project_dir,
                model=self.model,
                max_iterations=self.max_iterations,
            )
            v1.buffer = self.buffer
            v1.streaming = self.streaming
            await v1.run_loop(on_session_start, on_session_end)
        else:
            await self.run(self._prompt)

    async def route_prompt(self, prompt: str) -> WorkflowConfig:
        """Classify prompt into workflow."""
        return self.router.classify(prompt, self.project_dir)

    async def run_analyst(self) -> dict[str, Any]:
        """Run analyst agent -- returns analysis results."""
        definition = self.factory.create_definition(AgentType.ANALYST)
        logger.info(f"Analyst agent: {definition.model}")
        return {"status": "completed", "type": "analyst"}

    async def run_planner(self, workflow: WorkflowConfig, prompt: str) -> dict[str, Any]:
        """Run planner agent -- returns execution plan."""
        definition = self.factory.create_definition(
            AgentType.PLANNER, task_context=prompt
        )
        logger.info(f"Planner agent: {definition.model}")
        return {"status": "completed", "type": "planner", "plan": {}}

    async def run_implementer(self, task: dict[str, Any], context: str) -> tuple[str, str]:
        """Run implementer agent -- returns (status, result)."""
        definition = self.factory.create_definition(
            AgentType.IMPLEMENTER, task_context=context
        )
        logger.info(f"Implementer agent: {definition.model}")
        return ("completed", "implementation_result")

    async def run_validator(self, task: dict[str, Any], result: str) -> dict[str, Any]:
        """Run validator agent -- returns validation results."""
        definition = self.factory.create_definition(AgentType.VALIDATOR)
        logger.info(f"Validator agent: {definition.model}")
        return {"status": "PASS", "type": "validator"}

    async def run_reporter(self, phase: dict[str, Any]) -> str:
        """Run reporter agent -- returns summary."""
        self.factory.create_definition(AgentType.REPORTER)
        return "Phase report generated"

    def request_pause(self) -> None:
        """Request pause after current agent completes."""
        self._pause_requested = True

    def request_stop(self) -> None:
        """Request stop after current agent completes."""
        self._stop_requested = True

    def resume(self) -> None:
        """Resume paused orchestration."""
        self._pause_requested = False

    def on_event(self, event_type: str, handler: Callable[..., Any]) -> None:
        """Register event handler."""
        self.streaming.on(event_type, handler)

    def get_status(self) -> dict[str, Any]:
        """Get current orchestrator status."""
        return {
            "running": self._running,
            "paused": self._pause_requested,
            "project_dir": str(self.project_dir),
            "model": self.model,
            "session_count": self.state.session_count,
            "is_first_run": self.state.is_first_run,
            "workflow": (
                self._current_workflow.workflow_type.value
                if self._current_workflow
                else None
            ),
        }

    @staticmethod
    def _resolve_agent_type(name: str) -> AgentType | None:
        """Map agent name string to AgentType enum."""
        mapping = {
            "analyst": AgentType.ANALYST,
            "planner": AgentType.PLANNER,
            "implementer": AgentType.IMPLEMENTER,
            "validator": AgentType.VALIDATOR,
            "reporter": AgentType.REPORTER,
            "router": AgentType.ROUTER,
            "context_manager": AgentType.CONTEXT_MANAGER,
        }
        return mapping.get(name)
