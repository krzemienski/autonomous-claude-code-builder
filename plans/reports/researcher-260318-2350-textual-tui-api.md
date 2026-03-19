# Textual Framework API Research
## ACLI v2 TUI Enhancements

**Date**: 2026-03-18
**Textual Version**: 7.0.0
**Research Scope**: Complete Widget API surface, CSS system, keybinding system, worker patterns, message system

---

## 1. Widget Base Class API

### Class Signature
```python
from textual.widget import Widget
from textual.app import ComposeResult

class CustomWidget(Widget):
    def __init__(
        self,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
    ) -> None:
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled, markup=markup)
```

### Required Methods

#### `compose()` → ComposeResult
- **Purpose**: Declare child widgets (for compound widgets)
- **Return type**: `ComposeResult` (generator/iterable of widgets)
- **Usage pattern**:
```python
def compose(self) -> ComposeResult:
    yield Static("Title")
    with Vertical(id="container"):
        yield RichLog(id="logs")
        yield Static("Footer")
```

#### `on_mount()` → None
- **Purpose**: Lifecycle hook called after widget mounts to DOM
- **Called when**: Widget appears in the widget tree
- **Usage**: Initialize UI state, start workers, attach callbacks
```python
def on_mount(self) -> None:
    """Called when the widget is mounted."""
    self.run_worker(self._background_task(), exclusive=True)
```

### Core Methods

#### `render()` → str | RenderableType
- Returns content for stateless widgets (called on every repaint)
- Alternative to `compose()` for simple widgets
- Example: `return "[#0abdc6]HELLO[/]"` (Rich markup)

#### `watch_<attribute>(value)` → None
- Reactive property watcher pattern
- Called when reactive attribute changes
```python
def watch_status(self, new_status: str) -> None:
    self.log(f"Status changed to: {new_status}")
```

#### `query_one(selector, expect_type=None)` → Widget
- Get single child widget by ID or class
- Raises `NoMatches` if not found
```python
from textual.css.query import NoMatches
try:
    log = self.query_one("#log-stream", RichLog)
except NoMatches:
    pass
```

#### `run_worker(coro, exclusive=False, name=None)` → Worker
- Schedule async background task
- `exclusive=True` cancels previous workers with same name
- Returns `Worker` object with lifecycle control
```python
async def _consume_events(self) -> None:
    """Background task."""
    while True:
        await asyncio.sleep(0.1)

self.run_worker(self._consume_events(), exclusive=True, name="events")
```

### Class Variables

#### `DEFAULT_CSS: str`
- Scoped stylesheet for this widget (auto-scoped)
```python
DEFAULT_CSS = """
MyWidget {
    height: 100%;
    width: 1fr;
    border: solid blue;
}
"""
```

#### `SCOPED_CSS: bool = True`
- Auto-scope CSS to this widget class (default: True)

#### `COMPONENT_CLASSES: set[str]`
- Declare CSS class names for sub-components
```python
COMPONENT_CLASSES = {"widget--title", "widget--content"}
```

---

## 2. App Class API

### Class Signature
```python
from textual.app import App

class AgentMonitorApp(App):
    CSS_PATH = "cyberpunk.tcss"  # External stylesheet
    TITLE = "ACLI Agent Monitor"
    SUB_TITLE = "Autonomous CodeGen"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("p", "toggle_pause", "Pause"),
        Binding("enter", "drill_into_agent", "Detail"),
    ]
```

### Required Methods

#### `compose()` → ComposeResult
```python
def compose(self) -> ComposeResult:
    yield CyberHeader()
    with Horizontal(id="main"):
        with Vertical(id="left"):
            yield AgentGraph()
        with Vertical(id="right"):
            yield LogStream()
    yield Footer()
```

#### `on_mount()` -> None
```python
def on_mount(self) -> None:
    """Initialize UI and start workers."""
    self.run_worker(self._consume_events(), exclusive=True, name="events")
    self.run_worker(self._refresh_loop(), exclusive=True, name="refresh")
```

### Key Methods

#### `query_one(selector, expect_type=None)` → Widget
```python
log_widget = self.query_one("#log-stream-widget", LogStream)
header = self.query_one(CyberHeader)  # By class
stats = self.query_one("[id*='stats']", Static)  # CSS selector
```

