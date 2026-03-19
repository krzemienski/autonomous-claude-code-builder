# Agent Session Lifecycle

**Type:** Sequence Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/core/orchestrator_v2.py`
- `src/acli/core/agent.py`
- `src/acli/core/client.py`
- `src/acli/core/session.py`
- `src/acli/core/streaming.py`

## Purpose

Shows the complete lifecycle of a single agent session from prompt loading through SDK interaction to state persistence, enabling developers to understand how their project gets built turn by turn.

## Diagram

```mermaid
sequenceDiagram
    actor Dev as Developer
    participant CLI as CLI / TUI
    participant Orch as EnhancedOrchestrator
    participant State as ProjectState
    participant SDK as Claude Agent SDK
    participant Agent as Claude Agent
    participant Stream as StreamBuffer

    Dev->>CLI: acli run project/
    CLI->>Orch: run_loop(max_iterations)
    Note over Orch: Checks is_first_run 💾

    Orch->>State: start_session()
    Note over State: Returns type: initializer or coding ✅

    Orch->>Orch: load_prompt_template(type)
    Note over Orch: Tech-stack-adaptive prompt 🎯

    Orch->>SDK: create_sdk_client(project_dir, model)
    Note over SDK: Writes .claude_settings.json 🛡

    Orch->>SDK: client.query(prompt)
    Note over SDK: Sends to Claude CLI ⚡

    loop Agent Turns (55-160 per session)
        SDK->>Agent: AssistantMessage
        Agent->>Stream: handle_text / handle_tool_start
        Stream->>CLI: Live updates ⚡ Real-time feedback

        Agent->>SDK: ToolUse (Read, Write, Bash...)
        Note over SDK: Security hooks validate 🛡

        SDK->>Agent: ToolResult
        Agent->>Stream: handle_tool_end
    end

    SDK->>Orch: ResultMessage (turns, cost, stop_reason)
    Note over Orch: Logs to JSONL 📊

    alt RateLimitEvent
        SDK->>Orch: RateLimitEvent
        Note over Orch: Continues silently 🔄
    end

    alt Session Error
        SDK->>Orch: Error
        Orch->>State: end_session(status=error)
        Note over Orch: Retries up to 3x 🔄
    end

    Orch->>State: end_session(status=completed)
    Orch->>State: save() 💾
    Orch->>Stream: handle_progress(passing, total)
    Stream->>CLI: Progress update ✅

    Note over Orch: Wait 3s, then next session ⏱
```

## Key Insights

- **Adaptive Prompts**: Initializer vs coding prompts are selected automatically based on feature_list.json state
- **Error Resilience**: RateLimitEvent is handled gracefully; up to 3 consecutive errors before stopping
- **Live Feedback**: Every tool call and text block flows through StreamBuffer to the TUI in real-time
- **Session Cost Tracking**: ResultMessage captures exact cost and turn count per session

## Change History

- **2026-03-19:** Initial creation based on E2E validation findings
