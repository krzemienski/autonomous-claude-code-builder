# Architecture

This document describes the system architecture of the Autonomous CLI.

## Overview

The Autonomous CLI is a multi-agent autonomous coding system that converts plain English specifications into working applications through iterative development and browser-based testing. It includes a cyberpunk-themed Textual TUI for real-time agent monitoring, visualization, and drill-down analysis.

## System Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           Autonomous CLI (acli)                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐     ┌──────────────┐     ┌──────────────────────────────┐  │
│  │   CLI       │────→│ Orchestrator │────→│ Agent Monitor TUI (Textual)  │  │
│  │  Commands   │     │              │     │ ┌──────────┬───────────────┐ │  │
│  │ (Typer)     │     │  StreamBuffer│────→│ │ Agent    │ Log Stream    │ │  │
│  └─────────────┘     │  + Events    │     │ │ Graph    │ (full verbose)│ │  │
│    │                  └──────────────┘     │ ├──────────┼───────────────┤ │  │
│    │                         │             │ │ Agent    │ Stats +       │ │  │
│    │                         ↓             │ │ Detail   │ Tool Board    │ │  │
│    │                 ┌───────────────┐     │ └──────────┴───────────────┘ │  │
│    │                 │  Agent Session│     └──────────────────────────────┘  │
│    │                 │  (Initializer │                                       │
│    │                 │   or Coding)  │     ┌──────────────────────────────┐  │
│    │                 └───────────────┘     │ Legacy Dashboard (Rich.Live) │  │
│    │                         │             │ (headless/fallback mode)     │  │
│    │           ┌─────────────┼──────────┐  └──────────────────────────────┘  │
│    │           ↓             ↓          ↓                                    │
│    │   ┌───────────┐ ┌────────────┐ ┌──────────┐                           │
│    │   │ Security  │ │  Progress  │ │ Browser  │                           │
│    │   │  Hooks    │ │  Tracker   │ │ Manager  │                           │
│    │   └───────────┘ └────────────┘ └──────────┘                           │
│    │           │             │            │                                  │
│    │           ↓             ↓            ↓                                  │
│    │   ┌───────────┐ ┌────────────┐ ┌──────────┐                           │
│    │   │Validators │ │feature_list│ │Puppeteer/│                           │
│    │   │(pkill,    │ │   .json    │ │Playwright│                           │
│    │   │ chmod)    │ └────────────┘ └──────────┘                           │
│    │   └───────────┘                                                        │
│    │                                                                         │
│    └──→ OrchestratorBridge (TUI ↔ Real Orchestrator)                        │
│         ├─ AgentNode hierarchy (live agent tree)                             │
│         ├─ OrchestratorSnapshot (point-in-time state)                        │
│         ├─ Event callbacks (real StreamBuffer → TUI widgets)                 │
│         └─ Control commands (pause/resume/stop → real orchestrator)          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                              │
                              ↓
                    ┌──────────────────┐
                    │ Claude Agent SDK │
                    │ (Anthropic API)  │
                    └──────────────────┘
```

## Core Components

### 1. CLI Layer (`acli.cli`)

**Purpose**: User-facing command interface

**Commands**:
- `init` - Initialize new project
- `run` - Run autonomous coding loop (with optional TUI dashboard)
- `monitor` - Launch cyberpunk TUI for real-time agent monitoring
- `status` - Show progress
- `enhance` - Spec enhancement
- `config` - Configuration management
- `list-skills` - Discover available skills

**Implementation**: Typer-based CLI with subcommands

### 2. Orchestrator (`acli.core.orchestrator`)

**Purpose**: Coordinate agent sessions and manage workflow

**Responsibilities**:
- Detect first run vs continuation
- Select appropriate agent (initializer vs coding)
- Manage session lifecycle
- Coordinate with progress tracker
- Feed events to StreamBuffer for TUI consumption
- Handle pause/resume/stop controls

**Key Class**:
```python
class AgentOrchestrator:
    async def run_loop() -> None
    async def run_single_session() -> tuple[str, str]
    def request_pause() -> None
    def request_stop() -> None
    def resume() -> None
    def get_status() -> dict[str, Any]
