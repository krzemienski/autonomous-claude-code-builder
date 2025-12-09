# Architecture

This document describes the system architecture of the Autonomous CLI.

## Overview

The Autonomous CLI is a multi-agent autonomous coding system that converts plain English specifications into working applications through iterative development and browser-based testing.

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Autonomous CLI (acli)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐     ┌──────────────┐     ┌────────────────┐   │
│  │   CLI       │────→│ Orchestrator │────→│ Dashboard (TUI)│   │
│  │  Commands   │     │              │     │                │   │
│  └─────────────┘     └──────────────┘     └────────────────┘   │
│                              │                                  │
│                              ↓                                  │
│                      ┌───────────────┐                          │
│                      │  Agent Session│                          │
│                      │  (Initializer │                          │
│                      │   or Coding)  │                          │
│                      └───────────────┘                          │
│                              │                                  │
│            ┌─────────────────┼─────────────────┐                │
│            ↓                 ↓                 ↓                │
│    ┌───────────────┐ ┌──────────────┐ ┌──────────────┐         │
│    │   Security    │ │   Progress   │ │   Browser    │         │
│    │    Hooks      │ │   Tracker    │ │   Manager    │         │
│    └───────────────┘ └──────────────┘ └──────────────┘         │
│            │                 │                 │                │
│            ↓                 ↓                 ↓                │
│    ┌───────────────┐ ┌──────────────┐ ┌──────────────┐         │
│    │  Validators   │ │feature_list  │ │ Puppeteer/   │         │
│    │  (pkill,chmod)│ │    .json     │ │ Playwright   │         │
│    └───────────────┘ └──────────────┘ └──────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
                    ┌──────────────────┐
                    │  Claude Code SDK │
                    │  (Anthropic API) │
                    └──────────────────┘
```

## Core Components

### 1. CLI Layer (`acli.cli`)

**Purpose**: User-facing command interface

**Commands**:
- `init` - Initialize new project
- `run` - Run autonomous coding loop
- `status` - Show progress
- `enhance` - Spec enhancement
- `config` - Configuration management

**Implementation**: Typer-based CLI with subcommands

### 2. Orchestrator (`acli.core.orchestrator`)

**Purpose**: Coordinate agent sessions and manage workflow

**Responsibilities**:
- Detect first run vs continuation
- Select appropriate agent (initializer vs coding)
- Manage session lifecycle
- Coordinate with progress tracker
- Handle dashboard updates

**Key Methods**:
```python
async def run() -> None:
    """Main orchestration loop."""

def is_first_run() -> bool:
    """Check if this is the first run."""

async def run_initializer_session() -> None:
    """Run initializer agent."""

async def run_coding_session() -> None:
    """Run coding agent."""
```

### 3. Agent Session (`acli.core.session`)

**Purpose**: Execute single agent session with Claude

**Responsibilities**:
- Load appropriate prompt template
- Create Claude session with tools
- Stream responses to dashboard
- Execute tool calls
- Handle security hooks

**Session Types**:

1. **Initializer Session**:
   - Reads `app_spec.txt`
   - Generates `feature_list.json` (~200 features)
   - Creates project structure
   - Generates `init.sh` script

2. **Coding Session**:
   - Reads `feature_list.json`
   - Picks ONE incomplete feature
   - Implements feature with browser testing
   - Marks feature as passing
   - Commits changes

### 4. Security Layer (`acli.security`)

**Purpose**: Prevent dangerous operations

**Components**:

1. **Security Hook** (`hooks.py`):
   - Pre-tool-use validation
   - Command allowlist enforcement
   - Delegates to validators

2. **Validators** (`validators.py`):
   - `validate_pkill()` - Only dev processes
   - `validate_chmod()` - Only +x mode
   - `validate_init_script()` - Only ./init.sh

**Allowlist**:
```python
ALLOWED_COMMANDS = {
    "ls", "cat", "head", "tail", "wc", "grep",  # File inspection
    "cp", "mkdir", "chmod",                      # File operations
    "npm", "node",                               # Node.js
    "git",                                       # Version control
    "ps", "lsof", "sleep", "pkill",             # Process management
    "init.sh",                                   # Script execution
}
```

### 5. Progress Tracking (`acli.progress`)

**Purpose**: Track feature implementation progress

**Components**:

1. **Tracker** (`tracker.py`):
   ```python
   def get_total_count() -> int
   def get_completed_count() -> int
   def get_incomplete_count() -> int
   def get_progress_percentage() -> float
   ```

2. **Feature List** (`feature_list.py`):
   - JSON format storage
   - Feature schema validation
   - Progress persistence

3. **Display** (`display.py`):
   - Progress bar rendering
   - Status formatting

### 6. Browser Automation (`acli.browser`)

**Purpose**: Enable browser testing

**Components**:

1. **Manager** (`manager.py`):
   - Provider selection (Puppeteer/Playwright)
   - Wrapper instantiation
   - Tool loading

2. **Puppeteer Wrapper** (`puppeteer.py`):
   ```python
   def navigate(url: str) -> dict
   def click(selector: str) -> dict
   def fill(selector: str, value: str) -> dict
   def screenshot(name: str) -> dict
   ```

3. **Playwright Wrapper** (`playwright.py`):
   ```python
   def navigate(url: str) -> dict
   def snapshot() -> dict
   def click(uid: str, element: str) -> dict
   def fill(uid: str, element: str, value: str) -> dict
   ```

### 7. Dashboard (`acli.ui`)

**Purpose**: Real-time visibility

**Components**:

1. **Dashboard** (`dashboard.py`):
   - Multi-pane layout
   - Live updates
   - Tool board + Logs + Progress

2. **Tool Board** (`tool_board.py`):
   - Tool execution tracking
   - Status indicators
   - Timing information

3. **Logs** (`logs.py`):
   - Streaming log display
   - Level filtering
   - Timestamps

4. **Progress** (`progress.py`):
   - Progress bar
   - Percentage display

### 8. Spec Enhancement (`acli.spec`)

**Purpose**: Convert plain text to structured specs

**Components**:

1. **Enhancer** (`enhancer.py`):
   - Interactive prompting
   - Claude-powered conversion
   - JSON generation

2. **Validator** (`validator.py`):
   - Schema validation
   - Required fields check

3. **Schemas** (`schemas.py`):
   - Pydantic models
   - Type definitions

## Data Flow

### Initialization Flow

```
User: acli init my_app
  ↓
