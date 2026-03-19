"""
Prompt Input Widget
====================

Inline text input at bottom of TUI for sending new tasks.
"""

import logging

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static

logger = logging.getLogger(__name__)


class PromptInput(Widget):
    """Inline prompt input at bottom of TUI for sending new tasks."""

    class PromptSubmitted(Message):
        """Message emitted when a prompt is submitted."""

        def __init__(self, prompt: str) -> None:
            super().__init__()
            self.prompt = prompt

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Horizontal(id="prompt-container"):
            yield Static("[#0abdc6]>[/] ", id="prompt-icon")
            yield Input(
                placeholder="Enter task prompt...",
                id="prompt-field",
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        prompt_text = event.value.strip()
        if prompt_text:
            self.post_message(self.PromptSubmitted(prompt_text))
            event.input.value = ""
