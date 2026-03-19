# ACLI v2 System Architecture

**Type:** Architecture Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/cli.py`
- `src/acli/core/orchestrator_v2.py`
- `src/acli/core/agent.py`
- `src/acli/core/client.py`
- `src/acli/core/session.py`
- `src/acli/core/streaming.py`
- `src/acli/tui/app.py`
- `src/acli/security/validators.py`

## Purpose

Shows how a developer's project spec flows through ACLI's multi-agent orchestration to produce a working codebase, with security enforcement at every tool call and real-time visibility via the cyberpunk TUI.

## Diagram

```mermaid
graph TB
    subgraph "Front-Stage (Developer Experience)"
        Dev[Developer] --> CLI[CLI Commands 13 commands]
        CLI --> TUI[Cyberpunk TUI Monitor ⚡ Real-time agent visibility]
        CLI --> Headless[Headless Mode ⏱ Unattended builds]
        TUI --> Logs[Live Log Stream]
        TUI --> Progress[Progress Tracking 200 features]
    end

    subgraph "Back-Stage (Orchestration Engine)"
        CLI --> Orch[EnhancedOrchestrator v2 🎯 Routes prompts to agents]
        Orch --> Router[PromptRouter ✅ Classifies task type]
        Orch --> Factory[AgentFactory 🎯 Builds configured SDK clients]

        Router --> Init[Initializer Agent 📊 Reads spec, creates feature list]
        Router --> Code[Coding Agent 💾 Implements one feature per session]

        Init --> SDK[Claude Agent SDK ⚡ 55-160 turns per session]
        Code --> SDK

        SDK --> Security[Security Layer 🛡 16-command allowlist]
        Security --> Sandbox[OS Sandbox 🛡 File system isolation]
    end

    subgraph "Persistence Layer"
        Orch --> State[ProjectState 💾 Session tracking]
        Orch --> JSONL[SessionLogger 📊 JSONL event logs]
        Orch --> Features[feature_list.json 💾 Progress persistence]
        Orch --> Context[ContextStore 💾 Tech stack and analysis]
        Orch --> Memory[MemoryManager 💾 Project facts]
    end

    SDK --> Stream[StreamBuffer ⚡ Event-driven updates]
    Stream --> TUI
    State --> Progress

    Security -->|Blocked| Dev
    SDK -->|Error| Orch
    Orch -->|Retry 3x| SDK
```

## Key Insights

- **Autonomous Building**: Developer provides a spec, ACLI handles the entire build lifecycle across multiple agent sessions
- **Defense in Depth**: Four security layers (OS sandbox, file permissions, command allowlist, pre-tool hooks) protect against agent misuse
- **Real-time Visibility**: StreamBuffer feeds the TUI with live tool calls, text output, and progress without blocking agent execution
- **Resumable State**: JSONL logs + feature_list.json enable crash recovery and session replay

## Change History

- **2026-03-19:** Initial creation after E2E validation (200/200 features, 370 turns, $17.46)
