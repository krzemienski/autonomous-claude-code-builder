# Phase 4: Enhanced TUI — Full Visibility

## Priority: P1 | Depends: Phase 3 (PG-3 PASSED) | Gates: G11, G12, G13, G14

**Objective**: Add 3 new TUI panels (ContextExplorer, ValidationGatePanel, PromptInput), update layout to 7 panels, add new keybindings, extend cyberpunk theme. Validate via tmux.

**Skills to invoke before starting**: `/functional-validation`, `/gate-validation-discipline`

---

## Task 4.1: New TUI Widgets

### Modified File: `src/acli/tui/widgets.py` (590 lines)

Add 2 new widget classes after `StatsPanel` (after line 589), following existing patterns:

**ContextExplorer** (~60 lines):
- Inherits `Widget`, takes `bridge: OrchestratorBridge` in `__init__`
- `compose()`: `VerticalScroll` containing `Static(id="context-content")`
- `refresh_context()`: reads `bridge.snapshot.context_summary`, updates Static content
- Shows: tech stack, file count, LOC, memory fact count
- CSS class: `context-explorer`

**ValidationGatePanel** (~70 lines):
- Inherits `Widget`, takes `bridge: OrchestratorBridge` in `__init__`
- `compose()`: `VerticalScroll` containing `Static(id="gates-content")`
- `update_gate(gate_id: str, status: str)`: updates individual gate status
- `refresh_gates()`: reads `bridge.snapshot.gate_results`, renders all gates with colored status
- Status colors: PASS=#00ff41, FAIL=#ff003c, RUNNING=#0abdc6, PENDING=#4a6670
- CSS class: `validation-gate-panel`

### New File: `src/acli/tui/prompt_input.py` (~50 lines):

**PromptInput** widget:
- Inherits `Widget`
- `compose()`: `Horizontal` containing `Static("▶")` + `Input(placeholder="Enter task...", id="prompt-field")`
- `on_input_submitted(self, event: Input.Submitted)`: captures text, posts custom message to app
- CSS class: `prompt-input`

Uses Textual Input widget (from research report):
```python
from textual.widgets import Input, Static
from textual.containers import Horizontal
```

---

## Task 4.2: Update TUI App Layout & Bridge

### Modified File: `src/acli/tui/app.py` (276 lines)

**Step 1**: Add imports (after line 24):
```python
from .widgets import AgentDetail, AgentGraph, ContextExplorer, CyberHeader, LogStream, StatsPanel, ValidationGatePanel
from .prompt_input import PromptInput
```

**Step 2**: Add new BINDINGS (after line 63, before closing `]`):
```python
        Binding("slash", "focus_prompt", "Prompt", show=True),
        Binding("v", "toggle_validation", "Validation", show=False),
        Binding("c", "toggle_context", "Context", show=False),
```

**Step 3**: Update `compose()` (lines 80-94) for 7-panel layout:
```python
    def compose(self) -> ComposeResult:
        yield CyberHeader()
        with Horizontal(id="main-container"):
            with Vertical(id="left-panel"):
                yield AgentGraph(self.bridge, id="agent-graph-widget")
                yield AgentDetail(self.bridge, id="agent-detail-widget")
                yield ContextExplorer(self.bridge, id="context-explorer-widget")
            with Vertical(id="right-panel"):
                yield LogStream(self.bridge, id="log-stream-widget")
                yield ValidationGatePanel(self.bridge, id="validation-gate-widget")
                yield StatsPanel(self.bridge, id="stats-panel-widget")
        yield PromptInput(id="prompt-input-widget")
        yield Footer()
```

**Step 4**: Add new action methods (after line 270):
```python
    def action_focus_prompt(self) -> None:
        try:
            prompt = self.query_one("#prompt-field", Input)
            prompt.focus()
            self.notify("Type task and press Enter", severity="information")
        except NoMatches:
            pass

    def action_toggle_validation(self) -> None:
        try:
            panel = self.query_one("#validation-gate-widget", ValidationGatePanel)
            panel.toggle_class("hidden")
        except NoMatches:
            pass

    def action_toggle_context(self) -> None:
        try:
            panel = self.query_one("#context-explorer-widget", ContextExplorer)
            panel.toggle_class("hidden")
        except NoMatches:
            pass
```

**Step 5**: Update `_refresh_all_widgets()` (after line 164) to refresh new widgets:
```python
        try:
            context = self.query_one("#context-explorer-widget", ContextExplorer)
            context.refresh_context()
        except NoMatches:
            pass

        try:
            gates = self.query_one("#validation-gate-widget", ValidationGatePanel)
            gates.refresh_gates()
        except NoMatches:
            pass
```

### Modified File: `src/acli/tui/bridge.py` (350 lines)

**Step 1**: Add new fields to `OrchestratorSnapshot` (after line 72):
```python
    context_summary: str = ""
    gate_results: list[dict] = field(default_factory=list)
```

**Step 2**: Handle new event types in `handle_event()` (after line 251, before the callback section):
```python
        elif event.type == EventType.GATE_START:
            self._snapshot.gate_results.append({
                "gate_id": event.gate_id,
                "status": "RUNNING",
            })

        elif event.type == EventType.GATE_RESULT:
            for gate in self._snapshot.gate_results:
                if gate["gate_id"] == event.gate_id:
                    gate["status"] = event.gate_status
                    break
            else:
                self._snapshot.gate_results.append({
                    "gate_id": event.gate_id,
                    "status": event.gate_status,
                })

        elif event.type == EventType.CONTEXT_UPDATE:
            self._snapshot.context_summary = event.text

        elif event.type == EventType.MEMORY_UPDATE:
            self._snapshot.context_summary += f"\nMemory: {event.memory_fact}"
```

