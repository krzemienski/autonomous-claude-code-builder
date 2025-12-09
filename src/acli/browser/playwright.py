"""
Playwright MCP Integration
==========================

Wrapper for Playwright MCP server tools.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlaywrightConfig:
    """Playwright MCP server configuration."""
    command: str = "npx"
    args: list[str] = field(default_factory=lambda: ["@executeautomation/playwright-mcp-server"])

    def to_mcp_config(self) -> dict[str, Any]:
        """Convert to MCP server config format."""
        return {
            "command": self.command,
            "args": self.args,
        }


# Playwright tool definitions
PLAYWRIGHT_TOOLS = {
    "navigate": {
        "name": "mcp__playwright__browser_navigate",
        "description": "Navigate browser to URL",
        "params": ["url"],
    },
    "snapshot": {
        "name": "mcp__playwright__browser_snapshot",
        "description": "Get accessibility tree snapshot",
        "params": [],
    },
    "click": {
        "name": "mcp__playwright__browser_click",
        "description": "Click element by ref",
        "params": ["element", "ref"],
    },
    "type": {
        "name": "mcp__playwright__browser_type",
        "description": "Type text into element",
        "params": ["element", "ref", "text"],
    },
    "screenshot": {
        "name": "mcp__playwright__browser_take_screenshot",
        "description": "Take screenshot",
        "params": ["filename", "fullPage"],
    },
    "wait_for": {
        "name": "mcp__playwright__browser_wait_for",
        "description": "Wait for text or time",
        "params": ["text", "textGone", "time"],
    },
    "tabs": {
        "name": "mcp__playwright__browser_tabs",
        "description": "Manage browser tabs",
        "params": ["action", "index"],
    },
}


def get_playwright_tool_list() -> list[str]:
    """Get list of Playwright tool names."""
    return [tool["name"] for tool in PLAYWRIGHT_TOOLS.values()]


def get_playwright_config() -> dict[str, Any]:
    """Get Playwright MCP server configuration."""
    return PlaywrightConfig().to_mcp_config()


class PlaywrightHelper:
    """
    Helper for generating Playwright tool calls.

    Playwright uses accessibility tree refs for element selection.
    """

    @staticmethod
    def navigate(url: str) -> dict[str, Any]:
        """Generate navigate tool call."""
        return {
            "tool": "mcp__playwright__browser_navigate",
            "input": {"url": url},
        }

    @staticmethod
    def snapshot() -> dict[str, Any]:
        """Generate snapshot tool call."""
        return {
            "tool": "mcp__playwright__browser_snapshot",
            "input": {},
        }

    @staticmethod
    def click(element: str, ref: str) -> dict[str, Any]:
        """Generate click tool call."""
        return {
            "tool": "mcp__playwright__browser_click",
            "input": {"element": element, "ref": ref},
        }

    @staticmethod
    def fill(element: str, ref: str, text: str) -> dict[str, Any]:
        """Generate fill/type tool call."""
        return {
            "tool": "mcp__playwright__browser_type",
            "input": {"element": element, "ref": ref, "text": text},
        }

    @staticmethod
    def type_text(element: str, ref: str, text: str) -> dict[str, Any]:
        """Generate type tool call (alias for fill)."""
        return PlaywrightHelper.fill(element, ref, text)

    @staticmethod
    def screenshot(filename: str | None = None, full_page: bool = False) -> dict[str, Any]:
        """Generate screenshot tool call."""
        input_data = {}
        if filename:
            input_data["filename"] = filename
        if full_page:
            input_data["fullPage"] = True
        return {
            "tool": "mcp__playwright__browser_take_screenshot",
            "input": input_data,
        }

    @staticmethod
    def wait_for_text(text: str) -> dict[str, Any]:
        """Generate wait for text tool call."""
        return {
            "tool": "mcp__playwright__browser_wait_for",
            "input": {"text": text},
        }

    @staticmethod
    def wait_for_time(seconds: float) -> dict[str, Any]:
        """Generate wait for time tool call."""
        return {
            "tool": "mcp__playwright__browser_wait_for",
            "input": {"time": seconds},
        }

    @staticmethod
    def new_tab(url: str | None = None) -> dict[str, Any]:
        """Generate new tab tool call."""
        input_data = {"action": "new"}
        if url:
            input_data["url"] = url
        return {
            "tool": "mcp__playwright__browser_tabs",
            "input": input_data,
        }
