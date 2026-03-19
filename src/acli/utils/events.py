"""
Async Event Emitter
===================

Simple async event emitter for streaming events.
"""

import asyncio
from collections import defaultdict
from collections.abc import Callable
from typing import Any


class AsyncEventEmitter:  # type: ignore[misc]
    """Simple async event emitter."""

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event_type: str, handler: Callable) -> None:
        """Register event handler."""
        self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: Callable) -> None:
        """Unregister event handler."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass

    async def emit(self, event_type: str, *args: Any, **kwargs: Any) -> None:
        """Emit event to all registered handlers."""
        if event_type not in self._handlers:
            return

        for handler in self._handlers[event_type]:
            if asyncio.iscoroutinefunction(handler):
                await handler(*args, **kwargs)
            else:
                handler(*args, **kwargs)

    def clear(self, event_type: str | None = None) -> None:
        """Clear handlers for event type or all handlers."""
        if event_type:
            self._handlers.pop(event_type, None)
        else:
            self._handlers.clear()
