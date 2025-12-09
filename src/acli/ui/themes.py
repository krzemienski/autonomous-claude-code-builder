"""
Dashboard Color Themes
======================

Consistent color scheme for dashboard components.
"""

from dataclasses import dataclass


@dataclass
class Theme:
    """Dashboard color theme."""

    # Status colors
    success: str = "green"
    error: str = "red"
    warning: str = "yellow"
    info: str = "blue"
    pending: str = "dim"

    # Component colors
    tool_running: str = "cyan"
    tool_done: str = "green"
    tool_blocked: str = "red"

    # Progress colors
    progress_done: str = "green"
    progress_remaining: str = "dim"

    # Panel borders
    border_active: str = "blue"
    border_inactive: str = "dim"

    # Text
    text_primary: str = "white"
    text_secondary: str = "dim"
    text_highlight: str = "bold cyan"


# Default theme
DEFAULT_THEME = Theme()

# Dark theme (high contrast)
DARK_THEME = Theme(
    success="bright_green",
    error="bright_red",
    warning="bright_yellow",
    info="bright_blue",
    tool_running="bright_cyan",
    border_active="bright_blue",
)


def get_theme(name: str = "default") -> Theme:
    """Get theme by name."""
    themes = {
        "default": DEFAULT_THEME,
        "dark": DARK_THEME,
    }
    return themes.get(name, DEFAULT_THEME)
