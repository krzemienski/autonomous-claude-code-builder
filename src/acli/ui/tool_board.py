"""
Tool Board Panel
================

Displays real-time tool execution status.
Shows: tool name, arguments, status, duration.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from rich.console import Console, ConsoleOptions, RenderResult
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .themes import Theme, DEFAULT_THEME


@dataclass
class ToolEntry:
    """A single tool execution entry."""
    name: str
    status: str = "running"  # running, done, blocked, error
    args_preview: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    result_preview: str = ""
    error: str = ""

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() * 1000
        delta = datetime.now() - self.start_time
        return delta.total_seconds() * 1000


class ToolBoard:
    """
    Tool execution tracking board.

    Maintains a rolling list of recent tool executions.
    """

    def __init__(
        self,
        max_entries: int = 10,
        theme: Theme | None = None,
    ):
        self.entries: deque[ToolEntry] = deque(maxlen=max_entries)
        self.theme = theme or DEFAULT_THEME
        self._current_tool: ToolEntry | None = None

    def start_tool(self, name: str, args: dict[str, Any] | None = None) -> None:
        """Record tool execution start."""
        args_preview = ""
        if args:
            # Truncate args preview
            args_str = str(args)
            args_preview = args_str[:50] + "..." if len(args_str) > 50 else args_str

        entry = ToolEntry(name=name, args_preview=args_preview)
        self._current_tool = entry
        self.entries.append(entry)

    def end_tool(self, result: str = "", error: str = "") -> None:
        """Record tool execution end."""
        if self._current_tool:
            self._current_tool.end_time = datetime.now()
            self._current_tool.status = "error" if error else "done"
            self._current_tool.result_preview = result[:50] if result else ""
            self._current_tool.error = error
            self._current_tool = None

    def block_tool(self, reason: str) -> None:
        """Record tool blocked."""
        if self._current_tool:
            self._current_tool.end_time = datetime.now()
            self._current_tool.status = "blocked"
            self._current_tool.error = reason
            self._current_tool = None

    def render(self) -> Panel:
        """Render tool board as Rich Panel."""
        table = Table(
            show_header=True,
            header_style="bold",
            box=None,
            padding=(0, 1),
            expand=True,
        )

        table.add_column("Status", width=3)
        table.add_column("Tool", style="cyan", min_width=10)
        table.add_column("Time", justify="right", width=8)
        table.add_column("Args/Result", overflow="ellipsis")

        for entry in self.entries:
            # Status icon
            if entry.status == "running":
                status = Text("→", style=self.theme.tool_running)
            elif entry.status == "done":
                status = Text("✓", style=self.theme.tool_done)
            elif entry.status == "blocked":
                status = Text("✗", style=self.theme.tool_blocked)
            else:
                status = Text("!", style=self.theme.error)

            # Duration
            duration = f"{entry.duration_ms:.0f}ms"
            if entry.status == "running":
                duration = f"{entry.duration_ms:.0f}ms..."

            # Args/Result
            if entry.status == "running":
                detail = Text(entry.args_preview, style="dim")
            elif entry.error:
                detail = Text(entry.error[:30], style="red")
            elif entry.result_preview:
                detail = Text(entry.result_preview, style="dim")
            else:
                detail = Text("OK", style="green")

            table.add_row(status, entry.name, duration, detail)

        return Panel(
            table,
            title="[bold]Tool Board[/]",
            border_style=self.theme.border_active if self._current_tool else self.theme.border_inactive,
            padding=(0, 1),
        )

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield self.render()