#### `notify(message, *, title="", severity="information", timeout=None)` → None
- Show toast notification
- `severity`: "information" | "warning" | "error"
```python
self.notify("Orchestrator PAUSED", severity="warning")
self.notify("Feature completed!", severity="information", timeout=5.0)
```

#### `run_worker(work, name="", exclusive=False, exit_on_error=True, thread=False)` → Worker
```python
worker = self.run_worker(
    self._poll_state(),
    exclusive=True,
    name="poller",
    exit_on_error=True
)
```

#### `action_*` methods
- Keybinding action handlers (prefix: `action_`)
- Called by Binding when key pressed
```python
def action_toggle_pause(self) -> None:
    """Action for 'p' keybinding."""
    self.notify("Paused")

def action_quit(self) -> None:
    """Action for 'q' keybinding."""
    self.exit()
```

### Class Variables

| Variable | Type | Purpose |
|----------|------|---------|
| `CSS_PATH` | str | Path to external `.tcss` stylesheet |
| `CSS` | str | Inline CSS (string) |
| `TITLE` | str | App title in header |
| `SUB_TITLE` | str | Subtitle in header |
| `BINDINGS` | list[Binding] | Keyboard shortcuts |

---

## 3. Binding Class API

### Class Signature
```python
from textual.binding import Binding

Binding(
    key: str,
    action: str,
    description: str = "",
    show: bool = True,
    key_display: str | None = None,
    priority: bool = False,
    tooltip: str = "",
)
```

### Parameters

| Parameter | Type | Purpose |
|-----------|------|---------|
| `key` | str | Key name or chord (see Key Names below) |
| `action` | str | Action method name (without `action_` prefix) |
| `description` | str | Human-readable label for footer bar |
| `show` | bool | Show in footer bar (default: True) |
| `key_display` | str | Custom display text for key in footer |
| `priority` | bool | Priority keybindings (capture before others) |
| `tooltip` | str | Hover tooltip text |

### Supported Key Names

