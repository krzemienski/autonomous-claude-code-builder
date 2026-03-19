# CLAUDE.md — Autonomous CLI (acli) v2

## Project Overview

Autonomous CLI (`acli`) is a Python CLI tool providing universal autonomous coding with a cyberpunk-themed TUI dashboard. It uses the Claude Agent SDK to orchestrate multi-agent workflows that handle ANY prompt and ANY project type (greenfield + brownfield) with functional validation gates, deep context/memory management, and full TUI visibility.

**Version**: 2.0.0 | **License**: MIT | **Python**: >=3.11

## Quick Reference

```bash
# Install (development)
pip install -e ".[dev]"

# CLI commands (13 total)
acli init <project-dir>          # Initialize a new project
acli run <project-dir>           # Run autonomous coding agents
acli monitor <project-dir>       # Launch cyberpunk TUI dashboard
acli status <project-dir>        # Show project status
acli enhance <spec-file>         # Enhance a spec with AI
acli config get|set|list [key]   # Manage configuration
acli list-skills                 # List available skills
acli onboard <project-dir>       # Onboard existing codebase (v2)
acli prompt "task" --dir <dir>   # Execute single task without TUI (v2)
acli validate <project-dir>      # Run validation gates (v2)
acli session list|resume|replay  # Manage agent sessions (v2)
acli memory list|add|clear       # Manage project memory (v2)
acli context <project-dir>       # Show project context store (v2)

# Run tests
pytest tests/test_security.py -v          # 67 security tests
bash tests/run_e2e.sh                     # Full E2E suite (8 functional tests)
bash tests/functional/07-tui-validation.sh # TUI-specific tests
```

## Repository Structure

```
src/acli/                  # Main package (~9,400 LOC across 70 files)
├── cli.py                 # Typer CLI entry point (7 v1 commands)
├── cli_v2.py              # v2 CLI commands (6 new commands)
├── __main__.py            # python -m acli entry point
├── core/                  # Agent orchestration (Claude Agent SDK)
│   ├── orchestrator_v1.py # v1 two-agent pattern (Initializer + Coding)
│   ├── orchestrator_v2.py # v2 enhanced orchestrator (any prompt, multi-agent)
│   ├── agent.py           # Agent session execution
│   ├── client.py          # SDK client with MODEL_OPUS/MODEL_SONNET constants
│   ├── session.py         # Project state + JSONL SessionLogger
│   └── streaming.py       # Event-driven streaming (21 event types)
├── routing/               # Prompt classification (v2)
│   ├── router.py          # PromptRouter — classifies any prompt
│   └── workflows.py       # 8 WorkflowTypes + WorkflowConfig
├── context/               # Codebase knowledge management (v2)
│   ├── store.py           # ContextStore — persistent .acli/context/
│   ├── memory.py          # MemoryManager — cross-session facts
│   ├── chunker.py         # KnowledgeChunker — codebase segmentation
│   └── onboarder.py       # BrownfieldOnboarder — async analysis pipeline
├── agents/                # Multi-agent definitions (v2)
│   ├── definitions.py     # 7 AgentTypes with model routing (Opus/Sonnet)
│   └── factory.py         # AgentFactory — context/memory/skill injection
├── validation/            # Functional validation engine (v2)
│   ├── mock_detector.py   # Pre-tool-use hook blocking mock/test code
│   ├── evidence.py        # EvidenceCollector — real command execution
│   ├── gates.py           # GateRunner — PASS/FAIL with evidence
│   ├── engine.py          # ValidationEngine — orchestrates all gates
│   └── platforms/         # Platform-specific validators
│       ├── api.py         # APIValidator — curl against real servers
│       ├── cli.py         # CLIValidator — real binary execution
│       ├── web.py         # WebValidator — Playwright screenshots
│       ├── ios.py         # IOSValidator — simulator screenshots
│       └── generic.py     # GenericValidator — fallback
├── tui/                   # Cyberpunk Agent Monitor (Textual framework)
│   ├── app.py             # Main TUI application (7-panel layout)
│   ├── bridge.py          # Orchestrator connection + v2 event handling
│   ├── widgets.py         # UI components + ContextExplorer + ValidationGatePanel
│   ├── prompt_input.py    # Inline prompt widget
│   └── cyberpunk.tcss     # Neon theme (navy/cyan/pink/green)
├── ui/                    # Legacy Rich dashboard (fallback)
├── spec/                  # Spec enhancement (plain English → JSON)
├── security/              # Defense-in-depth security model
├── progress/              # Feature progress tracking with persistence
├── browser/               # Browser automation (Puppeteer + Playwright MCP)
├── integration/           # External integrations + SkillEngine
├── prompts/templates/     # Agent prompt templates
└── utils/                 # Logging and event definitions
```

## Architecture

### v2 Multi-Agent Orchestration

The v2 `EnhancedOrchestrator` accepts ANY prompt and routes it through a typed agent pipeline:

