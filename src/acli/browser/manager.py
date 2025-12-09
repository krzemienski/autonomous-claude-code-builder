"""
Unified Browser Interface & Manager
====================================

Provides consistent interface for browser automation
regardless of backend (Puppeteer or Playwright).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .puppeteer import (
    PuppeteerConfig,
    PuppeteerHelper,
    get_puppeteer_tool_list,
)
from .playwright import (
    PlaywrightConfig,
    PlaywrightHelper,
    get_playwright_tool_list,
)


class BrowserBackend(str, Enum):
    """Available browser automation backends."""
    PUPPETEER = "puppeteer"
    PLAYWRIGHT = "playwright"
    BOTH = "both"


@dataclass
class BrowserConfig:
    """Combined browser configuration."""
    backend: BrowserBackend = BrowserBackend.BOTH
    puppeteer: PuppeteerConfig | None = None
    playwright: PlaywrightConfig | None = None

    def __post_init__(self):
        if self.backend in (BrowserBackend.PUPPETEER, BrowserBackend.BOTH):
            self.puppeteer = self.puppeteer or PuppeteerConfig()
        if self.backend in (BrowserBackend.PLAYWRIGHT, BrowserBackend.BOTH):
            self.playwright = self.playwright or PlaywrightConfig()

    def get_mcp_servers(self) -> dict[str, Any]:
        """Get MCP server configurations."""
        servers = {}

        if self.puppeteer:
            servers["puppeteer"] = self.puppeteer.to_mcp_config()
        if self.playwright:
            servers["playwright"] = self.playwright.to_mcp_config()

        return servers

    def get_tool_list(self) -> list[str]:
        """Get list of available browser tools."""
        tools = []

        if self.puppeteer:
            tools.extend(get_puppeteer_tool_list())
        if self.playwright:
            tools.extend(get_playwright_tool_list())

        return tools


class UnifiedBrowser:
    """
    Unified interface for browser automation.

    Abstracts differences between Puppeteer and Playwright.
    """

    def __init__(self, backend: BrowserBackend = BrowserBackend.PLAYWRIGHT):
        self.backend = backend

    def navigate(self, url: str) -> dict[str, Any]:
        """Generate navigate command."""
        if self.backend == BrowserBackend.PUPPETEER:
            return PuppeteerHelper.navigate(url)
        else:
            return PlaywrightHelper.navigate(url)

    def click(
        self,
        selector: str | None = None,
        element: str | None = None,
        ref: str | None = None,
    ) -> dict[str, Any]:
        """Generate click command."""
        if self.backend == BrowserBackend.PUPPETEER:
            if not selector:
                raise ValueError("Puppeteer requires selector")
            return PuppeteerHelper.click(selector)
        else:
            if not element or not ref:
                raise ValueError("Playwright requires element and ref")
            return PlaywrightHelper.click(element, ref)

    def type_text(
        self,
        text: str,
        selector: str | None = None,
        element: str | None = None,
        ref: str | None = None,
    ) -> dict[str, Any]:
        """Generate type text command."""
        if self.backend == BrowserBackend.PUPPETEER:
            if not selector:
                raise ValueError("Puppeteer requires selector")
            return PuppeteerHelper.fill(selector, text)
        else:
            if not element or not ref:
                raise ValueError("Playwright requires element and ref")
            return PlaywrightHelper.type_text(element, ref, text)

    def screenshot(self, name: str | None = None) -> dict[str, Any]:
        """Generate screenshot command."""
        if self.backend == BrowserBackend.PUPPETEER:
            return PuppeteerHelper.screenshot(name or "screenshot")
        else:
            return PlaywrightHelper.screenshot(name)

    def wait(self, text: str | None = None, seconds: float | None = None) -> dict[str, Any]:
        """Generate wait command."""
        if self.backend == BrowserBackend.PLAYWRIGHT:
            if text:
                return PlaywrightHelper.wait_for_text(text)
            elif seconds:
                return PlaywrightHelper.wait_for_time(seconds)
        # Puppeteer doesn't have native wait - use evaluate
        return PuppeteerHelper.evaluate(f"await new Promise(r => setTimeout(r, {int((seconds or 1) * 1000)}))")

    def get_page_info(self) -> dict[str, Any]:
        """Get page info command."""
        if self.backend == BrowserBackend.PLAYWRIGHT:
            return PlaywrightHelper.snapshot()
        else:
            return PuppeteerHelper.evaluate("({url: location.href, title: document.title})")


def get_browser_instructions(backend: BrowserBackend = BrowserBackend.PLAYWRIGHT) -> str:
    """
    Get instructions for agent on how to use browser automation.

    Returns markdown instructions for inclusion in agent prompts.
    """
    if backend == BrowserBackend.PUPPETEER:
        return """
## Browser Testing (Puppeteer)

Use these tools for browser automation:

1. **Navigate**: `mcp__puppeteer__puppeteer_navigate` with `url`
2. **Click**: `mcp__puppeteer__puppeteer_click` with `selector` (CSS)
3. **Fill**: `mcp__puppeteer__puppeteer_fill` with `selector` and `value`
4. **Screenshot**: `mcp__puppeteer__puppeteer_screenshot` with `name`
5. **Evaluate**: `mcp__puppeteer__puppeteer_evaluate` with `script`

Example flow:
1. Navigate to localhost:3000
2. Fill #email with "test@example.com"
3. Click button[type="submit"]
4. Screenshot "after_login"
"""
    else:
        return """
## Browser Testing (Playwright)

Use these tools for browser automation:

1. **Navigate**: `mcp__playwright__browser_navigate` with `url`
2. **Snapshot**: `mcp__playwright__browser_snapshot` to get accessibility tree
3. **Click**: `mcp__playwright__browser_click` with `element` (description) and `ref` (from snapshot)
4. **Type**: `mcp__playwright__browser_type` with `element`, `ref`, and `text`
5. **Wait**: `mcp__playwright__browser_wait_for` with `text` or `time`
6. **Screenshot**: `mcp__playwright__browser_take_screenshot`

Example flow:
1. Navigate to localhost:3000
2. Snapshot to see available elements
3. Click element="Submit button" ref="B1"
4. Wait for text="Success"
5. Screenshot
"""


def get_default_browser_config() -> BrowserConfig:
    """Get default browser configuration."""
    return BrowserConfig(backend=BrowserBackend.BOTH)