CLI: Create project directory
  ↓
CLI: Create app_spec.txt
  ↓
CLI: Optionally enhance spec
  ↓
Project ready for development
```

### Coding Loop Flow

```
User: acli run
  ↓
Orchestrator: Check for feature_list.json
  ↓
┌─────────────────────────────────────┐
│ First Run? (no feature_list.json)  │
└─────────────────────────────────────┘
  │
  ├─ YES: Run Initializer Session
  │    ↓
  │  Read app_spec.txt
  │    ↓
  │  Generate feature_list.json (~200 features)
  │    ↓
  │  Create init.sh
  │    ↓
  │  Initialize project
  │
  └─ NO: Run Coding Session
       ↓
     Read feature_list.json
       ↓
     Pick ONE incomplete feature
       ↓
     Implement feature
       ↓
     Test with browser
       ↓
     Mark feature as passing
       ↓
     Commit changes
       ↓
     Loop until all features complete
```

### Tool Execution Flow

```
Agent decides to use tool
  ↓
Security Hook: Pre-tool-use validation
  ↓
┌─────────────────┐
│ Tool = Bash?    │
└─────────────────┘
  │
  ├─ YES: Extract commands
  │    ↓
  │  Check against allowlist
  │    ↓
  │  Run validators if needed
  │    ↓
  │  Allow or Block
  │
  └─ NO: Allow (no validation)
```

## Security Architecture

### Defense-in-Depth

1. **Command Allowlist**: Only 16 commands permitted
2. **Per-Command Validators**: Extra validation for sensitive commands
3. **Shlex Parsing**: Prevent injection attacks
4. **Filesystem Restriction**: Project directory only
5. **OS-Level Sandbox**: Bash isolation

### Security Boundaries

```
┌───────────────────────────────────────┐
│        Agent (Claude Code SDK)        │
└───────────────────────────────────────┘
              │
              ↓ Tool Call
┌───────────────────────────────────────┐
│      Pre-Tool-Use Security Hook       │
│   - Command extraction                │
│   - Allowlist check                   │
│   - Validator dispatch                │
└───────────────────────────────────────┘
              │
              ↓ Validated
┌───────────────────────────────────────┐
│        Tool Execution Layer           │
│   - Sandbox environment               │
│   - Project directory restriction     │
└───────────────────────────────────────┘
```

## Configuration

### Config Hierarchy

1. **User config**: `~/.config/acli/config.json`
2. **Project config**: `.acli/config.json` (future)
3. **Defaults**: Hardcoded in `acli.config`

### Config Schema

```json
{
  "model": "claude-sonnet-4-20250514",
  "max_iterations": null,
  "browser_provider": "puppeteer",
  "dashboard": true,
  "headless": false
}
```

## File Structure

### Project Directory Layout

```
my_app/
├── app_spec.txt          # Original specification
├── feature_list.json     # Progress tracking
├── init.sh               # Setup script (generated)
├── src/                  # Application code
├── package.json          # Dependencies
└── .git/                 # Version control
```

### Feature List Schema

```json
[
  {
    "id": 1,
    "component": "Login",
    "description": "Email input accepts valid email format",
    "passes": true
  }
]
```

## Extension Points

### Adding New Commands

1. Add command to `ALLOWED_COMMANDS`
2. Create validator if needed
3. Register in `VALIDATORS`

### Adding New MCP Tools

1. Implement wrapper in `acli.browser`
2. Register in `BrowserManager`
3. Update tool mapping

### Custom Prompt Templates

1. Create template in `prompts/templates/`
2. Reference in orchestrator
3. Add session type

## Performance Considerations

### Dashboard Updates

- Debounced updates (100ms)
- Incremental rendering
- Tool board limited to 10 recent tools

### Progress Tracking

- In-memory caching
- File writes on change only
- JSON streaming for large files

### Browser Automation

- Headless mode by default
- Screenshot optimization
- Page navigation caching

## Future Enhancements

1. **Pause/Resume**: Mid-session control
2. **Tool Approval**: Manual approval mode
3. **Spec Editing**: Mid-flight spec changes
4. **Multi-Project**: Parallel project support
5. **Plugin System**: Custom tool integration
