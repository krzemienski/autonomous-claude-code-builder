# ACLI v2 Agent Model Routing

**Type:** Architecture Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/agents/definitions.py`
- `src/acli/agents/factory.py`
- `src/acli/core/orchestrator_v2.py`

## Purpose

Shows how each of the 7 agent types is routed to the optimal Claude model — Opus for deep reasoning tasks (analysis, planning) and Sonnet for fast execution tasks (implementation, validation) — with per-agent configuration of thinking mode, max turns, and tool sets.

## Diagram

```mermaid
graph TB
    subgraph Front-Stage["Front-Stage (User Experience)"]
        User((User))
        Prompt["User Prompt<br/>Any task, any project type"]
        Result["Completed Work<br/>Code + Validation Evidence + Report"]

        User -->|"submits"| Prompt
        Result --> User
    end

    subgraph Back-Stage["Back-Stage (Implementation)"]
        Router["PromptRouter ⚡<br/>Classifies → WorkflowType<br/>Determines agent sequence"]

        Factory["AgentFactory 🎯<br/>Injects context, memory, skills<br/>Applies model routing per AgentType"]

        subgraph OpusTrack["Opus Track — Deep Reasoning"]
            direction TB
            Analyst["ANALYST ⚡<br/>Model: claude-opus-4-6<br/>Thinking: extended<br/>Max Turns: 10<br/>Tools: read-only filesystem,<br/>context store queries"]
            Planner["PLANNER ⚡<br/>Model: claude-opus-4-6<br/>Thinking: extended<br/>Max Turns: 8<br/>Tools: read-only filesystem,<br/>context store, memory read"]
        end

        subgraph SonnetTrack["Sonnet Track — Fast Execution"]
            direction TB
            AgentRouter["ROUTER ⏱️<br/>Model: claude-sonnet-4-6<br/>Thinking: standard<br/>Max Turns: 3<br/>Tools: minimal (classification only)"]
            Implementer["IMPLEMENTER ⏱️<br/>Model: claude-sonnet-4-6<br/>Thinking: standard<br/>Max Turns: 25<br/>Tools: full filesystem R/W,<br/>shell (16-cmd allowlist),<br/>browser automation"]
            Validator["VALIDATOR ✅<br/>Model: claude-sonnet-4-6<br/>Thinking: standard<br/>Max Turns: 15<br/>Tools: shell (curl, node, python),<br/>evidence collector,<br/>platform validators"]
            CtxManager["CONTEXT_MANAGER 💾<br/>Model: claude-sonnet-4-6<br/>Thinking: standard<br/>Max Turns: 5<br/>Tools: context store R/W,<br/>memory R/W, chunker"]
            Reporter["REPORTER 📊<br/>Model: claude-sonnet-4-6<br/>Thinking: standard<br/>Max Turns: 5<br/>Tools: read-only filesystem,<br/>evidence reader"]
        end

        subgraph Pipeline["Orchestration Pipeline 🔄"]
            Seq["Agent Sequence<br/>Router → Analyst → Planner →<br/>[Implementer → Validator]×N → Reporter"]
            Retry["Validation Failure 🔄<br/>Loop back to Implementer<br/>with failure evidence"]
        end

        Prompt --> Router
        Router --> Factory

        Factory -->|"deep reasoning needed"| OpusTrack
        Factory -->|"fast execution needed"| SonnetTrack

        AgentRouter -->|"WorkflowType"| Analyst
        Analyst -->|"analysis report"| Planner
        Planner -->|"implementation plan"| Implementer
        Implementer -->|"code changes"| Validator
        Validator -->|"PASS ✅"| Reporter
        Validator -->|"FAIL ❌"| Retry
        Retry -->|"evidence + feedback"| Implementer
        Reporter --> Result

        CtxManager -.->|"updates context<br/>between phases"| Analyst
        CtxManager -.->|"updates context<br/>between phases"| Planner
        CtxManager -.->|"updates context<br/>between phases"| Implementer
    end

    ErrorPath["Agent Error Recovery 🔄<br/>Max retries exceeded →<br/>Report partial results to user"]
    Retry -->|"max retries"| ErrorPath
    ErrorPath --> Result

    style Front-Stage stroke:#0ff,stroke-width:2px
    style Back-Stage stroke:#f0f,stroke-width:2px
    style OpusTrack stroke:#f90,stroke-width:2px
    style SonnetTrack stroke:#09f,stroke-width:2px
```

## Key Insights

- **User Impact 1:** The user gets high-quality analysis and planning (Opus handles the hard thinking) without paying Opus costs for every agent — only 2 of 7 agents use Opus, keeping cost proportional to reasoning depth.
- **User Impact 2:** The Implementer-Validator loop runs on fast Sonnet with up to 25 turns, so iterative code-and-validate cycles complete quickly rather than bottlenecking on expensive model calls.
- **Technical Enabler:** Per-agent tool scoping limits blast radius — the Router gets classification-only tools (3 max turns), the Implementer gets full filesystem + shell, and the Validator gets evidence collection tools. No agent has more power than its role requires.

## Change History

- **2026-03-19:** Initial creation (v2 bootstrap)
