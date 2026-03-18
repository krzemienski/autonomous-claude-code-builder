# CLAUDE.md — Autonomous CLI (acli)

## Project Overview

Autonomous CLI (`acli`) is a Python CLI tool providing Claude Code-like autonomous coding with a cyberpunk-themed TUI dashboard. It uses the Claude Agent SDK to orchestrate multi-agent workflows that read specs, generate feature lists, and implement features autonomously with browser-based testing.

**Version**: 1.0.0 | **License**: MIT | **Python**: >=3.11

## Quick Reference

```bash
# Install (development)
pip install -e ".[dev]"

# CLI commands
acli init <project-dir>          # Initialize a new project
acli run <project-dir>           # Run autonomous coding agents
acli monitor <project-dir>       # Launch cyberpunk TUI dashboard
acli status <project-dir>        # Show project status
acli enhance <spec-file>         # Enhance a spec with AI
acli config get|set|list [key]   # Manage configuration
acli list-skills                 # List available skills

# Run tests
pytest tests/test_security.py -v          # 67 security tests
bash tests/run_e2e.sh                     # Full E2E suite (8 functional tests)
bash tests/functional/07-tui-validation.sh # TUI-specific tests
```

## Repository Structure

```
src/acli/                  # Main package (~6,100 LOC across 40 files)
├── cli.py                 # Typer CLI entry point (7 commands)
├── __main__.py            # python -m acli entry point
├── core/                  # Agent orchestration (Claude Agent SDK)
│   ├── orchestrator.py    # Two-agent pattern (Initializer + Coding)
│   ├── agent.py           # Agent session execution
│   ├── client.py          # SDK client with security settings
│   ├── session.py         # Project state management
│   └── streaming.py       # Event-driven streaming architecture
├── tui/                   # Cyberpunk Agent Monitor (Textual framework)
│   ├── app.py             # Main TUI application
│   ├── bridge.py          # Real orchestrator connection
│   ├── widgets.py         # UI components (panels, logs, stats)
│   └── cyberpunk.tcss     # Neon theme (navy/cyan/pink/green)
├── ui/                    # Legacy Rich dashboard (fallback)
├── spec/                  # Spec enhancement (plain English → JSON)
│   ├── enhancer.py        # LLM-powered spec conversion
│   ├── refinement.py      # Interactive refinement loop
│   ├── schemas.py         # Pydantic data models
│   └── validator.py       # Spec validation
├── security/              # Defense-in-depth security model
│   ├── validators.py      # Per-command validators
│   └── hooks.py           # Pre-tool-use security hooks
├── progress/              # Feature progress tracking with persistence
├── browser/               # Browser automation (Puppeteer + Playwright MCP)
├── integration/           # External integrations (Claude config, skills, MCP)
├── prompts/templates/     # Agent prompt templates (initializer.md, coding.md)
└── utils/                 # Logging and event definitions

tests/                     # FUNCTIONAL TESTS ONLY (no mocks)
├── run_e2e.sh             # Master test runner
├── test_security.py       # 67 security tests (Python/pytest)
└── functional/            # 9 shell script E2E tests (00-setup → 99-cleanup)

docs/                      # Documentation
├── ARCHITECTURE.md        # System design and components
├── QUICKSTART.md          # Getting started guide
├── API.md                 # Python API reference
├── ORCHESTRATOR.md        # Agent orchestration details
└── browser-automation.md  # Browser automation guide
```

## Architecture

### Two-Agent Pattern

1. **Initializer Agent** (Session #1): Reads `app_spec.txt`, generates `feature_list.json` (~200 features), creates project structure
2. **Coding Agent** (Sessions 2+): Implements ONE feature at a time, tests with browser automation, commits passing features, resumes from progress file

### Security Model (16-Command Allowlist)

Allowed commands: `ls`, `cat`, `npm`, `npx`, `git`, `python`, `pip`, `node`, `curl`, `wget`, `touch`, `mkdir`, `rm`, `echo`, `chmod`, `pkill`

Per-command validators:
- `pkill`: Only dev processes (node, npm, npx, vite, next, webpack, tsc)
- `chmod`: Only `+x` mode
- `init.sh`: Must be `./init.sh` exactly

Defense layers: OS sandbox → file permissions → command allowlist → shlex parsing → pre-tool-use hooks

### Streaming & TUI

- Event-driven `StreamBuffer` for real-time agent activity
- Textual-based cyberpunk TUI with agent hierarchy, live logs, stats dashboard
- Keyboard navigation: `j/k` scroll, `F1-F4` filter tabs, `p/s/q` controls

## Development Workflow

### Setup

```bash
git clone <repo-url>
cd autonomous-claude-code-builder
pip install -e ".[dev]"
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude Agent SDK |

Config resolution order: env vars → `~/.config/acli/config.json` → `~/.claude/config.json`

### Code Quality

```bash
ruff check src/                  # Lint (PEP 8, line-length: 100)
mypy src/acli/                   # Type check (strict mode)
pytest tests/test_security.py -v # Security tests
```

### Testing Strategy

**No mocks, no unit tests** — functional/E2E tests only:
- `tests/test_security.py`: 67 Python tests for security validators
- `tests/functional/00-99`: Shell script E2E tests for full workflows
- Coverage targets: 80% overall, 100% security, 90% core

### Commit Convention

Conventional Commits: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`

## Code Conventions

- **Style**: PEP 8 via ruff, 100-char line length, Python 3.11 target
- **Type hints**: Mandatory (`mypy --strict`, `disallow_untyped_defs: true`)
- **Docstrings**: Google-style format
- **Imports**: stdlib → third-party → local
- **Async**: All orchestrator/agent code uses `async/await` with `asyncio`
- **Validation**: Pydantic v2 models for all data schemas

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `claude-agent-sdk>=0.1.48` | Claude Agents API integration |
| `typer>=0.9.0` | CLI framework |
| `textual>=1.0.0` | Cyberpunk TUI dashboard |
| `rich>=13.7.0` | Terminal formatting (legacy dashboard) |
| `pydantic>=2.5.0` | Data validation and schemas |
| `httpx>=0.25.0` | HTTP client |

## Common Tasks

### Adding a new CLI command
Edit `src/acli/cli.py` — add a new `@app.command()` function using Typer conventions.

### Modifying security rules
Edit `src/acli/security/validators.py` for per-command validators, `hooks.py` for pre-tool-use hooks. Run `pytest tests/test_security.py -v` after changes — 100% coverage required.

### Updating TUI
Widgets in `src/acli/tui/widgets.py`, styling in `src/acli/tui/cyberpunk.tcss`, app logic in `src/acli/tui/app.py`. Validate with `bash tests/functional/07-tui-validation.sh`.

### Adding browser automation tools
Extend `src/acli/browser/puppeteer.py` or `playwright.py`. Each provider exposes 7 MCP tools.
