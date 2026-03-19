"""Browser automation module exports."""

from .manager import (
    BrowserBackend,
    BrowserConfig,
    UnifiedBrowser,
    get_browser_instructions,
    get_default_browser_config,
)
from .playwright import (
    PLAYWRIGHT_TOOLS,
    PlaywrightConfig,
    PlaywrightHelper,
    get_playwright_config,
    get_playwright_tool_list,
)
from .puppeteer import (
    PUPPETEER_TOOLS,
    PuppeteerConfig,
    PuppeteerHelper,
    get_puppeteer_config,
    get_puppeteer_tool_list,
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
