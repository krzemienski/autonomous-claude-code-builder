"""
Async Streaming Handlers
========================

Event-based streaming for real-time tool and message updates.
Integrates with Rich dashboard through async generators.
"""

import asyncio
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..utils import AsyncEventEmitter


class EventType(str, Enum):
    """Types of streaming events."""

    TEXT = "text"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    TOOL_BLOCKED = "tool_blocked"
    ERROR = "error"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    PROGRESS = "progress"

    # v2 additions — multi-agent orchestration events
    AGENT_SPAWN = "agent_spawn"
    AGENT_COMPLETE = "agent_complete"
    ANALYSIS_UPDATE = "analysis_update"
    PLAN_CREATED = "plan_created"
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    GATE_START = "gate_start"
    GATE_RESULT = "gate_result"
    CONTEXT_UPDATE = "context_update"
    MEMORY_UPDATE = "memory_update"
    THINKING = "thinking"
    MOCK_DETECTED = "mock_detected"
    PROMPT_RECEIVED = "prompt_received"


@dataclass
class StreamEvent:
    """A single streaming event."""

    type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)

    # Text event fields
    text: str = ""

    # Tool event fields
    tool_name: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)
    tool_result: str = ""
    tool_error: str = ""
    tool_duration_ms: float = 0

    # Session fields
    session_id: int = 0
    session_type: str = ""

    # Progress fields
    features_done: int = 0
    features_total: int = 0

    # v2 agent fields
    agent_id: str = ""
    agent_type: str = ""
    model: str = ""

    # v2 gate fields
    gate_id: str = ""
    gate_status: str = ""
    evidence_path: str = ""

    # v2 phase fields
    phase_id: str = ""
    phase_name: str = ""

    # v2 memory fields
    memory_fact: str = ""


class StreamBuffer:
    """
    Buffer for streaming events with async iteration.

    Allows multiple consumers to read the same stream.
    """

    def __init__(self, max_size: int = 1000):
        self._events: list[StreamEvent] = []
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._new_event = asyncio.Event()

    async def push(self, event: StreamEvent) -> None:
        """Add event to buffer."""
        async with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_size:
                self._events = self._events[-self._max_size :]
            self._new_event.set()

    async def iter_from(self, index: int = 0) -> AsyncIterator[StreamEvent]:
        """Iterate events starting from index."""
        current = index
        while True:
            async with self._lock:
                while current < len(self._events):
                    yield self._events[current]
                    current += 1
                self._new_event.clear()

            # Wait for new events
            await self._new_event.wait()

    def get_recent(self, count: int = 50) -> list[StreamEvent]:
        """Get recent events (synchronous)."""
        return self._events[-count:]

    def clear(self) -> None:
        """Clear buffer."""
        self._events.clear()


