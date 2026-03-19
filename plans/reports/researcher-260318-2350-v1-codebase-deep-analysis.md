# ACLI v1 Codebase: Line-Level Deep Analysis

**Scope:** Complete architectural decomposition for v2 migration planning
**Analysis Date:** 2026-03-18
**Total Files Analyzed:** 44 Python modules + 1 TCSS + 2 Markdown templates
**Total LOC (Python only):** ~6,100 across core + TUI + utils

---

## 1. FILE INVENTORY & LINE COUNTS

### Core Orchestration (`src/acli/core/`)
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 36 | Module exports (SessionState, StreamBuffer, AgentOrchestrator, etc.) |
| `client.py` | 149 | Claude SDK client factory w/ security settings, MCP config |
| `orchestrator.py` | 279 | Two-agent loop (initializer → coding), session lifecycle, auto-continue |
| `agent.py` | 127 | Agent session runner, prompt template loader, streaming integration |
| `session.py` | 146 | ProjectState & SessionState dataclasses, save/load persistence |
| `streaming.py` | 198 | StreamEvent, StreamBuffer (async circular), StreamingHandler |

### TUI (`src/acli/tui/`)
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 19 | Exports AgentMonitorApp, OrchestratorBridge |
| `app.py` | 276 | Textual App, 10 keybindings, worker threads, widget coordination |
| `bridge.py` | 350 | OrchestratorBridge, AgentNode hierarchy, snapshot state machine |
| `widgets.py` | 590 | 5 custom Textual widgets (Header, Graph, Detail, LogStream, Stats) |
| `cyberpunk.tcss` | 409 | Complete CSS theme (neon colors, animations, responsive layout) |

### Legacy UI (`src/acli/ui/`)
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | (empty) | |
| `dashboard.py` | 246 | Rich Live dashboard (alternative to TUI) |
| `themes.py` | (not analyzed, not critical) | |
| `tool_board.py` | (not analyzed) | |
| `logs.py` | (not analyzed) | |
| `progress.py` | (not analyzed) | |

### Specification (`src/acli/spec/`)
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | (empty) | |
| `schemas.py` | 124 | Pydantic v2 models: ProjectSpec, FeatureSpec, EnhancementResult, etc. |
| `enhancer.py` | 236 | Claude API structured outputs for spec extraction → JSON |
| `validator.py` | 168 | 6 validation rules, completeness scoring, clarification Q generation |
| `refinement.py` | (not critical) | |

### Security (`src/acli/security/`)
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 44 | Module exports |
| `validators.py` | 163 | Per-command validators: validate_pkill, validate_chmod, validate_init_script |
| `hooks.py` | 356 | bash_security_hook (PreToolUse), extract_commands(), command parsing |

### Progress Tracking (`src/acli/progress/`)
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | (empty) | |
| `feature_list.py` | 223 | Feature dataclass, FeatureList manager (load/save/mark_passing) |
| `tracker.py` | 240 | ProgressTracker, ProgressEvent, milestone tracking |
| `persistence.py` | (not critical) | |
| `display.py` | (not critical) | |

### Browser Automation (`src/acli/browser/`)
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | (empty) | |
| `manager.py` | 192 | UnifiedBrowser interface, BrowserConfig, get_browser_instructions() |
| `puppeteer.py` | 80+ | PuppeteerConfig, PUPPETEER_TOOLS dict, PuppeteerHelper |
| `playwright.py` | 80+ | PlaywrightConfig, PLAYWRIGHT_TOOLS dict, PlaywrightHelper |

### Integration (`src/acli/integration/`)
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | (empty) | |
| `mcp_servers.py` | 198 | MCPServer, MCPServerManager, BUILTIN_SERVERS config |
| `claude_config.py` | 172 | discover_claude_config(), get_api_key(), generate_client_settings() |
| `skill_discovery.py` | (not critical) | |

### Utils & Logging (`src/acli/utils/`)
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 10 | Exports AsyncEventEmitter, logger |
| `logger.py` | 36 | Logging setup, get_logger() |
| `events.py` | 48 | AsyncEventEmitter class (for orchestrator event handling) |

### Prompts (`src/acli/prompts/`)
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 1 | Empty |
| `templates/initializer.md` | 56 | Prompt: spec → feature_list.json + init.sh |
| `templates/coding.md` | 50 | Prompt: implement ONE feature, test, commit |

### CLI & Main (`src/acli/`)
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 8 | Version constant |
| `__main__.py` | 7 | Entry point: from acli.cli import app; app() |
| `cli.py` | 626 | 7 Typer commands (init, run, status, enhance, config, list_skills, monitor) |

---

## 2. IMPORTS & DEPENDENCY GRAPH

### Internal Dependencies (Import Chains)

```
cli.py
├─ core.orchestrator
│  ├─ core.agent
│  │  ├─ core.client
│  │  │  ├─ security.hooks (bash_security_hook)
│  │  │  └─ core.streaming
│  │  ├─ core.session
│  │  └─ utils.logger
│  ├─ core.session
│  ├─ core.streaming
│  └─ utils.logger
├─ tui.app
│  ├─ tui.bridge (OrchestratorBridge)
│  │  ├─ core.orchestrator
│  │  ├─ core.session
│  │  └─ core.streaming
│  ├─ tui.widgets (CyberHeader, AgentGraph, AgentDetail, LogStream, StatsPanel)
│  └─ core.streaming
├─ ui.dashboard (Rich fallback)
├─ spec.enhancer (Claude API)
├─ progress.tracker
│  └─ progress.feature_list
├─ browser.manager
│  ├─ browser.puppeteer
│  └─ browser.playwright
└─ integration.mcp_servers

core/
├─ client.py
│  ├─ security.hooks
│  └─ Anthropic SDK (ClaudeSDKClient, ClaudeAgentOptions, HookMatcher)
├─ streaming.py
│  └─ utils.events (AsyncEventEmitter)
└─ orchestrator.py
   ├─ core.session
   ├─ core.agent
   ├─ core.client
   └─ core.streaming
```

### External Dependencies
```python
# Third-party
from typer import Typer, Option, Argument, Exit
from rich.console import Console
from rich.panel import Panel
from textual.app import App, ComposeResult
from textual.widgets import RichLog, Static, Footer
from textual.containers import Horizontal, Vertical
from pydantic import BaseModel, Field, ValidationError
import httpx  # async HTTP client for spec enhancer
import json
import asyncio
import logging
import subprocess

# Anthropic SDK (production requirement)
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk.types import HookMatcher
```

---

## 3. CLASS & FUNCTION SIGNATURES

