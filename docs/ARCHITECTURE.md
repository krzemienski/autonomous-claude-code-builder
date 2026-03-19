# Architecture — ACLI v2 (Shannon-ACLI)

This document describes the system architecture of the Autonomous CLI v2.

## Overview

ACLI v2 is a universal autonomous coding system that accepts ANY prompt and ANY project type. It extends v1's two-agent pattern with multi-agent orchestration, functional validation gates, deep context/memory management, and enhanced TUI visibility.

## System Diagram (v2)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Autonomous CLI v2 (acli)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌───────────────┐     ┌───────────────────────────┐  │
│  │ CLI          │────→│ PromptRouter  │────→│ EnhancedOrchestrator (v2) │  │
│  │ (13 commands)│     │ (8 workflows) │     │                           │  │
│  │ cli.py +     │     └───────────────┘     │  ┌─────────────────────┐  │  │
│  │ cli_v2.py    │              │            │  │ AgentFactory        │  │  │
│  └──────────────┘              ↓            │  │ (context + memory   │  │  │
│                        ┌───────────────┐    │  │  + skill injection) │  │  │
│                        │ WorkflowConfig│    │  └─────────────────────┘  │  │
│                        │ ├─ type       │    │           │               │  │
│                        │ ├─ agents[]   │    │           ↓               │  │
│                        │ ├─ model_tier │    │  ┌─────────────────────┐  │  │
│                        │ └─ platform   │    │  │ Agent Pipeline      │  │  │
│                        └───────────────┘    │  │ Router → Analyst    │  │  │
│                                             │  │ → Planner           │  │  │
│                                             │  │ → [Impl → Valid]×N  │  │  │
│                                             │  │ → Reporter          │  │  │
│                                             │  └─────────────────────┘  │  │
│                                             └───────────────────────────┘  │
│                                                        │                   │
│    ┌───────────────┐    ┌─────────────┐    ┌──────────┴──────────┐       │
│    │ ContextStore  │    │ MemoryMgr   │    │ ValidationEngine    │       │
│    │ .acli/context/│    │ .acli/memory│    │ EvidenceCollector   │       │
│    │ ├─ analysis   │    │ ├─ facts[]  │    │ GateRunner          │       │
│    │ ├─ tech_stack │    │ └─ inject   │    │ MockDetector        │       │
│    │ ├─ conventions│    │   prompt    │    │ Platform validators │       │
│    │ └─ decisions  │    └─────────────┘    └─────────────────────┘       │
│    └───────────────┘                                                      │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Agent Monitor TUI (Textual) — 7-panel cyberpunk dashboard           │  │
│  │ ┌────────────┬────────────┬──────────────────────────────────────┐  │  │
│  │ │ AgentGraph │ AgentDetail│ LogStream (F1:All F2:Tools F3:Err)   │  │  │
│  │ ├────────────┤            ├──────────────────────────────────────┤  │  │
│  │ │ Context    │            │ ValidationGatePanel                  │  │  │
│  │ │ Explorer   │            │ VG-1.1 PASS │ VG-1.2 PASS │ ...    │  │  │
│  │ ├────────────┴────────────┼──────────────────────────────────────┤  │  │
│  │ │                         │ StatsPanel (progress, tools, errors) │  │  │
│  │ ├─────────────────────────┴──────────────────────────────────────┤  │  │
│  │ │ > PromptInput (inline task entry)                              │  │  │
│  │ └───────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Security     │  │ SkillEngine  │  │ SessionLogger│  │ Browser      │  │
│  │ 16-cmd allow │  │ Agent/plat/  │  │ JSONL to     │  │ Puppeteer +  │  │
│  │ + MockDetect │  │ keyword map  │  │ .acli/sess/  │  │ Playwright   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                             │
│  v1 compat: AgentOrchestrator (orchestrator_v1.py) still available         │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ↓
                    ┌──────────────────┐
                    │ Claude Agent SDK │
                    │ claude-opus-4-6  │
                    │ claude-sonnet-4-6│
                    └──────────────────┘
```

## Agent Orchestration Sequence

```
User Prompt
    │
    ↓
PromptRouter.classify()
    │ ── detects: platform, source files, intent keywords
    ↓
WorkflowConfig
    │ ── workflow_type, agent_sequence, model_tier, platform
    ↓
EnhancedOrchestrator.run()
    │
    ├─→ ANALYST (Opus) ── codebase analysis, tech stack detection
    │       ↓
    ├─→ PLANNER (Opus) ── create execution plan with tasks
    │       ↓
    ├─→ IMPLEMENTER (Sonnet) ── implement one task
    │       ↓
    ├─→ VALIDATOR (Sonnet) ── functional validation with evidence
    │       │
    │       ├─ PASS → next task
    │       └─ FAIL → retry (max 3) → escalate to Opus
    │       ↓
    └─→ REPORTER (Sonnet) ── generate phase summary
