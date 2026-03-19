"""Inline prompt input widget for sending tasks to orchestrator."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static


class PromptInput(Widget):
    """Inline prompt input at bottom of TUI for sending new tasks."""

    DEFAULT_CSS = """
    PromptInput {
        height: 3;
        dock: bottom;
        border-top: solid $accent;
    }
    PromptInput > Horizontal {
        height: 3;
    }
    PromptInput Input {
        width: 1fr;
    }
    PromptInput .prompt-label {
        width: auto;
        padding: 0 1;
        color: $text;
    }
    """

    class Submitted(Message):
        """Sent when user submits a prompt."""
        def __init__(self, value: str) -> None:
            """Initialize with the submitted prompt value."""
            super().__init__()
            self.value = value

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Horizontal():
            yield Static("[bold cyan]>[/] ", classes="prompt-label")
            yield Input(placeholder="Enter task prompt...", id="prompt-field")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.value.strip():
            self.post_message(self.Submitted(event.value.strip()))
            event.input.value = ""