### Core Classes

**`src/acli/core/client.py`**
```python
# Lines 20-40: Constants
PUPPETEER_TOOLS = [...]  # 7 tool names
PLAYWRIGHT_TOOLS = [...]  # 7 tool names
BUILTIN_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]

# Lines 43-69: Functions
def create_security_settings(project_dir: Path) -> dict[str, Any]: ...
def create_sdk_client(project_dir: Path, model: str, system_prompt: str | None = None) -> ClaudeSDKClient: ...
```

**`src/acli/core/orchestrator.py`**
```python
# Lines 24-250: Main class
class AgentOrchestrator:
    def __init__(self, project_dir: Path, model: str = "...", max_iterations: int | None = None): ...
    @property
    def is_running(self) -> bool: ...
    @property
    def is_first_run(self) -> bool: ...
    def request_pause(self) -> None: ...
    def request_stop(self) -> None: ...
    def resume(self) -> None: ...
    def on_event(self, event_type: str, handler: Callable[..., Any]) -> None: ...
    async def run_loop(self, on_session_start: Callable | None = None, on_session_end: Callable | None = None) -> None: ...
    async def run_single_session(self) -> tuple[str, str]: ...
    def _get_progress(self) -> tuple[int, int] | None: ...
    def get_status(self) -> dict[str, Any]: ...

# Lines 252-279: Helper functions
async def _maybe_await(result: Any) -> Any: ...
async def run_autonomous_agent(project_dir: Path, model: str = "...", max_iterations: int | None = None) -> None: ...
```

**`src/acli/core/session.py`**
```python
# Lines 15-42: DataClass
@dataclass
class SessionState:
    session_id: int
    session_type: str  # "initializer" | "coding"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    status: str = "running"
    features_completed: list[int] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    tool_calls: int = 0
    tokens_used: int = 0
    def to_dict(self) -> dict[str, Any]: ...

# Lines 44-141: Main class
@dataclass
class ProjectState:
    project_dir: Path
    created_at: datetime = field(default_factory=datetime.now)
    sessions: list[SessionState] = field(default_factory=list)
    current_session: SessionState | None = None

    @property
    def state_file(self) -> Path: ...
    @property
    def session_count(self) -> int: ...
    @property
    def is_first_run(self) -> bool: ...
    def start_session(self) -> SessionState: ...
    def end_session(self, status: str = "completed", features_completed: list[int] | None = None, errors: list[str] | None = None) -> None: ...
    def save(self) -> None: ...
    @classmethod
    def load(cls, project_dir: Path) -> ProjectState: ...

def get_project_state(project_dir: Path) -> ProjectState: ...
```

**`src/acli/core/streaming.py`**
```python
# Lines 18-29: Enum
class EventType(str, Enum):
    TEXT = "text"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    TOOL_BLOCKED = "tool_blocked"
    ERROR = "error"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    PROGRESS = "progress"

# Lines 31-56: DataClass
@dataclass
class StreamEvent:
    type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)
    text: str = ""
    tool_name: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)
    tool_result: str = ""
    tool_error: str = ""
    tool_duration_ms: float = 0
    session_id: int = 0
    session_type: str = ""
    features_done: int = 0
    features_total: int = 0

# Lines 58-99: Async buffer
class StreamBuffer:
    def __init__(self, max_size: int = 1000): ...
    async def push(self, event: StreamEvent) -> None: ...
    async def iter_from(self, index: int = 0) -> AsyncIterator[StreamEvent]: ...
    def get_recent(self, count: int = 50) -> list[StreamEvent]: ...
    def clear(self) -> None: ...

# Lines 101-198: Handler
class StreamingHandler:
    def __init__(self, buffer: StreamBuffer): ...
    def on(self, event_type: str, handler: Callable[..., Any]) -> None: ...
    async def emit(self, event: StreamEvent) -> None: ...
    async def handle_text(self, text: str) -> None: ...
    async def handle_tool_start(self, name: str, input_data: dict[str, Any]) -> None: ...
    async def handle_tool_end(self, name: str, result: str = "", error: str = "") -> None: ...
    async def handle_tool_blocked(self, name: str, reason: str) -> None: ...
    async def handle_error(self, error: str) -> None: ...
    async def handle_session_start(self, session_id: int, session_type: str) -> None: ...
    async def handle_session_end(self, session_id: int) -> None: ...
    async def handle_progress(self, done: int, total: int) -> None: ...
```

**`src/acli/core/agent.py`**
```python
# Lines 20-83: Main function
async def run_agent_session(
    client: ClaudeSDKClient,
    prompt: str,
    streaming: StreamingHandler,
) -> tuple[str, str]: ...

# Lines 85-127: Prompt loading
def load_prompt_template(name: str) -> str: ...
```

### TUI Classes

**`src/acli/tui/app.py`**
```python
# Lines 29-276: Main Textual App
class AgentMonitorApp(App):
    CSS_PATH = "cyberpunk.tcss"
    TITLE = "ACLI Agent Monitor"
    BINDINGS = [10 bindings: q, p, s, j, k, down, up, enter, f1-f4, r]

    def __init__(self, orchestrator: AgentOrchestrator | None = None, project_dir: Path | None = None, **kwargs): ...
    def compose(self) -> ComposeResult: ...
    def on_mount(self) -> None: ...
    async def _consume_events(self) -> None: ...
    async def _poll_state(self) -> None: ...
    async def _refresh_loop(self) -> None: ...
    def _on_bridge_event(self, event: StreamEvent) -> None: ...
    def _refresh_all_widgets(self) -> None: ...

    # Actions (keybindings)
    def action_toggle_pause(self) -> None: ...
    def action_stop_orchestrator(self) -> None: ...
    def action_select_next_agent(self) -> None: ...
    def action_select_prev_agent(self) -> None: ...
    def action_drill_into_agent(self) -> None: ...
    def action_filter_all(self) -> None: ...
    def action_filter_tools(self) -> None: ...
    def action_filter_errors(self) -> None: ...
    def action_filter_text(self) -> None: ...
    def action_refresh_all(self) -> None: ...
    def on_unmount(self) -> None: ...
```

