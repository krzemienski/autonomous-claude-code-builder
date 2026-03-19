# Cyberpunk TUI Agent Monitor

**Type:** Feature Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/tui/app.py`
- `src/acli/tui/bridge.py`
- `src/acli/tui/widgets.py`
- `src/acli/tui/cyberpunk.tcss`
- `src/acli/core/streaming.py`

## Purpose

Gives developers real-time visibility into autonomous agent activity through a full-screen terminal dashboard, replacing opaque log output with an interactive monitoring experience.

## Diagram

```mermaid
graph TD
    subgraph "Front-Stage (Developer Experience)"
        Dev[Developer launches TUI] --> Monitor[acli monitor project/ ⚡]
        Monitor --> Header[Header: Status + Timer ⏱]
        Monitor --> Agents[Agent Hierarchy Panel 🎯]
        Monitor --> LogPanel[Live Log Stream ⚡ Full verbosity]
        Monitor --> Stats[Stats Dashboard 📊]
        Monitor --> Tools[Tool Execution Board 🛡]

        Dev --> Nav[Keyboard Navigation]
        Nav --> JK[j/k: Scroll agents]
        Nav --> F1F4[F1-F4: Filter log tabs]
        Nav --> PSQ[p: Pause  s: Stop  q: Quit]
    end

    subgraph "Back-Stage (Event Pipeline)"
        Orch[EnhancedOrchestrator] --> Buffer[StreamBuffer ⚡ Lock-free event ring]

        Buffer --> Bridge[TUI Bridge 🎯 Maps events to widgets]

        Bridge --> TextEvent[handle_text ⚡ Agent output]
        Bridge --> ToolEvent[handle_tool_start/end 🛡 Tool calls]
        Bridge --> SessionEvent[handle_session_start/end 📊 Session lifecycle]
        Bridge --> ProgressEvent[handle_progress 💾 Feature completion]

        TextEvent --> LogPanel
        ToolEvent --> Tools
        SessionEvent --> Agents
        ProgressEvent --> Stats
    end

    Orch -->|Error| ErrorEvent[handle_error 🔄]
    ErrorEvent --> LogPanel
    Orch -->|Blocked| BlockEvent[handle_tool_blocked 🛡]
    BlockEvent --> LogPanel

    PSQ -->|Pause| Orch
    PSQ -->|Stop| Orch
```

## Key Insights

- **4 FPS Refresh**: TUI updates at 4 frames per second for smooth real-time display without CPU overhead
- **Event-Driven**: StreamBuffer decouples agent execution from TUI rendering, preventing blocking
- **Keyboard-First**: All controls accessible via single keystrokes (j/k/p/s/q/F1-F4)
- **Dual Mode**: `--attach` runs orchestrator alongside TUI; `--detached` views existing state

## Change History

- **2026-03-19:** Initial creation; TUI verified via tmux capture (45 lines, header rendered)