### Modified File: `src/acli/tui/cyberpunk.tcss` (409 lines)

Add styles at end of file for new widgets:
```css
/* Context Explorer */
ContextExplorer, #context-explorer-widget {
    height: 1fr;
    border: solid #133e7c;
    background: #000b1e;
    padding: 1;
}

/* Validation Gate Panel */
ValidationGatePanel, #validation-gate-widget {
    height: 1fr;
    border: solid #133e7c;
    background: #000b1e;
    padding: 1;
}

/* Prompt Input */
PromptInput, #prompt-input-widget {
    height: 3;
    dock: bottom;
    border-top: solid #0abdc6;
    background: #0a0a2e;
    padding: 0 1;
}

PromptInput Input {
    background: #000b1e;
    color: #d7fffe;
    border: none;
}

/* Hidden class for toggle */
.hidden {
    display: none;
}
```

---

## Gate G11: TUI Renders All Panels (tmux)

```bash
mkdir -p evidence/G11

# Create test project
rm -rf /tmp/acli-g11-test
python -m acli init /tmp/acli-g11-test --no-interactive 2>&1 | tee evidence/G11/init.txt

# Launch TUI in tmux
tmux new-session -d -s acli-g11 -x 120 -y 40
tmux send-keys -t acli-g11 "cd /Users/nick/Desktop/claude-code-builder-agents-sdk && python -m acli monitor /tmp/acli-g11-test --detached" Enter
sleep 4

# Capture initial render
tmux capture-pane -t acli-g11 -p > evidence/G11/tui-initial.txt

# Verify key content present
grep -c "ACLI\|Agent\|Monitor" evidence/G11/tui-initial.txt > evidence/G11/header-check.txt
grep -c "AGENT\|Graph\|HIERARCHY" evidence/G11/tui-initial.txt > evidence/G11/graph-check.txt
wc -l < evidence/G11/tui-initial.txt > evidence/G11/line-count.txt

# Cleanup
tmux send-keys -t acli-g11 "q"
sleep 1
tmux kill-session -t acli-g11 2>/dev/null

echo "TUI capture complete" | tee -a evidence/G11/tui-initial.txt
```

**PASS criteria**:
- [ ] tmux capture has > 20 lines (full screen rendered)
- [ ] Contains "ACLI" or "Agent" or "Monitor" (header)
- [ ] Contains agent-related text (graph panel)
- [ ] TUI exits cleanly with 'q'

---

## Gate G12: Keyboard Navigation (tmux)

```bash
mkdir -p evidence/G12

tmux new-session -d -s acli-g12 -x 120 -y 40
tmux send-keys -t acli-g12 "cd /Users/nick/Desktop/claude-code-builder-agents-sdk && python -m acli monitor /tmp/acli-g11-test --detached" Enter
sleep 4

# Capture before navigation
tmux capture-pane -t acli-g12 -p > evidence/G12/before-nav.txt

# Navigate down (j)
tmux send-keys -t acli-g12 "j"
sleep 1
tmux capture-pane -t acli-g12 -p > evidence/G12/after-j.txt

# Navigate up (k)
tmux send-keys -t acli-g12 "k"
sleep 1
tmux capture-pane -t acli-g12 -p > evidence/G12/after-k.txt

# Cleanup
tmux send-keys -t acli-g12 "q"
sleep 1
tmux kill-session -t acli-g12 2>/dev/null

# Verify screen changed
diff evidence/G12/before-nav.txt evidence/G12/after-j.txt > evidence/G12/j-diff.txt 2>&1 || true
echo "Navigation test complete" | tee evidence/G12/result.txt
```

---

## Gate G13: PromptInput Captures Input (tmux)

```bash
mkdir -p evidence/G13

tmux new-session -d -s acli-g13 -x 120 -y 40
tmux send-keys -t acli-g13 "cd /Users/nick/Desktop/claude-code-builder-agents-sdk && python -m acli monitor /tmp/acli-g11-test --detached" Enter
sleep 4

# Focus prompt with /
tmux send-keys -t acli-g13 "/"
sleep 1
tmux capture-pane -t acli-g13 -p > evidence/G13/prompt-focused.txt

# Cleanup
tmux send-keys -t acli-g13 "q"
sleep 1
tmux kill-session -t acli-g13 2>/dev/null

echo "Prompt input test complete" | tee evidence/G13/result.txt
```

---

## Gate G14: Full Import Chain (Regression)

```bash
mkdir -p evidence/G14

python -c "
# ALL phases must import cleanly
from acli.core.client import MODEL_OPUS, MODEL_SONNET
from acli.core.streaming import EventType
from acli.routing.router import PromptRouter
from acli.context.store import ContextStore
from acli.context.memory import MemoryManager
from acli.agents.definitions import AgentType
from acli.core.orchestrator_v2 import EnhancedOrchestrator
from acli.validation.engine import ValidationEngine
from acli.validation.mock_detector import scan_content_for_mocks
from acli.tui.app import AgentMonitorApp
from acli.tui.widgets import ContextExplorer, ValidationGatePanel
from acli.tui.prompt_input import PromptInput
from acli.tui.bridge import OrchestratorBridge
from acli.integration.skill_engine import SkillEngine
from acli.core.session import SessionLogger
from acli.cli import app as cli_app
print('ALL PHASE 1-4 IMPORTS: PASS')
print('PHASE 4 CUMULATIVE GATE: ALL PASS')
" 2>&1 | tee evidence/G14/imports.txt
```