```

## Core Components

### 1. CLI Layer (`acli.cli` + `acli.cli_v2`)

**v1 commands** (cli.py): `init`, `run`, `monitor`, `status`, `enhance`, `config`, `list-skills`
**v2 commands** (cli_v2.py): `onboard`, `prompt`, `validate`, `session`, `memory`, `context`

### 2. Prompt Router (`acli.routing`)

Classifies any prompt into 8 workflow types:

| Type | Trigger | Agent Sequence |
|------|---------|---------------|
| GREENFIELD_APP | app_spec.txt, <4 source files | analyst → planner → implementer → validator |
| BROWNFIELD_ONBOARD | source files, no .acli/context | analyst → planner |
| BROWNFIELD_TASK | source files + task prompt | planner → implementer → validator |
| DEBUG | "fix"/"debug"/"broken" keywords | analyst → implementer → validator |
| REFACTOR | "refactor"/"migrate" keywords | analyst → planner → implementer → validator |
| CLI_TOOL | Cargo.toml present | analyst → planner → implementer → validator |
| IOS_APP | .xcodeproj/.xcworkspace | analyst → planner → implementer → validator |
| FREE_TASK | fallback | implementer → validator |

### 3. Enhanced Orchestrator (`acli.core.orchestrator_v2`)

Replaces v1's 2-agent pattern with dynamic multi-agent pipeline.

**Key methods**: `run(prompt)`, `run_loop()` (v1 compat), `route_prompt()`, `run_analyst()`, `run_planner()`, `run_implementer()`, `run_validator()`, `run_reporter()`

**Controls**: `request_pause()`, `request_stop()`, `resume()`, `get_status()`

> Agent method bodies are scaffolded but not yet wired to real SDK `query()` calls.

### 4. Agent Architecture (`acli.agents`)

7 agent types with model routing:

| Agent | Model | Max Turns | Purpose |
|-------|-------|-----------|---------|
| ROUTER | Sonnet | 10 | Classify prompt |
| ANALYST | Opus | 50 | Codebase analysis |
| PLANNER | Opus | 50 | Create execution plan |
| IMPLEMENTER | Sonnet | 200 | Write code |
| VALIDATOR | Sonnet | 30 | Functional validation |
| CONTEXT_MANAGER | Sonnet | 20 | Manage knowledge |
| REPORTER | Sonnet | 10 | Generate reports |

`AgentFactory` injects ContextStore data + MemoryManager facts + SkillEngine skills into each agent's system prompt.

### 5. Context & Memory (`acli.context`)

| Component | Storage | Purpose |
|-----------|---------|---------|
| ContextStore | `.acli/context/*.json` | Codebase analysis, tech stack, conventions, decisions |
| MemoryManager | `.acli/memory/project_memory.json` | Cross-session categorized facts |
| KnowledgeChunker | In-memory | Split source files into retrievable segments |
| BrownfieldOnboarder | Populates ContextStore | Async pipeline: discover → detect → map → store |

### 6. Validation Engine (`acli.validation`)

Enforces the **Iron Rule**: no mocks, no test files, real system validation only.

| Component | Purpose |
|-----------|---------|
| MockDetector | Pre-tool-use hook blocking mock/test code (20+ patterns) |
| EvidenceCollector | Saves text/JSON/command output as evidence files |
| GateRunner | Executes validation gates with real shell commands |
| ValidationEngine | Orchestrates per-task and per-phase gates |
| Platform Validators | API (curl), CLI (binary exec), Web (Playwright), iOS (simctl), Generic |

### 7. Streaming (`acli.core.streaming`)

21 event types: 8 v1 (TEXT, TOOL_START, TOOL_END, TOOL_BLOCKED, ERROR, SESSION_START, SESSION_END, PROGRESS) + 13 v2 (AGENT_SPAWN, AGENT_COMPLETE, ANALYSIS_UPDATE, PLAN_CREATED, PHASE_START, PHASE_END, GATE_START, GATE_RESULT, CONTEXT_UPDATE, MEMORY_UPDATE, THINKING, MOCK_DETECTED, PROMPT_RECEIVED).

### 8. TUI (`acli.tui`)

7-panel cyberpunk dashboard:

| Panel | Purpose | Keys |
|-------|---------|------|
| AgentGraph | Agent hierarchy | j/k navigate |
| AgentDetail | Deep drill-down | Enter |
| ContextExplorer | Tech stack, memory facts | c toggle |
| LogStream | Full-verbosity event log | F1-F4 filter |
| ValidationGatePanel | Gate PASS/FAIL status | v toggle |
| StatsPanel | Progress, tools, errors | — |
| PromptInput | Inline task entry | / focus |

### 9. Skill Engine (`acli.integration.skill_engine`)

Auto-detects relevant skills for each agent based on: agent type mapping, platform mapping, task context keyword matching. Scans `~/.claude/skills/` for available SKILL.md files.

### 10. Session Logger (`acli.core.session.SessionLogger`)

JSONL logging to `.acli/sessions/`. Each line: `{type, session_id, timestamp, ...data}`. Supports `list_sessions()` and `load_session()` for replay.

## Security

- 16-command allowlist with per-command validators
- Mock detection hook on Write/Edit tools (20+ regex patterns)
- Defense layers: OS sandbox → file permissions → command allowlist → shlex parsing → pre-tool-use hooks → mock detection

## File Structure

```
src/acli/                          # ~9,400 LOC across 70 files
├── cli.py + cli_v2.py             # 13 CLI commands
├── core/
│   ├── orchestrator_v1.py         # v1 two-agent pattern (preserved)
│   ├── orchestrator_v2.py         # v2 enhanced orchestrator
│   ├── client.py                  # SDK client (MODEL_OPUS/MODEL_SONNET)
│   ├── session.py                 # ProjectState + SessionLogger
│   └── streaming.py               # 21 event types
├── routing/                       # Prompt classification (v2)
├── context/                       # Context/memory management (v2)
├── agents/                        # 7-type agent definitions (v2)
├── validation/                    # Functional validation engine (v2)
│   └── platforms/                 # 5 platform validators
├── tui/                           # 7-panel cyberpunk TUI
├── integration/                   # SkillEngine + external integrations
├── security/                      # 16-command allowlist + mock detection
├── spec/                          # Spec enhancement
├── progress/                      # Feature tracking
├── browser/                       # Puppeteer + Playwright
├── prompts/                       # Agent prompt templates
└── utils/                         # Logger, event emitter
```