**Single Keys**:
- `q`, `w`, `e`, `r`, `t`, `y`, `u`, `i`, `o`, `p`, `a`, `s`, `d`, `f`, `g`, `h`, `j`, `k`, `l`, `z`, `x`, `c`, `v`, `b`, `n`, `m`
- `0` - `9`
- `slash` (for `/`)
- `backslash` (for `\`)
- `comma`, `period`, `semicolon`, `colon`
- `at`, `hash`, `dollar`, `percent`

**Navigation Keys**:
- `enter`, `escape`, `tab`, `backspace`, `delete`, `home`, `end`
- `up`, `down`, `left`, `right`
- `pageup`, `pagedown`

**Function Keys**:
- `f1`, `f2`, `f3`, `f4`, `f5`, `f6`, `f7`, `f8`, `f9`, `f10`, `f11`, `f12`

**Modifiers** (combine with `+`):
- `ctrl+c`, `ctrl+z`, `shift+p`, `alt+e`
- `ctrl+shift+s` (triple modifier)

### Usage Examples

```python
BINDINGS = [
    Binding("q", "quit", "Quit", priority=True),
    Binding("j", "select_next_agent", "Next", show=False),
    Binding("k", "select_prev_agent", "Prev", show=False),
    Binding("enter", "drill_into_agent", "Detail"),
    Binding("f1", "filter_all", "All Logs"),
    Binding("slash", "search", "Search"),
    Binding("ctrl+c", "interrupt", "Interrupt"),
]
```

---

## 4. Container Classes

### Horizontal Container
```python
from textual.containers import Horizontal

with Horizontal(id="main-row", classes="panel"):
    yield Static("Left")
    yield Static("Right")
```

**Layout**: Children arranged left-to-right
**Properties**: Same as Widget + layout-specific CSS

### Vertical Container
```python
from textual.containers import Vertical

with Vertical(id="main-col"):
    yield Static("Top")
    yield Static("Bottom")
```

**Layout**: Children arranged top-to-bottom

### VerticalScroll Container
```python
from textual.containers import VerticalScroll

yield VerticalScroll(
    Static("Long content..."),
    id="scrollable"
)
```

**Layout**: Vertical with scrollbar support
**Properties**: Adds scroll-specific CSS (scrollbar-color, scrollbar-size, etc.)

### Grid Container
```python
from textual.containers import Grid

with Grid(id="data-grid"):
    yield Static("Cell 1")
    yield Static("Cell 2")
```

**CSS Layout**: CSS Grid (define in stylesheet with `grid-template-columns` etc.)

---

## 5. Static Widget API

### Class Signature
```python
from textual.widgets import Static

Static(
    content: str | RenderableType = "",
    *,
    expand: bool = False,
    shrink: bool = False,
    markup: bool = True,
    name: str | None = None,
    id: str | None = None,
    classes: str | None = None,
    disabled: bool = False,
)
```

### Key Methods

#### `update(content, *, layout=True)` → None
- Update displayed content
- `layout=True`: Re-trigger layout calculation
```python
static = self.query_one("#title", Static)
static.update("[#0abdc6]NEW TITLE[/]")
```

### Rich Markup Support
```python
# Color: [#RRGGBB]text[/]
Static("[#0abdc6]Cyan text[/]")

# Style: [bold]bold[/], [italic]italic[/], [underline]underline[/]
Static("[bold #ff003c]Red Bold[/]")

# Combinable
Static("[bold #00ff41]✓ Success[/]")
```

---

## 6. RichLog Widget API

### Class Signature
```python
from textual.widgets import RichLog

RichLog(
    *,
    max_lines: int | None = None,
    min_width: int = 78,
    wrap: bool = False,
    highlight: bool = False,
    markup: bool = False,
    auto_scroll: bool = True,
    name: str | None = None,
    id: str | None = None,
    classes: str | None = None,
    disabled: bool = False,
)
```

### Key Methods

#### `write(content, width=None, expand=False, shrink=True, scroll_end=None, animate=False)` → Self
- Add content to log (appends)
- Supports Rich renderables or strings
- Chainable (returns self)
```python
log = self.query_one("#log-stream", RichLog)

# Text with markup
log.write("[#0abdc6]INFO[/] Starting process")

# Rich renderables
from rich.console import Console
log.write(Console().render_str("[#ff003c]ERROR[/] Failed"))

# Chain calls
log.write("Line 1").write("Line 2").write("Line 3")
```

### Properties

| Property | Type | Purpose |
|----------|------|---------|
| `max_lines` | int | Max buffer size (None = unlimited) |
| `highlight` | bool | Syntax highlighting (default: False) |
| `markup` | bool | Enable Rich markup (default: False) |
| `auto_scroll` | bool | Auto-scroll to bottom (default: True) |
| `wrap` | bool | Word-wrap long lines (default: False) |

---

## 7. Input Widget API

### Class Signature
```python
from textual.widgets import Input

Input(
    value: str | None = None,
    placeholder: str = "",
    highlighter: Highlighter | None = None,
    password: bool = False,
    *,
    restrict: str | None = None,
    type: InputType = "text",  # "text" | "integer" | "number"
    max_length: int = 0,
    suggester: Suggester | None = None,
    validators: Validator | Iterable[Validator] | None = None,
    validate_on: Iterable[InputValidationOn] | None = None,
    valid_empty: bool = False,
    select_on_focus: bool = True,
    name: str | None = None,
    id: str | None = None,
    classes: str | None = None,
    disabled: bool = False,
    tooltip: RenderableType | None = None,
    compact: bool = False,
) -> None
```

### Key Properties (Reactive)

| Property | Type | Purpose |
|----------|------|---------|
| `value` | str | Current input text |
| `cursor_position` | int | Position of cursor |
| `selection` | tuple[int, int] | Selected text range |
| `placeholder` | str | Hint text when empty |
| `password` | bool | Obscure input (bullets) |
| `valid_empty` | bool | Allow empty valid values |

### Key Methods

#### `validate(value: str)` → ValidationResult
- Run validators against value
```python
result = input_widget.validate("user@example.com")
if result.is_valid:
    print("Valid!")
```

#### `insert_text_at_cursor(text)` → None
```python
input_widget.insert_text_at_cursor("prefix_")
```

#### `select_all()` → None
```python
input_widget.select_all()
```

#### `clear()` → None
```python
input_widget.clear()
```

### Events

| Event | Trigger | Handler |
|-------|---------|---------|
| `Changed` | Value modified | `on_input_changed(event)` |
| `Submitted` | Enter pressed | `on_input_submitted(event)` |
| `Blurred` | Focus lost | `on_input_blurred(event)` |

```python
def on_input_changed(self, event: Input.Changed) -> None:
    """Called when input value changes."""
    print(f"New value: {event.value}")

def on_input_submitted(self, event: Input.Submitted) -> None:
    """Called when user presses Enter."""
    self.process_input(event.value)
```

---

## 8. Reactive Properties API

### Syntax
```python
from textual.reactive import reactive

class MyWidget(Widget):
    count: int = reactive(0)
    status: str = reactive("idle")
    selected_id: str = reactive("")
```

### Parameters
```python
reactive(
    default: T | Callable[[], T],
    *,
    layout: bool = False,      # Trigger layout recalc
    repaint: bool = True,      # Trigger widget repaint
    init: bool = True,         # Call watcher on init
    always_update: bool = False,  # Update even if value same
    recompose: bool = False,   # Trigger compose() re-run
    bindings: bool = False,    # Update keybindings
    toggle_class: str | None = None,  # Toggle CSS class
)
```

### Watcher Pattern
```python
def watch_selected_id(self, new_id: str) -> None:
    """Called when selected_id changes."""
    self.refresh_detail()
```

### Computed Reactive
```python
class MyWidget(Widget):
    index: int = reactive(0)

    def compute_index(self) -> int:
        """Compute index from other state."""
        return self._internal_index

    # Watcher fires on computed changes
    def watch_index(self, new_index: int) -> None:
        self.log(f"Index now: {new_index}")
```

---

## 9. Worker System API

### `run_worker()` Signature
```python
App.run_worker(
    work: Coroutine[Any, Any, ResultType],
    name: str = "",
    group: str = "default",
    description: str = "",
    exit_on_error: bool = True,
    start: bool = True,
    exclusive: bool = False,
    thread: bool = False,
) -> Worker[ResultType]
```

### Parameters

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `work` | Coroutine | - | Async function to run |
| `exclusive` | bool | False | Cancel previous workers with same name |
| `name` | str | "" | Unique name for this worker |
| `exit_on_error` | bool | True | Exit app if worker raises exception |
| `thread` | bool | False | Run in thread pool (for sync code) |
| `start` | bool | True | Start immediately |

### Usage Examples

#### Exclusive Worker (Cancel Previous)
```python
# First call
self.run_worker(self._consume_events(), exclusive=True, name="events")

# Later: Previous worker auto-cancelled before starting this one
self.run_worker(self._consume_events(), exclusive=True, name="events")
```

#### Multiple Concurrent Workers
```python
self.run_worker(self._consume_events(), exclusive=True, name="events")
self.run_worker(self._poll_state(), exclusive=True, name="poller")
self.run_worker(self._refresh_loop(), exclusive=True, name="refresh")
```

#### Worker with Result
```python
async def _fetch_data(self) -> dict:
    await asyncio.sleep(1)
    return {"status": "complete"}

worker = self.run_worker(self._fetch_data(), name="fetch")
# Later: result = worker.result  (blocks until done)
```

---

## 10. CSS System

### Textual CSS (TCSS) Syntax
```css
/* Element selectors */
Widget {
    width: 100%;
    height: auto;
}

/* ID selectors */
#main-container {
    border: solid #0abdc6;
}

