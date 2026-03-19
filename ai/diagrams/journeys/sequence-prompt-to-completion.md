# Prompt-to-Completion Journey

**Type:** Sequence Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/cli_v2.py`
- `src/acli/core/orchestrator_v2.py`
- `src/acli/routing/router.py`
- `src/acli/agents/factory.py`
- `src/acli/validation/engine.py`
- `src/acli/core/session.py`

## Purpose

Shows the full lifecycle from a user typing `acli run` or `acli prompt` through prompt classification, multi-agent pipeline execution, validation gates, and final result delivery -- exposing both the user-facing experience and back-stage orchestration decisions.

## Diagram

```mermaid
sequenceDiagram
    autonumber

    box Front-Stage (User Experience)
        participant U as User
        participant CLI as CLI (typer)
    end

    box Back-Stage (Implementation)
        participant PR as PromptRouter
        participant ORC as EnhancedOrchestrator
        participant AF as AgentFactory
        participant AP as AgentPipeline
        participant VE as ValidationEngine
        participant SL as SessionLogger
    end

    Note over U,CLI: User enters prompt via terminal or TUI

    U->>CLI: acli run <project-dir> / acli prompt "task"
    CLI->>CLI: Parse args, resolve project path

    alt Missing ANTHROPIC_API_KEY
        CLI-->>U: Error: API key not configured
    end

    CLI->>ORC: initialize(project_dir, prompt)
    Note right of ORC: ⚡ Load ContextStore + MemoryManager

    ORC->>PR: classify(prompt)
    Note right of PR: 🎯 Match to 1 of 8 WorkflowTypes
    PR-->>ORC: WorkflowType + WorkflowConfig

    alt Unknown / ambiguous prompt
        PR-->>ORC: FREE_TASK fallback
        Note right of PR: 🔄 Graceful degradation
    end

    ORC->>AF: create_agents(workflow_config)
    Note right of AF: 💾 Inject context, memory, skills per agent type

    AF-->>ORC: Agent[] (Router, Analyst, Planner, Implementer, Validator, Reporter)

    ORC->>SL: start_session(project_dir)
    Note right of SL: 💾 Open JSONL log file

    rect rgb(240, 248, 255)
        Note over AP,VE: Agent Pipeline Execution

        ORC->>AP: run(ROUTER agent, Sonnet, 10 turns)
        AP-->>ORC: Routing decision
        SL->>SL: log(AGENT_SPAWN)

        ORC->>AP: run(ANALYST agent, Opus, 50 turns)
        Note right of AP: ⚡ Deep codebase analysis
        AP-->>ORC: Analysis report
        SL->>SL: log(AGENT_SPAWN)

        ORC->>AP: run(PLANNER agent, Opus, 50 turns)
        Note right of AP: 🎯 Implementation plan with phases
        AP-->>ORC: Plan document
        SL->>SL: log(AGENT_SPAWN)

        loop Implementer-Validator cycle (N iterations)
            ORC->>AP: run(IMPLEMENTER agent, Sonnet, 200 turns)
            Note right of AP: ⚡ Code generation + file writes
            AP-->>ORC: Implementation artifacts
            SL->>SL: log(AGENT_SPAWN)

            ORC->>VE: run_gates(artifacts)
            Note right of VE: ✅ Platform validators execute real commands

            alt Gate PASS
                VE-->>ORC: PASS + evidence files
                Note right of VE: 💾 Evidence saved to .acli/evidence/
            else Gate FAIL
                VE-->>ORC: FAIL + failure details
                Note right of VE: 🔄 Loop back to Implementer
            end
            SL->>SL: log(GATE_RESULT)
        end

        ORC->>AP: run(REPORTER agent, Sonnet, 20 turns)
        Note right of AP: 📊 Summarize outcomes
        AP-->>ORC: Final report
        SL->>SL: log(AGENT_SPAWN)
    end

    ORC->>SL: end_session(status)
    Note right of SL: 💾 Flush JSONL, record duration

    ORC-->>CLI: CompletionResult(report, evidence, session_id)

    alt TUI mode (acli run)
        CLI-->>U: Live dashboard updated throughout
        Note over U,CLI: 7-panel cyberpunk TUI with real-time events
    else Terminal mode (acli prompt)
        CLI-->>U: Summary + evidence paths printed
    end

    alt Pipeline error (any stage)
        ORC-->>CLI: Error with last successful stage
        CLI-->>U: Partial result + error context + session ID for resume
        Note over U: 🔄 User can run: acli session resume <id>
    end
```

## Key Insights

- **User Impact 1:** Users never interact with agent internals -- the CLI and TUI abstract the full pipeline into a single command with live feedback or a final summary.
- **User Impact 2:** Session IDs enable resume-from-failure, so a crashed run does not lose all progress.
- **Technical Enabler:** The Implementer-Validator loop with real evidence (not mocks) ensures code actually works before the pipeline reports success. Opus handles analysis/planning; Sonnet handles high-throughput implementation.

## Change History

- **2026-03-19:** Initial creation (v2 bootstrap)
