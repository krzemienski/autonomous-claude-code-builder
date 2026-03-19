"""
Claude Config Discovery
=======================

Discovers and reads configuration from ~/.claude/ directory.
Provides optional integration with Claude Code ecosystem.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ClaudeConfig:
    """Configuration from ~/.claude/ directory."""

    # Paths
    claude_home: Path = field(default_factory=lambda: Path.home() / ".claude")

    # Discovered settings
    api_key: str | None = None
    default_model: str | None = None
    mcp_servers: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)

    @property
    def exists(self) -> bool:
        """Check if ~/.claude/ directory exists."""
        return self.claude_home.exists()

    @property
    def config_file(self) -> Path:
        """Path to main config file."""
        return self.claude_home / "config.json"

    @property
    def settings_file(self) -> Path:
        """Path to settings file."""
        return self.claude_home / "settings.json"

    @property
    def skills_dir(self) -> Path:
        """Path to skills directory."""
        return self.claude_home / "skills"

    @property
    def mcp_servers_file(self) -> Path:
        """Path to MCP servers config."""
        return self.claude_home / "mcp_servers.json"


def discover_claude_config() -> ClaudeConfig:
    """
    Discover Claude Code configuration.

    Reads from:
    - ~/.claude/config.json
    - ~/.claude/settings.json
    - ~/.claude/mcp_servers.json
    - Environment variables (ANTHROPIC_API_KEY)
    """
    config = ClaudeConfig()

    if not config.exists:
        # No ~/.claude/ directory - check env only
        config.api_key = os.environ.get("ANTHROPIC_API_KEY")
        return config

    # Read config.json
    if config.config_file.exists():
        try:
            with open(config.config_file) as f:
                data = json.load(f)
            config.api_key = data.get("api_key")
            config.default_model = data.get("model")
        except (json.JSONDecodeError, IOError):
            pass

    # Read settings.json
    if config.settings_file.exists():
        try:
            with open(config.settings_file) as f:
                config.settings = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Read MCP servers
    if config.mcp_servers_file.exists():
        try:
            with open(config.mcp_servers_file) as f:
                config.mcp_servers = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Override with environment
    env_key = os.environ.get("ANTHROPIC_API_KEY")
    if env_key:
        config.api_key = env_key

    return config


def get_api_key() -> str | None:
    """Get API key from config or environment."""
    config = discover_claude_config()
    return config.api_key


def get_default_model() -> str:
    """Get default model from config or use fallback."""
    config = discover_claude_config()
    return config.default_model or "claude-sonnet-4-6"


def get_mcp_servers() -> dict[str, Any]:
    """Get MCP servers from Claude config."""
    config = discover_claude_config()
    return config.mcp_servers


def generate_client_settings(
    project_dir: Path,
    additional_permissions: list[str] | None = None,
) -> Path:
    """
    Generate .claude_settings.json for a project.

    Merges global settings with project-specific ones.
    """
    config = discover_claude_config()

    # Base settings
    settings = {
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
            ],
        },
    }

    # Add additional permissions
    if additional_permissions:
        settings["permissions"]["allow"].extend(additional_permissions)

    # Merge with global settings if available
    if config.settings:
        global_perms = config.settings.get("permissions", {}).get("allow", [])
        settings["permissions"]["allow"].extend(global_perms)

    # Write to project
    settings_path = project_dir / ".claude_settings.json"
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    return settings_path


def is_claude_available() -> bool:
    """Check if Claude Code ecosystem is available."""
    config = discover_claude_config()
    return config.exists and config.api_key is not None
