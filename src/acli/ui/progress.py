"""
Progress Panel
==============

Displays feature completion progress with visual bar.
"""

from dataclasses import dataclass

from rich.console import Console, ConsoleOptions, RenderResult
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from .themes import Theme, DEFAULT_THEME


@dataclass
class ProgressState:
    """Current progress state."""
    features_done: int = 0
    features_total: int = 0
    current_feature: str = ""
    session_number: int = 0
    session_type: str = ""
    elapsed_time: str = "00:00:00"

    @property
    def percentage(self) -> float:
        if self.features_total == 0:
            return 0.0
        return (self.features_done / self.features_total) * 100


class ProgressPanel:
    """
    Progress display panel with visual bar and stats.
    """

    def __init__(self, theme: Theme | None = None):
        self.state = ProgressState()
        self.theme = theme or DEFAULT_THEME

    def update(
        self,
        features_done: int | None = None,
        features_total: int | None = None,
        current_feature: str | None = None,
        session_number: int | None = None,
        session_type: str | None = None,
        elapsed_time: str | None = None,
    ) -> None:
        """Update progress state."""
        if features_done is not None:
            self.state.features_done = features_done
        if features_total is not None:
            self.state.features_total = features_total
        if current_feature is not None:
            self.state.current_feature = current_feature
        if session_number is not None:
            self.state.session_number = session_number
        if session_type is not None:
            self.state.session_type = session_type
        if elapsed_time is not None:
            self.state.elapsed_time = elapsed_time

    def render(self) -> Panel:
        """Render progress panel."""
        # Progress bar
        bar = ProgressBar(
            total=max(self.state.features_total, 1),
            completed=self.state.features_done,
            width=40,
            complete_style=self.theme.progress_done,
            finished_style=self.theme.success,
        )

        # Stats table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="dim")
        table.add_column("Value", style="bold")

        percentage = self.state.percentage
        table.add_row("Progress", f"{self.state.features_done}/{self.state.features_total} ({percentage:.1f}%)")
        table.add_row("Session", f"#{self.state.session_number} ({self.state.session_type})")
        table.add_row("Elapsed", self.state.elapsed_time)

        if self.state.current_feature:
            feature_text = self.state.current_feature
            if len(feature_text) > 40:
                feature_text = feature_text[:37] + "..."
            table.add_row("Current", feature_text)

        # Combine
        content = Text()
        content.append_text(Text.from_markup("\n"))

        return Panel(
            table,
            title="[bold]Progress[/]",
            subtitle=f"{bar}",
            border_style=self.theme.border_active if self.state.session_type else self.theme.border_inactive,
            padding=(0, 1),
        )

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield self.render()
