"""Browser automation module exports."""

from .puppeteer import (
    PuppeteerConfig,
    PuppeteerHelper,
    PUPPETEER_TOOLS,
    get_puppeteer_tool_list,
    get_puppeteer_config,
)
from .playwright import (
    PlaywrightConfig,
    PlaywrightHelper,
    PLAYWRIGHT_TOOLS,
    get_playwright_tool_list,
    get_playwright_config,
)
from .manager import (
    BrowserBackend,
    BrowserConfig,
    UnifiedBrowser,
    get_browser_instructions,
    get_default_browser_config,
)

__all__ = [
    # Puppeteer
    "PuppeteerConfig",
    "PuppeteerHelper",
    "PUPPETEER_TOOLS",
    "get_puppeteer_tool_list",
    "get_puppeteer_config",
    # Playwright
    "PlaywrightConfig",
    "PlaywrightHelper",
    "PLAYWRIGHT_TOOLS",
    "get_playwright_tool_list",
    "get_playwright_config",
    # Manager/Unified
    "BrowserBackend",
    "BrowserConfig",
    "UnifiedBrowser",
    "get_browser_instructions",
    "get_default_browser_config",
]
