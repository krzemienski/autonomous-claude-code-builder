"""
Orchestrator Bridge
====================

Direct connection between the TUI and the real ACLI orchestrator.
No mocks. No fakes. Reads live StreamBuffer events and orchestrator state.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from ..core.orchestrator import AgentOrchestrator
from ..core.session import get_project_state
from ..core.streaming import EventType, StreamBuffer, StreamEvent

logger = logging.getLogger(__name__)


@dataclass
class AgentNode:
    """Represents a single agent in the hierarchy."""

    agent_id: str
    agent_type: str  # "orchestrator", "initializer", "coding"
    status: str = "idle"  # idle, running, completed, error, paused
    session_id: int = 0
    start_time: datetime | None = None
    end_time: datetime | None = None
    tool_calls: int = 0
    current_tool: str = ""
    features_done: int = 0
    features_total: int = 0
    errors: list[str] = field(default_factory=list)
    children: list["AgentNode"] = field(default_factory=list)
    last_text: str = ""

    @property
    def duration_seconds(self) -> float:
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    @property
    def is_active(self) -> bool:
        return self.status in ("running",)


@dataclass
class OrchestratorSnapshot:
    """Point-in-time snapshot of the full orchestrator state."""

    timestamp: datetime = field(default_factory=datetime.now)
    running: bool = False
    paused: bool = False
    project_dir: str = ""
    model: str = ""
    session_count: int = 0
    is_first_run: bool = True
    features_done: int = 0
    features_total: int = 0
    current_session_id: int = 0
    current_session_type: str = ""
    agents: list[AgentNode] = field(default_factory=list)
    total_tool_calls: int = 0
    total_errors: int = 0
    events_processed: int = 0


class OrchestratorBridge:
    """
    Bridge between the real ACLI orchestrator and the TUI.

    Consumes the orchestrator's StreamBuffer directly and maintains
    a live agent hierarchy model that the TUI widgets read from.
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator | None = None,
        project_dir: Path | None = None,
    ):
        self._orchestrator = orchestrator
        self._project_dir = project_dir or (
            orchestrator.project_dir if orchestrator else Path(".")
        )

        # Live state
        self._root = AgentNode(
            agent_id="orchestrator",
            agent_type="orchestrator",
        )
        self._current_agent: AgentNode | None = None
        self._snapshot = OrchestratorSnapshot(
            project_dir=str(self._project_dir),
        )

        # Event tracking
        self._event_index = 0
        self._callbacks: list[Callable[[StreamEvent], Any]] = []
        self._running = False

        # Load existing state from disk if available
        self._load_persisted_state()

    @property
    def snapshot(self) -> OrchestratorSnapshot:
        return self._snapshot

    @property
    def root_agent(self) -> AgentNode:
        return self._root

    @property
    def buffer(self) -> StreamBuffer | None:
        if self._orchestrator:
            return self._orchestrator.buffer
        return None

    def on_event(self, callback: Callable[[StreamEvent], Any]) -> None:
        """Register a callback for every new event from the real orchestrator."""
        self._callbacks.append(callback)

    def _load_persisted_state(self) -> None:
        """Load state from the real .acli_state.json on disk."""
        state_file = self._project_dir / ".acli_state.json"
        if not state_file.exists():
            return

        try:
            state = get_project_state(self._project_dir)
            self._snapshot.session_count = state.session_count
            self._snapshot.is_first_run = state.is_first_run

            # Reconstruct agent history from real sessions
            for session in state.sessions:
                node = AgentNode(
                    agent_id=f"session-{session.session_id}",
                    agent_type=session.session_type,
                    session_id=session.session_id,
                    status=session.status,
                    start_time=session.start_time,
                    end_time=session.end_time,
                    tool_calls=session.tool_calls,
                    errors=session.errors,
                )
                self._root.children.append(node)

            # Load feature progress from real feature_list.json
            self._load_feature_progress()

        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            logger.debug("Failed to load persisted state: %s", e)

    def _load_feature_progress(self) -> None:
        """Load progress from real feature_list.json."""
        feature_file = self._project_dir / "feature_list.json"
        if not feature_file.exists():
            return

        try:
            with open(feature_file) as f:
                data = json.load(f)

            if isinstance(data, list):
                features = data
            elif isinstance(data, dict) and "features" in data:
                features = data["features"]
            else:
                return

            self._snapshot.features_total = len(features)
            self._snapshot.features_done = sum(
                1 for f in features if f.get("passes", False)
            )
            self._root.features_total = self._snapshot.features_total
            self._root.features_done = self._snapshot.features_done
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug("Failed to load feature progress: %s", e)

    def handle_event(self, event: StreamEvent) -> None:
        """Process a real event from the orchestrator's stream."""
        self._snapshot.events_processed += 1

        if event.type == EventType.SESSION_START:
            node = AgentNode(
                agent_id=f"session-{event.session_id}",
                agent_type=event.session_type,
                session_id=event.session_id,
                status="running",
                start_time=event.timestamp,
            )
            self._root.children.append(node)
            self._current_agent = node
            self._root.status = "running"

            self._snapshot.running = True
            self._snapshot.current_session_id = event.session_id
            self._snapshot.current_session_type = event.session_type
            self._snapshot.session_count = event.session_id

        elif event.type == EventType.SESSION_END:
            if self._current_agent:
                self._current_agent.status = "completed"
                self._current_agent.end_time = event.timestamp
                self._current_agent = None

            # Update snapshot and root to reflect no active agents
            has_active = any(c.status == "running" for c in self._root.children)
            if not has_active:
                self._snapshot.running = False
                self._root.status = "idle"

        elif event.type == EventType.TOOL_START:
            self._snapshot.total_tool_calls += 1
            if self._current_agent:
                self._current_agent.tool_calls += 1
                self._current_agent.current_tool = event.tool_name

        elif event.type == EventType.TOOL_END:
            if self._current_agent:
                self._current_agent.current_tool = ""
                if event.tool_error:
                    self._current_agent.errors.append(event.tool_error[:200])

        elif event.type == EventType.TOOL_BLOCKED:
            self._snapshot.total_errors += 1
            if self._current_agent:
                self._current_agent.current_tool = ""
                self._current_agent.errors.append(f"BLOCKED: {event.tool_error[:200]}")

        elif event.type == EventType.ERROR:
            self._snapshot.total_errors += 1
            if self._current_agent:
                self._current_agent.status = "error"
                self._current_agent.errors.append(event.text[:200])

        elif event.type == EventType.PROGRESS:
            self._snapshot.features_done = event.features_done
            self._snapshot.features_total = event.features_total
            self._root.features_done = event.features_done
            self._root.features_total = event.features_total

        elif event.type == EventType.TEXT:
            if self._current_agent:
                self._current_agent.last_text = event.text[:500]

        # Notify TUI callbacks
        for cb in self._callbacks:
            try:
                result = cb(event)
                if asyncio.iscoroutine(result):
                    asyncio.ensure_future(result)
            except Exception:
                logger.debug("Event callback error for %s", event.type, exc_info=True)

    async def consume_events(self, stop_event: asyncio.Event | None = None) -> None:
        """
        Consume events from the real orchestrator's StreamBuffer.

        This is the core loop that keeps the TUI in sync with reality.
        """
        if not self._orchestrator:
            return

        stop_event = stop_event or asyncio.Event()
        self._running = True

        # Update model and project dir from real orchestrator
        self._snapshot.model = self._orchestrator.model
        self._snapshot.project_dir = str(self._orchestrator.project_dir)

        try:
            async for event in self._orchestrator.buffer.iter_from(self._event_index):
                if stop_event.is_set():
                    break
                self._event_index += 1
                self.handle_event(event)
        finally:
            self._running = False

    async def poll_state(
        self,
        interval: float = 1.0,
        stop_event: asyncio.Event | None = None,
    ) -> None:
        """
        Periodically poll orchestrator status and feature_list.json.

        Catches state changes that aren't in the event stream (e.g.
        external git commits, manual feature_list.json edits).
        """
        stop_event = stop_event or asyncio.Event()

        while not stop_event.is_set():
            if self._orchestrator:
                status = self._orchestrator.get_status()
                self._snapshot.running = status["running"]
                self._snapshot.paused = status["paused"]
                self._root.status = (
                    "running" if status["running"]
                    else "paused" if status["paused"]
                    else "idle"
                )

            # Re-read feature progress from disk
            self._load_feature_progress()

            await asyncio.sleep(interval)

    def get_agent_by_id(self, agent_id: str) -> AgentNode | None:
        """Find an agent node by ID."""
        if self._root.agent_id == agent_id:
            return self._root
        for child in self._root.children:
            if child.agent_id == agent_id:
                return child
        return None

    def get_active_agents(self) -> list[AgentNode]:
        """Get all currently active agents."""
        active = []
        if self._root.is_active:
            active.append(self._root)
        for child in self._root.children:
            if child.is_active:
                active.append(child)
        return active

    def get_all_agents_flat(self) -> list[AgentNode]:
        """Get all agents in a flat list (root + children)."""
        return [self._root] + list(self._root.children)

    def send_command(self, command: str) -> None:
        """Send a control command to the real orchestrator."""
        if not self._orchestrator:
            return

        if command == "pause":
            self._orchestrator.request_pause()
        elif command == "resume":
            self._orchestrator.resume()
        elif command == "stop":
            self._orchestrator.request_stop()
