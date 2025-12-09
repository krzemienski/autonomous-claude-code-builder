# Browser Automation Module

## Overview

The browser automation module provides unified access to Puppeteer and Playwright MCP servers for browser-based feature verification.

## Architecture

```
src/acli/browser/
├── __init__.py      # Module exports
├── puppeteer.py     # Puppeteer MCP wrapper (7 tools)
├── playwright.py    # Playwright MCP wrapper (7 tools)
└── manager.py       # Unified interface & session manager
```

## Quick Start

### Basic Usage

```python
from acli.browser import (
    BrowserBackend,
    BrowserConfig,
    UnifiedBrowser,
    get_default_browser_config,
)

# Get default configuration (both backends)
config = get_default_browser_config()
servers = config.get_mcp_servers()
tools = config.get_tool_list()

# Use unified browser interface
browser = UnifiedBrowser(BrowserBackend.PLAYWRIGHT)
browser.navigate("http://localhost:3000")
browser.screenshot("homepage")
```

### Configuration

```python
# Playwright only
config = BrowserConfig(backend=BrowserBackend.PLAYWRIGHT)

# Puppeteer only
config = BrowserConfig(backend=BrowserBackend.PUPPETEER)

# Both (default)
config = BrowserConfig(backend=BrowserBackend.BOTH)
```

## Available Tools

### Puppeteer Tools (7)
- `navigate` - Navigate to URL
- `screenshot` - Capture page/element
- `click` - Click element (CSS selector)
- `fill` - Fill input field
- `select` - Select dropdown option
- `hover` - Hover over element
- `evaluate` - Execute JavaScript

### Playwright Tools (7)
- `navigate` - Navigate to URL
- `snapshot` - Get accessibility tree
- `click` - Click element (accessibility ref)
- `type` - Type text into element
- `screenshot` - Capture page/element
- `wait_for` - Wait for text or time
- `tabs` - Manage browser tabs

## Helper Classes

### PuppeteerHelper

```python
from acli.browser import PuppeteerHelper

# Generate tool calls
PuppeteerHelper.navigate("http://example.com")
PuppeteerHelper.click("#submit-btn")
PuppeteerHelper.fill("#email", "test@example.com")
PuppeteerHelper.screenshot("login-page")
PuppeteerHelper.evaluate("console.log('test')")

# Advanced helpers
PuppeteerHelper.get_text(".title")
PuppeteerHelper.wait_for_selector(".loading", timeout_ms=5000)
```

### PlaywrightHelper

```python
from acli.browser import PlaywrightHelper

# Generate tool calls
PlaywrightHelper.navigate("http://example.com")
PlaywrightHelper.snapshot()
PlaywrightHelper.click("Submit Button", "B1")
PlaywrightHelper.type_text("Email Field", "I1", "test@example.com")
PlaywrightHelper.screenshot("login-page.png", full_page=True)
PlaywrightHelper.wait_for_text("Success")
PlaywrightHelper.wait_for_time(2.5)
PlaywrightHelper.new_tab("http://example.com")
```

## Integration with Orchestrator

```python
from acli.browser import get_puppeteer_config, get_playwright_config

# Add to MCP servers
mcp_servers = {
    "puppeteer": get_puppeteer_config(),
    "playwright": get_playwright_config(),
}

# Whitelist browser tools
from acli.browser import get_puppeteer_tool_list, get_playwright_tool_list

allowed_tools = (
    get_puppeteer_tool_list() + 
    get_playwright_tool_list()
)
```

## Agent Instructions

```python
from acli.browser import get_browser_instructions, BrowserBackend

# Add to agent prompt
playwright_instructions = get_browser_instructions(BrowserBackend.PLAYWRIGHT)
puppeteer_instructions = get_browser_instructions(BrowserBackend.PUPPETEER)
```

## Testing

All modules include comprehensive tests:

- Syntax validation
- Import verification
- Configuration generation
- Tool count verification (14 total)
- Helper method functionality
- Unified interface abstraction
- MCP server config format

Run tests:
```bash
python3 -m py_compile src/acli/browser/*.py
python3 -c "from src.acli.browser import *"
```

## Dependencies

- Python 3.10+ (for union type syntax)
- MCP protocol support
- Puppeteer MCP server (via npx)
- Playwright MCP server (via npx)

## File Ownership

Phase 08 exclusively owns:
- `src/acli/browser/puppeteer.py`
- `src/acli/browser/playwright.py`
- `src/acli/browser/manager.py`
- `src/acli/browser/__init__.py`

No conflicts with other parallel phases.
