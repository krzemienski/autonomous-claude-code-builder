# Architecture

This document describes the system architecture of the Autonomous CLI (ACLI v2 / Shannon-ACLI).

## Overview

ACLI v2 is a universal autonomous coding system that handles **any prompt, any project type** — greenfield and brownfield — with multi-agent orchestration, functional validation gates, deep context/memory management, and full TUI visibility. It builds on the v1 two-agent pattern while adding routing, context awareness, and phase-gated validation.

## v2 System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ACLI v2 (Shannon-ACLI)                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐      ┌───────────────┐      ┌──────────────────────────────┐ │
│  │   CLI (13)   │─────→│ Prompt Router │─────→│ Enhanced Orchestrator (v2)   │ │
│  │   Commands   │      │               │      │                              │ │
│  │   (Typer)    │      │ Classifies:   │      │  Workflow: GREENFIELD_APP    │ │
│  │              │      │ • greenfield  │      │  Agents: [analyst, planner,  │ │
│  │  init        │      │ • brownfield  │      │    implementer, validator]   │ │
│  │  run         │      │ • debug       │      │                              │ │
│  │  monitor     │      │ • refactor    │      │  ┌──────────────────────┐    │ │
│  │  status      │      │ • ios_app     │      │  │   Agent Factory      │    │ │
│  │  onboard     │      │ • cli_tool    │      │  │   Creates agents     │    │ │
│  │  prompt      │      │ • free_task   │      │  │   with injected:     │    │ │
│  │  validate    │      └───────────────┘      │  │   • Context          │    │ │
│  │  session     │              │              │  │   • Memory           │    │ │
│  │  memory      │              ↓              │  │   • Skills           │    │ │
│  │  context     │      ┌───────────────┐      │  └──────────────────────┘    │ │
│  │  config      │      │ WorkflowConfig│      │             │               │ │
│  │  enhance     │      │ • agent_seq   │      │             ↓               │ │
│  │  list-skills │      │ • model_tier  │      │  ┌──────────────────────┐   │ │
│  └──────────────┘      │ • platform    │      │  │   Agent Graph Loop   │   │ │
│                        └───────────────┘      │  │                      │   │ │
│                                               │  │   Router ──→ ···     │   │ │
│                                               │  │   Analyst ──→ ···    │   │ │
│                                               │  │   Planner ──→ ···    │   │ │
│                                               │  │   Implementer ──→ ··│   │ │
│                                               │  │   Validator ──→ ··· │   │ │
│                                               │  │   Reporter ──→ ···  │   │ │
│                                               │  └──────────────────────┘   │ │
│                                               └──────────────────────────────┘ │
│                                                          │                     │
│         ┌────────────────────────────────────────────────┼──────────┐          │
│         ↓                    ↓                           ↓          ↓          │
│  ┌────────────┐   ┌──────────────┐   ┌──────────────┐  ┌────────────────┐    │
│  │  Context   │   │   Memory     │   │  Validation  │  │  Skill Engine  │    │
│  │  Store     │   │  Manager     │   │  Engine      │  │                │    │
│  │            │   │              │   │              │  │  Auto-detects  │    │
│  │ .acli/     │   │ .acli/       │   │ .acli/       │  │  per agent +   │    │
│  │  context/  │   │  memory/     │   │  evidence/   │  │  platform      │    │
│  │            │   │              │   │              │  │                │    │
│  │ • analysis │   │ • facts.json │   │ • Mock       │  │  Maps:         │    │
│  │ • tech_stk │   │ • cross-sess │   │   Detector   │  │  validator →   │    │
│  │ • convntns │   │ • injection  │   │ • Evidence   │  │    functional  │    │
│  │ • decisions│   │   prompt     │   │   Collector  │  │  planner →     │    │
│  │ • chunks   │   │              │   │ • Gate Runner│  │    create-plan │    │
│  └────────────┘   └──────────────┘   │ • Platform   │  └────────────────┘    │
│                                      │   Validators │                         │
│                                      └──────────────┘                         │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │              Agent Monitor TUI (Textual) — 7 Panels                    │   │
│  │  ┌──────────────┬────────────┬──────────────────────────────────────┐  │   │
│  │  │ Agent Graph  │ Agent      │ Log Stream (F1-F4 filters)          │  │   │
│  │  │ (hierarchy)  │ Detail     │                                     │  │   │
│  │  ├──────────────┤ (drilldown)├──────────────────────────────────────┤  │   │
│  │  │ Context      │            │ Validation Gates (PASS/FAIL/RUNNING)│  │   │
│  │  │ Explorer     │            ├──────────────────────────────────────┤  │   │
│  │  │ (tech stack, │            │ Stats Panel + Tool Board            │  │   │
│  │  │  memory)     │            │                                     │  │   │
│  │  ├──────────────┴────────────┴──────────────────────────────────────┤  │   │
│  │  │  > Prompt Input ________________________________________________│  │   │
│  │  └─────────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│  ┌───────────────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ Session Logger (JSONL)│  │ Security │  │ Progress │  │ Browser Manager  │ │
│  │ .acli/sessions/*.jsonl│  │ Hooks    │  │ Tracker  │  │ Puppeteer/       │ │
│  │ list / load / replay  │  │ 16-cmd   │  │ feat_list│  │ Playwright MCP   │ │
│  └───────────────────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ↓
                       ┌──────────────────────────┐
                       │    Claude Agent SDK       │
                       │  ┌──────────┬───────────┐ │
                       │  │ Opus 4.6 │ Sonnet 4.6│ │
                       │  │(analyst, │(implement,│ │
                       │  │ planner, │ validator,│ │
                       │  │ ctx_mgr) │ reporter) │ │
                       │  └──────────┴───────────┘ │
                       │  Adaptive thinking        │
                       └──────────────────────────┘
```

## Agent Pipeline Diagram

```
   User Prompt                     Project Directory
       │                                  │
       ▼                                  ▼
  ┌─────────┐    ┌──────────────────────────────┐
  │ Prompt   │    │ File System Signals           │
  │ Intent   │    │ .xcodeproj? → IOS_APP        │
  │ Analysis │    │ Cargo.toml? → CLI_TOOL       │
  │          │    │ app_spec.txt + no src? → GREEN│
  │ fix/debug│    │ >3 src files? → BROWNFIELD   │
  │ add/build│    │ .acli/context? → onboarded   │
  │ refactor │    └──────────────────────────────┘
  └─────┬───┘                │
        └────────┬───────────┘
                 ▼
        ┌────────────────┐
        │ WorkflowConfig │
        │ type: DEBUG    │
        │ agents: [A,I,V]│
        │ model: opus    │
        │ platform: cli  │
        └───────┬────────┘
                │
     ┌──────────┼───────────────────────────────┐
     ▼          ▼              ▼                 ▼
  ┌──────┐  ┌──────┐     ┌──────────┐     ┌──────────┐
  │ANALYS│  │PLANNE│     │IMPLEMENT │     │ VALIDATE │
  │  T   │  │  R   │     │   ER     │     │   OR     │
  │      │  │      │     │          │     │          │
  │Opus  │  │Opus  │     │ Sonnet   │     │ Sonnet   │
  │50turn│  │30turn│     │ 200 turn │     │ 50 turn  │
  │      │  │      │     │          │     │          │
  │Read  │  │Read  │     │Read/Write│     │Read/Bash │
  │Glob  │  │Glob  │     │Edit/Glob │     │Glob/Grep │
  │Grep  │  │Grep  │     │Grep/Bash │     │          │
  │Bash  │  │Write │     │          │     │ Evidence │
  └──┬───┘  └──┬───┘     └────┬─────┘     └────┬─────┘
     │         │              │                 │
     ▼         ▼              ▼                 ▼
  ┌──────────────────────────────────────────────────┐
  │              Context Injection                    │
  │  System Prompt = template + context + memory +    │
  │                  skills + task_context             │
  └──────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
                    ┌─────────────────────────────────┐
                    │        StreamBuffer (1000)        │
                    │   Async circular event buffer     │
                    └──────────┬──────────────────────┘
                               │
              ┌────────────────┼─────────────────────┐
              │                │                     │
              ▼                ▼                     ▼
   ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐
   │ TUI Bridge    │  │ Legacy Dash   │  │ Session Logger   │
   │               │  │ (Rich.Live)   │  │ (JSONL)          │
   │ AgentNode     │  │               │  │                  │
   │ hierarchy     │  │ Console       │  │ .acli/sessions/  │
   │               │  │ output        │  │ s_001.jsonl      │
   │ Snapshot      │  │               │  │ s_002.jsonl      │
   │ (point-in-    │  │               │  │                  │
   │  time state)  │  │               │  │ Events:          │
   │               │  │               │  │ session_start    │
   │ Gate results  │  │               │  │ tool_use         │
   │ Context summ. │  │               │  │ assistant_text   │
   └───────┬───────┘  └───────────────┘  │ decision         │
           │                              │ session_end      │
           ▼                              └──────────────────┘
   ┌───────────────────────────────────┐
   │          TUI Widgets              │
   │                                   │
   │  Event Types (21):                │
   │  v1: TEXT, TOOL_*, ERROR,         │
   │      SESSION_*, PROGRESS          │
   │                                   │
   │  v2: AGENT_SPAWN, AGENT_COMPLETE, │
   │      PHASE_START, PHASE_END,      │
   │      GATE_START, GATE_RESULT,     │
   │      CONTEXT_UPDATE,              │
   │      MEMORY_UPDATE, THINKING,     │
   │      MOCK_DETECTED,               │
   │      PROMPT_RECEIVED,             │
   │      ANALYSIS_UPDATE,             │
   │      PLAN_CREATED                 │
   └───────────────────────────────────┘
```

## Validation & Mock Detection Diagram

```
  Agent writes code
        │
        ▼
  ┌──────────────────┐     ┌──────────────────────────────────────┐
  │ Pre-Tool-Use     │────→│ Mock Detection Hook                  │
  │ Hook (Write/Edit)│     │                                      │
  └──────────────────┘     │ Scans for 20 patterns:               │
                           │  • unittest.mock, Mock(), @patch     │
                           │  • jest.mock, jest.fn, sinon         │
                           │  • :memory:, mongomock               │
                           │  • TEST_MODE, TESTING=True           │
                           │  • .test.*, _test.*, test_*          │
                           │                                      │
                           │ Decision:                             │
                           │  {} → allow                          │
                           │  {decision: "block"} → reject + emit │
                           │    MOCK_DETECTED event                │
                           └──────────────────────────────────────┘
                                         │
                           ┌─────────────┴──────────────┐
                           ▼                            ▼
                     ┌──────────┐               ┌──────────────┐
                     │  ALLOW   │               │    BLOCK     │
                     │  (clean  │               │  (mock/test  │
                     │   code)  │               │   detected)  │
                     └──────────┘               └──────────────┘

  Validation Gate Flow:
  ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
  │ Task     │───→│ Gate Criteria │───→│ Evidence     │───→│ PASS /   │
  │ Complete │    │ (shell cmds   │    │ Collector    │    │ FAIL     │
  │          │    │  exit 0=pass) │    │ (saves to    │    │          │
  │          │    │              │    │  .acli/       │    │ Blocking:│
  │          │    │              │    │  evidence/)   │    │  FAIL →  │
  │          │    │              │    │              │    │  stop    │
  └──────────┘    └──────────────┘    └──────────────┘    └──────────┘

  Platform Validators:
  ┌────────────────────────────────────────────────────────┐
  │ CLIValidator    │ echo, python -c, binary execution    │
  │ APIValidator    │ curl against running servers         │
  │ WebValidator    │ Playwright screenshot + selectors    │
  │ IOSValidator    │ xcrun simctl + simulator screenshots │
  │ GenericValidator│ Any shell command, exit code check   │
  └────────────────────────────────────────────────────────┘
```

## Persistence Layer Diagram

```
  project_dir/
  ├── app_spec.txt              ← User's project specification
  ├── feature_list.json         ← Progress tracking (v1)
  ├── .acli_state.json          ← Session history (v1)
  ├── .claude_settings.json     ← SDK security config
  │
  └── .acli/                    ← v2 persistent state
      ├── context/
      │   ├── codebase_analysis.json   ← Architecture map
      │   ├── tech_stack.json          ← Detected stack
      │   ├── conventions.json         ← Code patterns
      │   ├── decisions.jsonl          ← Append-only log
      │   └── knowledge_chunks/        ← Chunked source
      │
      ├── memory/
      │   └── project_memory.json      ← Cross-session facts
      │
      ├── sessions/
      │   ├── s_001.jsonl              ← Session 1 events
      │   ├── s_002.jsonl              ← Session 2 events
      │   └── ...
      │
      └── evidence/
          ├── vg1.1-models.txt         ← Gate evidence
          ├── vg1.2-events.txt
          └── ...
```

## v1 System Diagram (preserved)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           Autonomous CLI (acli) v1                           │
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

### 1. CLI Layer (`acli.cli`) — 13 Commands

**Purpose**: User-facing command interface

**v1 Commands**:
- `init` - Initialize new project (+ `--onboard` flag for brownfield)
- `run` - Run autonomous coding loop (+ `--prompt` option for v2)
- `monitor` - Launch cyberpunk TUI for real-time agent monitoring
- `status` - Show progress
- `enhance` - Spec enhancement
- `config` - Configuration management
- `list-skills` - Discover available skills

**v2 Commands**:
- `onboard` - Brownfield codebase analysis and context population
- `prompt` - Send single task without TUI (headless v2 orchestrator)
- `validate` - Run validation gates only
- `session` - List, resume, replay agent sessions (JSONL)
- `memory` - List, add, clear cross-session memory facts
- `context` - Show/manage context store contents

### 2. Prompt Router (`acli.routing`)

**Purpose**: Classify any user prompt into a workflow type

**Workflow Types** (8):

| Type | Trigger | Agent Sequence |
|------|---------|---------------|
| `GREENFIELD_APP` | `app_spec.txt` + no source files | analyst → planner → implementer → validator |
| `BROWNFIELD_ONBOARD` | Source files + no context | analyst → context_manager |
| `BROWNFIELD_TASK` | Source files + "add/implement" | analyst → planner → implementer → validator |
| `REFACTOR` | Source files + "refactor/migrate" | analyst → planner → implementer → validator |
| `DEBUG` | Source files + "fix/debug/broken" | analyst → implementer → validator |
| `CLI_TOOL` | `Cargo.toml` or Go binary indicators | analyst → planner → implementer → validator |
| `IOS_APP` | `.xcodeproj` or `.xcworkspace` | analyst → planner → implementer → validator |
| `FREE_TASK` | None of the above | implementer → validator |

### 3. Enhanced Orchestrator (`acli.core.orchestrator_v2`)

**Purpose**: Universal orchestration for any prompt and project type

**Key Differences from v1**:
- Accepts any prompt (not just initializer/coding binary)
- Uses PromptRouter for workflow classification
- Spawns agents dynamically via AgentFactory
- Context-aware system prompts (context + memory + skills injection)
- Phase-gated progression with streaming events

**v1 Orchestrator** (`orchestrator_v1.py`): Preserved for backwards compatibility

### 4. Agent Factory (`acli.agents`)

**Purpose**: Create configured SDK clients for 7 agent types

**Agent Types**:

| Type | Model | Max Turns | Tools |
|------|-------|-----------|-------|
| Router | Sonnet | 10 | Read, Glob |
| Analyst | **Opus** | 50 | Read, Glob, Grep, Bash |
| Planner | **Opus** | 30 | Read, Glob, Grep, Write |
| Implementer | Sonnet | 200 | Read, Write, Edit, Glob, Grep, Bash |
| Validator | Sonnet | 50 | Read, Glob, Grep, Bash |
| Context Manager | **Opus** | 30 | Read, Glob, Grep, Write |
| Reporter | Sonnet | 20 | Read, Glob, Write |

### 5. Context & Memory (`acli.context`)

**ContextStore**: Persistent codebase knowledge in `.acli/context/`
- `codebase_analysis.json` — Architecture map
- `tech_stack.json` — Detected technology stack
- `conventions.json` — Code patterns and style
- `decisions.jsonl` — Append-only decision log

**MemoryManager**: Cross-session facts in `.acli/memory/project_memory.json`
- Stores categorized facts (architecture, gotchas, etc.)
- Produces formatted injection prompt for agent system prompts

**KnowledgeChunker**: Chunks source files for retrieval (max 4000 chars/chunk)

**BrownfieldOnboarder**: Full codebase analysis pipeline (tech stack → architecture → conventions → chunking)

### 6. Validation Engine (`acli.validation`)

**Mock Detector**: Pre-tool-use hook blocking test/mock code (20 patterns)

**Evidence Collector**: Captures text, JSON, and command output as evidence files

**Gate Runner**: Executes validation gates with shell commands (exit 0 = pass)

**Platform Validators** (5):
- `CLIValidator` — binary/module execution
- `APIValidator` — curl against running servers
- `WebValidator` — Playwright screenshots
- `IOSValidator` — Simulator screenshots
- `GenericValidator` — Any shell command

### 7. Agent Monitor TUI (`acli.tui`)

**Purpose**: Full-screen cyberpunk-themed terminal dashboard for real-time agent monitoring

**Technology**: Textual >=1.0 (Python TUI framework, async-native, CSS-styled)

**Components** (v2 — 7 panels):

| Component | File | Purpose |
|-----------|------|---------|
| `AgentMonitorApp` | `app.py` | Main Textual app with keybindings |
| `OrchestratorBridge` | `bridge.py` | Direct connection to real orchestrator |
| `AgentGraph` | `widgets.py` | ASCII agent hierarchy visualization |
| `AgentDetail` | `widgets.py` | Deep drill-down into selected agent |
| `ContextExplorer` | `widgets.py` | **(v2)** Tech stack + memory facts display |
| `LogStream` | `widgets.py` | Full-verbosity event log streaming |
| `ValidationGatePanel` | `widgets.py` | **(v2)** Gate status (PASS/FAIL/RUNNING) |
| `StatsPanel` | `widgets.py` | Progress, metrics, tool board |
| `CyberHeader` | `widgets.py` | System status bar |
| `PromptInput` | `prompt_input.py` | **(v2)** Inline task prompt submission |
| Cyberpunk Theme | `cyberpunk.tcss` | 507-line CSS theme |

**Layout** (v2 — 7 panels + prompt):
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
│  ◆ CODING          │ VALIDATION GATES                        │
│  Status: running   │   ✓ VG-1.1: PASS                       │
│  Tools: 15         │   ✓ VG-1.2: PASS                       │
│  Duration: 5m30s   │   → VG-1.3: RUNNING                    │
│────────────────────├─────────────────────────────────────────┤
│  CONTEXT EXPLORER  │ PROGRESS ████████░░░░░░ 10/200 5.0%    │
│  Python / FastAPI  │ Sessions: 2 │ Tools: 15 │ Errors: 0    │
│  • Uses DI         │ RECENT TOOLS                             │
│  • All routes in   │   ✓ Write 88ms │ ✓ Bash 150ms          │
│    src/api/v1/     │                                          │
├────────────────────┴─────────────────────────────────────────┤
│ > Enter task prompt... _                                     │
├──────────────────────────────────────────────────────────────┤
│ q Quit p Pause s Stop ↑↓ Nav / Prompt v Valid c Context     │
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
| `/` | **(v2)** Focus prompt input |
| `v` | **(v2)** Toggle validation panel |
| `c` | **(v2)** Toggle context panel |

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

**Event Types** (21 total):

v1: `TEXT`, `TOOL_START`, `TOOL_END`, `TOOL_BLOCKED`, `ERROR`, `SESSION_START`, `SESSION_END`, `PROGRESS`

v2: `AGENT_SPAWN`, `AGENT_COMPLETE`, `ANALYSIS_UPDATE`, `PLAN_CREATED`, `PHASE_START`, `PHASE_END`, `GATE_START`, `GATE_RESULT`, `CONTEXT_UPDATE`, `MEMORY_UPDATE`, `THINKING`, `MOCK_DETECTED`, `PROMPT_RECEIVED`

## File Structure

```
src/acli/
├── cli.py                       # Typer CLI (13 commands)
├── __init__.py                  # Version 2.0.0
├── core/                        # Agent orchestration engine
│   ├── orchestrator.py          # v1 orchestrator (entry point)
│   ├── orchestrator_v1.py       # v1 orchestrator (preserved copy)
│   ├── orchestrator_v2.py       # v2 EnhancedOrchestrator
│   ├── agent.py                 # Agent session logic (Claude Agent SDK)
│   ├── client.py                # SDK client (Opus/Sonnet routing)
│   ├── session.py               # Session state + JSONL SessionLogger
│   └── streaming.py             # Event streaming (21 event types)
├── routing/                     # (v2) Prompt classification
│   ├── router.py                # PromptRouter (8 workflow types)
│   └── workflows.py             # WorkflowType + WorkflowConfig
├── context/                     # (v2) Codebase knowledge
│   ├── store.py                 # ContextStore (.acli/context/)
│   ├── memory.py                # MemoryManager (.acli/memory/)
│   ├── chunker.py               # KnowledgeChunker
│   └── onboarder.py             # BrownfieldOnboarder
├── agents/                      # (v2) Agent type system
│   ├── definitions.py           # 7 AgentTypes + AgentDefinition
│   └── factory.py               # AgentFactory (context injection)
├── validation/                  # (v2) Iron Rule enforcement
│   ├── mock_detector.py         # Mock detection hook (20 patterns)
│   ├── evidence.py              # EvidenceCollector
│   ├── gates.py                 # ValidationGate + GateRunner
│   ├── engine.py                # ValidationEngine
│   └── platforms/               # Platform-specific validators
│       ├── api.py               # APIValidator (curl)
│       ├── cli.py               # CLIValidator (commands)
│       ├── web.py               # WebValidator (Playwright)
│       ├── ios.py               # IOSValidator (simulator)
│       └── generic.py           # GenericValidator (shell)
├── tui/                         # Cyberpunk Agent Monitor TUI
│   ├── app.py                   # Main Textual application (7 panels)
│   ├── bridge.py                # OrchestratorBridge (v2 events)
│   ├── widgets.py               # All TUI widgets (v1 + v2)
│   ├── prompt_input.py          # (v2) Inline prompt widget
│   └── cyberpunk.tcss           # Cyberpunk Neon CSS (507 lines)
├── integration/                 # External integrations
│   ├── skill_engine.py          # (v2) SkillEngine auto-detection
│   ├── claude_config.py         # ~/.claude/ discovery
│   ├── skill_discovery.py       # Skill parsing
│   └── mcp_servers.py           # MCP server management
├── ui/                          # Legacy Rich-based dashboard
├── security/                    # Defense-in-depth security
├── spec/                        # Spec enhancement
├── progress/                    # Progress tracking
├── browser/                     # Browser automation (Puppeteer/Playwright)
├── prompts/                     # Prompt templates
└── utils/                       # Logger, event emitter
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