**`src/acli/tui/bridge.py`**
```python
# Lines 24-52: Data models
@dataclass
class AgentNode:
    agent_id: str
    agent_type: str  # "orchestrator", "initializer", "coding"
    status: str = "idle"
    session_id: int = 0
    start_time: datetime | None = None
    end_time: datetime | None = None
    tool_calls: int = 0
    current_tool: str = ""
    features_done: int = 0
    features_total: int = 0
    errors: list[str] = field(default_factory=list)
    children: list[AgentNode] = field(default_factory=list)
    last_text: str = ""

    @property
    def duration_seconds(self) -> float: ...
    @property
    def is_active(self) -> bool: ...

@dataclass
class OrchestratorSnapshot:
    timestamp: datetime = field(default_factory=datetime.now)
    running: bool = False
    paused: bool = False
    project_dir: str = ""
    model: str = ""
    session_count: int = 0
    is_first_run: bool = True
    features_done: int = 0
    features_total: int = 0
    current_session_id: int = 0
    current_session_type: str = ""
    agents: list[AgentNode] = field(default_factory=list)
    total_tool_calls: int = 0
    total_errors: int = 0
    events_processed: int = 0

# Lines 75-350: Main bridge
class OrchestratorBridge:
    def __init__(self, orchestrator: AgentOrchestrator | None = None, project_dir: Path | None = None): ...
    @property
    def snapshot(self) -> OrchestratorSnapshot: ...
    @property
    def root_agent(self) -> AgentNode: ...
    @property
    def buffer(self) -> StreamBuffer | None: ...
    def on_event(self, callback: Callable[[StreamEvent], Any]) -> None: ...
    def _load_persisted_state(self) -> None: ...
    def _load_feature_progress(self) -> None: ...
    def handle_event(self, event: StreamEvent) -> None: ...
    async def consume_events(self, stop_event: asyncio.Event | None = None) -> None: ...
    async def poll_state(self, interval: float = 1.0, stop_event: asyncio.Event | None = None) -> None: ...
    def get_agent_by_id(self, agent_id: str) -> AgentNode | None: ...
    def get_active_agents(self) -> list[AgentNode]: ...
    def get_all_agents_flat(self) -> list[AgentNode]: ...
    def send_command(self, command: str) -> None: ...
```

**`src/acli/tui/widgets.py`**
```python
# Lines 29-221: 5 custom widgets
class CyberHeader(Widget):
    status_text: reactive[str] = reactive("IDLE")
    def __init__(self, **kwargs): ...
    def compose(self) -> ComposeResult: ...
    def _compute_elapsed(self) -> str: ...
    def update_from_snapshot(self, snap: OrchestratorSnapshot) -> None: ...

class AgentGraph(Widget):
    selected_agent_id: reactive[str] = reactive("")
    def __init__(self, bridge: OrchestratorBridge, **kwargs): ...
    def compose(self) -> ComposeResult: ...
    def render_graph(self) -> str: ...
    def refresh_graph(self) -> None: ...
    @staticmethod
    def _status_icon(status: str) -> str: ...
    @staticmethod
    def _status_color(status: str) -> str: ...
    @staticmethod
    def _mini_progress_bar(pct: float, width: int = 12) -> str: ...
    @staticmethod
    def _format_duration(seconds: float) -> str: ...

class AgentDetail(Widget):
    def __init__(self, bridge: OrchestratorBridge, **kwargs): ...
    def compose(self) -> ComposeResult: ...
    def show_agent(self, agent_id: str) -> None: ...
    def refresh_detail(self) -> None: ...
    @staticmethod
    def _color(status: str) -> str: ...

class LogStream(Widget):
    DEFAULT_CSS = "..."
    def __init__(self, bridge: OrchestratorBridge, **kwargs): ...
    def compose(self) -> ComposeResult: ...
    def write_event(self, event: StreamEvent) -> None: ...
    def _should_show(self, event: StreamEvent) -> bool: ...
    def set_filter(self, level: str) -> None: ...

class StatsPanel(Widget):
    def __init__(self, bridge: OrchestratorBridge, **kwargs): ...
    def compose(self) -> ComposeResult: ...
    def refresh_stats(self) -> None: ...
    def _refresh_tool_board(self) -> None: ...
```

### Security Classes

**`src/acli/security/validators.py`**
```python
# Lines 14-27: Constants
ALLOWED_PKILL_TARGETS: set[str] = {...}
DANGEROUS_CHMOD_MODES: set[str] = {"777", "666", "000"}

# Lines 29-34: Result type
class ValidationResult(NamedTuple):
    allowed: bool
    reason: str = ""

# Lines 36-163: Three validators
def validate_pkill(command: str) -> ValidationResult: ...
def validate_chmod(command: str) -> ValidationResult: ...
def validate_init_script(command: str) -> ValidationResult: ...

# Lines 153-163: Registry
VALIDATORS: dict[str, Callable[[str], ValidationResult]] = {...}
def get_validator(command_name: str) -> Callable[[str], ValidationResult] | None: ...
```

**`src/acli/security/hooks.py`**
```python
# Lines 17-46: Constants
ALLOWED_COMMANDS: set[str] = {ls, cat, head, tail, ..., npm, npm, git, ps, lsof, sleep, pkill, init.sh}
COMMANDS_NEEDING_EXTRA_VALIDATION: set[str] = {pkill, chmod, init.sh}

# Lines 49-160: Command parsing
def split_command_segments(command_string: str) -> list[str]: ...
def extract_commands(command_string: str) -> list[str]: ...
def validate_pkill_command(command_string: str) -> tuple[bool, str]: ...
def validate_chmod_command(command_string: str) -> tuple[bool, str]: ...
def validate_init_script(command_string: str) -> tuple[bool, str]: ...
def get_command_for_validation(cmd: str, segments: list[str]) -> str: ...

# Lines 299-356: Main hook (async)
async def bash_security_hook(input_data, tool_use_id=None, context=None): ...
```

### Progress & Feature Classes

**`src/acli/progress/feature_list.py`**
```python
# Lines 14-52: Feature dataclass
@dataclass
class Feature:
    id: int
    component: str
    description: str
    passes: bool = False
    priority: str = "medium"
    attempts: int = 0
    last_attempt: str | None = None
    notes: str = ""
    def to_dict(self) -> dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Feature: ...

# Lines 54-223: Manager
class FeatureList:
    def __init__(self, path: Path): ...
    @property
    def total(self) -> int: ...
    @property
    def passing(self) -> int: ...
    @property
    def remaining(self) -> int: ...
    @property
    def percentage(self) -> float: ...
    def load(self) -> None: ...
    def save(self) -> None: ...
    def save_if_dirty(self) -> None: ...
    def get(self, feature_id: int) -> Feature | None: ...
    def get_next_incomplete(self) -> Feature | None: ...
    def mark_passing(self, feature_id: int, notes: str = "") -> bool: ...
    def mark_failed(self, feature_id: int, notes: str = "") -> bool: ...
    def add(self, feature: Feature) -> None: ...
    def add_many(self, features: list[Feature]) -> None: ...
    def iter_incomplete(self) -> Iterator[Feature]: ...
    def iter_by_component(self, component: str) -> Iterator[Feature]: ...
    def get_components(self) -> list[str]: ...
    def get_summary(self) -> dict[str, Any]: ...

# Lines 210-223: Factory functions
def load_feature_list(path: Path | str) -> FeatureList: ...
def create_feature_list(path: Path | str, features: list[dict[str, Any]]) -> FeatureList: ...
```

