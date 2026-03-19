---
title: "ACLI v2 (Shannon) — Full Implementation Plan"
description: "20x-granularity plan: 6 phases, 21 gates, real CLI validation with ALR payload"
status: completed
priority: P1
effort: 40h
branch: m4-v2
tags: [acli, v2, shannon, agent-sdk, tui, validation]
created: 2026-03-18
---

# ACLI v2 (Shannon) — Implementation Plan

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        acli CLI (Typer)                             │
│  init | run | monitor | status | enhance | config | list-skills    │
│  + NEW: onboard | prompt | validate | session | memory | context   │
├──────────────┬──────────────────────────┬──────────────────────────┤
│  Router      │  Orchestrator v2         │  Validation Engine       │
│  classify()  │  AgentOrchestrator       │  MockDetector            │
│  → greenfield│  multi-agent dispatch    │  EvidenceCollector       │
│  → brownfield│  JSONL session logging   │  CLIValidator            │
│  → onboard   │  cost/token tracking     │  PlatformValidator       │
├──────────────┼──────────────────────────┼──────────────────────────┤
│  Agent Defs  │  Skill Engine            │  Context Store           │
│  AgentFactory│  SkillRegistry           │  ProjectContext          │
│  AgentConfig │  SkillMatcher            │  TechStackDetector       │
│  agent tiers │  auto-invoke             │  MemoryManager           │
├──────────────┴──────────────────────────┴──────────────────────────┤
│                     Core Infrastructure                            │
│  client.py (model routing, thinking config, hooks)                 │
│  streaming.py (extended EventType enum + new events)               │
│  session.py (v2 state with cost/token/agent tracking)              │
├───────────────────────────────────────────────────────────────────┤
│                     TUI (Textual 7.0)                              │
│  7-panel layout: Header | AgentGraph | AgentDetail | LogStream    │
│  PromptInput | StatsPanel | CostTracker                            │
│  tmux-verifiable via capture-pane                                  │
└───────────────────────────────────────────────────────────────────┘
```

## Phase Summary

| # | Phase | Files Changed | Files New | Gates | Effort |
|---|-------|--------------|-----------|-------|--------|
| 1 | Core Infrastructure | 4 | 2 | G1-G3 | 6h |
| 2 | Agent Architecture | 2 | 4 | G4-G7 | 8h |
| 3 | Validation Engine | 0 | 4 | G8-G10 | 5h |
| 4 | Enhanced TUI | 3 | 1 | G11-G14 | 8h |
| 5 | CLI Integration | 1 | 3 | G15-G18 | 6h |
| 6 | Final Integration | 3 | 0 | G19-G21 | 7h |
| **Total** | | **13** | **14** | **21** | **40h** |

## Gate Manifest (All Blocking, Sequential)

| Gate | Phase | Validation | Method |
|------|-------|-----------|--------|
| G1 | 1 | pip install + acli --version | CLI exec |
| G2 | 1 | Model strings updated (no stale) | grep + CLI |
| G3 | 1 | Context store + router init test | acli init |
| G4 | 2 | Agent factory creates agents | acli run --headless |
| G5 | 2 | JSONL session logging | file inspection |
| G6 | 2 | Skill engine lists skills | acli list-skills |
| G7 | 2 | Orchestrator v2 single iteration | acli run --max-iterations 1 |
| G8 | 3 | Mock detector blocks test files | hook output |
| G9 | 3 | Evidence collector saves output | file inspection |
| G10 | 3 | acli validate runs CLI checks | acli validate |
| G11 | 4 | TUI renders 7 panels | tmux capture-pane |
| G12 | 4 | Keyboard nav (j/k/enter) works | tmux send-keys |
| G13 | 4 | PromptInput captures input | tmux send-keys |
| G14 | 4 | CostTracker shows real data | tmux capture-pane |
| G15 | 5 | All 13 commands respond --help | CLI exec loop |
| G16 | 5 | Session/memory/context commands | acli session/memory/context |
| G17 | 5 | ALR init + status workflow | acli init + status |
| G18 | 5 | Onboard existing project | acli onboard |
| G19 | 6 | Lint + type check pass | ruff + mypy |
| G20 | 6 | ALR greenfield E2E | full workflow |
| G21 | 6 | ALR brownfield E2E + TUI tmux | full workflow + tmux |

## Validation Protocol Summary

1. **Real CLI execution** — Every gate runs `pip install -e ".[dev]"` then real `acli` commands
2. **ALR payload** — Awesome-List-Researcher spec used as test project
3. **tmux TUI verification** — `tmux capture-pane` for all TUI gates
4. **Dual-agent verification** — 2 independent verifier agents read evidence and confirm PASS
5. **Skills at every gate** — `/functional-validation` + `/gate-validation-discipline` invoked before each gate

## SDK Facts (from researcher-260318-2350-claude-agent-sdk-api.md)

- Package: `claude-agent-sdk` v0.1.49, wraps Claude CLI subprocess (NOT direct API)
- Full model IDs: `"claude-opus-4-6-20250514"`, `"claude-sonnet-4-6-20250514"`
- Thinking: `thinking={"type": "adaptive"}` + `effort="high"` (effort is SEPARATE field on ClaudeAgentOptions)
- Hooks: `HookMatcher(matcher="Bash", hooks=[my_hook])` in dict keyed by HookEvent string
- Hook return: `{"continue_": True}` to allow, `{"continue_": False, "decision": "block", "reason": "..."}` to block
- Messages: `AssistantMessage.content = list[TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock]`
- Cost: `ResultMessage.total_cost_usd` (cumulative), `ResultMessage.usage` (token breakdown)
- Output format: `output_format` field (NOT output_config — prompt had this wrong)
- Session: `async with ClaudeSDKClient(options) as client: await client.query(); async for msg in client.receive_response()`
- AgentDefinition: `model` accepts "sonnet"|"opus"|"haiku"|"inherit" shorthand

## v1 Codebase Key Locations (from researcher-260318-2350-v1-codebase-deep-analysis.md)

| File | Lines | Stale Model Strings |
|------|-------|---------------------|
| `core/client.py` | 149 | None (passed as param) |
| `core/orchestrator.py` | 279 | Line 38: `"claude-sonnet-4-20250514"`, Line 261: `"claude-opus-46"` (TYPO) |
| `core/streaming.py` | 198 | None |
| `core/session.py` | 146 | None |
| `cli.py` | 626 | Lines 211, 454, 565: `"claude-sonnet-4-20250514"` |
| `spec/enhancer.py` | 236 | Lines 60, 110, 187: `"claude-sonnet-4-20250514"` |
| `spec/refinement.py` | — | Line 89: `"claude-sonnet-4-20250514"` |
| `integration/claude_config.py` | 172 | Line 115: `"claude-sonnet-4-20250514"` |

**Total: 11 stale model strings across 6 files**

## Execution Command

```bash
/cook /Users/nick/Desktop/claude-code-builder-agents-sdk/plans/260318-2351-acli-v2-shannon/plan.md
```

## Phase Files

- [Gate Protocol](./gate-protocol.md) — shared validation procedure for all gates
- [Phase 1: Core Infrastructure](./phases/01-PLAN-core-infrastructure.md)
- [Phase 2: Agent Architecture](./phases/02-PLAN-agent-architecture.md)
- [Phase 3: Validation Engine](./phases/03-PLAN-validation-engine.md)
- [Phase 4: Enhanced TUI](./phases/04-PLAN-enhanced-tui.md)
- [Phase 5: CLI Integration](./phases/05-PLAN-cli-integration.md)
- [Phase 6: Final Integration](./phases/06-PLAN-final-integration.md)

## Research Reports

- `plans/reports/researcher-260318-2350-claude-agent-sdk-api.md` — 1,384 lines, full SDK API
- `plans/reports/researcher-260318-2350-v1-codebase-deep-analysis.md` — 44 files line-level analysis
- `plans/reports/researcher-260318-2350-textual-tui-api.md` — Textual 7.0.0 framework API
- `plans/reports/researcher-260318-2350-alr-validation-design.md` — 7 ALR validation scenarios, tmux automation
