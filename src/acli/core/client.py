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
from ..validation.mock_detector import mock_detection_hook

# Model routing constants
MODEL_OPUS = "claude-opus-4-6"
MODEL_SONNET = "claude-sonnet-4-6"

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
    model: str | None = None,
    system_prompt: str | None = None,
    model_tier: Literal["opus", "sonnet"] = "sonnet",
) -> ClaudeSDKClient:
    """
    Create Claude SDK client with security configuration.

    Args:
        project_dir: Project directory (cwd for agent)
        model: Explicit Claude model override (takes precedence over model_tier)
        system_prompt: Optional system prompt override
        model_tier: Model tier selection — "opus" for deep reasoning, "sonnet" for standard

    Returns:
        Configured ClaudeSDKClient
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    # Resolve model: explicit override > tier-based selection
    if model:
        resolved_model = model
    elif model_tier == "opus":
        resolved_model = MODEL_OPUS
    else:
        resolved_model = MODEL_SONNET

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
                HookMatcher(matcher="Write", hooks=[mock_detection_hook]),
                HookMatcher(matcher="Edit", hooks=[mock_detection_hook]),
            ],
        },
    )

    default_system = (
        "You are an expert full-stack developer building a production-quality "
        "web application. Follow best practices and write clean, tested code."
    )

    # Build options with tier-specific thinking/effort
    options_kwargs: dict[str, Any] = {
        "model": resolved_model,
        "system_prompt": system_prompt or default_system,
        "allowed_tools": [*BUILTIN_TOOLS, *PUPPETEER_TOOLS, *PLAYWRIGHT_TOOLS],
        "mcp_servers": mcp_servers,
        "hooks": hooks,
        "max_turns": 200,
        "cwd": str(project_dir),
        "settings": str(settings_file),
        "thinking": {"type": "adaptive"},
    }

    if model_tier == "opus":
        options_kwargs["effort"] = "high"

    return ClaudeSDKClient(
        options=ClaudeAgentOptions(**options_kwargs)
    )