/* Class selectors */
.panel {
    background: #000b1e;
    padding: 1;
}

/* Pseudo-selectors */
Widget:focus {
    border: solid #ea00d9;
}

Widget:hover {
    background: #001a33;
}

/* Combined */
#left-panel > Vertical {
    width: 35%;
}
```

### Layout Properties
```css
/* Sizing */
width: 50% | 1fr | 20 | auto
height: 50% | 1fr | 5 | auto
min-width: 40
max-width: 80

/* Spacing */
padding: 1 | 1 2 | 0 1 2 3
margin: 1 | 1 2 | 0 1 2 3

/* Borders */
border: solid | heavy | double | [color]
border-top: solid #0abdc6
border-right: heavy #133e7c

/* Positioning */
offset: 0 2      /* x y */
dock: top | right | bottom | left

/* Background & Foreground */
background: #000b1e
color: #d7fffe
```

### Rich Text Colors (in Widgets)
```python
# Inline markup
Static("[#0abdc6]Cyan text[/]")
Static("[#ff003c bold]Bold red[/]")
Static("[on #000b1e #d7fffe]White on dark navy[/]")
```

### Scrollbar Styling
```css
* {
    scrollbar-size: 1 1;
    scrollbar-color: #133e7c;
    scrollbar-color-hover: #0abdc6;
    scrollbar-color-active: #ea00d9;
    scrollbar-background: #000b1e;
    scrollbar-background-hover: #001a33;
}
```

---

## 11. Message & Event System

### Custom Message Class
```python
from textual.message import Message