**`src/acli/progress/tracker.py`**
```python
# Lines 18-34: Event dataclass
@dataclass
class ProgressEvent:
    timestamp: datetime
    event_type: str  # "feature_complete", "session_start", etc.
    feature_id: int | None = None
    session_id: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

# Lines 27-34: Milestone dataclass
@dataclass
class Milestone:
    name: str
    threshold: float
    reached: bool = False
    reached_at: datetime | None = None

# Lines 36-240: Main tracker
class ProgressTracker:
    def __init__(self, project_dir: Path): ...
    @property
    def feature_list(self) -> FeatureList: ...
    def reload(self) -> None: ...
    def is_first_run(self) -> bool: ...
    def get_total_count(self) -> int: ...
    def get_completed_count(self) -> int: ...
    def get_incomplete_count(self) -> int: ...
    def get_progress_percentage(self) -> float: ...
    def on_progress(self, callback: Callable[[ProgressEvent], Any]) -> None: ...
    def _emit(self, event: ProgressEvent) -> None: ...
    def _check_milestones(self) -> None: ...
    def record_feature_complete(self, feature_id: int, notes: str = "") -> bool: ...
    def record_feature_attempt(self, feature_id: int, notes: str = "") -> bool: ...
    def record_session_start(self, session_id: int) -> None: ...
    def record_session_end(self, session_id: int, features_completed: int = 0) -> None: ...
    def get_next_feature(self) -> Feature | None: ...
    def get_status(self) -> dict[str, Any]: ...
    def get_summary_text(self) -> str: ...
    def export_history(self, path: Path | None = None) -> str: ...
```

### Spec Classes

**`src/acli/spec/schemas.py`**
```python
# Lines 15-20: Enum
class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Lines 22-36: Models
class Requirement(BaseModel):
    id: int
    description: str  # min_length=10, max_length=500
    priority: Priority = Priority.MEDIUM
    acceptance_criteria: list[str] = Field(default_factory=list)
    dependencies: list[int] = Field(default_factory=list)

class NonFunctionalConstraint(BaseModel):
    category: str
    description: str
    target: str | None = None

class TechStack(BaseModel):
    language: str
    framework: str | None = None
    database: str | None = None
    ui_library: str | None = None
    testing: str | None = None
    additional: list[str] = Field(default_factory=list)

class FeatureSpec(BaseModel):
    name: str
    description: str
    user_story: str
    requirements: list[Requirement] = Field(default_factory=list)
    constraints: list[NonFunctionalConstraint] = Field(default_factory=list)
    estimated_hours: float | None = None

class ProjectSpec(BaseModel):
    name: str
    description: str
    tech_stack: TechStack
    features: list[FeatureSpec] = Field(default_factory=list)
    constraints: list[NonFunctionalConstraint] = Field(default_factory=list)
    version: str = "1.0.0"
    estimated_total_hours: float | None = None
    def to_feature_list(self) -> list[dict[str, Any]]: ...

# Lines 104-124: Result models
class ClarificationQuestion(BaseModel):
    field: str
    question: str
    suggestions: list[str] = Field(default_factory=list)
    required: bool = False

class EnhancementResult(BaseModel):
    spec: ProjectSpec
    completeness_score: float
    clarifications_needed: list[ClarificationQuestion] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
```

### Browser Classes

**`src/acli/browser/manager.py`**
```python
# Lines 25-30: Enum
class BrowserBackend(str, Enum):
    PUPPETEER = "puppeteer"
    PLAYWRIGHT = "playwright"
    BOTH = "both"

# Lines 32-66: Config
@dataclass
class BrowserConfig:
    backend: BrowserBackend = BrowserBackend.BOTH
    puppeteer: PuppeteerConfig | None = None
    playwright: PlaywrightConfig | None = None
    def __post_init__(self): ...
    def get_mcp_servers(self) -> dict[str, Any]: ...
    def get_tool_list(self) -> list[str]: ...

# Lines 68-141: Unified interface
class UnifiedBrowser:
    def __init__(self, backend: BrowserBackend = BrowserBackend.PLAYWRIGHT): ...
    def navigate(self, url: str) -> dict[str, Any]: ...
    def click(self, selector: str | None = None, element: str | None = None, ref: str | None = None) -> dict[str, Any]: ...
    def type_text(self, text: str, selector: str | None = None, element: str | None = None, ref: str | None = None) -> dict[str, Any]: ...
    def screenshot(self, name: str | None = None) -> dict[str, Any]: ...
    def wait(self, text: str | None = None, seconds: float | None = None) -> dict[str, Any]: ...
    def get_page_info(self) -> dict[str, Any]: ...

# Lines 143-192: Factories & helpers
def get_browser_instructions(backend: BrowserBackend = BrowserBackend.PLAYWRIGHT) -> str: ...
def get_default_browser_config() -> BrowserConfig: ...
```

---

## 4. INTERFACE CONTRACTS (PUBLIC METHOD SIGNATURES)

### Orchestrator Interface
```python
# Core coordination
orchestrator = AgentOrchestrator(project_dir, model, max_iterations)
await orchestrator.run_loop(on_session_start, on_session_end)
status = orchestrator.get_status()  # → dict with running, paused, progress

# Control
orchestrator.request_pause()
orchestrator.request_stop()
orchestrator.resume()

# Events
orchestrator.on_event(event_type: str, handler: Callable)
```

### TUI Interface
```python
# Launch
app = AgentMonitorApp(orchestrator=orch, project_dir=proj_dir)
app.run()  # Textual blocking call

# Communication
bridge.send_command("pause" | "resume" | "stop")
agent_node = bridge.get_agent_by_id(agent_id)
snapshot = bridge.snapshot  # OrchestratorSnapshot
```

### Feature Tracking Interface
```python
# Load/save
fl = load_feature_list(path)  # → FeatureList
fl.load()
fl.save()

# Query
next_feat = fl.get_next_incomplete()  # → Feature | None
comps = fl.get_components()  # → list[str]
summary = fl.get_summary()  # → dict

# Mutate
fl.mark_passing(feature_id, notes)
fl.mark_failed(feature_id, notes)
fl.add(feature)
```

