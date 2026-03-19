# TUI Dashboard

**Type:** Feature Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/tui/app.py`
- `src/acli/tui/bridge.py`
- `src/acli/tui/widgets.py`
- `src/acli/tui/prompt_input.py`
- `src/acli/tui/cyberpunk.tcss`

## Purpose

Provides real-time visibility into the multi-agent orchestration pipeline through a 7-panel cyberpunk terminal UI, so users can monitor, steer, and debug autonomous coding sessions without leaving the terminal.

## Diagram

```mermaid
graph TD
    subgraph "Front-Stage (User Experience)"
        User([User]) -->|"acli monitor ."| LaunchTUI[Launch TUI Dashboard]
        LaunchTUI --> Dashboard["7-Panel Cyberpunk Layout"]

        Dashboard --> PanelGroup["Panel Interactions"]
        PanelGroup --> NavAgent["j/k: Scroll Agent List"]
        PanelGroup --> FilterLog["F1-F4: Filter Log Events"]
        PanelGroup --> ViewVal["v: Toggle Validation Panel"]
        PanelGroup --> ViewCtx["c: Toggle Context Explorer"]
        PanelGroup --> TypePrompt["/: Open Prompt Input"]
        PanelGroup --> CtrlFlow["p: Pause | s: Stop | q: Quit"]

        TypePrompt -->|"Enter new prompt"| InlineCmd[Submit Inline Command]
        InlineCmd --> Dashboard

        CtrlFlow -->|"q"| Quit[Exit TUI]
        Quit --> User
    end

    subgraph "Back-Stage (Implementation)"
        LaunchTUI --> AppInit["TUI App.__init__()\nTextual Framework ⚡"]
        AppInit --> Bridge["OrchestratorBridge\n.connect() 🔄"]
        Bridge --> Orchestrator["EnhancedOrchestrator\nevent stream ⚡"]

        Orchestrator --> Events["21 Event Types 📊"]
        Events --> V1Events["v1: FEATURE_START\nFEATURE_COMPLETE\nBROWSER_ACTION\nSESSION_START\nSESSION_END\nPROGRESS\nERROR\nBUILD_STATUS"]
        Events --> V2Events["v2: AGENT_SPAWN\nAGENT_COMPLETE\nGATE_RESULT\nCONTEXT_UPDATE\nMEMORY_WRITE\nROUTE_DECISION\nPIPELINE_STAGE\nVALIDATION_START\nVALIDATION_END\nEVIDENCE_CAPTURED\nSKILL_INVOKED\nPROMPT_CLASSIFIED\nSESSION_REPLAY"]

        V1Events --> Dispatch["Bridge Event\nDispatcher 🔄"]
        V2Events --> Dispatch

        Dispatch --> P1["AgentGraph\nAgent DAG ⚡"]
        Dispatch --> P2["AgentDetail\nSelected Agent Info 📊"]
        Dispatch --> P3["ContextExplorer\nBrowse Context Store 💾"]
        Dispatch --> P4["LogStream\n21 Types, F1-F4 Filter ⏱️"]
        Dispatch --> P5["ValidationGatePanel\nPASS/FAIL Gates ✅"]
        Dispatch --> P6["StatsPanel\nTokens, Duration, Cost 📊"]
        Dispatch --> P7["PromptInput\nInline / Commands 🎯"]

        P1 --> Render["Textual Reactive\nRender Cycle ⚡"]
        P2 --> Render
        P3 --> Render
        P4 --> Render
        P5 --> Render
        P6 --> Render
        P7 --> Render

        Render --> Theme["cyberpunk.tcss\nNavy/Cyan/Pink/Green 🎯"]
        Theme --> Dashboard

        InlineCmd --> Bridge
        Bridge -->|"Forward prompt"| Orchestrator

        CtrlFlow -->|"p: pause"| PauseOrch["Pause Orchestrator ⏱️"]
        CtrlFlow -->|"s: stop"| StopOrch["Stop Orchestrator 🛡️"]
        PauseOrch --> Bridge
        StopOrch --> Bridge

        Bridge -.->|"Connection lost"| ReconnErr["Show 'Disconnected'\nBanner, Auto-Retry 🔄"]
        ReconnErr --> Bridge

        Orchestrator -.->|"Agent crash"| CrashEvent["Emit ERROR Event ⏱️"]
        CrashEvent --> Dispatch

        Render -.->|"Terminal too small"| ResizeErr["Collapse Panels\nto Minimum Layout 🔄"]
        ResizeErr --> Dashboard
    end
```

## Key Insights

- **Full Visibility Without Context Switching:** Users see agent DAGs, validation gates, context state, and cost metrics in one terminal screen. No browser tabs, no log file tailing.
- **Interactive Steering:** The inline prompt input (`/`) and pause/stop controls let users redirect or halt autonomous work in real-time rather than waiting for completion.
- **Technical Enabler:** The OrchestratorBridge decouples the TUI from the orchestrator, so the 21 event types flow through a single dispatch path and panels subscribe to only the events they need.

## Change History

- **2026-03-19:** Initial creation (v2 bootstrap)
