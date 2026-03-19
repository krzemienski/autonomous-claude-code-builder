# Textual TUI API Research Summary
## Quick Reference for ACLI v2 Implementation

**Installed Version**: Textual 7.0.0
**Report Location**: `researcher-260318-2350-textual-tui-api.md` (970 lines)

---

## Core API Signatures (Copy-Paste Ready)

### 1. Widget Base Class
```python
from textual.widget import Widget
from textual.app import ComposeResult

class MyWidget(Widget):
    def __init__(self, *children, name=None, id=None, classes=None, disabled=False, markup=True):
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled, markup=markup)

    def compose(self) -> ComposeResult:
        yield ChildWidget()

    def on_mount(self) -> None:
        """Lifecycle: called after widget mounts to DOM."""
        pass
```

### 2. App Class
```python
from textual.app import App
from textual.binding import Binding

class MyApp(App):
    CSS_PATH = "styles.tcss"
    TITLE = "My App"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("f1", "filter_all", "All", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Static("Left")
            yield Static("Right")
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._background_task(), exclusive=True, name="bg")

    def action_quit(self) -> None:
        self.exit()

    async def _background_task(self):
        while True:
            await asyncio.sleep(1)
```

### 3. Static Widget (Content Display)
```python
from textual.widgets import Static

widget = Static(
    "[#0abdc6]Colored Text[/]",
    id="my-static",
    expand=False,
    markup=True
)

# Update content
widget.update("[#ff003c]New Content[/]")
```

### 4. RichLog Widget (Scrolling Log)
```python
from textual.widgets import RichLog

log = RichLog(
    max_lines=1000,
    wrap=True,
    highlight=False,
    markup=True,
    auto_scroll=True,
    id="log-stream"
)

# Write lines (chainable)
log.write("[#0abdc6]INFO[/] Starting").write("[#ff003c]ERROR[/] Failed")
```

### 5. Input Widget (Text Entry)
```python
from textual.widgets import Input

input_field = Input(
    placeholder="Search...",
    value="",
    password=False,
    id="search-input"
)

# Events
def on_input_changed(self, event: Input.Changed):
    print(f"Value: {event.value}")

def on_input_submitted(self, event: Input.Submitted):
    self.process(event.value)
```

### 6. Binding Keys (for BINDINGS list)
```python
# Single keys
Binding("q", "action", "Description")
Binding("j", "next", "Next")
Binding("slash", "search", "Search")

# Function keys
Binding("f1", "filter_all", "All")
Binding("f12", "debug", "Debug")

# Navigation
Binding("enter", "confirm", "Confirm")
Binding("escape", "cancel", "Cancel")
Binding("tab", "focus_next", "Focus Next")

# Modifiers
Binding("ctrl+c", "interrupt", "Interrupt")
Binding("ctrl+shift+s", "save", "Save")
Binding("alt+e", "edit", "Edit")
```

### 7. Containers (Layout)
```python
from textual.containers import Horizontal, Vertical, VerticalScroll

# Horizontal layout
with Horizontal(id="row"):
    yield Static("Left")
    yield Static("Right")

# Vertical layout
with Vertical(id="col"):
    yield Static("Top")
    yield Static("Bottom")

# Scrollable vertical
with VerticalScroll(id="scrollable"):
    yield Static("Long content...\n" * 100)
```

### 8. Reactive Properties
```python
from textual.reactive import reactive

class MyWidget(Widget):
    selected_id: str = reactive("")
    count: int = reactive(0, init=False)

    def watch_selected_id(self, new_id: str) -> None:
        """Auto-called when selected_id changes."""
        self.log(f"Selected: {new_id}")
        self.refresh()
```

### 9. Workers (Background Tasks)
```python
# In on_mount() or action method
self.run_worker(
    self._background_task(),
    exclusive=True,  # Cancel previous worker with same name
    name="bg_task",
    exit_on_error=True
)

async def _background_task(self):
    while True:
        # Do work
        await asyncio.sleep(0.25)
        # Update UI
        self.refresh_display()
```

### 10. Query & Update Pattern
```python
from textual.css.query import NoMatches

try:
    widget = self.query_one("#my-id", StaticType)
    widget.update("new content")
except NoMatches:
    pass
```

---

## Common Patterns from ACLI v1

### Pattern 1: Bridge Connection (Real Data)
```python
class MyWidget(Widget):
    def __init__(self, bridge: OrchestratorBridge, **kwargs):
        super().__init__(**kwargs)
        self.bridge = bridge

    def on_mount(self) -> None:
        self.bridge.on_event(self._on_event)

    def _on_event(self, event: StreamEvent) -> None:
        self.refresh_display()
```

### Pattern 2: Refresh Loop
```python
def on_mount(self) -> None:
    self.run_worker(self._refresh_loop(), exclusive=True, name="refresh")

async def _refresh_loop(self) -> None:
    while not self._stop_event.is_set():
        self._refresh_all()
        await asyncio.sleep(0.25)  # 4 FPS

def _refresh_all(self) -> None:
    try:
        graph = self.query_one("#graph", AgentGraph)
        graph.refresh()
    except NoMatches:
        pass
```