### Security Hook Interface
```python
# Called by SDK PreToolUse hook
result = await bash_security_hook(input_data, tool_use_id, context)
# Returns: {} (allow) or {"decision": "block", "reason": "..."} (block)

# Input data shape
input_data = {
    "tool_name": "Bash",
    "tool_input": {"command": "ls -la"}
}
```

---

## 5. MODEL STRING LOCATIONS

**Claude Model References (v1 hardcoded):**
| File | Line | Model | Context |
|------|------|-------|---------|
| `cli.py` | 211 | `"claude-sonnet-4-20250514"` | run command default |
| `cli.py` | 454 | `"claude-sonnet-4-20250514"` | config default |
| `cli.py` | 565 | `"claude-sonnet-4-20250514"` | monitor command default |
| `core/orchestrator.py` | 38 | `"claude-sonnet-4-20250514"` | AgentOrchestrator.__init__ |
| `core/orchestrator.py` | 261 | `"claude-opus-46"` | run_autonomous_agent (different!) |
| `core/client.py` | 132-135 | System prompt | Default: "You are an expert full-stack developer..." |
| `spec/enhancer.py` | 60 | `"claude-sonnet-4-20250514"` | call_claude_api default |
| `spec/enhancer.py` | 110 | `"claude-sonnet-4-20250514"` | enhance_spec default |
| `spec/enhancer.py` | 187 | `"claude-sonnet-4-20250514"` | refine_spec_with_answers |
| `spec/enhancer.py` | 74 | `"2023-06-01"` | API version |
| `spec/enhancer.py` | 74 | `"structured-outputs-2025-11-13"` | Beta header |

**Structured Output API Endpoint:**
| File | Line | URL |
|------|------|-----|
| `spec/enhancer.py` | 90 | `https://api.anthropic.com/v1/messages` |

---

## 6. SECURITY HOOK CHAIN (Exact Flow)

### Entry Point: `bash_security_hook` (line 299, hooks.py)
```
Input: {"tool_name": "Bash", "tool_input": {"command": "..."}}
↓
Line 313: Check if tool_name == "Bash"
↓
Line 316-318: Extract command string
↓
Line 321: extract_commands(command) → list[str]
  └─ Lines 79-160: Parse shell syntax, handle pipes, semicolons, quoted strings
  └─ Returns all base command names (e.g., ["npm", "git"])
↓
Line 331: split_command_segments(command) → list[str]
  └─ Lines 49-76: Split on &&, ||, ; while respecting quotes
  └─ Returns segments like ["npm install", "git add ."]
↓
Line 334-339: For each cmd in commands:
  └─ Check if cmd in ALLOWED_COMMANDS (line 17-46)
  └─ If NOT allowed: BLOCK with reason
  └─ If allowed but in COMMANDS_NEEDING_EXTRA_VALIDATION:
     ├─ Line 344: get_command_for_validation(cmd, segments)
     ├─ Line 349: get_validator(cmd) from validators.py registry
     ├─ Line 351: validator(cmd_segment) → ValidationResult
     └─ If not allowed: BLOCK with validator's reason
↓
Return {} (allow) or {"decision": "block", "reason": "..."} (block)
```

### Validators (validators.py)

**validate_pkill (line 36):**
- Input: `"pkill node"` or `"pkill -f 'node server.js'"`
- Lines 45-70: shlex.parse, extract target process name
- Check against ALLOWED_PKILL_TARGETS (line 15): {node, npm, npx, vite, next, webpack, tsc}
- Return ValidationResult(allowed=True/False, reason="...")

**validate_chmod (line 73):**
- Input: `"chmod +x script.sh"` or `"chmod 777 file"` (BLOCKED)
- Lines 82-116: Parse mode + files
- Check: mode must match regex `r"^[ugoa]*\+x$"` (line 113)
- Block: dangerous modes {777, 666, 000}, flags (-R), other modes
- Return ValidationResult(allowed=True/False, reason="...")

**validate_init_script (line 119):**
- Input: `"./init.sh"` (allowed) or `"/etc/init.sh"` (blocked)
- Lines 127-149: Simple path check
- Only allow: `./init.sh` exactly
- Block: absolute paths (/), directory traversal (..)
- Return ValidationResult(allowed=True/False, reason="...")

### Integration with SDK

**client.py (line 113):**
```python
hooks = cast(
    dict[Literal["PreToolUse", ...], list[HookMatcher]],
    {
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[bash_security_hook]),
        ],
    },
)

# Passed to ClaudeAgentOptions (line 137-148)
ClaudeSDKClient(
    options=ClaudeAgentOptions(
        hooks=hooks,  # ← SDK calls bash_security_hook before executing Bash tool
        ...
    )
)
```

---

## 7. STREAMING PIPELINE (Exact Flow)

### 1. Event Generation: `StreamingHandler.handle_*` → `StreamBuffer`

**File:** `core/streaming.py`, lines 122-198

```
run_agent_session (agent.py:20)
├─ Lines 38-75: async for msg in client.receive_response()
│  └─ Incoming SDK message types:
│     ├─ AssistantMessage.content[].TextBlock.text
│     ├─ AssistantMessage.content[].ToolUseBlock (name, input)
│     └─ UserMessage.content[].ToolResultBlock (content, is_error)
│
├─ Call: await streaming.handle_text(text)
│  └─ StreamingHandler.handle_text (line 122)
│     └─ Create StreamEvent(type=TEXT, text=text)
│     └─ await self.emit(event)
│        └─ await self.buffer.push(event)
│           └─ StreamBuffer._events.append(event)
│           └─ Set self._new_event.set() (for waiting consumers)
│
├─ Call: await streaming.handle_tool_start(name, input)
│  └─ StreamingHandler.handle_tool_start (line 127)
│     └─ Record self._current_tool_start = datetime.now()
│     └─ Create StreamEvent(type=TOOL_START, tool_name=name, tool_input=input)
│     └─ await self.emit(event) → buffer.push()
│
├─ Call: await streaming.handle_tool_end(name, result, error)
│  └─ StreamingHandler.handle_tool_end (line 137)
│     └─ Calculate duration = now - _current_tool_start
│     └─ Create StreamEvent(type=TOOL_END, tool_duration_ms=duration, tool_error=error)
│     └─ await self.emit(event) → buffer.push()
│
└─ Call: await streaming.handle_error(error_msg)
   └─ StreamingHandler.handle_error (line 168)
      └─ Create StreamEvent(type=ERROR, text=error)
      └─ await self.emit(event) → buffer.push()
```

