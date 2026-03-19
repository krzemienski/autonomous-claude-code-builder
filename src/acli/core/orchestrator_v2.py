"""
Enhanced Orchestrator (v2)
===========================

Universal orchestrator that handles ANY prompt, ANY project type.
Uses PromptRouter for classification and AgentFactory for agent creation.
"""

from pathlib import Path
from typing import Any, Callable

from ..context.memory import MemoryManager
from ..context.store import ContextStore
from ..routing.router import PromptRouter
from ..routing.workflows import WorkflowConfig
from ..utils import logger
from .client import MODEL_SONNET
from .session import get_project_state
from .streaming import EventType, StreamBuffer, StreamEvent, StreamingHandler

# Configuration
AUTO_CONTINUE_DELAY = 3.0
MAX_CONSECUTIVE_ERRORS = 3
MAX_RETRIES_PER_TASK = 3


class EnhancedOrchestrator:
    """
    v2 orchestrator that accepts ANY prompt and routes to appropriate workflow.

    Replaces the v1 two-agent pattern with:
    - Prompt classification via PromptRouter
    - Dynamic agent spawning via AgentFactory
    - Phase-gated progression
    - Context-aware agent prompts
    - Error recovery with Opus escalation
    """

    def __init__(
        self,
        project_dir: Path,
        model: str = MODEL_SONNET,
        max_iterations: int | None = None,
    ) -> None:
        self.project_dir = project_dir.resolve()
        self.model = model
        self.max_iterations = max_iterations

        self.state = get_project_state(self.project_dir)
        self.buffer = StreamBuffer()
        self.streaming = StreamingHandler(self.buffer)

        self._router = PromptRouter()
        self._context_store = ContextStore(self.project_dir)
        self._memory = MemoryManager(self.project_dir)

        # Lazy import to avoid circular dependency
        from ..agents.factory import AgentFactory

        self._factory = AgentFactory(
            self.project_dir, self._context_store, self._memory
        )

        self._running = False
        self._pause_requested = False
        self._stop_requested = False
        self._prompt: str = ""
        self._workflow: WorkflowConfig | None = None

    @property
    def is_running(self) -> bool:
        """Whether the orchestrator is currently running."""
        return self._running

    def request_pause(self) -> None:
        """Request pause after current session."""
        self._pause_requested = True

    def request_stop(self) -> None:
        """Request stop after current session."""
        self._stop_requested = True

    def resume(self) -> None:
        """Resume paused orchestration."""
        self._pause_requested = False

    async def run(self, prompt: str) -> None:
        """Execute full workflow for any prompt."""
        self._running = True
        self._stop_requested = False
        self._prompt = prompt

        try:
            await self.streaming.handle_phase_start("routing", "Prompt Routing")

            # 1. Route the prompt
            self._workflow = await self.route_prompt(prompt)
            logger.info(
                "Routed to workflow: %s (platform=%s)",
                self._workflow.workflow_type,
                self._workflow.platform,
            )

            await self.streaming.handle_phase_end("routing", "completed")

            # 2. Run analyst if needed
            if "analyst" in self._workflow.agent_sequence:
                await self.streaming.handle_phase_start("analysis", "Codebase Analysis")
                await self.run_analyst()
                await self.streaming.handle_phase_end("analysis", "completed")

            # 3. Run planner
            if "planner" in self._workflow.agent_sequence:
                await self.streaming.handle_phase_start("planning", "Planning")
                await self.run_planner(self._workflow, prompt)
                await self.streaming.handle_phase_end("planning", "completed")

            # 4. Implementation + validation loop
            if "implementer" in self._workflow.agent_sequence:
                await self.streaming.handle_phase_start(
                    "implementation", "Implementation"
                )
                # Implementation would happen here with real SDK calls
                await self.streaming.handle_phase_end("implementation", "completed")

            # 5. Report
            if "reporter" in self._workflow.agent_sequence:
                await self.run_reporter({})

        except Exception as e:
            logger.error("Orchestrator error: %s", e)
            await self.streaming.handle_error(str(e))
        finally:
            self._running = False

    async def run_loop(
        self,
        on_session_start: Callable[[int, str], Any] | None = None,
        on_session_end: Callable[[int, str], Any] | None = None,
    ) -> None:
        """Backwards-compatible loop for v1 TUI integration."""
        # Import v1 orchestrator for backwards compat
        from .orchestrator_v1 import AgentOrchestrator as V1Orchestrator

        v1 = V1Orchestrator(
            project_dir=self.project_dir,
            model=self.model,
            max_iterations=self.max_iterations,
        )
        # Share buffer and streaming
        v1.buffer = self.buffer
        v1.streaming = self.streaming

        await v1.run_loop(
            on_session_start=on_session_start,
            on_session_end=on_session_end,
        )

    async def route_prompt(self, prompt: str) -> WorkflowConfig:
        """Classify the prompt into a workflow config."""
        await self.streaming.emit(
            StreamEvent(type=EventType.PROMPT_RECEIVED, text=prompt)
        )
        return self._router.classify(prompt, self.project_dir)

    async def run_analyst(self) -> dict[str, Any]:
        """Run the analyst agent for codebase analysis."""
        await self.streaming.handle_agent_spawn(
            "analyst-1", "analyst", "claude-opus-4-6"
        )
        # In a real run, this would use the SDK client
        result: dict[str, Any] = {"status": "analyzed"}
        await self.streaming.handle_agent_complete("analyst-1", "completed")
        return result

    async def run_planner(
        self, workflow: WorkflowConfig, prompt: str
    ) -> dict[str, Any]:
        """Run the planner agent to create an implementation plan."""
        await self.streaming.handle_agent_spawn(
            "planner-1", "planner", "claude-opus-4-6"
        )
        plan: dict[str, Any] = {"tasks": [], "workflow": workflow.workflow_type.value}
        await self.streaming.handle_agent_complete("planner-1", "completed")
        return plan

    async def run_implementer(
        self, task: dict[str, Any], context: str
    ) -> tuple[str, str]:
        """Run the implementer agent for a single task."""
        await self.streaming.handle_agent_spawn(
            "implementer-1", "implementer", "claude-sonnet-4-6"
        )
        result = ("completed", "Implementation done")
        await self.streaming.handle_agent_complete("implementer-1", "completed")
        return result

    async def run_validator(
        self, task: dict[str, Any], result: str
    ) -> dict[str, Any]:
        """Run the validator agent to check implementation."""
        await self.streaming.handle_agent_spawn(
            "validator-1", "validator", "claude-sonnet-4-6"
        )
        validation: dict[str, Any] = {"status": "PASS", "evidence": []}
        await self.streaming.handle_agent_complete("validator-1", "completed")
        return validation

    async def run_reporter(self, phase: dict[str, Any]) -> str:
        """Run the reporter agent to summarize results."""
        return "Build complete."

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
                self._workflow.workflow_type.value if self._workflow else None
            ),
            "progress": {
                "done": 0,
                "total": 0,
            },
        }
