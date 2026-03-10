"""
MCP Server Management
=====================

Manages Model Context Protocol server configurations.
"""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MCPServer:
    """An MCP server configuration."""
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    def to_config(self) -> dict[str, Any]:
        """Convert to config format."""
        config = {
            "command": self.command,
            "args": self.args,
        }
        if self.env:
            config["env"] = self.env
        return config


# Built-in MCP server configurations
BUILTIN_SERVERS = {
    "puppeteer": MCPServer(
        name="puppeteer",
        command="npx",
        args=["puppeteer-mcp-server"],
    ),
    "playwright": MCPServer(
        name="playwright",
        command="npx",
        args=["@executeautomation/playwright-mcp-server"],
    ),
    "filesystem": MCPServer(
        name="filesystem",
        command="npx",
        args=["@anthropic/mcp-server-filesystem"],
    ),
    "git": MCPServer(
        name="git",
        command="npx",
        args=["@anthropic/mcp-server-git"],
    ),
    "fetch": MCPServer(
        name="fetch",
        command="npx",
        args=["@anthropic/mcp-server-fetch"],
    ),
}


class MCPServerManager:
    """
    Manages MCP server configurations.
    """

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or (Path.home() / ".claude" / "mcp_servers.json")
        self._servers: dict[str, MCPServer] = {}
        self._loaded = False

    def load(self) -> None:
        """Load servers from config file."""
        # Start with builtins
        self._servers = {name: server for name, server in BUILTIN_SERVERS.items()}

        # Load custom servers
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    data = json.load(f)

                for name, config in data.items():
                    self._servers[name] = MCPServer(
                        name=name,
                        command=config.get("command", ""),
                        args=config.get("args", []),
                        env=config.get("env", {}),
                    )
            except (json.JSONDecodeError, IOError):
                pass

        self._loaded = True

    def save(self) -> None:
        """Save custom servers to config file."""
        # Only save non-builtin servers
        custom = {
            name: server.to_config()
            for name, server in self._servers.items()
            if name not in BUILTIN_SERVERS
        }

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(custom, f, indent=2)

    def get(self, name: str) -> MCPServer | None:
        """Get server by name."""
        if not self._loaded:
            self.load()
        return self._servers.get(name)

    def list_all(self) -> list[MCPServer]:
        """List all servers."""
        if not self._loaded:
            self.load()
        return list(self._servers.values())

    def add(self, server: MCPServer) -> None:
        """Add or update a server."""
        if not self._loaded:
            self.load()
        self._servers[server.name] = server
        self.save()

    def remove(self, name: str) -> bool:
        """Remove a server."""
        if not self._loaded:
            self.load()
        if name in self._servers and name not in BUILTIN_SERVERS:
            del self._servers[name]
            self.save()
            return True
        return False

    def get_config_for_client(
        self,
        names: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get MCP server config for SDK client.

        Args:
            names: Server names to include (None = all enabled)

        Returns:
            Dict suitable for ClaudeAgentOptions.mcp_servers
        """
        if not self._loaded:
            self.load()

        if names is None:
            servers = [s for s in self._servers.values() if s.enabled]
        else:
            servers = [self._servers[n] for n in names if n in self._servers]

        return {s.name: s.to_config() for s in servers}

    def check_availability(self, name: str) -> bool:
        """Check if an MCP server is available (command exists)."""
        server = self.get(name)
        if not server:
            return False

        try:
            # Check if command is available
            result = subprocess.run(
                ["which", server.command],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False


def get_default_mcp_servers() -> dict[str, Any]:
    """Get default MCP server configuration."""
    manager = MCPServerManager()
    return manager.get_config_for_client(["puppeteer", "playwright"])


def list_mcp_servers() -> list[dict[str, Any]]:
    """List all available MCP servers."""
    manager = MCPServerManager()
    return [
        {
            "name": s.name,
            "command": s.command,
            "builtin": s.name in BUILTIN_SERVERS,
        }
        for s in manager.list_all()
    ]