### 2. Buffer Storage: `StreamBuffer` (lines 58-99)

```
StreamBuffer (max_size=1000 events)
├─ _events: list[StreamEvent]  # Circular: keep last 1000
├─ _lock: asyncio.Lock()  # Thread-safe access
├─ _new_event: asyncio.Event()  # Signaled when new event pushed
│
├─ async push(event: StreamEvent):
│  └─ Lock, append event, trim to max_size, set _new_event
│
└─ async iter_from(index: int):
   └─ Infinite async generator
   └─ Yields events starting from index
   └─ When no more events, waits on _new_event
   └─ (Used by TUI and dashboard to consume real-time events)
```

### 3. TUI Consumption: `OrchestratorBridge` (bridge.py, lines 262-286)

```
OrchestratorBridge.consume_events (line 262)
├─ async for event in orchestrator.buffer.iter_from(self._event_index)
│  ├─ self._event_index += 1
│  ├─ self.handle_event(event) (line 186)
│  │  ├─ Update self._snapshot (OrchestratorSnapshot)
│  │  ├─ Update self._root (AgentNode hierarchy)
│  │  ├─ Route to handlers:
│  │  │  ├─ SESSION_START: Create new AgentNode, append to _root.children
│  │  │  ├─ SESSION_END: Mark agent as completed
│  │  │  ├─ TOOL_START: Increment tool_calls, set current_tool
│  │  │  ├─ TOOL_END/TOOL_BLOCKED/ERROR: Append to errors, update status
│  │  │  ├─ PROGRESS: Update _snapshot.features_done/total
│  │  │  └─ TEXT: Update _current_agent.last_text
│  │  │
│  │  └─ Notify callbacks (line 254-260)
│  │     └─ for cb in self._callbacks: cb(event)
│  │
│  └─ TUI widgets call bridge._on_bridge_event
│     └─ app.py line 128: try log_widget.write_event(event)

└─ Runs until stop_event.is_set() or orchestrator stops
```

### 4. Widget Display: Textual rendering (app.py, widgets.py)

```
app.py: on_mount (line 96)
├─ Register bridge callback: self.bridge.on_event(self._on_bridge_event)
├─ Start background workers:
│  ├─ self.run_worker(self._consume_events())  # Line 103
│  │  └─ await self.bridge.consume_events(self._stop_event)
│  │     └─ Feeds events to bridge, which calls callbacks
│  │
│  ├─ self.run_worker(self._poll_state())  # Line 105
│  │  └─ Every 1s: poll orchestrator.get_status()
│  │
│  └─ self.run_worker(self._refresh_loop())  # Line 106
│     └─ Every 0.25s (4 FPS): refresh all widgets
│
└─ _on_bridge_event (line 128): Immediate callback when real event arrives
   └─ Try to get LogStream widget
   └─ log_widget.write_event(event) (line 132)
      └─ Format event with Rich markup (timestamps, colors)
      └─ Write to RichLog widget

CyberHeader.update_from_snapshot (widgets.py:53)
├─ Read snap.running, snap.paused, snap.current_session_id
├─ Update status_text reactive field
├─ Query and update child Static widgets with colors

AgentGraph.refresh_graph (widgets.py:174)
├─ Read self.bridge.root_agent
├─ Render ASCII art hierarchy (lines 101-172)
│  ├─ Root status + progress bar
│  ├─ For each child session:
│  │  ├─ Show session # [type]
│  │  ├─ Show duration, tool_calls, current_tool
│  │  ├─ Show error count
│  │  └─ Show last_text snippet if running
│  └─ Use colored connectors (├─, ╰─)
├─ Update Static("graph-content") widget

LogStream.write_event (widgets.py:364)
├─ Filter by _log_level_filter (all, tools, errors, text)
├─ Format event based on type:
│  ├─ TEXT: "[#0abdc6]TXT[/] {text}"
│  ├─ TOOL_START: "[#ea00d9]TOL[/] ▶ {tool_name}"
│  ├─ TOOL_END: "[#00ff41]TOL[/] ✓ {tool_name} {duration}ms"
│  ├─ TOOL_BLOCKED: "[#ff003c]BLK[/] ⊘ {tool_name}: {reason}"
│  ├─ ERROR: "[#ff003c]ERR[/] {text}"
│  ├─ SESSION_START: "[#00ff41]SES[/] ═══ Session #{id} [{type}] ═══"
│  ├─ SESSION_END: "[#0abdc6]SES[/] ═══ Session #{id} ENDED ═══"
│  └─ PROGRESS: "[#f5a623]PRG[/] Features: {done}/{total} ({pct}%)"
├─ Write to RichLog widget
└─ Auto-scroll to bottom

StatsPanel.refresh_stats (widgets.py:484)
├─ Read snap.features_done, snap.features_total
├─ Draw progress bar: █ filled, ░ empty (30 chars wide)
├─ Show metrics: Sessions, Tools, Errors, Events
├─ Show model, project_dir
└─ _refresh_tool_board (line 534)
   ├─ Get recent 100 events from buffer
   ├─ Filter for TOOL_START/END/BLOCKED
   ├─ Pair starts with ends (track duration)
   ├─ Show last 8 tool executions
   └─ Display active (running) tools with elapsed time
```

---

## 8. SESSION LIFECYCLE (ProjectState → SessionState)

### Initialization (orchestrator.run_loop, line 78)

```
orchestrator = AgentOrchestrator(project_dir, model, max_iterations)
├─ self.state = get_project_state(project_dir)  (line 45)
│  └─ ProjectState.load(project_dir)  (session.py:107)
│     ├─ Try to read .acli_state.json
│     └─ If not exists, return new empty ProjectState
├─ self.buffer = StreamBuffer()  (line 46)
└─ self.streaming = StreamingHandler(self.buffer)  (line 47)
```

### Session Start (lines 118-133)

```
# Each iteration of run_loop
session = self.state.start_session()  (session.py:69)
├─ session_type = "initializer" if is_first_run else "coding"
├─ Create SessionState(session_id=count+1, session_type=session_type)
└─ self.current_session = session

# Emit event
await self.streaming.handle_session_start(session.session_id, session.session_type)
├─ Create StreamEvent(type=SESSION_START, session_id, session_type)
└─ await buffer.push(event)

# Optional callback
if on_session_start:
    await _maybe_await(on_session_start(session.session_id, session.session_type))
```

### Session Run (lines 147-152)

