"""
Puppeteer MCP Integration
=========================

Wrapper for Puppeteer MCP server tools.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PuppeteerConfig:
    """Puppeteer MCP server configuration."""
    command: str = "npx"
    args: list[str] = field(default_factory=lambda: ["puppeteer-mcp-server"])

    def to_mcp_config(self) -> dict[str, Any]:
        """Convert to MCP server config format."""
        return {
            "command": self.command,
            "args": self.args,
        }


# Puppeteer tool definitions
PUPPETEER_TOOLS = {
    "navigate": {
        "name": "mcp__puppeteer__puppeteer_navigate",
        "description": "Navigate browser to URL",
        "params": ["url"],
    },
    "screenshot": {
        "name": "mcp__puppeteer__puppeteer_screenshot",
        "description": "Take screenshot of page or element",
        "params": ["name", "selector", "width", "height"],
    },
    "click": {
        "name": "mcp__puppeteer__puppeteer_click",
        "description": "Click an element",
        "params": ["selector"],
    },
    "fill": {
        "name": "mcp__puppeteer__puppeteer_fill",
        "description": "Fill input field",
        "params": ["selector", "value"],
    },
    "select": {
        "name": "mcp__puppeteer__puppeteer_select",
        "description": "Select dropdown option",
        "params": ["selector", "value"],
    },
    "hover": {
        "name": "mcp__puppeteer__puppeteer_hover",
        "description": "Hover over element",
        "params": ["selector"],
    },
    "evaluate": {
        "name": "mcp__puppeteer__puppeteer_evaluate",
        "description": "Execute JavaScript in browser",
        "params": ["script"],
    },
}


def get_puppeteer_tool_list() -> list[str]:
    """Get list of Puppeteer tool names."""
    return [tool["name"] for tool in PUPPETEER_TOOLS.values()]


def get_puppeteer_config() -> dict[str, Any]:
    """Get Puppeteer MCP server configuration."""
    return PuppeteerConfig().to_mcp_config()


class PuppeteerHelper:
    """
    Helper for generating Puppeteer tool calls.

    Used in prompt generation to guide agent tool usage.
    """

    @staticmethod
    def navigate(url: str) -> dict[str, Any]:
        """Generate navigate tool call."""
        return {
            "tool": "mcp__puppeteer__puppeteer_navigate",
            "input": {"url": url},
        }

    @staticmethod
    def click(selector: str) -> dict[str, Any]:
        """Generate click tool call."""
        return {
            "tool": "mcp__puppeteer__puppeteer_click",
            "input": {"selector": selector},
        }

    @staticmethod
    def fill(selector: str, value: str) -> dict[str, Any]:
        """Generate fill tool call."""
        return {
            "tool": "mcp__puppeteer__puppeteer_fill",
            "input": {"selector": selector, "value": value},
        }

    @staticmethod
    def screenshot(name: str, selector: str | None = None) -> dict[str, Any]:
        """Generate screenshot tool call."""
        input_data = {"name": name}
        if selector:
            input_data["selector"] = selector
        return {
            "tool": "mcp__puppeteer__puppeteer_screenshot",
            "input": input_data,
        }

    @staticmethod
    def evaluate(script: str) -> dict[str, Any]:
        """Generate evaluate tool call."""
        return {
            "tool": "mcp__puppeteer__puppeteer_evaluate",
            "input": {"script": script},
        }

    @staticmethod
    def get_text(selector: str) -> dict[str, Any]:
        """Generate script to get element text."""
        script = f"document.querySelector('{selector}')?.textContent || ''"
        return PuppeteerHelper.evaluate(script)

    @staticmethod
    def wait_for_selector(selector: str, timeout_ms: int = 5000) -> dict[str, Any]:
        """Generate script to wait for selector."""
        script = f"""
            await new Promise((resolve, reject) => {{
                const start = Date.now();
                const check = () => {{
                    if (document.querySelector('{selector}')) {{
                        resolve(true);
                    }} else if (Date.now() - start > {timeout_ms}) {{
                        reject(new Error('Timeout waiting for {selector}'));
                    }} else {{
                        setTimeout(check, 100);
                    }}
                }};
                check();
            }});
        """
        return PuppeteerHelper.evaluate(script)
