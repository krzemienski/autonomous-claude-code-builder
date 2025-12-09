"""
Dashboard Controller
====================

Main dashboard with multi-pane layout using Rich.Live.
Coordinates tool board, logs, and progress panels.
"""

import asyncio
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from ..core.streaming import StreamBuffer, StreamEvent, EventType
from .tool_board import ToolBoard
from .logs import LogPanel, LogLevel
from .progress import ProgressPanel
from .themes import Theme, get_theme


class Dashboard:
    """
    Main dashboard with real-time updates.

    Layout:
    ┌──────────────────────────────────────────────────────────┐
    │                        Header                             │
    ├────────────────────┬─────────────────────────────────────┤
    │    Tool Board      │              Logs                   │
    │    (20%)           │              (60%)                  │
    │                    │                                     │
    ├────────────────────┴─────────────────────────────────────┤
    │                       Progress                            │
    └──────────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        console: Console | None = None,
        theme: str = "default",
        refresh_rate: float = 4.0,
    ):
        self.console = console or Console()
        self.theme = get_theme(theme)
        self.refresh_rate = refresh_rate

        # Panels
        self.tool_board = ToolBoard(theme=self.theme)
        self.logs = LogPanel(theme=self.theme)
        self.progress = ProgressPanel(theme=self.theme)

        # State
        self._running = False
        self._start_time: datetime | None = None

    def _create_layout(self) -> Layout:
        """Create dashboard layout."""
        layout = Layout()

        layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=6),
        )

        layout["main"].split_row(
            Layout(name="tools", ratio=1),
            Layout(name="logs", ratio=2),
        )

        return layout

    def _render_header(self) -> Panel:
        """Render header panel."""
        title = Text("AUTONOMOUS CLI", style="bold blue")
        status = Text(" RUNNING ", style="bold white on green") if self._running else Text(" IDLE ", style="bold white on dim")

        elapsed = "00:00:00"
        if self._start_time:
            delta = datetime.now() - self._start_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        header = Text.assemble(
            title,
            " | ",
            status,
            " | ",
            ("Elapsed: ", "dim"),
            (elapsed, "cyan"),
        )

        return Panel(header, border_style="blue", padding=(0, 1))

    def _update_layout(self, layout: Layout) -> None:
        """Update layout with current panel renders."""
        layout["header"].update(self._render_header())
        layout["tools"].update(self.tool_board.render())
        layout["logs"].update(self.logs.render(height=15))
        layout["footer"].update(self.progress.render())

    async def process_events(self, buffer: StreamBuffer) -> None:
        """Process events from stream buffer."""
        async for event in buffer.iter_from(0):
            self._handle_event(event)

    def _handle_event(self, event: StreamEvent) -> None:
        """Handle a single stream event."""
        if event.type == EventType.TEXT:
            # Add text to logs
            self.logs.add(event.text[:100], level=LogLevel.INFO)

        elif event.type == EventType.TOOL_START:
            self.tool_board.start_tool(event.tool_name, event.tool_input)
            self.logs.add(f"Tool: {event.tool_name}", level=LogLevel.TOOL)

        elif event.type == EventType.TOOL_END:
            self.tool_board.end_tool(
                result=event.tool_result,
                error=event.tool_error,
            )
            if event.tool_error:
                self.logs.add(f"Tool error: {event.tool_error}", level=LogLevel.ERROR)

        elif event.type == EventType.TOOL_BLOCKED:
            self.tool_board.block_tool(event.tool_error)
            self.logs.add(f"BLOCKED: {event.tool_error}", level=LogLevel.WARNING)

        elif event.type == EventType.ERROR:
            self.logs.add(event.text, level=LogLevel.ERROR)

        elif event.type == EventType.SESSION_START:
            self._running = True
            self._start_time = datetime.now()
            self.progress.update(
                session_number=event.session_id,
                session_type=event.session_type,
            )
            self.logs.add(f"Session {event.session_id} started ({event.session_type})", level=LogLevel.INFO)

        elif event.type == EventType.SESSION_END:
            self.logs.add(f"Session {event.session_id} ended", level=LogLevel.INFO)

        elif event.type == EventType.PROGRESS:
            self.progress.update(
                features_done=event.features_done,
                features_total=event.features_total,
            )

    async def run(
        self,
        buffer: StreamBuffer,
        stop_event: asyncio.Event | None = None,
    ) -> None:
        """
        Run dashboard with live updates.

        Args:
            buffer: Stream buffer to consume events from
            stop_event: Event to signal dashboard stop
        """
        stop_event = stop_event or asyncio.Event()
        layout = self._create_layout()

        async def update_loop() -> None:
            """Update dashboard periodically."""
            while not stop_event.is_set():
                self._update_layout(layout)
                await asyncio.sleep(1 / self.refresh_rate)

        async def event_loop() -> None:
            """Process events from buffer."""
            async for event in buffer.iter_from(0):
                if stop_event.is_set():
                    break
                self._handle_event(event)

        with Live(
            layout,
            console=self.console,
            refresh_per_second=self.refresh_rate,
            transient=False,
        ) as live:
            self._update_layout(layout)

            # Run both loops concurrently
            update_task = asyncio.create_task(update_loop())
            event_task = asyncio.create_task(event_loop())

            try:
                # Wait for stop signal
                await stop_event.wait()
            finally:
                update_task.cancel()
                event_task.cancel()
                try:
                    await update_task
                except asyncio.CancelledError:
                    pass
                try:
                    await event_task
                except asyncio.CancelledError:
                    pass

    def run_headless(self, buffer: StreamBuffer) -> None:
        """
        Run in headless mode (no TUI, just log output).

        Useful for CI/CD or when dashboard is disabled.
        """
        for event in buffer.get_recent(100):
            self._handle_event(event)

            if event.type == EventType.TEXT:
                self.console.print(event.text, end="")
            elif event.type == EventType.TOOL_START:
                self.console.print(f"\n[cyan][Tool: {event.tool_name}][/]")
            elif event.type == EventType.TOOL_END:
                if event.tool_error:
                    self.console.print(f"[red]   Error: {event.tool_error}[/]")
                else:
                    self.console.print("[green]   Done[/]")
            elif event.type == EventType.ERROR:
                self.console.print(f"[red]Error: {event.text}[/]")


async def run_dashboard(
    buffer: StreamBuffer,
    theme: str = "default",
) -> None:
    """Convenience function to run dashboard."""
    dashboard = Dashboard(theme=theme)
    stop_event = asyncio.Event()

    # Run until interrupted
    try:
        await dashboard.run(buffer, stop_event)
    except KeyboardInterrupt:
        stop_event.set()