class MyWidget(Widget):
    class CustomEvent(Message):
        """Custom message from this widget."""
        def __init__(self, data: str):
            super().__init__()
            self.data = data
```

### Posting Messages
```python
# From child widget to parent
self.post_message(MyWidget.CustomEvent("hello"))

# Parent handles message
def on_my_widget_custom_event(self, event: MyWidget.CustomEvent) -> None:
    print(f"Received: {event.data}")
```

### Built-in Widget Events

#### Static Widget
```python
def on_static_mounted(self, event: Static.Mounted) -> None:
    """Called when static widget mounts."""
    pass
```

#### Input Widget
```python
def on_input_changed(self, event: Input.Changed) -> None:
    """Called when input value changes."""
    print(f"Value: {event.value}")

def on_input_submitted(self, event: Input.Submitted) -> None:
    """Called when user presses Enter."""
    self.process(event.value)

def on_input_blurred(self, event: Input.Blurred) -> None:
    """Called when focus leaves input."""
    pass
```

#### RichLog Widget
```python
def on_richlog_line_selected(self, event: RichLog.LineSelected) -> None:
    """Called when user clicks/selects a line."""
    print(f"Line: {event.line_index}")
```

---

## 12. Advanced Patterns from ACLI TUI

### Pattern 1: Bridge Pattern (Real Data Connection)
```python
class MyWidget(Widget):
    def __init__(self, bridge: OrchestratorBridge, **kwargs):
        super().__init__(**kwargs)
        self.bridge = bridge

    def on_mount(self) -> None:
        self.bridge.on_event(self._on_bridge_event)

    def _on_bridge_event(self, event: StreamEvent) -> None:
        # Handle real event from orchestrator
        self.refresh_display()
```

### Pattern 2: Refresh Loop
```python
def on_mount(self) -> None:
    self.run_worker(self._refresh_loop(), exclusive=True, name="refresh")

async def _refresh_loop(self) -> None:
    while not self._stop_event.is_set():
        self._refresh_all_widgets()
        await asyncio.sleep(0.25)  # 4 FPS

def _refresh_all_widgets(self) -> None:
    try:
        widget = self.query_one("#my-widget", MyWidget)
        widget.refresh_data()
    except NoMatches:
        pass
```

### Pattern 3: Reactive UI State
```python
class AgentGraph(Widget):
    selected_agent_id: reactive[str] = reactive("")

    def watch_selected_agent_id(self, new_id: str) -> None:
        """Called when selection changes."""
        self.refresh_graph()

    def refresh_graph(self) -> None:
        content = self.query_one("#graph-content", Static)
        content.update(self.render_graph())
```

### Pattern 4: Exclusive Workers
```python
def on_mount(self) -> None:
    # Only one active at a time per name
    self.run_worker(self._consume_events(), exclusive=True, name="events")
    self.run_worker(self._poll_state(), exclusive=True, name="poller")
    self.run_worker(self._refresh_loop(), exclusive=True, name="refresh")
```

---

## 13. Import Paths (Textual 7.0.0)

```python
# App & Widgets
from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import (
    Static,
    RichLog,
    Input,
    Button,
    Select,
    DataTable,
    Header,
    Footer,
    Label,
)

