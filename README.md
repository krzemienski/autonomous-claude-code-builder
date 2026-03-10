# Autonomous CLI (acli)

Interactive autonomous coding tool with cyberpunk agent monitoring TUI, real-time streaming, spec enhancement, and multi-agent visibility.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Cyberpunk Agent Monitor TUI**: Full-screen Textual dashboard with agent hierarchy visualization, real-time log streaming, drill-down detail views, and neon-themed interface
- **Two-Agent Pattern**: Initializer + Coding agents for systematic development
- **Real-time Streaming**: Event-driven architecture streaming all agent activity to the TUI
- **Spec Enhancement**: Convert plain English descriptions to structured JSON specs
- **Browser Automation**: Puppeteer and Playwright MCP integration for testing
- **Progress Tracking**: Feature-based progress with persistence
- **Security Model**: 16-command allowlist with defense-in-depth
- **Claude Agent SDK**: Built on the latest Anthropic Agent SDK (`claude-agent-sdk>=0.1.48`)

## Installation

```bash
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

# 3. Run with the cyberpunk TUI dashboard
cd my_app
acli run

# 4. Or launch the dedicated monitor TUI
acli monitor

# 5. Check progress
acli status
```

## Commands

| Command | Description |
|---------|-------------|
| `acli init <name>` | Initialize new project with spec enhancement |
| `acli run [dir]` | Run autonomous coding loop (launches TUI by default) |
| `acli monitor [dir]` | Launch cyberpunk TUI for real-time agent monitoring |
| `acli status [dir]` | Show progress status |
| `acli enhance [file]` | Enhance plain-text spec interactively |
| `acli config` | Manage configuration |
| `acli list-skills` | Discover available skills |

## Agent Monitor TUI

The `acli monitor` command (or `acli run --dashboard`) launches a full-screen cyberpunk-themed terminal dashboard:

```
┌──────────────────────────────────────────────────────────────┐
│  ⟁ ACLI AGENT MONITOR │ ● RUNNING │ S#2 [coding] │ 05:30  │
├────────────────────┬─────────────────────────────────────────┤
│  AGENT HIERARCHY   │ LOGS │ F1:All F2:Tools F3:Errors F4:Text│
│  ◆ ORCHESTRATOR    │ 14:32:15 TXT Creating structure...      │
│  ├─ ✓ S#1 [init]  │ 14:32:16 TOL ▶ Bash npm init -y         │
│  ╰─ ◆ S#2 [code]  │ 14:32:17 TOL ✓ Bash 150ms OK            │
│    ⚡ Write        │ 14:32:18 SES ═══ Session #2 END ═══     │
│────────────────────├─────────────────────────────────────────┤
│  ◆ CODING          │ PROGRESS ████████░░░░░░ 10/200 5.0%    │
│  Status: running   │ Sessions: 2 │ Tools: 15 │ Errors: 0    │
│  Duration: 5m30s   │ RECENT TOOLS                             │
│  Tools: 15         │   ✓ Write 88ms │ → Read 23ms...         │
├────────────────────┴─────────────────────────────────────────┤
│ q Quit  p Pause/Resume  s Stop  ↑↓ Navigate  Enter Detail   │
└──────────────────────────────────────────────────────────────┘
```

### TUI Features

- **Agent Hierarchy Graph**: Visualize orchestrator and all session agents with status icons, tool indicators, duration, and error counts
- **Full-Verbosity Log Streaming**: Every event (text, tools, sessions, progress, errors) streamed in real-time with color-coded levels
- **Agent Drill-Down**: Select any agent with j/k keys and press Enter to see full details
- **Log Filtering**: F1 (All), F2 (Tools only), F3 (Errors only), F4 (Text only)
- **Live Controls**: Pause (p), Resume (p), Stop (s) the running orchestrator
- **Stats Dashboard**: Feature progress bar, session count, tool calls, error rate
- **Recent Tool Board**: Last 8 tool executions with status icons and timing
- **Cyberpunk Neon Theme**: Deep navy (#000b1e), neon cyan (#0abdc6), hot pink (#ea00d9), matrix green (#00ff41)

### Monitor Modes

```bash
# Attach mode (default): launches orchestrator + TUI together
acli monitor ./my_app

# Detached mode: view-only, connect to existing project state
acli monitor ./my_app --detached

# With custom model and iteration limit
acli monitor ./my_app --model claude-sonnet-4-20250514 --max-iterations 10
```

## Configuration

```bash
acli config model claude-opus-4
acli config max_iterations 10
acli config --list
```

Configuration file: `~/.config/acli/config.json`

## Security

The agent operates with restricted permissions:

- **Sandbox**: OS-level bash isolation
- **Filesystem**: Project directory only
- **Commands**: 16 allowed commands (ls, cat, npm, git, etc.)
- **Validators**: Extra validation for pkill, chmod, init.sh

## Architecture

### Two-Agent Pattern

**Session 1: Initializer** - Reads `app_spec.txt`, generates `feature_list.json` (~200 test cases), creates project structure

**Sessions 2+: Coding Agent** - Implements ONE feature at a time, tests with browser automation, marks passing, commits

### System Components

```
src/acli/
├── cli.py          # Typer CLI (7 commands)
├── core/           # Agent orchestration (Claude Agent SDK)
├── tui/            # Cyberpunk Agent Monitor TUI (Textual)
├── ui/             # Legacy Rich dashboard (fallback)
├── security/       # Defense-in-depth security
├── spec/           # Spec enhancement
├── progress/       # Progress tracking
├── browser/        # Browser automation (Puppeteer/Playwright)
├── integration/    # External integrations
└── prompts/        # Prompt templates
```

## Requirements

- Python 3.11+
- Node.js 18+ (for MCP servers)
- `ANTHROPIC_API_KEY` environment variable
- `claude-agent-sdk>=0.1.48`
- `textual>=1.0.0`

## Development

```bash
pip install -e ".[dev]"

# Run TUI functional validation
bash tests/functional/07-tui-validation.sh

# Run security tests
python -m pytest tests/test_security.py -v
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design with TUI architecture
- [Quick Start](docs/QUICKSTART.md) - Getting started guide
- [API Reference](docs/API.md) - Python API reference
- [Orchestrator](docs/ORCHESTRATOR.md) - Agent orchestration engine

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Built with:
- [Claude Agent SDK](https://github.com/anthropics/claude-code-sdk) - Anthropic Agent SDK
- [Textual](https://github.com/Textualize/textual) - TUI framework
- [Rich](https://github.com/Textualize/rich) - Terminal formatting
- [Typer](https://github.com/tiangolo/typer) - CLI framework
- [Pydantic](https://github.com/pydantic/pydantic) - Data validation
