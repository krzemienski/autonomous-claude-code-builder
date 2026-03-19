"""
Log Streaming Panel
===================

Displays real-time log stream with filtering.
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from rich.console import Console, ConsoleOptions, RenderResult
from rich.panel import Panel
from rich.text import Text

from .themes import DEFAULT_THEME, Theme


class LogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    TOOL = "tool"


@dataclass
class LogEntry:
    """A single log entry."""
    timestamp: datetime
    level: LogLevel
    message: str
    source: str = ""  # agent_id or component name


class LogPanel:
    """
    Streaming log panel with level filtering.
    """

    def __init__(
        self,
        max_entries: int = 100,
        min_level: LogLevel = LogLevel.INFO,
        theme: Theme | None = None,
    ):
        self.entries: deque[LogEntry] = deque(maxlen=max_entries)
        self.min_level = min_level
        self.theme = theme or DEFAULT_THEME
        self._level_order = [
            LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING,
            LogLevel.ERROR, LogLevel.TOOL,
        ]

    def add(
        self,
        message: str,
        level: LogLevel = LogLevel.INFO,
        source: str = "",
    ) -> None:
        """Add log entry."""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            source=source,
        )
        self.entries.append(entry)

    def set_min_level(self, level: LogLevel) -> None:
        """Set minimum log level to display."""
        self.min_level = level

    def _should_show(self, level: LogLevel) -> bool:
        """Check if level should be displayed."""
        if level == LogLevel.TOOL:
            return True  # Always show tool events
        return self._level_order.index(level) >= self._level_order.index(self.min_level)

    def _format_entry(self, entry: LogEntry) -> Text:
        """Format a single log entry."""
        # Timestamp
        ts = entry.timestamp.strftime("%H:%M:%S")

        # Level color
        level_colors = {
            LogLevel.DEBUG: self.theme.pending,
            LogLevel.INFO: self.theme.info,
            LogLevel.WARNING: self.theme.warning,
            LogLevel.ERROR: self.theme.error,
            LogLevel.TOOL: self.theme.tool_running,
        }
        color = level_colors.get(entry.level, "white")

        # Level prefix
        level_prefix = {
            LogLevel.DEBUG: "DBG",
            LogLevel.INFO: "INF",
            LogLevel.WARNING: "WRN",
            LogLevel.ERROR: "ERR",
            LogLevel.TOOL: "TOL",
        }
        prefix = level_prefix.get(entry.level, "???")

        # Build text
        text = Text()
        text.append(f"{ts} ", style="dim")
        text.append(f"[{prefix}] ", style=color)

        if entry.source:
            text.append(f"{entry.source}: ", style="cyan")

        text.append(entry.message)

        return text

    def render(self, height: int = 15) -> Panel:
        """Render log panel."""
        lines = []

        # Filter and get recent entries
        filtered = [e for e in self.entries if self._should_show(e.level)]
        recent = list(filtered)[-height:]

        for entry in recent:
            lines.append(self._format_entry(entry))

        # Pad with empty lines if needed
        while len(lines) < height:
            lines.insert(0, Text(""))

        content = Text("\n").join(lines)

        return Panel(
            content,
            title=f"[bold]Logs[/] [dim]({self.min_level.value}+)[/]",
            border_style=self.theme.border_inactive,
            padding=(0, 1),
        )

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield self.render()


# Convenience functions
def create_log_panel(
    min_level: LogLevel = LogLevel.INFO,
    max_entries: int = 100,
) -> LogPanel:
    """Create a new log panel."""
    return LogPanel(max_entries=max_entries, min_level=min_level)