# Containers
from textual.containers import (
    Horizontal,
    Vertical,
    VerticalScroll,
    HorizontalScroll,
    Grid,
    ScrollableContainer,
)

# Bindings & Keybindings
from textual.binding import Binding

# Reactive Properties
from textual.reactive import reactive, var

# Events & Messages
from textual.message import Message
from textual.events import Key, Mount, Blur

# CSS Query
from textual.css.query import NoMatches, QueryType

# Styling
from textual.css.constants import SeverityLevel  # "information", "warning", "error"

# Workers
from textual.worker import Worker, WorkerState

# Input Validation
from textual.widgets._input import InputValidationOn  # "blur", "changed", "submitted"
```

---

## 14. Tmux Headless Execution

### Headless Textual with TERM=xterm-256color
```bash
# Set environment
export TEXTUAL=debug
export TERM=xterm-256color

# Run in tmux pane (headless, piped output)
tmux new-session -d -s acli-tui -x 180 -y 50 \
  "python -m acli monitor /path/to/project"

# Capture output
tmux capture-pane -t acli-tui -p > /tmp/tui-output.txt

# Send input
tmux send-keys -t acli-tui "q" Enter

# Kill session
tmux kill-session -t acli-tui
```

### Validation Testing Pattern
```bash
#!/bin/bash
# tests/functional/07-tui-validation.sh

# Start TUI in tmux
tmux new-session -d -s test-tui -x 180 -y 50 "python -m acli monitor ."

# Wait for startup
sleep 2

# Verify header rendered
tmux capture-pane -t test-tui -p | grep -q "ACLI AGENT MONITOR" || exit 1

# Send keybinding
tmux send-keys -t test-tui "j" Enter
sleep 1

# Verify state changed
tmux capture-pane -t test-tui -p | grep -q "Next Agent" || exit 1

# Cleanup
tmux kill-session -t test-tui
```

---

## 15. Key Findings for ACLI v2 Enhancements

### Strengths Verified in Current Implementation
1. **ComposeResult pattern**: Proper use of `yield` for widget hierarchy
2. **Exclusive workers**: Prevents duplicate runners, clean lifecycle
3. **Rich markup**: Full color/style support in Static/RichLog
4. **Binding system**: Complete keybinding + footer integration works well
5. **Reactive properties**: Selected state properly drives UI updates
6. **CSS scoping**: Custom cyberpunk.tcss loaded and applied correctly

### Enhancement Opportunities
1. **Input widget** integration: Add search/filter inputs (not currently in ACLI v1)
   - Use `Input(placeholder="Search logs...", id="search-input")`
   - Handle `on_input_changed` to filter RichLog output
   - Add `f` keybinding → focus input

2. **Grid layout** for agent table (alternative to ASCII graph)
   - Use `DataTable` widget for sortable agent list
   - React to agent selection state
   - More scalable for 100+ agents

3. **Custom Message system** for inter-widget communication
   - Define `AgentSelected(agent_id: str)` message
   - Reduce direct bridge coupling
   - Enables modular testing

4. **Footer context awareness**
   - Use app-level message dispatch
   - Show context-specific keybindings (F1-F4 only when viewing logs)
   - Implement with `Footer.get_key_display()` override

5. **Modal dialogs** for confirmation/input
   - Use `ScreenStack` API (not covered in this research)
   - Suspend/resume main app flow
   - Research separate doc needed

---

## Unresolved Questions

1. **How to implement ScreenStack for modal dialogs?** (requires additional research on `textual.screen` module)
2. **Can RichLog be filtered/searched in-place without re-rendering?** (performance optimization for 10K+ lines)
3. **What's the best pattern for persistent tmux session communication?** (FIFO pipes vs. file polling vs. socket)
4. **How to implement drag-drop in Textual TUI?** (mouse event details needed)
5. **Can worker output be captured and displayed differently based on severity?** (worker message filtering)

---

**Report Generated**: 2026-03-18 23:50
**Total API Methods Documented**: 45+
**Widget Classes Covered**: 8 (Static, RichLog, Input, App, Widget, Containers x3)
**Example Patterns**: 12 (from ACLI codebase analysis)