### Pattern 3: Notification
```python
# Show toast notification
self.notify("Operation complete!", severity="information", timeout=3.0)
self.notify("Error occurred!", severity="error")
self.notify("Warning!", severity="warning")
```

---

## CSS Syntax (Textual CSS / TCSS)

```css
/* Element selector */
MyWidget {
    width: 50%;
    height: 1fr;
    border: solid #0abdc6;
    background: #000b1e;
    color: #d7fffe;
    padding: 1;
}

/* ID selector */
#main-container {
    width: 100%;
}

/* Class selector */
.panel {
    background: #001a33;
    border: heavy #133e7c;
}

/* Pseudo-selectors */
MyWidget:focus {
    border: solid #ea00d9;
}

MyWidget:hover {
    background: #012f3f;
}

/* Combination */
#left-panel > Vertical {
    width: 35%;
    border-right: heavy #133e7c;
}

/* Responsive sizing */
width: 100%          /* Percentage of parent */
width: 1fr           /* Fractional unit (flex-like) */
width: 30            /* Fixed character width */
width: auto          /* Content-based */

height: 50%
height: 1fr
height: 10
height: auto

/* Scrollbars */
scrollbar-size: 1 1
scrollbar-color: #133e7c
scrollbar-color-hover: #0abdc6
scrollbar-color-active: #ea00d9
```

---

## Rich Markup (in Static, RichLog, etc.)

```python
# Colors: [#RRGGBB]text[/]
"[#0abdc6]Cyan text[/]"
"[#ff003c]Red text[/]"
"[#00ff41]Green text[/]"

# Styles
"[bold]Bold[/]"
"[italic]Italic[/]"
"[underline]Underline[/]"

# Combined
"[bold #ff003c]Bold red[/]"
"[underline #0abdc6]Cyan underline[/]"

# Background
"[on #000b1e #d7fffe]White on dark navy[/]"

# Icons
"✓ Success"
"✗ Error"
"◆ Running"
"◇ Idle"
```

---

## Import Statements (Copy-Paste)

```python
# Core
from textual.app import App, ComposeResult
from textual.widget import Widget

# Widgets
from textual.widgets import (
    Static,
    RichLog,
    Input,
    Header,
    Footer,
    Button,
    Select,
    Label,
)

# Containers
from textual.containers import (
    Horizontal,
    Vertical,
    VerticalScroll,
    Grid,
)

# Keybindings
from textual.binding import Binding

# Reactive
from textual.reactive import reactive

# Query
from textual.css.query import NoMatches

# Events
from textual.message import Message
```

---

## Keybinding Names Reference

**Alphabet**: `a` - `z`
**Numbers**: `0` - `9`
**Symbols**: `slash`, `backslash`, `comma`, `period`, `semicolon`, `colon`, `at`, `hash`, `dollar`
**Navigation**: `up`, `down`, `left`, `right`, `home`, `end`, `pageup`, `pagedown`
**Special**: `enter`, `escape`, `tab`, `backspace`, `delete`, `insert`
**Function**: `f1` - `f12`
**Modifiers**: `ctrl+`, `shift+`, `alt+`, `ctrl+shift+`

**Examples**:
- `"q"` → Quit
- `"j"` → Down
- `"k"` → Up
- `"slash"` → Forward slash (/)
- `"f1"` - `"f4"` → Function keys
- `"ctrl+c"` → Ctrl+C
- `"ctrl+shift+s"` → Ctrl+Shift+S

---

## Worker Lifecycle

```python
# In on_mount()
worker = self.run_worker(
    self._task(),
    exclusive=True,      # Cancel previous workers named "bg"
    name="bg",
    exit_on_error=True   # Exit app if exception raised
)

# Worker states
# PENDING → RUNNING → SUCCESS (or ERROR or CANCELLED)

async def _task(self):
    try:
        result = await self.do_work()
        return result
    except Exception as e:
        # Logged and handled by framework
        raise

# Query worker state
if worker.is_finished():
    result = worker.result
```

---

## Key Learnings for v2

1. **Exclusive workers**: Set for all background tasks to prevent duplicates
2. **ComposeResult**: Use `yield` syntax for clean widget hierarchy
3. **Rich markup**: Supports colors, styles, inline in string literals
4. **CSS scoping**: TCSS automatically scoped to widget class
5. **Keybindings**: Footer auto-populated from BINDINGS list
6. **Query pattern**: Always wrap in try/except NoMatches
7. **Reactive watches**: Auto-called when reactive property changes
8. **Static.update()**: Layout=True triggers full recalc if needed
9. **RichLog.write()**: Chainable, auto-scrolls if enabled
10. **on_mount()**: Optimal place to start workers and initialize state

---

## Next Steps for Implementation

1. **Search/Filter feature**: Use Input widget + on_input_changed handler
2. **Sortable agent table**: Replace ASCII graph with DataTable widget
3. **Modal dialogs**: Research textual.screen.ScreenStack API separately
4. **Inter-widget messaging**: Implement custom Message classes
5. **Performance**: Profile RichLog with 10K+ lines (may need pagination)

---

**Report**: `/Users/nick/Desktop/claude-code-builder-agents-sdk/plans/reports/researcher-260318-2350-textual-tui-api.md`
**Full Doc**: 970 lines, 15 sections, 45+ API methods covered
**Generated**: 2026-03-18 23:50
