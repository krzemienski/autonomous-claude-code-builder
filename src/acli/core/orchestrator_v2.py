"""
Enhanced Multi-Agent Orchestrator (v2)
=======================================

Routes prompts, dispatches typed agents, tracks sessions with JSONL logging.
Backwards-compatible with v1 AgentOrchestrator interface.
"""

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..agents.factory import AgentFactory
from ..context.memory import MemoryManager
from ..context.store import ContextStore
from ..routing.router import PromptRouter
from ..routing.workflows import WorkflowConfig
from ..utils import logger
from .agent import load_prompt_template, run_agent_session
from .client import create_sdk_client
from .session import SessionLogger, get_project_state
from .streaming import StreamBuffer, StreamingHandler

# Configuration
AUTO_CONTINUE_DELAY = 3.0
MAX_CONSECUTIVE_ERRORS = 3


class EnhancedOrchestrator:
    """
    v2 orchestrator with prompt routing, typed agents, and JSONL logging.

    Backwards-compatible: exposes same run_loop/get_status interface as v1.
    """

    def __init__(
        self,
        project_dir: Path,
        model: str = "claude-sonnet-4-6",
        max_iterations: int | None = None,
    ) -> None:
        self.project_dir = project_dir.resolve()
        self.model = model
        self.max_iterations = max_iterations

        self.state = get_project_state(self.project_dir)
        self.buffer = StreamBuffer()
        self.streaming = StreamingHandler(self.buffer)

        self.context_store = ContextStore(self.project_dir)
        self.memory_manager = MemoryManager(self.project_dir)
        self.router = PromptRouter()
        self.factory = AgentFactory(
            self.project_dir, self.context_store, self.memory_manager,
        )

        self._running = False
        self._pause_requested = False
        self._stop_requested = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_first_run(self) -> bool:
        return self.state.is_first_run

    def request_pause(self) -> None:
        self._pause_requested = True

    def request_stop(self) -> None:
        self._stop_requested = True

    def resume(self) -> None:
        self._pause_requested = False

    def on_event(self, event_type: str, handler: Callable[..., Any]) -> None:
        self.streaming.on(event_type, handler)

    async def route_prompt(self, prompt: str) -> WorkflowConfig:
        """Classify a prompt into a workflow configuration."""
        return self.router.classify(prompt, self.project_dir)

    async def run_analyst(self) -> dict[str, Any]:
        """Run the analyst agent for codebase analysis."""
        await self.streaming.handle_agent_spawn("analyst-1", "analyst", "opus")
        # Placeholder — real implementation calls SDK client
        result = {"status": "analyzed", "files": 0}
        await self.streaming.handle_agent_complete("analyst-1", "completed")
        return result

    async def run_planner(
        self, workflow: WorkflowConfig, prompt: str,
    ) -> dict[str, Any]:
        """Run the planner agent to create implementation plan."""
        await self.streaming.handle_agent_spawn("planner-1", "planner", "opus")
        result = {"status": "planned", "tasks": []}
        await self.streaming.handle_agent_complete("planner-1", "completed")
        return result

    async def run_implementer(
        self, task: str, context: str,
    ) -> tuple[str, str]:
        """Run the implementer agent on a single task."""
        await self.streaming.handle_agent_spawn("impl-1", "implementer", "sonnet")
        status, response = "completed", "Implementation placeholder"
        await self.streaming.handle_agent_complete("impl-1", status)
        return status, response

    async def run_validator(
        self, task: str, result: str,
    ) -> dict[str, Any]:
        """Run the validator agent on implementation results."""
        await self.streaming.handle_agent_spawn("val-1", "validator", "sonnet")
        validation = {"passed": True, "evidence": []}
        await self.streaming.handle_agent_complete("val-1", "completed")
        return validation

    async def run_reporter(self, phase: str) -> str:
        """Run the reporter agent for phase summary."""
        return f"Phase {phase} complete."

    async def run(self, prompt: str) -> None:
        """Run the full agent pipeline for a given prompt."""
        self._running = True
        try:
            workflow = await self.route_prompt(prompt)
            await self.streaming.handle_phase_start("routing", "Prompt Classification")

            if workflow.requires_onboarding and not self.context_store.is_onboarded():
                await self.streaming.handle_phase_start("onboard", "Codebase Onboarding")
                await self.run_analyst()
                await self.streaming.handle_phase_end("onboard", "completed")

            await self.streaming.handle_phase_start("planning", "Task Planning")
            plan = await self.run_planner(workflow, prompt)
            await self.streaming.handle_phase_end("planning", "completed")

            for i, task in enumerate(plan.get("tasks", [prompt])):
                task_str = task if isinstance(task, str) else str(task)
                await self.streaming.handle_phase_start(
                    f"impl-{i}", f"Implementing: {task_str[:50]}",
                )
                status, response = await self.run_implementer(task_str, "")
                if status == "completed":
                    await self.run_validator(task_str, response)
                await self.streaming.handle_phase_end(f"impl-{i}", status)

            report = await self.run_reporter("all")
            self.memory_manager.add_fact("session", f"Completed: {prompt[:100]}")
        finally:
            self._running = False

    async def run_loop(
        self,
        on_session_start: Callable[[int, str], Any] | None = None,
        on_session_end: Callable[[int, str], Any] | None = None,
    ) -> None:
        """
        v1-compatible loop: reads app_spec.txt, runs sessions.

        Falls back to v1 two-agent pattern (initializer + coding) when
        no prompt routing is needed.
        """
        self._running = True
        self._stop_requested = False
        consecutive_errors = 0
        iteration = 0

        logger.info(f"Starting v2 autonomous loop in {self.project_dir}")
        logger.info(f"Model: {self.model}")

        try:
            while not self._stop_requested:
                iteration += 1

                if self.max_iterations and iteration > self.max_iterations:
                    logger.info(f"Reached max iterations ({self.max_iterations})")
                    break

                if self._pause_requested:
                    logger.info("Paused. Call resume() to continue.")
                    while self._pause_requested and not self._stop_requested:
                        await asyncio.sleep(0.5)
                    if self._stop_requested:
                        break

                session = self.state.start_session()
                session_logger = SessionLogger(self.project_dir, str(session.session_id))
                session_logger.log_event("session_start", {
                    "session_type": session.session_type,
                    "model": self.model,
                    "iteration": iteration,
                })

                logger.info(f"Session {session.session_id}: {session.session_type}")
                await self.streaming.handle_session_start(
                    session.session_id, session.session_type,
                )

                if on_session_start:
                    await _maybe_await(
                        on_session_start(session.session_id, session.session_type),
                    )

                prompt_name = (
                    "initializer" if session.session_type == "initializer" else "coding"
                )
                prompt = load_prompt_template(prompt_name)
                client = create_sdk_client(self.project_dir, self.model)

                async with client:
                    status, response = await run_agent_session(
                        client, prompt, self.streaming,
                    )

                session_logger.log_event("session_end", {
                    "status": status,
                    "response_length": len(response),
                })
                session_logger.close()

                if status == "error":
                    consecutive_errors += 1
                    self.state.end_session(status="error", errors=[response])
                    logger.warning(
                        f"Session error ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})",
                    )
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        logger.error("Too many consecutive errors, stopping")
                        break
                else:
                    consecutive_errors = 0
                    self.state.end_session(status="completed")

                await self.streaming.handle_session_end(session.session_id)

                if on_session_end:
                    await _maybe_await(on_session_end(session.session_id, status))

                self.state.save()

                progress = self._get_progress()
                if progress:
                    await self.streaming.handle_progress(progress[0], progress[1])

                if not self._stop_requested:
                    logger.info(f"Next session in {AUTO_CONTINUE_DELAY}s...")
                    await asyncio.sleep(AUTO_CONTINUE_DELAY)

        finally:
            self._running = False
            self.state.save()
            logger.info("v2 autonomous loop ended")

    def _get_progress(self) -> tuple[int, int] | None:
        """Get current progress from feature_list.json."""
        feature_file = self.project_dir / "feature_list.json"
        if not feature_file.exists():
            return None
        try:
            import json
            with open(feature_file) as f:
                features = json.load(f)
            total = len(features)
            passing = sum(1 for feat in features if feat.get("passes", False))
            return passing, total
        except Exception:
            return None

    def get_status(self) -> dict[str, Any]:
        """Get current orchestrator status (v1-compatible)."""
        progress = self._get_progress()
        return {
            "running": self._running,
            "paused": self._pause_requested,
            "project_dir": str(self.project_dir),
            "model": self.model,
            "session_count": self.state.session_count,
            "is_first_run": self.is_first_run,
            "progress": {
                "done": progress[0] if progress else 0,
                "total": progress[1] if progress else 0,
            },
        }


async def _maybe_await(result: Any) -> Any:
    """Await if coroutine, otherwise return."""
    if asyncio.iscoroutine(result):
        return await result
    return result