```

### 3. Agent Session (`acli.core.agent`)

**Purpose**: Execute single agent session with Claude

**Session Types**:

1. **Initializer Session**: Reads `app_spec.txt`, generates `feature_list.json` (~200 features), creates project structure
2. **Coding Session**: Picks ONE incomplete feature, implements, tests, marks passing, commits

### 4. Agent Monitor TUI (`acli.tui`)

**Purpose**: Full-screen cyberpunk-themed terminal dashboard for real-time agent monitoring

**Technology**: Textual 8.x (Python TUI framework, async-native, CSS-styled)

**Components**:

| Component | File | Purpose |
|-----------|------|---------|
| `AgentMonitorApp` | `app.py` | Main Textual app with keybindings |
| `OrchestratorBridge` | `bridge.py` | Direct connection to real orchestrator |
| `AgentGraph` | `widgets.py` | ASCII agent hierarchy visualization |
| `AgentDetail` | `widgets.py` | Deep drill-down into selected agent |
| `LogStream` | `widgets.py` | Full-verbosity event log streaming |
| `StatsPanel` | `widgets.py` | Progress, metrics, tool board |
| `CyberHeader` | `widgets.py` | System status bar |
| Cyberpunk Theme | `cyberpunk.tcss` | 408-line CSS theme |

**Layout**:
```
┌──────────────────────────────────────────────────────────────┐
│  ⟁ ACLI AGENT MONITOR │ ● RUNNING │ S#2 [coding] │ 05:30  │
├────────────────────┬─────────────────────────────────────────┤
│  AGENT HIERARCHY   │ LOGS │ F1:All F2:Tools F3:Errors F4:Text│
│  ◆ ORCHESTRATOR    │ 14:32:15 TXT Creating structure...      │
│  ├─ ✓ S#1 [init]  │ 14:32:16 TOL ▶ Bash npm init -y         │
│  ╰─ ◆ S#2 [code]  │ 14:32:17 TOL ✓ Bash 150ms OK            │
│    ⚡ Write        │ 14:32:18 TOL ▶ Write src/App.jsx         │
│────────────────────├─────────────────────────────────────────┤
│  ◆ CODING          │ PROGRESS ████████░░░░░░ 10/200 5.0%    │
│  Status: running   │ Sessions: 2 │ Tools: 15 │ Errors: 0    │
│  Tools: 15         │ RECENT TOOLS                             │
│  Duration: 5m30s   │   ✓ Write 88ms │ ✓ Bash 150ms          │
├────────────────────┴─────────────────────────────────────────┤
│ q Quit  p Pause/Resume  s Stop  ↑↓ Navigate  Enter Detail   │
└──────────────────────────────────────────────────────────────┘
```

**Keyboard Navigation**:
| Key | Action |
|-----|--------|
| `q` | Quit |
| `p` | Pause/Resume orchestrator |
| `s` | Stop orchestrator |
| `j`/`k` or `↑`/`↓` | Navigate agents |
| `Enter` | Drill into selected agent |
| `F1`-`F4` | Switch log filter (All/Tools/Errors/Text) |
| `Tab` | Cycle focus |

**Cyberpunk Color Palette**:
| Color | Hex | Usage |
|-------|-----|-------|
| Deep Navy | `#000b1e` | Background |
| Neon Cyan | `#0abdc6` | Primary, borders |
| Hot Pink | `#ea00d9` | Tool names, highlights |
| Matrix Green | `#00ff41` | Success, running |
| Neon Red | `#ff003c` | Errors, blocked |
| Amber | `#f5a623` | Warnings, paused |
| Ice White | `#d7fffe` | Primary text |
| Steel Gray | `#4a6670` | Muted, timestamps |
| Electric Blue | `#133e7c` | Borders, connectors |

### 5. Legacy Dashboard (`acli.ui`)

**Purpose**: Lightweight Rich.Live-based dashboard (headless/fallback mode)

Used when `--no-dashboard` or `--headless` flags are set.

### 6. Security Layer (`acli.security`)

**Purpose**: Prevent dangerous operations via defense-in-depth

**Layers**:
1. OS-level sandbox
2. Filesystem restriction (project directory only)
3. 16-command allowlist
4. Per-command validators (pkill, chmod, init.sh)
5. Shlex parsing to prevent injection

### 7. Streaming Infrastructure (`acli.core.streaming`)

**Purpose**: Event-driven communication between orchestrator and all UI layers

**Data Flow**:
```
Claude Agent SDK → StreamingHandler → StreamBuffer → OrchestratorBridge → TUI Widgets
                                                  ↘ Legacy Dashboard (Rich.Live)
```

**Event Types**: TEXT, TOOL_START, TOOL_END, TOOL_BLOCKED, ERROR, SESSION_START, SESSION_END, PROGRESS

## File Structure

```
src/acli/
├── cli.py                     # Typer CLI (7 commands)
├── core/                      # Agent orchestration engine
│   ├── orchestrator.py        # Multi-agent coordinator
│   ├── agent.py               # Agent session logic (Claude Agent SDK)
│   ├── client.py              # SDK client configuration
│   ├── session.py             # Session state management
│   └── streaming.py           # Event streaming + buffering
├── tui/                       # Cyberpunk Agent Monitor TUI
│   ├── app.py                 # Main Textual application
│   ├── bridge.py              # OrchestratorBridge (real data only)
│   ├── widgets.py             # All TUI widgets
│   └── cyberpunk.tcss         # Cyberpunk Neon CSS theme
├── ui/                        # Legacy Rich-based dashboard
├── security/                  # Defense-in-depth security
├── spec/                      # Spec enhancement
├── progress/                  # Progress tracking
├── browser/                   # Browser automation (Puppeteer/Playwright)
├── integration/               # External integrations
├── prompts/                   # Prompt templates
└── utils/                     # Logger, event emitter
```

## Extension Points

### Adding New TUI Widgets

1. Create widget class in `tui/widgets.py`
2. Add to `app.py` compose method
3. Wire up to `OrchestratorBridge` data
4. Style in `cyberpunk.tcss`

### Adding New Agent Types

1. Create prompt template in `prompts/templates/`
2. Add session type to orchestrator
3. Bridge automatically picks up new sessions via StreamBuffer events

### Adding New Commands to Security Allowlist

1. Add command to `ALLOWED_COMMANDS` in `hooks.py`
2. Create validator if needed in `validators.py`
3. Register in `VALIDATORS` dict
