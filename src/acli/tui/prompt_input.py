"""Prompt input widget for the TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static


class PromptInput(Widget):
    """Bottom bar prompt input for sending tasks to the orchestrator."""

    class Submitted(Message):
        """Posted when the user submits a prompt."""

        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static("[#0abdc6]▶[/] ", classes="prompt-caret")
            yield Input(placeholder="Enter task...", id="prompt-field")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Capture submitted text and post to app."""
        if event.value.strip():
            self.post_message(self.Submitted(event.value.strip()))
            event.input.value = ""