```
prompt = load_prompt_template(prompt_name)  (agent.py:85)
├─ Read from prompts/templates/{initializer,coding}.md
└─ Or fallback to hardcoded prompts (lines 94-125)

client = create_sdk_client(project_dir, model)  (client.py:71)
├─ Create ClaudeSDKClient with security hooks
└─ Cwd set to project_dir

async with client:
    status, response = await run_agent_session(client, prompt, streaming)
    (agent.py:20)
    ├─ await client.query(prompt)
    ├─ async for msg in client.receive_response()
    └─ Stream events via streaming.handle_*()
```

### Session End (lines 155-175)

```
if status == "error":
    consecutive_errors += 1
    self.state.end_session(status="error", errors=[response])  (session.py:79)
else:
    consecutive_errors = 0
    self.state.end_session(status="completed")

# end_session method (line 79):
├─ self.current_session.end_time = datetime.now()
├─ self.current_session.status = status
├─ self.sessions.append(self.current_session)
└─ self.current_session = None

# Emit event
await self.streaming.handle_session_end(session.session_id)
├─ Create StreamEvent(type=SESSION_END, session_id)
└─ await buffer.push(event)

# Save state to disk
self.state.save()  (session.py:96)
├─ Write .acli_state.json with all session history
└─ Persist: project_dir, created_at, sessions[] (each with to_dict())

# Update progress
progress = self._get_progress()  (line 215)
├─ Read feature_list.json
├─ Count total features
├─ Count passing features
└─ Return (passing, total)

if progress:
    await self.streaming.handle_progress(progress[0], progress[1])
    ├─ Create StreamEvent(type=PROGRESS, features_done, features_total)
    └─ await buffer.push(event)
```

### Auto-Continue (lines 183-185)

```
# Between sessions
if not self._stop_requested:
    await asyncio.sleep(AUTO_CONTINUE_DELAY)  # 3.0 seconds
    # Loop continues: next iteration creates new session
```

### Pause/Stop Handling (lines 110-115)

```
if self._pause_requested:
    logger.info("Paused. Call resume() to continue.")
    while self._pause_requested and not self._stop_requested:
        await asyncio.sleep(0.5)
    if self._stop_requested:
        break
```

---

## 9. TUI WIDGET TREE & CSS (cyberpunk.tcss)

### Widget Hierarchy (app.py, lines 80-94)

```
ComposeResult:
├─ CyberHeader (id="header")
│  └─ Horizontal
│     ├─ Static: "⟁ ACLI AGENT MONITOR" (id="header-title")
│     ├─ Static: "● RUNNING" (id="header-status")
│     └─ Static: "S#1 [initializer] | 00:12:45" (id="header-elapsed")
│
├─ Horizontal (id="main-container")
│  ├─ Vertical (id="left-panel", width=35%)
│  │  ├─ AgentGraph (id="agent-graph-widget", height=50%)
│  │  │  └─ VerticalScroll
│  │  │     └─ Static (id="graph-content")
│  │  │        └─ ASCII tree rendering (line 101-172)
│  │  │
│  │  └─ AgentDetail (id="agent-detail-widget", height=50%)
│  │     └─ Vertical
│  │        ├─ Static: "◆ ORCHESTRATOR (orchestrator)" (id="agent-detail-title")
│  │        └─ VerticalScroll
│  │           └─ Static: property lines (id="agent-detail-body")
│  │
│  └─ Vertical (id="right-panel", width=65%)
│     ├─ LogStream (id="log-stream-widget", height=60%)
│     │  └─ Vertical
│     │     ├─ Horizontal (id="log-header")
│     │     │  └─ Static: filter bar (id="log-filter-bar")
│     │     └─ RichLog (id="log-stream")
│     │
│     └─ StatsPanel (id="stats-panel-widget", height=40%)
│        └─ Vertical
│           ├─ Static: progress + metrics (id="stats-content")
│           └─ Static: recent tools (id="tool-board")
│
└─ Footer (keybindings)
```

### CSS IDs & Classes (cyberpunk.tcss)

**Key Colors:**
```
Deep navy void:     #000b1e
Dark teal:          #001a33
Neon cyan:          #0abdc6
Hot pink/magenta:   #ea00d9
Matrix green:       #00ff41
Neon red:           #ff003c
Ice white:          #d7fffe
Steel gray:         #4a6670
Electric blue border: #133e7c
```

**Widget Styling:**
- `#header`: dock=top, height=3, heavy bottom border
- `#main-container`: height=1fr (fills)
- `#left-panel`: width=35%, heavy right border
- `#right-panel`: width=65%
- `#agent-graph`: height=50%, heavy bottom border
- `#agent-detail`: height=50%
- `#log-panel`: height=60%, border bottom
- `#log-stream`: RichLog, scrollbar with custom colors, auto_scroll=True
- `#stats-panel`: height=40%
- `#tool-board`: max-height=12 (8 tools + header)

**Reactive Classes:**
- `.agent-node`: #0abdc6 (active agents)
- `.agent-node-active`: #00ff41 bold
- `.agent-node-error`: #ff003c bold
- `.agent-node-idle`: #4a6670
- `.agent-connector`: #133e7c
- `.tool-status-running`: #0abdc6 bold
- `.tool-status-done`: #00ff41
- `.tool-status-blocked`: #ff003c bold

---

## 10. CLI COMMAND SIGNATURES (cli.py)

**Command Structure (Typer):** 7 commands total

```python
@app.callback()
def main(version: bool = Option(...)):
    """Global options, called before any command."""

@app.command()
def init(
    project_name: str = Argument(...),
    template: str = Option("default", "--template", "-t"),
    spec: Path | None = Option(None, "--spec", "-s"),
    interactive: bool = Option(True, "--interactive/--no-interactive"),
) -> None:
    """Create project directory, feature_list.json, init.sh, .gitignore."""

@app.command()
def run(
    project_dir: Path = Argument(Path("."), help="..."),
    model: str = Option("claude-sonnet-4-20250514", "--model", "-m"),
    max_iterations: int | None = Option(None, "--max-iterations"),
    dashboard: bool = Option(True, "--dashboard/--no-dashboard"),
    headless: bool = Option(False, "--headless"),
    verbose: bool = Option(False, "--verbose", "-v"),
) -> None:
    """Launch orchestrator loop, optionally with TUI."""

@app.command()
def status(
    project_dir: Path = Argument(Path("."), help="..."),
    verbose: bool = Option(False, "--verbose", "-v"),
) -> None:
    """Show progress: total features, passing, remaining, percentage."""

@app.command()
def enhance(
    spec_file: Path | None = Argument(None, help="..."),
    output: Path | None = Option(None, "--output", "-o"),
    format: str = Option("json", "--format", "-f"),
) -> None:
    """Placeholder: spec enhancement (Claude API)."""

@app.command()
def config(
    key: str | None = Argument(None, help="..."),
    value: str | None = Argument(None, help="..."),
    list_all: bool = Option(False, "--list", "-l"),
) -> None:
    """Get/set config in ~/.config/acli/config.json."""

@app.command()
def list_skills(
    verbose: bool = Option(False, "--verbose", "-v"),
) -> None:
    """List skills in ~/.claude/skills/."""

@app.command()
def monitor(
    project_dir: Path = Argument(Path("."), help="..."),
    model: str = Option("claude-sonnet-4-20250514", "--model", "-m"),
    max_iterations: int | None = Option(None, "--max-iterations"),
    attach: bool = Option(True, "--attach/--detached"),
) -> None:
    """Launch cyberpunk TUI (optionally with live orchestrator)."""
```

