"""
Multi-Agent Orchestrator
========================

Coordinates the 2-agent pattern (initializer + coding) with
session management and automatic continuation.
"""

import asyncio
from pathlib import Path
from typing import Any, Callable

from ..utils import logger
from .agent import load_prompt_template, run_agent_session
from .client import create_sdk_client
from .session import get_project_state
from .streaming import StreamBuffer, StreamingHandler

# Configuration
AUTO_CONTINUE_DELAY = 3.0  # seconds between sessions
MAX_CONSECUTIVE_ERRORS = 3


class AgentOrchestrator:
    """
    Orchestrates autonomous coding agent loop.

    Manages:
    - Session lifecycle (start, run, end)
    - Two-agent pattern (initializer vs coding)
    - Automatic continuation
    - Error recovery
    """

    def __init__(
        self,
        project_dir: Path,
        model: str = "claude-sonnet-4-6",
        max_iterations: int | None = None,
    ):
        self.project_dir = project_dir.resolve()
        self.model = model
        self.max_iterations = max_iterations

        self.state = get_project_state(self.project_dir)
        self.buffer = StreamBuffer()
        self.streaming = StreamingHandler(self.buffer)

        self._running = False
        self._pause_requested = False
        self._stop_requested = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_first_run(self) -> bool:
        """Check if this is first run (no feature_list.json)."""
        return self.state.is_first_run

    def request_pause(self) -> None:
        """Request pause after current session."""
        self._pause_requested = True

    def request_stop(self) -> None:
        """Request stop after current session."""
        self._stop_requested = True

    def resume(self) -> None:
        """Resume paused orchestration."""
        self._pause_requested = False

    def on_event(self, event_type: str, handler: Callable[..., Any]) -> None:
        """Register event handler."""
        self.streaming.on(event_type, handler)

    async def run_loop(
        self,
        on_session_start: Callable[[int, str], Any] | None = None,
        on_session_end: Callable[[int, str], Any] | None = None,
    ) -> None:
        """
        Run the autonomous agent loop.

        Args:
            on_session_start: Called when session starts (session_id, type)
            on_session_end: Called when session ends (session_id, status)
        """
        self._running = True
        self._stop_requested = False
        consecutive_errors = 0

        logger.info(f"Starting autonomous loop in {self.project_dir}")
        logger.info(f"Model: {self.model}")
        logger.info(f"Max iterations: {self.max_iterations or 'unlimited'}")

        iteration = 0

        try:
            while not self._stop_requested:
                iteration += 1

                # Check max iterations
                if self.max_iterations and iteration > self.max_iterations:
                    logger.info(f"Reached max iterations ({self.max_iterations})")
                    break

                # Check pause
                if self._pause_requested:
                    logger.info("Paused. Call resume() to continue.")
                    while self._pause_requested and not self._stop_requested:
                        await asyncio.sleep(0.5)
                    if self._stop_requested:
                        break

                # Start session
                session = self.state.start_session()
                logger.info(f"Session {session.session_id}: {session.session_type}")

                await self.streaming.handle_session_start(
                    session.session_id,
                    session.session_type,
                )

                if on_session_start:
                    await _maybe_await(
                        on_session_start(
                            session.session_id,
                            session.session_type,
                        )
                    )

                # Get prompt
                prompt_name = (
                    "initializer" if session.session_type == "initializer" else "coding"
                )
                prompt = load_prompt_template(prompt_name)

                # Create client (fresh context)
                client = create_sdk_client(
                    self.project_dir,
                    self.model,
                )

                # Run session
                async with client:
                    status, response = await run_agent_session(
                        client,
                        prompt,
                        self.streaming,
                    )

                # Handle result
                if status == "error":
                    consecutive_errors += 1
                    self.state.end_session(status="error", errors=[response])
                    logger.warning(
                        f"Session error ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})"
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

                # Save state
                self.state.save()

                # Update progress
                progress = self._get_progress()
                if progress:
                    await self.streaming.handle_progress(progress[0], progress[1])

                # Auto-continue delay
                if not self._stop_requested:
                    logger.info(f"Next session in {AUTO_CONTINUE_DELAY}s...")
                    await asyncio.sleep(AUTO_CONTINUE_DELAY)

        finally:
            self._running = False
            self.state.save()
            logger.info("Autonomous loop ended")

    async def run_single_session(self) -> tuple[str, str]:
        """Run a single session (for testing/debugging)."""
        session = self.state.start_session()

        prompt_name = (
            "initializer" if session.session_type == "initializer" else "coding"
        )
        prompt = load_prompt_template(prompt_name)

        client = create_sdk_client(self.project_dir, self.model)

        async with client:
            status, response = await run_agent_session(
                client,
                prompt,
                self.streaming,
            )

        self.state.end_session(status=status)
        self.state.save()

        return status, response

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
            passing = sum(1 for f in features if f.get("passes", False))
            return passing, total
        except Exception:
            return None

    def get_status(self) -> dict[str, Any]:
        """Get current orchestrator status."""
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


async def run_autonomous_agent(
    project_dir: Path,
    model: str = "claude-sonnet-4-6",
    max_iterations: int | None = None,
) -> None:
    """
    Convenience function to run autonomous agent.

    Args:
        project_dir: Project directory
        model: Claude model
        max_iterations: Max sessions (None = unlimited)
    """
    orchestrator = AgentOrchestrator(
        project_dir=project_dir,
        model=model,
        max_iterations=max_iterations,
    )

    await orchestrator.run_loop()
