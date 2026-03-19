# ACLI v2 System Overview

**Type:** Architecture Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/cli.py`
- `src/acli/cli_v2.py`
- `src/acli/core/orchestrator_v2.py`
- `src/acli/routing/router.py`
- `src/acli/agents/definitions.py`
- `src/acli/validation/engine.py`
- `src/acli/tui/app.py`

## Purpose

Shows how a user's prompt flows from CLI entry through routing, orchestration, agent execution, and validation — with the TUI providing real-time monitoring at every stage.

## Diagram

```mermaid
graph TB
    subgraph Front-Stage["Front-Stage (User Experience)"]
        User((User))
        CLI["CLI Entry<br/>13 Typer Commands<br/>cli.py + cli_v2.py"]
        TUI["Cyberpunk TUI Dashboard<br/>7-Panel Layout<br/>AgentGraph | AgentDetail | ContextExplorer<br/>LogStream | ValidationGatePanel | StatsPanel | PromptInput"]
        Output["Final Output<br/>Code + Evidence + Report"]

        User -->|"acli run / prompt / validate"| CLI
        CLI -->|"acli monitor"| TUI
        Output --> User
    end

    subgraph Back-Stage["Back-Stage (Implementation)"]
        Router["PromptRouter ⚡<br/>Classifies into 8 WorkflowTypes<br/>greenfield | brownfield_onboard | brownfield_task<br/>refactor | debug | cli_tool | ios_app | free_task"]

        Orchestrator["EnhancedOrchestrator 🔄<br/>Multi-Agent Pipeline<br/>Router → Analyst → Planner →<br/>[Implementer → Validator]×N → Reporter"]

        subgraph AgentLayer["Agent Layer"]
            AgentFactory["AgentFactory 🎯<br/>Context/Memory/Skill Injection"]
            Agents["7 Agent Types ⚡<br/>ROUTER | ANALYST | PLANNER<br/>IMPLEMENTER | VALIDATOR<br/>CONTEXT_MANAGER | REPORTER"]
        end

        subgraph ContextLayer["Context & Memory"]
            ContextStore["ContextStore 💾<br/>.acli/context/<br/>Tech Stack, Conventions, Decisions"]
            Memory["MemoryManager 💾<br/>.acli/memory/project_memory.json<br/>Cross-Session Facts"]
            Chunker["KnowledgeChunker 📊<br/>Codebase Segmentation"]
            Onboarder["BrownfieldOnboarder 🔄<br/>Async Analysis Pipeline"]
        end

        subgraph ValidationLayer["Validation Engine"]
            MockDetector["MockDetector 🛡️<br/>Pre-Tool-Use Hook<br/>20+ Patterns Block Mock/Test Code"]
            Evidence["EvidenceCollector ✅<br/>Real Command Output"]
            Gates["GateRunner ✅<br/>PASS/FAIL with Evidence"]
            Validators["Platform Validators ⚡<br/>API (curl) | CLI (binary exec)<br/>Web (Playwright) | iOS (simctl) | Generic"]
        end

        subgraph SecurityLayer["Security"]
            Security["Defense-in-Depth 🛡️<br/>OS Sandbox → File Perms →<br/>16-Cmd Allowlist → shlex →<br/>Pre-Tool Hooks → Mock Detection"]
        end

        Streaming["Event Streaming 📊<br/>21 Event Types<br/>AGENT_SPAWN | GATE_RESULT<br/>CONTEXT_UPDATE | ..."]

        CLI -->|"prompt + project-dir"| Router
        Router -->|"WorkflowType + config"| Orchestrator
        Orchestrator --> AgentFactory
        AgentFactory -->|"spawns with injection"| Agents
        Agents -->|"reads/writes"| ContextStore
        Agents -->|"reads/writes"| Memory
        Agents -->|"uses"| Chunker
        Router -->|"brownfield workflows"| Onboarder
        Onboarder --> ContextStore
        Agents -->|"code changes"| MockDetector
        MockDetector -->|"blocked"| ErrorPath
        MockDetector -->|"allowed"| Evidence
        Evidence --> Gates
        Gates --> Validators
        Validators -->|"PASS"| Output
        Agents --> Security
        Orchestrator --> Streaming
        Streaming --> TUI
    end

    ErrorPath["Error Recovery 🔄<br/>Retry without mocks<br/>Re-route agent"]
    ErrorPath -->|"retry"| Orchestrator

    style Front-Stage stroke:#0ff,stroke-width:2px
    style Back-Stage stroke:#f0f,stroke-width:2px
```

## Key Insights

- **User Impact 1:** A single prompt triggers the full pipeline — the user never manually coordinates agents, validation, or context loading.
- **User Impact 2:** The TUI streams 21 event types in real time, so the user sees exactly which agent is active, what validation gates passed/failed, and what context was loaded.
- **Technical Enabler:** The PromptRouter's 8 workflow types mean the same CLI handles greenfield apps, brownfield tasks, debugging, refactoring, and platform-specific work (iOS, CLI, Web) without the user specifying a mode.

## Change History

- **2026-03-19:** Initial creation (v2 bootstrap)
