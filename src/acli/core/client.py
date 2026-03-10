"""
Claude SDK Client Configuration
================================

Setup and configuration for ClaudeSDKClient with security settings.
"""

import json
import os
from pathlib import Path
from typing import Any, Literal, cast

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import HookMatcher

from ..security import bash_security_hook


# MCP tool definitions
PUPPETEER_TOOLS = [
    "mcp__puppeteer__puppeteer_navigate",
    "mcp__puppeteer__puppeteer_screenshot",
    "mcp__puppeteer__puppeteer_click",
    "mcp__puppeteer__puppeteer_fill",
    "mcp__puppeteer__puppeteer_select",
    "mcp__puppeteer__puppeteer_hover",
    "mcp__puppeteer__puppeteer_evaluate",
]

PLAYWRIGHT_TOOLS = [
    "mcp__playwright__browser_navigate",
    "mcp__playwright__browser_snapshot",
    "mcp__playwright__browser_click",
    "mcp__playwright__browser_type",
    "mcp__playwright__browser_take_screenshot",
    "mcp__playwright__browser_wait_for",
    "mcp__playwright__browser_tabs",
]

BUILTIN_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]


def create_security_settings(project_dir: Path) -> dict[str, Any]:
    """
    Create security settings dict.

    Args:
        project_dir: Project directory

    Returns:
        Security settings dictionary
    """
    return {
        "sandbox": {"enabled": True, "autoAllowBashIfSandboxed": True},
        "permissions": {
            "defaultMode": "acceptEdits",
            "allow": [
                "Read(./**)",
                "Write(./**)",
                "Edit(./**)",
                "Glob(./**)",
                "Grep(./**)",
                "Bash(*)",
                *PUPPETEER_TOOLS,
                *PLAYWRIGHT_TOOLS,
            ],
        },
    }


def create_sdk_client(
    project_dir: Path,
    model: str,
    system_prompt: str | None = None,
) -> ClaudeSDKClient:
    """
    Create Claude SDK client with security configuration.

    Args:
        project_dir: Project directory (cwd for agent)
        model: Claude model to use
        system_prompt: Optional system prompt override

    Returns:
        Configured ClaudeSDKClient
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    project_dir = project_dir.resolve()
    project_dir.mkdir(parents=True, exist_ok=True)

    # Write security settings
    settings = create_security_settings(project_dir)
    settings_file = project_dir / ".claude_settings.json"
    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2)

    # MCP servers configuration
    mcp_servers: dict[str, Any] = {
        "puppeteer": {
            "command": "npx",
            "args": ["puppeteer-mcp-server"],
        },
        "playwright": {
            "command": "npx",
            "args": ["@executeautomation/playwright-mcp-server"],
        },
    }

    # Security hooks - cast to expected type
    hooks = cast(
        dict[
            Literal[
                "PreToolUse",
                "PostToolUse",
                "UserPromptSubmit",
                "Stop",
                "SubagentStop",
                "PreCompact",
            ],
            list[HookMatcher],
        ],
        {
            "PreToolUse": [
                HookMatcher(matcher="Bash", hooks=[bash_security_hook]),
            ],
        },
    )

    default_system = (
        "You are an expert full-stack developer building a production-quality "
        "web application. Follow best practices and write clean, tested code."
    )

    return ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=model,
            system_prompt=system_prompt or default_system,
            allowed_tools=[*BUILTIN_TOOLS, *PUPPETEER_TOOLS, *PLAYWRIGHT_TOOLS],
            mcp_servers=mcp_servers,
            hooks=hooks,
            max_turns=100,
            cwd=str(project_dir),
            settings=str(settings_file),
        )
    )
