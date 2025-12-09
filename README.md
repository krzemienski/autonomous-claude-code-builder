# Autonomous CLI (acli)

Interactive autonomous coding tool with real-time streaming dashboard, spec enhancement, and multi-agent visibility.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Real-time Dashboard**: Multi-pane TUI showing tool execution, logs, and progress
- **Spec Enhancement**: Convert plain English descriptions to structured JSON specs
- **Two-Agent Pattern**: Initializer + Coding agents for systematic development
- **Browser Automation**: Puppeteer and Playwright MCP integration for testing
- **Progress Tracking**: Feature-based progress with persistence
- **Security Model**: 16-command allowlist with defense-in-depth

## Installation

```bash
# Using pip
pip install autonomous-cli

# From source
git clone https://github.com/claude-code-skills-factory/autonomous-cli
cd autonomous-cli
pip install -e .
```

## Quick Start

```bash
# 1. Initialize a new project
acli init my_app

# 2. Add your app specification
echo "Build a todo app with add, complete, and delete tasks" > my_app/app_spec.txt

# 3. Run the autonomous agent
cd my_app
acli run

# 4. Check progress
acli status
```

## Commands

| Command | Description |
|---------|-------------|
| `acli init <name>` | Initialize new project with spec enhancement |
| `acli run [dir]` | Run autonomous coding loop |
| `acli status [dir]` | Show progress status |
| `acli enhance [file]` | Enhance plain-text spec interactively |
| `acli config` | Manage configuration |

## Dashboard

The real-time dashboard shows:

```
┌──────────────────────────────────────────────────────────┐
│                    AUTONOMOUS CLI                         │
├────────────────────┬─────────────────────────────────────┤
│    Tool Board      │              Logs                    │
│ ✓ Bash (1.2s)      │ 14:32:15 [INF] Session started      │
│ ✓ Write (0.5s)     │ 14:32:16 [TOL] Tool: Bash           │
│ → Read (0.3s...)   │ 14:32:17 [TOL] Tool: Write          │
├────────────────────┴─────────────────────────────────────┤
│ Progress: 15/200 (7.5%) ████░░░░░░░░░░░░░░░░            │
└──────────────────────────────────────────────────────────┘
```

## Configuration

```bash
# Set default model
acli config model claude-opus-4

# Set max iterations
acli config max_iterations 10

# List all config
acli config --list
```

Configuration file: `~/.config/acli/config.json`

## Security

The agent operates with restricted permissions:

- **Sandbox**: OS-level bash isolation
- **Filesystem**: Project directory only
- **Commands**: 16 allowed commands (ls, cat, npm, git, etc.)
- **Validators**: Extra validation for pkill, chmod, init.sh

### Allowed Commands

```python
# File inspection
ls, cat, head, tail, wc, grep

# File operations
cp, mkdir, chmod (+x only)

# Node.js development
npm, node

# Version control
git

# Process management
ps, lsof, sleep, pkill (dev processes only)

# Script execution
init.sh (./init.sh only)
```

## Requirements

- Python 3.11+
- Node.js 18+ (for MCP servers)
- ANTHROPIC_API_KEY environment variable

### Optional MCP Servers

For browser automation:

```bash
# Puppeteer (default)
npm install -g puppeteer-mcp-server

# Playwright (alternative)
npm install -g @executeautomation/playwright-mcp-server
```

## Documentation

- [Installation Guide](docs/installation.md)
- [Quick Start](docs/quickstart.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)

## Architecture

### Two-Agent Pattern

**Session 1: Initializer**
- Reads `app_spec.txt`
- Generates `feature_list.json` (~200 test cases)
- Creates project structure
- Runs `init.sh` setup script

**Sessions 2+: Coding Agent**
- Reads progress from `feature_list.json`
- Implements ONE feature at a time
- Tests with browser automation
- Marks feature as passing
- Commits changes

### Progress Tracking

Progress is tracked in `feature_list.json`:

```json
[
  {
    "id": 1,
    "component": "Login",
    "description": "Email input accepts valid format",
    "passes": true
  },
  {
    "id": 2,
    "component": "Login",
    "description": "Password toggles visibility",
    "passes": false
  }
]
```

## Development

```bash
# Clone repository
git clone https://github.com/claude-code-skills-factory/autonomous-cli
cd autonomous-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=acli --cov-report=html

# Type checking
mypy src/acli

# Linting
ruff check src/
```

## Testing

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_security.py

# Run with verbose output
pytest -v

# Run integration tests
pytest -m integration
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Support

- Issues: https://github.com/claude-code-skills-factory/autonomous-cli/issues
- Documentation: https://github.com/claude-code-skills-factory/autonomous-cli#readme

## Credits

Built with:
- [Claude Code SDK](https://github.com/anthropics/claude-code-sdk)
- [Rich](https://github.com/Textualize/rich) - Terminal UI
- [Typer](https://github.com/tiangolo/typer) - CLI framework
- [Pydantic](https://github.com/pydantic/pydantic) - Data validation