1. **PromptRouter** classifies into 8 workflow types (greenfield, brownfield, debug, refactor, iOS, CLI, free task)
2. **AgentFactory** spawns typed agents with context/memory/skill injection
3. **Agent pipeline**: Router → Analyst → Planner → [Implementer → Validator]×N → Reporter
4. **Validation gates** enforce functional validation with real evidence at every phase

**Agent types** (7): ROUTER, ANALYST, PLANNER, IMPLEMENTER, VALIDATOR, CONTEXT_MANAGER, REPORTER
**Model routing**: Analyst + Planner → `claude-opus-4-6` | Others → `claude-sonnet-4-6`

> **Note**: v2 agent methods in `orchestrator_v2.py` are scaffolded but not yet wired to real SDK `query()` calls. The orchestrator structure, routing, context, and validation are complete. SDK execution wiring is the next development phase.

### v1 Two-Agent Pattern (preserved)

1. **Initializer Agent** (Session #1): Reads `app_spec.txt`, generates `feature_list.json`
2. **Coding Agent** (Sessions 2+): Implements features one-by-one with browser testing

### Security Model (16-Command Allowlist + Mock Detection)

Allowed commands: `ls`, `cat`, `npm`, `npx`, `git`, `python`, `pip`, `node`, `curl`, `wget`, `touch`, `mkdir`, `rm`, `echo`, `chmod`, `pkill`

v2 additions:
- **Mock detection hook**: Pre-tool-use hook blocks Write/Edit of mock/test code (20+ patterns)
- Defense layers: OS sandbox → file permissions → command allowlist → shlex parsing → pre-tool-use hooks → mock detection

### Streaming & TUI

- 21 event types (8 v1 + 13 v2: AGENT_SPAWN, GATE_RESULT, CONTEXT_UPDATE, etc.)
- 7-panel cyberpunk TUI: AgentGraph, AgentDetail, ContextExplorer, LogStream, ValidationGatePanel, StatsPanel, PromptInput
- Keyboard: `j/k` scroll, `F1-F4` filter, `p/s/q` controls, `/` prompt, `v` validation, `c` context

### Context & Memory System

- **ContextStore**: Persistent codebase knowledge at `.acli/context/` (analysis, tech stack, conventions, decisions)
- **MemoryManager**: Cross-session facts at `.acli/memory/project_memory.json`
- **KnowledgeChunker**: Codebase file segmentation for retrieval
- **BrownfieldOnboarder**: Async pipeline for existing project analysis

### Validation Engine

- **EvidenceCollector**: Saves text/JSON/command output as evidence files
- **GateRunner**: Executes validation gates with real shell commands
- **Platform validators**: API (curl), CLI (binary exec), Web (Playwright), iOS (simctl), Generic
- **Mock detector**: 20+ regex patterns blocking test/mock code creation

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

### Code Quality

```bash
ruff check src/                  # Lint (PEP 8, line-length: 100)
mypy src/acli/                   # Type check (strict mode)
pytest tests/test_security.py -v # Security tests
```

### Testing Strategy

**No mocks, no unit tests** — functional/E2E tests only.

## Code Conventions

- **Style**: PEP 8 via ruff, 100-char line length, Python 3.11+
- **Type hints**: Mandatory, Google-style docstrings
- **Imports**: stdlib → third-party → local
- **Async**: All orchestrator/agent code uses `async/await`
- **Validation**: Pydantic v2 models for data schemas
- **File size**: <200 lines preferred, 800 max

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `claude-agent-sdk>=0.1.48` | Claude Agents API (adaptive thinking, effort param) |
| `typer>=0.9.0` | CLI framework |
| `textual>=1.0.0` | Cyberpunk TUI dashboard |
| `rich>=13.7.0` | Terminal formatting |
| `pydantic>=2.5.0` | Data validation |
| `httpx>=0.25.0` | HTTP client |

## Common Tasks

### Adding a new CLI command
- v1 commands: edit `src/acli/cli.py`
- v2 commands: edit `src/acli/cli_v2.py` (registered via `register_v2_commands()`)

### Modifying security rules
Edit `src/acli/security/validators.py` for command validators, `hooks.py` for pre-tool-use hooks, `validation/mock_detector.py` for mock detection patterns.

### Updating TUI
Widgets in `src/acli/tui/widgets.py`, new widgets in separate files (e.g., `prompt_input.py`), styling in `cyberpunk.tcss`, app logic in `app.py`.

### Adding a new agent type
1. Add to `AgentType` enum in `src/acli/agents/definitions.py`
2. Add config to `AGENT_CONFIGS` dict
3. Wire into `EnhancedOrchestrator._resolve_agent_type()`

### Adding a new workflow type
1. Add to `WorkflowType` enum in `src/acli/routing/workflows.py`
2. Add classification rule in `PromptRouter.classify()`
3. Add agent sequence in router's `_get_agent_sequence()`