**Async Helper (line 40):**
```python
async def _run_tui_with_orchestrator(orchestrator, project_dir) -> None:
    """Concurrent TUI + orchestrator with cancellation."""
    tui_task = asyncio.create_task(tui.run_async())
    orch_task = asyncio.create_task(orchestrator.run_loop())
    done, pending = await asyncio.wait([tui_task, orch_task], return_when=FIRST_COMPLETED)
    # Cancel losing task
```

---

## 11. EXTENSION POINTS FOR V2

### Critical Hook-In Locations

1. **Orchestrator Loop (orchestrator.py:78-190)**
   - Lines 78-107: Main while loop — can add sub-agent dispatch here
   - Lines 118-133: Session start callbacks
   - Lines 147-152: Agent session execution — can fork/parallelize
   - Lines 155-175: End session, state save — can add custom handlers
   - Insertion: Add feature selection logic, multi-agent branching

2. **Session Lifecycle (session.py:69-95)**
   - Line 69: start_session() — can route to different agent types
   - Line 79: end_session() — can inject middleware before save
   - Line 96: save() — can trigger webhooks
   - Insertion: Custom session types beyond "initializer"/"coding"

3. **Streaming Pipeline (streaming.py:101-198)**
   - Lines 117-120: emit() — central event dispatch
   - Lines 122-197: handle_*() methods — can add custom event types
   - Line 111: AsyncEventEmitter — already extensible
   - Insertion: Sub-agent events, metrics, custom telemetry

4. **Security Hooks (hooks.py:299-356)**
   - Line 313: Check tool_name — can add custom tool validators
   - Line 321: extract_commands() — can add stricter parsing
   - Line 349: get_validator() — can register new command validators
   - Insertion: Per-project security policies, allowlists

5. **TUI Widgets (app.py, widgets.py)**
   - Line 86: AgentGraph.render_graph() — can show sub-agent tree
   - Lines 364-439: LogStream.write_event() — can add custom event rendering
   - Line 484-532: StatsPanel.refresh_stats() — can add metrics
   - Insertion: Sub-agent status panels, custom visualizations

6. **Feature Tracking (feature_list.py:131-142)**
   - Line 131: get_next_incomplete() — can use custom selection logic
   - Line 143: mark_passing() — can trigger callbacks
   - Insertion: Feature dependencies, parallel feature groups

7. **Progress Tracking (tracker.py:103-116)**
   - Lines 107-116: _check_milestones() — event-driven
   - Line 90: on_progress() callback registration
   - Insertion: Custom milestone definitions, external reporting

8. **Client Configuration (client.py:71-149)**
   - Lines 113-130: hooks dict — register new PreToolUse hooks
   - Lines 141-143: allowed_tools — can extend with custom tools
   - Insertion: Per-project tool allowlists, new MCP servers

### Model String Configuration Points
- `cli.py`: Lines 211, 454, 565 (default model options)
- `orchestrator.py`: Lines 38, 261 (AG constructor, run_autonomous_agent)
- `enhancer.py`: Lines 60, 110, 187 (spec API calls)
- **V2 Strategy**: Move to centralized config or env var with fallback

### State File Locations
- `.acli_state.json`: Session history (serialized ProjectState)
- `feature_list.json`: Progress tracking (Feature list)
- `.claude_settings.json`: Generated by client.py (SDK settings)

---

## 12. UNRESOLVED QUESTIONS FOR V2 PLANNING

1. **Sub-Agent Coordination:** How do sub-agents (e.g., parallel feature implementations) share session state? Should they use separate StreamBuffer instances or a unified one?

2. **Agent Type Extension:** What's the taxonomy for new agent types? Beyond "initializer" and "coding", are there "reviewer", "integrator", "tester" agents?

3. **Tool Call Batching:** Should multi-agent mode batch tool calls (collect from all agents, execute, return) or stream independently?

4. **Failure Recovery:** When a sub-agent fails, should it auto-retry, escalate to orchestrator, or trigger a separate "repair agent"?

5. **Feature Dependencies:** feature_list.json tracks IDs but not inter-feature dependencies. Should v2 model feature DAGs?

6. **Model Routing:** Should different agents use different models (e.g., Opus for architecture, Haiku for simple tasks)? How to specify?

7. **TUI Sub-Agent Tree:** How deep should the agent hierarchy visualization go? Should it collapse parallel sub-agents or show full tree?

8. **Spec Enhancement:** The `enhance` command is a placeholder. Should v2 integrate with structured outputs API for real spec generation?

9. **Commit Strategy:** Coding agent commits per-feature. For parallel features, should commits be ordered by dependency or by completion time?

10. **Progress Persistence:** Feature_list.json is the only progress source. Should v2 also use .acli_state.json for feature-to-session mapping?

---

## Summary Stats

| Metric | Count |
|--------|-------|
| Total Python files | 42 |
| Total LOC (core + TUI + utils) | ~6,100 |
| Core files | 6 (client, orchestrator, agent, session, streaming, __init__) |
| Public classes | 25+ |
| Public methods | 100+ |
| CLI commands | 7 |
| Event types (EventType enum) | 8 |
| Security validators | 3 (pkill, chmod, init.sh) |
| TUI widgets | 5 (Header, Graph, Detail, LogStream, Stats) |
| CSS color definitions | 14 |
| Pydantic models | 10+ |
| Browser backends | 2 (Puppeteer, Playwright) |
| MCP servers (builtin) | 5 (puppeteer, playwright, filesystem, git, fetch) |

---

**Report Generated:** 2026-03-18 23:50 UTC
**Analyst:** Researcher Agent (a4fdc0c2a5892d70f)
**Scope:** Comprehensive line-level analysis for v2 migration planning