class StreamingHandler:
    """
    Handles streaming updates from Claude SDK.

    Converts SDK messages into StreamEvents and pushes to buffer.
    """

    def __init__(self, buffer: StreamBuffer):
        self.buffer = buffer
        self._current_tool_start: datetime | None = None
        self._emitter = AsyncEventEmitter()  # type: ignore[no-untyped-call]

    def on(self, event_type: str, handler: Callable[..., Any]) -> None:
        """Register event handler."""
        self._emitter.on(event_type, handler)

    async def emit(self, event: StreamEvent) -> None:
        """Emit event to handlers and buffer."""
        await self.buffer.push(event)
        await self._emitter.emit(event.type.value, event)

    async def handle_text(self, text: str) -> None:
        """Handle text chunk from assistant."""
        event = StreamEvent(type=EventType.TEXT, text=text)
        await self.emit(event)

    async def handle_tool_start(self, name: str, input_data: dict[str, Any]) -> None:
        """Handle tool execution start."""
        self._current_tool_start = datetime.now()
        event = StreamEvent(
            type=EventType.TOOL_START,
            tool_name=name,
            tool_input=input_data,
        )
        await self.emit(event)

    async def handle_tool_end(
        self,
        name: str,
        result: str = "",
        error: str = "",
    ) -> None:
        """Handle tool execution end."""
        duration = 0.0
        if self._current_tool_start:
            delta = datetime.now() - self._current_tool_start
            duration = delta.total_seconds() * 1000
            self._current_tool_start = None

        event = StreamEvent(
            type=EventType.TOOL_END,
            tool_name=name,
            tool_result=result[:500] if result else "",
            tool_error=error,
            tool_duration_ms=duration,
        )
        await self.emit(event)

    async def handle_tool_blocked(self, name: str, reason: str) -> None:
        """Handle blocked tool execution."""
        event = StreamEvent(
            type=EventType.TOOL_BLOCKED,
            tool_name=name,
            tool_error=reason,
        )
        await self.emit(event)

    async def handle_error(self, error: str) -> None:
        """Handle error event."""
        event = StreamEvent(type=EventType.ERROR, text=error)
        await self.emit(event)

    async def handle_session_start(self, session_id: int, session_type: str) -> None:
        """Handle session start."""
        event = StreamEvent(
            type=EventType.SESSION_START,
            session_id=session_id,
            session_type=session_type,
        )
        await self.emit(event)

    async def handle_session_end(self, session_id: int) -> None:
        """Handle session end."""
        event = StreamEvent(
            type=EventType.SESSION_END,
            session_id=session_id,
        )
        await self.emit(event)

    async def handle_progress(self, done: int, total: int) -> None:
        """Handle progress update."""
        event = StreamEvent(
            type=EventType.PROGRESS,
            features_done=done,
            features_total=total,
        )
        await self.emit(event)

    async def handle_agent_spawn(self, agent_id: str, agent_type: str, model: str) -> None:
        """Handle new agent creation."""
        event = StreamEvent(
            type=EventType.AGENT_SPAWN,
            agent_id=agent_id,
            agent_type=agent_type,
            model=model,
        )
        await self.emit(event)

    async def handle_agent_complete(self, agent_id: str, status: str) -> None:
        """Handle agent completion."""
        event = StreamEvent(
            type=EventType.AGENT_COMPLETE,
            agent_id=agent_id,
            gate_status=status,
        )
        await self.emit(event)

    async def handle_gate_start(self, gate_id: str, criteria: str) -> None:
        """Handle validation gate start."""
        event = StreamEvent(
            type=EventType.GATE_START,
            gate_id=gate_id,
            text=criteria,
        )
        await self.emit(event)

    async def handle_gate_result(self, gate_id: str, status: str, evidence_path: str) -> None:
        """Handle validation gate result."""
        event = StreamEvent(
            type=EventType.GATE_RESULT,
            gate_id=gate_id,
            gate_status=status,
            evidence_path=evidence_path,
        )
        await self.emit(event)

    async def handle_context_update(self, key: str, summary: str) -> None:
        """Handle context store update."""
        event = StreamEvent(
            type=EventType.CONTEXT_UPDATE,
            text=f"{key}: {summary}",
        )
        await self.emit(event)

    async def handle_memory_update(self, fact: str) -> None:
        """Handle memory fact addition."""
        event = StreamEvent(
            type=EventType.MEMORY_UPDATE,
            memory_fact=fact,
        )
        await self.emit(event)

    async def handle_phase_start(self, phase_id: str, phase_name: str) -> None:
        """Handle phase start."""
        event = StreamEvent(
            type=EventType.PHASE_START,
            phase_id=phase_id,
            phase_name=phase_name,
        )
        await self.emit(event)

    async def handle_phase_end(self, phase_id: str, status: str) -> None:
        """Handle phase completion."""
        event = StreamEvent(
            type=EventType.PHASE_END,
            phase_id=phase_id,
            gate_status=status,
        )
        await self.emit(event)
