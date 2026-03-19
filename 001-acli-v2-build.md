# ACLI v2 (Shannon-ACLI) — Gated Execution Prompt

<mock_detection_protocol>
## ⛔ IRON RULE — READ BEFORE EVERY TASK

Before executing ANY task in this prompt, check your intent:

- Creating `.test.*`, `_test.*`, `*Tests.*`, `test_*` files → **STOP**
- Importing mock libraries (`unittest.mock`, `pytest-mock`, `nock`, `sinon`, `jest.mock`) → **STOP**
- Creating in-memory databases (`SQLite :memory:`, `:memory:`, `H2`, `mongomock`) → **STOP**
- Adding `TEST_MODE`, `NODE_ENV=test`, `TESTING=true` flags → **STOP**
- Rendering components in isolation (Testing Library, Storybook) → **STOP**
- Writing `mock.patch`, `@patch`, `MagicMock`, `Mock()` → **STOP**
- Creating fake/stub HTTP clients (`httpretty`, `responses`, `nock`) → **STOP**
- Using `monkeypatch` to replace real services → **STOP**

**Fix the REAL system instead. No exceptions.**

If at any point during execution you feel the urge to write a test file or mock a dependency, that urge is a signal that the real system has a problem. Fix the real system.
</mock_detection_protocol>

---

<objective>
Transform the existing ACLI v1 codebase (autonomous-claude-code-builder, ~7,300 LOC, 40 files) into ACLI v2 (Shannon-ACLI) — a universal autonomous coding system that handles ANY prompt, ANY project type (greenfield + brownfield), with multi-agent orchestration, functional validation gates, deep context/memory management, and full TUI visibility.

The v2 build is **additive** — v1 is preserved and extended. No files are deleted; the orchestrator is replaced, everything else is enhanced or new.
</objective>

<context>
<codebase>
Existing project: `autonomous-claude-code-builder`
Language: Python 3.11+ | Framework: Typer CLI + Textual TUI
Package: `src/acli/` with modules: core/, tui/, ui/, spec/, security/, progress/, browser/, integration/, prompts/, utils/
Entry point: `src/acli/cli.py` (Typer, 7 commands)
Key dependencies: claude-agent-sdk>=0.1.48, textual>=1.0.0, rich>=13.7.0, typer>=0.9.0, pydantic>=2.5.0, httpx>=0.25.0
Current orchestrator: 2-agent pattern (Initializer + Coding) in `core/orchestrator.py`
Current TUI: 4-panel cyberpunk dashboard in `tui/app.py` + `tui/widgets.py`
Architecture doc: `ARCHITECTURE_V2.md` contains the full target design
</codebase>

<models>
Primary planning/analysis model: `claude-opus-4-6` (128k output, 1M context, adaptive thinking)
Primary implementation model: `claude-sonnet-4-6` (64k output, 1M context, adaptive thinking)
Adaptive thinking: `{"type": "adaptive", "effort": "high"}` for Opus, `{"type": "adaptive"}` for Sonnet
Deprecated on 4.6: `budget_tokens`, `thinking: {type: "enabled"}`, assistant-turn prefills (Opus only)
API change: `output_format` → `output_config.format`
</models>

<target_platforms>
This is a **CLI + TUI** project (Python package). Validation uses:
- CLI: `python -m acli <command>` execution + exit codes
- API: `curl` against running servers spawned by agents
- TUI: Textual app rendering verification via import + instantiation
- Generic: File existence, JSON structure, Python import checks
</target_platforms>
</context>

<skills_inventory>
**MANDATORY: Load and follow these skills before starting**

| Skill | Relevance | When |
|-------|-----------|------|
| `functional-validation` | Iron Rule enforcement, evidence protocols | Every validation gate |
| `python-agent-sdk` | ClaudeSDKClient patterns, tools, hooks, MCP | Agent factory, orchestrator |
| `create-validation-plan` | Phase-gated planning with blocking gates | This prompt's structure |
| `optimize-prompt` | Agent system prompt generation | Agent factory prompts |
| `prompt-engineering-expert` | Prompt quality for sub-agent prompts | Agent factory |
| `prompt-engineering-patterns` | Advanced techniques (CoT, XML, prefilling) | Agent prompts |
| `create-meta-prompts` | Multi-stage prompt pipelines | Orchestrator prompt chain |
| `create-agent-skills` | If creating new skills during build | Optional |

**Action**: Read each relevant skill's SKILL.md before the phase that uses it.
</skills_inventory>

<exploration_required>
**MANDATORY: Before proposing ANY code changes**

1. Read the existing file with `cat` or Read tool
2. Understand current implementation — imports, classes, functions, dependencies
3. Identify what changes vs. what stays
4. Only THEN write new code

Never overwrite a file without reading it first. The v1 codebase is working code — don't break it.
</exploration_required>

---

# PHASE 1: Core Infrastructure — Routing, Context, Model Updates

**Objective**: Create the routing module, context/memory store, and update the SDK client for Claude 4.6 models with adaptive thinking.

**New files created in this phase:**
- `src/acli/routing/__init__.py`
- `src/acli/routing/router.py`
- `src/acli/routing/workflows.py`
- `src/acli/context/__init__.py`
- `src/acli/context/store.py`
- `src/acli/context/memory.py`
- `src/acli/context/chunker.py`
- `src/acli/context/onboarder.py`

**Modified files:**
- `src/acli/core/client.py` — model IDs, adaptive thinking, output_config
- `src/acli/core/streaming.py` — new event types
- `pyproject.toml` — new dependencies

---

<task id="1.1">
## Task 1.1: Update SDK Client for Claude 4.6

Read `src/acli/core/client.py`. Update:

1. Default model from `claude-sonnet-4-20250514` to `claude-sonnet-4-6`
2. Add model routing constants:
   ```python
   MODEL_OPUS = "claude-opus-4-6"
   MODEL_SONNET = "claude-sonnet-4-6"
   ```
3. Add adaptive thinking configuration to `ClaudeAgentOptions`:
   ```python
   thinking={"type": "adaptive", "effort": "high"}  # for Opus agents
   thinking={"type": "adaptive"}                      # for Sonnet agents
   ```
4. Update `create_sdk_client()` to accept `model_tier: Literal["opus", "sonnet"]` parameter and route accordingly
5. Update `max_turns` from 100 to 200 (longer agent sessions for v2)
6. Add `output_config` if structured output is needed (replaces deprecated `output_format`)

Also update every reference to the old model string in:
- `src/acli/cli.py` (run command default, monitor command default, config default)
- `src/acli/spec/enhancer.py` (call_claude_api default model)
- `src/acli/spec/refinement.py` (interactive_enhancement default)

Files: `src/acli/core/client.py`, `src/acli/cli.py`, `src/acli/spec/enhancer.py`, `src/acli/spec/refinement.py`
</task>

<validation_gate id="VG-1.1" blocking="true">
Prerequisites: `cd` into project root | `pip install -e ".[dev]"` succeeds (exit 0)
Execute:
```bash
python -c "
from acli.core.client import MODEL_OPUS, MODEL_SONNET, create_sdk_client
assert MODEL_OPUS == 'claude-opus-4-6', f'Expected claude-opus-4-6, got {MODEL_OPUS}'
assert MODEL_SONNET == 'claude-sonnet-4-6', f'Expected claude-sonnet-4-6, got {MODEL_SONNET}'
print('MODEL constants: PASS')
" 2>&1 | tee evidence/vg1.1-models.txt

grep -r "claude-sonnet-4-20250514" src/ 2>&1 | tee evidence/vg1.1-old-model.txt
```
Pass criteria:
- Python import + assertion exits 0
- `MODEL_OPUS == 'claude-opus-4-6'`
- `MODEL_SONNET == 'claude-sonnet-4-6'`
- grep for old model string returns **zero** matches (no stale references)
Review: `cat evidence/vg1.1-models.txt` — confirm "PASS" printed | `cat evidence/vg1.1-old-model.txt` — confirm empty
Verdict: PASS → proceed to 1.2 | FAIL → fix client.py and all references → re-run from prerequisites
Mock guard: IF tempted to mock the SDK client → STOP → fix the REAL import path
</validation_gate>

---

<task id="1.2">
## Task 1.2: Extend Streaming Event Types

Read `src/acli/core/streaming.py`. Add new event types to the `EventType` enum:

```python
# v2 additions
AGENT_SPAWN = "agent_spawn"
AGENT_COMPLETE = "agent_complete"
ANALYSIS_UPDATE = "analysis_update"
PLAN_CREATED = "plan_created"
PHASE_START = "phase_start"
PHASE_END = "phase_end"
GATE_START = "gate_start"
GATE_RESULT = "gate_result"
CONTEXT_UPDATE = "context_update"
MEMORY_UPDATE = "memory_update"
THINKING = "thinking"
MOCK_DETECTED = "mock_detected"
PROMPT_RECEIVED = "prompt_received"
```

Add corresponding handler methods to `StreamingHandler`:
- `handle_agent_spawn(agent_id, agent_type, model)`
- `handle_agent_complete(agent_id, status)`
- `handle_gate_start(gate_id, criteria)`
- `handle_gate_result(gate_id, status, evidence_path)`
- `handle_context_update(key, summary)`
- `handle_memory_update(fact)`
- `handle_phase_start(phase_id, phase_name)`
- `handle_phase_end(phase_id, status)`

Extend `StreamEvent` dataclass with fields for the new event types:
- `agent_id: str`, `agent_type: str`, `model: str`
- `gate_id: str`, `gate_status: str`, `evidence_path: str`
- `phase_id: str`, `phase_name: str`
- `memory_fact: str`

Files: `src/acli/core/streaming.py`
</task>

<validation_gate id="VG-1.2" blocking="true">
Prerequisites: VG-1.1 PASSED
Execute:
```bash
python -c "
from acli.core.streaming import EventType, StreamEvent, StreamingHandler, StreamBuffer
import asyncio

# Verify all new event types exist
new_types = [
    'AGENT_SPAWN', 'AGENT_COMPLETE', 'ANALYSIS_UPDATE', 'PLAN_CREATED',
    'PHASE_START', 'PHASE_END', 'GATE_START', 'GATE_RESULT',
    'CONTEXT_UPDATE', 'MEMORY_UPDATE', 'THINKING', 'MOCK_DETECTED', 'PROMPT_RECEIVED'
]
for t in new_types:
    assert hasattr(EventType, t), f'Missing EventType.{t}'

# Verify StreamingHandler has new methods
handler = StreamingHandler(StreamBuffer())
new_methods = [
    'handle_agent_spawn', 'handle_agent_complete',
    'handle_gate_start', 'handle_gate_result',
    'handle_context_update', 'handle_memory_update',
    'handle_phase_start', 'handle_phase_end'
]
for m in new_methods:
    assert hasattr(handler, m), f'Missing StreamingHandler.{m}'

# Verify StreamEvent has new fields
event = StreamEvent(type=EventType.AGENT_SPAWN)
assert hasattr(event, 'agent_id')
assert hasattr(event, 'gate_id')
assert hasattr(event, 'phase_id')
assert hasattr(event, 'memory_fact')

print('ALL NEW EVENT TYPES: PASS')
print('ALL NEW HANDLERS: PASS')
print('ALL NEW FIELDS: PASS')
" 2>&1 | tee evidence/vg1.2-events.txt
```
Pass criteria:
- All 13 new EventType members exist
- All 8 new handler methods exist on StreamingHandler
- StreamEvent has agent_id, gate_id, phase_id, memory_fact fields
- Python exits 0 with 3 "PASS" lines
Review: `cat evidence/vg1.2-events.txt` — confirm 3 PASS lines, no errors
Verdict: PASS → proceed to 1.3 | FAIL → fix streaming.py → re-run
Mock guard: IF tempted to mock StreamBuffer → STOP → use real StreamBuffer instance
</validation_gate>

---

<task id="1.3">
## Task 1.3: Create Routing Module — PromptRouter & WorkflowType

Create `src/acli/routing/` package:

**`workflows.py`** — Define workflow types:
```python
class WorkflowType(str, Enum):
    GREENFIELD_APP = "greenfield_app"
    BROWNFIELD_ONBOARD = "brownfield_onboard"
    BROWNFIELD_TASK = "brownfield_task"
    REFACTOR = "refactor"
    DEBUG = "debug"
    CLI_TOOL = "cli_tool"
    IOS_APP = "ios_app"
    FREE_TASK = "free_task"

@dataclass
class WorkflowConfig:
    workflow_type: WorkflowType
    requires_onboarding: bool
    agent_sequence: list[str]  # e.g., ["analyst", "planner", "implementer", "validator"]
    model_tier: str  # "opus" or "sonnet" for primary agent
    platform: str  # "cli", "api", "web", "ios", "full-stack", "generic"
```

**`router.py`** — Classify any input:
```python
class PromptRouter:
    """Classifies any user prompt into a WorkflowType with config."""
    
    def classify(self, prompt: str, project_dir: Path) -> WorkflowConfig:
        """
        Classification logic:
        1. Check project_dir for platform signals (.xcodeproj, package.json, etc.)
        2. Check for existing codebase (brownfield indicators)
        3. Parse prompt text for intent signals (build, fix, refactor, etc.)
        4. Return WorkflowConfig with agent sequence and model tier
        """
```

Classification rules:
- `.xcodeproj` or `.xcworkspace` present → `IOS_APP`
- `Cargo.toml` or CLI binary indicators → `CLI_TOOL`
- `app_spec.txt` present AND no significant source files → `GREENFIELD_APP`
- Significant source files present + prompt says "add/implement/create" → `BROWNFIELD_TASK`
- Significant source files present + prompt says "fix/debug/broken" → `DEBUG`
- Significant source files present + prompt says "refactor/migrate/convert" → `REFACTOR`
- Source files present but no feature_list.json, no app_spec.txt → `BROWNFIELD_ONBOARD`
- None of the above → `FREE_TASK`

"Significant source files" = more than 3 non-config files in common source extensions (.py, .ts, .js, .swift, .rs, .go, .java).

Files: `src/acli/routing/__init__.py`, `src/acli/routing/router.py`, `src/acli/routing/workflows.py`
</task>

<validation_gate id="VG-1.3" blocking="true">
Prerequisites: VG-1.2 PASSED
Execute:
```bash
mkdir -p evidence

# Test 1: Classification of a greenfield scenario
python -c "
from pathlib import Path
from acli.routing.router import PromptRouter
from acli.routing.workflows import WorkflowType
import tempfile, os

router = PromptRouter()

# Greenfield: app_spec.txt, no source files
with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    (p / 'app_spec.txt').write_text('Build a todo app')
    result = router.classify('Build a todo app with React', p)
    assert result.workflow_type == WorkflowType.GREENFIELD_APP, f'Expected GREENFIELD_APP, got {result.workflow_type}'
    print(f'Greenfield: {result.workflow_type} — PASS')

# Brownfield: existing Python files + task prompt
with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    (p / 'src').mkdir()
    for i in range(5):
        (p / 'src' / f'module{i}.py').write_text(f'# module {i}')
    result = router.classify('Add JWT authentication to the API', p)
    assert result.workflow_type in (WorkflowType.BROWNFIELD_TASK, WorkflowType.BROWNFIELD_ONBOARD), f'Expected brownfield, got {result.workflow_type}'
    assert result.requires_onboarding == True, 'Brownfield should require onboarding'
    print(f'Brownfield: {result.workflow_type} — PASS')

# Debug: existing code + debug language
with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    (p / 'src').mkdir()
    for i in range(5):
        (p / 'src' / f'module{i}.py').write_text(f'# module {i}')
    (p / '.acli').mkdir()
    (p / '.acli' / 'context').mkdir(parents=True)
    (p / '.acli' / 'context' / 'codebase_analysis.json').write_text('{}')
    result = router.classify('Fix the broken login endpoint', p)
    assert result.workflow_type == WorkflowType.DEBUG, f'Expected DEBUG, got {result.workflow_type}'
    print(f'Debug: {result.workflow_type} — PASS')

# iOS: .xcodeproj present
with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    (p / 'MyApp.xcodeproj').mkdir()
    result = router.classify('Add a settings screen', p)
    assert result.workflow_type == WorkflowType.IOS_APP, f'Expected IOS_APP, got {result.workflow_type}'
    print(f'iOS: {result.workflow_type} — PASS')

print('ALL ROUTER CLASSIFICATIONS: PASS')
" 2>&1 | tee evidence/vg1.3-router.txt
```
Pass criteria:
- Greenfield classification → `GREENFIELD_APP` — PASS
- Brownfield classification → brownfield type with `requires_onboarding=True` — PASS
- Debug classification → `DEBUG` — PASS
- iOS classification → `IOS_APP` — PASS
- All 4 scenarios pass, Python exits 0
Review: `cat evidence/vg1.3-router.txt` — confirm 4 individual PASS lines + final "ALL ROUTER CLASSIFICATIONS: PASS"
Verdict: PASS → proceed to 1.4 | FAIL → fix router logic → re-run
Mock guard: Uses real temp directories with real files — no mocking filesystem
</validation_gate>

---

<task id="1.4">
## Task 1.4: Create Context Store & Memory Manager

Create `src/acli/context/` package:

**`store.py`** — ContextStore:
```python
class ContextStore:
    """
    Persistent codebase knowledge store.
    
    Reads/writes to .acli/context/ directory:
    - codebase_analysis.json: Full architecture map
    - dependency_graph.json: Import relationships
    - conventions.json: Code patterns and style
    - tech_stack.json: Detected technology stack
    - decisions.jsonl: Append-only decision log
    """
    
    def __init__(self, project_dir: Path): ...
    def initialize(self) -> None: ...  # Create .acli/context/ structure
    def store_analysis(self, analysis: dict) -> None: ...
    def store_tech_stack(self, tech_stack: dict) -> None: ...
    def store_conventions(self, conventions: dict) -> None: ...
    def log_decision(self, key: str, value: str, confidence: float) -> None: ...
    def get_analysis(self) -> dict | None: ...
    def get_tech_stack(self) -> dict | None: ...
    def get_context_summary(self) -> str: ...  # Human-readable summary for agent prompts
    def is_onboarded(self) -> bool: ...  # True if codebase_analysis.json exists and non-empty
```

**`memory.py`** — MemoryManager:
```python
class MemoryManager:
    """
    Cross-session memory — facts that persist across agent sessions.
    
    Stores to .acli/memory/project_memory.json
    """
    
    def __init__(self, project_dir: Path): ...
    def add_fact(self, category: str, fact: str) -> None: ...
    def get_facts(self, category: str | None = None) -> list[dict]: ...
    def get_injection_prompt(self) -> str: ...  # Formatted for system prompt injection
    def clear(self) -> None: ...
    @property
    def fact_count(self) -> int: ...
```

**`chunker.py`** — KnowledgeChunker:
```python
class KnowledgeChunker:
    """
    Chunks codebase into retrievable knowledge segments.
    Stores to .acli/context/knowledge_chunks/
    """
    
    def chunk_codebase(self, project_dir: Path, max_chunk_size: int = 4000) -> list[dict]: ...
    def get_relevant_chunks(self, query: str, top_k: int = 3) -> list[str]: ...
```

**`onboarder.py`** — BrownfieldOnboarder:
```python
class BrownfieldOnboarder:
    """
    Full codebase analysis and context population for brownfield projects.
    
    Executes:
    1. File tree discovery
    2. Tech stack detection
    3. Architecture mapping
    4. Convention detection
    5. Context store population
    6. Knowledge chunking
    """
    
    async def onboard(self, project_dir: Path, streaming: StreamingHandler) -> dict: ...
    def detect_tech_stack(self, project_dir: Path) -> dict: ...
    def detect_conventions(self, project_dir: Path) -> dict: ...
    def map_architecture(self, project_dir: Path) -> dict: ...
```

All classes must use Pydantic where appropriate for data validation, type hints throughout, Google-style docstrings, and async where I/O is involved.

Files: `src/acli/context/__init__.py`, `src/acli/context/store.py`, `src/acli/context/memory.py`, `src/acli/context/chunker.py`, `src/acli/context/onboarder.py`
</task>

<validation_gate id="VG-1.4" blocking="true">
Prerequisites: VG-1.3 PASSED
Execute:
```bash
python -c "
from pathlib import Path
from acli.context.store import ContextStore
from acli.context.memory import MemoryManager
from acli.context.chunker import KnowledgeChunker
from acli.context.onboarder import BrownfieldOnboarder
import tempfile, json

# Test ContextStore
with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    store = ContextStore(p)
    store.initialize()
    
    # Verify directory structure created
    assert (p / '.acli' / 'context').is_dir(), '.acli/context/ not created'
    
    # Store and retrieve tech stack
    stack = {'language': 'Python', 'framework': 'FastAPI', 'database': 'PostgreSQL'}
    store.store_tech_stack(stack)
    retrieved = store.get_tech_stack()
    assert retrieved == stack, f'Tech stack mismatch: {retrieved}'
    
    # Store analysis and verify onboarded
    store.store_analysis({'files': 47, 'architecture': 'layered'})
    assert store.is_onboarded(), 'Should be onboarded after storing analysis'
    
    # Log decision
    store.log_decision('auth_strategy', 'JWT with httpOnly cookies', 0.95)
    
    # Get context summary (string for system prompt)
    summary = store.get_context_summary()
    assert isinstance(summary, str) and len(summary) > 0, 'Context summary should be non-empty string'
    
    print('ContextStore: PASS')

# Test MemoryManager
with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    (p / '.acli' / 'memory').mkdir(parents=True)
    mem = MemoryManager(p)
    
    mem.add_fact('architecture', 'Uses dependency injection via Depends()')
    mem.add_fact('architecture', 'All routes in src/api/v1/')
    mem.add_fact('gotcha', 'PostgreSQL requires explicit connection pool cleanup')
    
    assert mem.fact_count == 3, f'Expected 3 facts, got {mem.fact_count}'
    
    arch_facts = mem.get_facts('architecture')
    assert len(arch_facts) == 2, f'Expected 2 architecture facts, got {len(arch_facts)}'
    
    injection = mem.get_injection_prompt()
    assert 'dependency injection' in injection.lower(), 'Injection prompt should contain stored facts'
    
    print('MemoryManager: PASS')

# Test KnowledgeChunker
with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    src = p / 'src'
    src.mkdir()
    for i in range(5):
        (src / f'module{i}.py').write_text(f'def func_{i}():\\n    return {i}\\n' * 20)
    
    chunker = KnowledgeChunker()
    chunks = chunker.chunk_codebase(p)
    assert len(chunks) > 0, 'Should produce at least 1 chunk'
    assert all('content' in c for c in chunks), 'Each chunk should have content field'
    
    print('KnowledgeChunker: PASS')

# Test BrownfieldOnboarder import
onboarder = BrownfieldOnboarder()
assert hasattr(onboarder, 'onboard'), 'Missing onboard method'
assert hasattr(onboarder, 'detect_tech_stack'), 'Missing detect_tech_stack'
assert hasattr(onboarder, 'detect_conventions'), 'Missing detect_conventions'
assert hasattr(onboarder, 'map_architecture'), 'Missing map_architecture'
print('BrownfieldOnboarder: PASS')

print('ALL CONTEXT MODULE: PASS')
" 2>&1 | tee evidence/vg1.4-context.txt
```
Pass criteria:
- ContextStore: creates dirs, stores/retrieves tech stack, logs decisions, reports onboarded, returns non-empty summary
- MemoryManager: stores 3 facts, retrieves by category, produces injection prompt with content
- KnowledgeChunker: produces non-empty chunks with content field
- BrownfieldOnboarder: has all 4 required methods
- Python exits 0 with 4 individual PASS + final "ALL CONTEXT MODULE: PASS"
Review: `cat evidence/vg1.4-context.txt` — confirm 5 PASS lines, no errors
Verdict: PASS → proceed to Phase 1 Gate | FAIL → fix context module → re-run
Mock guard: Uses real temp directories, real JSON files — no mocking filesystem
</validation_gate>

---

<phase_gate id="PG-1" blocking="true">
## Phase 1 Gate — Core Infrastructure Cumulative Validation

Prerequisites: VG-1.1, VG-1.2, VG-1.3, VG-1.4 all PASSED

Execute:
```bash
# Re-run ALL Phase 1 validations to catch regressions
python -c "
# 1. Model IDs
from acli.core.client import MODEL_OPUS, MODEL_SONNET
assert MODEL_OPUS == 'claude-opus-4-6'
assert MODEL_SONNET == 'claude-sonnet-4-6'

# 2. Event types
from acli.core.streaming import EventType
assert hasattr(EventType, 'AGENT_SPAWN')
assert hasattr(EventType, 'GATE_RESULT')
assert hasattr(EventType, 'MOCK_DETECTED')

# 3. Router
from acli.routing.router import PromptRouter
from acli.routing.workflows import WorkflowType
router = PromptRouter()

# 4. Context
from acli.context.store import ContextStore
from acli.context.memory import MemoryManager

# 5. No old model strings
import subprocess
result = subprocess.run(['grep', '-r', 'claude-sonnet-4-20250514', 'src/'], capture_output=True, text=True)
assert result.stdout.strip() == '', f'Stale model strings found: {result.stdout}'

print('PHASE 1 GATE: ALL PASS')
" 2>&1 | tee evidence/pg1-cumulative.txt
```
Pass criteria: All imports succeed, all assertions pass, no stale model strings, exits 0 with "PHASE 1 GATE: ALL PASS"
Review: `cat evidence/pg1-cumulative.txt`
Verdict: PASS → proceed to Phase 2 | FAIL → identify regression → fix → re-run entire Phase 1 gate
</phase_gate>

---

# PHASE 2: Agent Architecture — Factory, Orchestrator, Skill Engine

**Objective**: Create the agent factory with typed agents, replace the v1 orchestrator with EnhancedOrchestrator, build the skill engine, and add JSONL session logging.

**New files:**
- `src/acli/agents/__init__.py`
- `src/acli/agents/factory.py`
- `src/acli/agents/definitions.py`
- `src/acli/core/orchestrator_v2.py`
- `src/acli/integration/skill_engine.py`

**Modified files:**
- `src/acli/core/session.py` — JSONL logging
- `src/acli/core/__init__.py` — re-export new orchestrator
- `pyproject.toml` — version bump

---

<task id="2.1">
## Task 2.1: Create Agent Definitions & Factory

Create `src/acli/agents/` package:

**`definitions.py`** — Agent type definitions:
```python
class AgentType(str, Enum):
    ROUTER = "router"
    ANALYST = "analyst"
    PLANNER = "planner"
    IMPLEMENTER = "implementer"
    VALIDATOR = "validator"
    CONTEXT_MANAGER = "context_manager"
    REPORTER = "reporter"

@dataclass
class AgentDefinition:
    agent_type: AgentType
    model: str  # "claude-opus-4-6" or "claude-sonnet-4-6"
    system_prompt_template: str
    allowed_tools: list[str]
    max_turns: int
    thinking_config: dict
    output_budget: int
    
    @classmethod
    def for_type(cls, agent_type: AgentType, context: str = "", skills: str = "", memory: str = "") -> "AgentDefinition":
        """Factory method returning pre-configured definition for agent type."""
```

Define the 7 agent types with their model assignments, prompt templates, tool permissions, and thinking configs per the architecture doc.

**`factory.py`** — Agent creation:
```python
class AgentFactory:
    """
    Creates configured SDK clients for each agent type.
    
    Injects:
    - Context from ContextStore (codebase knowledge)
    - Memory from MemoryManager (cross-session facts)
    - Skills from SkillEngine (auto-detected)
    - Security hooks (bash validation + mock detection)
    """
    
    def __init__(self, project_dir: Path, context_store: ContextStore, memory_manager: MemoryManager): ...
    
    def create_agent(self, agent_type: AgentType, task_context: str = "") -> ClaudeSDKClient:
        """Create a fully configured agent client."""
    
    def _build_system_prompt(self, definition: AgentDefinition, task_context: str) -> str:
        """Build system prompt with context, memory, and skill injection."""
```

Files: `src/acli/agents/__init__.py`, `src/acli/agents/definitions.py`, `src/acli/agents/factory.py`
</task>

<validation_gate id="VG-2.1" blocking="true">
Prerequisites: Phase 1 Gate PASSED
Execute:
```bash
python -c "
from acli.agents.definitions import AgentType, AgentDefinition
from acli.agents.factory import AgentFactory
from acli.context.store import ContextStore
from acli.context.memory import MemoryManager
from pathlib import Path
import tempfile

# Verify all 7 agent types
expected_types = ['ROUTER', 'ANALYST', 'PLANNER', 'IMPLEMENTER', 'VALIDATOR', 'CONTEXT_MANAGER', 'REPORTER']
for t in expected_types:
    assert hasattr(AgentType, t), f'Missing AgentType.{t}'
print(f'All {len(expected_types)} AgentTypes: PASS')

# Verify definitions have correct model assignments
analyst_def = AgentDefinition.for_type(AgentType.ANALYST)
assert 'opus' in analyst_def.model, f'Analyst should use Opus, got {analyst_def.model}'

impl_def = AgentDefinition.for_type(AgentType.IMPLEMENTER)
assert 'sonnet' in impl_def.model, f'Implementer should use Sonnet, got {impl_def.model}'

planner_def = AgentDefinition.for_type(AgentType.PLANNER)
assert 'opus' in planner_def.model, f'Planner should use Opus, got {planner_def.model}'
print('Model assignments: PASS')

# Verify factory creates with context injection
with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    store = ContextStore(p)
    store.initialize()
    store.store_tech_stack({'language': 'Python', 'framework': 'FastAPI'})
    mem = MemoryManager(p)
    mem.add_fact('arch', 'Uses DI')
    
    factory = AgentFactory(p, store, mem)
    
    # Build system prompt — should contain context and memory
    prompt = factory._build_system_prompt(analyst_def, 'Analyze auth module')
    assert 'Python' in prompt or 'FastAPI' in prompt, 'System prompt should contain tech stack context'
    assert 'DI' in prompt or 'dependency' in prompt.lower(), 'System prompt should contain memory facts'
    print('Context injection in system prompt: PASS')

print('ALL AGENT ARCHITECTURE: PASS')
" 2>&1 | tee evidence/vg2.1-agents.txt
```
Pass criteria:
- All 7 AgentType members exist
- Analyst + Planner use Opus, Implementer uses Sonnet
- Factory builds system prompts containing injected context and memory
- Python exits 0 with 3 individual PASS + final "ALL AGENT ARCHITECTURE: PASS"
Review: `cat evidence/vg2.1-agents.txt` — confirm 4 PASS lines
Verdict: PASS → proceed to 2.2 | FAIL → fix definitions/factory → re-run
Mock guard: Uses real ContextStore and MemoryManager with temp dirs — no mocking
</validation_gate>

---

<task id="2.2">
## Task 2.2: Create EnhancedOrchestrator

Create `src/acli/core/orchestrator_v2.py`:

1. Rename existing `orchestrator.py` → `orchestrator_v1.py` (preserve, don't delete)
2. Create new `orchestrator_v2.py` implementing `EnhancedOrchestrator` class

Key changes from v1:
- Accepts ANY prompt (not just initializer/coding binary)
- Uses PromptRouter to classify workflow
- Spawns agents dynamically via AgentFactory
- Executes agent graph: Router → (Analyst?) → Planner → [Implementer → Validator]×N → Reporter
- Phase-gated progression with blocking gates
- Emits new event types (AGENT_SPAWN, PHASE_START, GATE_RESULT, etc.)
- Error recovery: 3 retries per task, escalation to Opus on repeated failure
- Pause/resume/stop controls (preserved from v1)

```python
class EnhancedOrchestrator:
    def __init__(self, project_dir: Path, model: str = "claude-sonnet-4-6", max_iterations: int | None = None): ...
    
    async def run(self, prompt: str) -> None:
        """Execute full workflow for any prompt."""
    
    async def run_loop(self, on_session_start=None, on_session_end=None) -> None:
        """Backwards-compatible loop for v1 TUI integration."""
    
    async def route_prompt(self, prompt: str) -> WorkflowConfig: ...
    async def run_analyst(self) -> dict: ...
    async def run_planner(self, workflow: WorkflowConfig, prompt: str) -> dict: ...
    async def run_implementer(self, task: dict, context: str) -> tuple[str, str]: ...
    async def run_validator(self, task: dict, result: str) -> dict: ...
    async def run_reporter(self, phase: dict) -> str: ...
    
    # v1 compatibility
    def request_pause(self) -> None: ...
    def request_stop(self) -> None: ...
    def resume(self) -> None: ...
    def get_status(self) -> dict: ...
```

3. Update `src/acli/core/__init__.py` to export `EnhancedOrchestrator` as the default `AgentOrchestrator`
4. Update `src/acli/cli.py` to import from the new orchestrator (keep backwards compat)

Files: `src/acli/core/orchestrator_v1.py` (rename), `src/acli/core/orchestrator_v2.py` (new), `src/acli/core/__init__.py`, `src/acli/cli.py`
</task>

<validation_gate id="VG-2.2" blocking="true">
Prerequisites: VG-2.1 PASSED
Execute:
```bash
python -c "
from pathlib import Path
from acli.core.orchestrator_v2 import EnhancedOrchestrator
import tempfile

# Verify class exists with all required methods
orch_methods = [
    'run', 'run_loop', 'route_prompt', 'run_analyst', 'run_planner',
    'run_implementer', 'run_validator', 'run_reporter',
    'request_pause', 'request_stop', 'resume', 'get_status'
]

with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    (p / 'app_spec.txt').write_text('Test')
    orch = EnhancedOrchestrator(project_dir=p)
    
    for method in orch_methods:
        assert hasattr(orch, method), f'Missing method: {method}'
    print(f'All {len(orch_methods)} methods: PASS')
    
    # Verify status structure
    status = orch.get_status()
    assert 'running' in status
    assert 'model' in status
    assert 'project_dir' in status
    print('Status structure: PASS')
    
    # Verify pause/resume/stop don't crash
    orch.request_pause()
    orch.resume()
    orch.request_stop()
    print('Control methods: PASS')

# Verify v1 preserved
from acli.core.orchestrator_v1 import AgentOrchestrator as V1Orchestrator
print('V1 orchestrator preserved: PASS')

# Verify CLI still imports correctly
from acli.cli import app
print('CLI import: PASS')

print('ALL ORCHESTRATOR V2: PASS')
" 2>&1 | tee evidence/vg2.2-orchestrator.txt
```
Pass criteria:
- EnhancedOrchestrator has all 12 required methods
- Status returns dict with expected keys
- Control methods don't crash
- V1 orchestrator preserved and importable
- CLI still imports without error
Review: `cat evidence/vg2.2-orchestrator.txt` — confirm 5 PASS + final "ALL ORCHESTRATOR V2: PASS"
Verdict: PASS → proceed to 2.3 | FAIL → fix orchestrator_v2 → re-run
Mock guard: No mocking the SDK client — real instantiation (just not calling API)
</validation_gate>

---

<task id="2.3">
## Task 2.3: Create Skill Engine with Auto-Detection

Create `src/acli/integration/skill_engine.py`:

```python
class SkillEngine:
    """
    Auto-detects and loads relevant skills for each agent type and task context.
    
    Scans available skills directories and matches against:
    - Agent type (validator → functional-validation)
    - Project platform (iOS → ios-validation-runner)
    - Task type (planning → create-validation-plan)
    - Technology keywords (ElevenLabs → elevenlabs skill)
    """
    
    AGENT_SKILL_MAP: dict[str, list[str]] = {
        "validator": ["functional-validation"],
        "planner": ["create-validation-plan", "create-plans"],
        "implementer": ["python-agent-sdk"],
    }
    
    PLATFORM_SKILL_MAP: dict[str, list[str]] = {
        "ios": ["ios-validation-runner"],
    }
    
    KEYWORD_SKILL_MAP: dict[str, list[str]] = {
        "elevenlabs": ["elevenlabs"],
        "prompt": ["optimize-prompt", "prompt-engineering-expert"],
    }
    
    def __init__(self, skills_dirs: list[Path] | None = None): ...
    def discover_skills(self) -> list[str]: ...
    def get_skills_for_agent(self, agent_type: str, platform: str = "", task_context: str = "") -> list[str]: ...
    def load_skill_content(self, skill_name: str) -> str | None: ...
    def get_combined_skill_prompt(self, skill_names: list[str]) -> str: ...
```

Files: `src/acli/integration/skill_engine.py`
</task>

<validation_gate id="VG-2.3" blocking="true">
Prerequisites: VG-2.2 PASSED
Execute:
```bash
python -c "
from acli.integration.skill_engine import SkillEngine

engine = SkillEngine()

# Test skill mapping for validator
validator_skills = engine.get_skills_for_agent('validator')
assert 'functional-validation' in validator_skills, f'Validator should include functional-validation, got {validator_skills}'
print(f'Validator skills ({len(validator_skills)}): PASS')

# Test skill mapping for planner
planner_skills = engine.get_skills_for_agent('planner')
assert 'create-validation-plan' in planner_skills or 'create-plans' in planner_skills, f'Planner should include planning skills, got {planner_skills}'
print(f'Planner skills ({len(planner_skills)}): PASS')

# Test platform-specific skill injection
ios_skills = engine.get_skills_for_agent('validator', platform='ios')
# Should include both base validator skills AND ios-specific
assert 'functional-validation' in ios_skills, 'Should include base skill'
print(f'iOS validator skills ({len(ios_skills)}): PASS')

# Test keyword detection
prompt_skills = engine.get_skills_for_agent('implementer', task_context='Create an ElevenLabs TTS integration')
# Should detect 'elevenlabs' keyword
has_elevenlabs = any('elevenlabs' in s for s in prompt_skills)
print(f'Keyword detection (elevenlabs={has_elevenlabs}): PASS')

print('ALL SKILL ENGINE: PASS')
" 2>&1 | tee evidence/vg2.3-skills.txt
```
Pass criteria:
- Validator gets `functional-validation`
- Planner gets planning skills
- iOS platform adds ios-specific skills
- Keyword detection finds relevant skills from task context
Review: `cat evidence/vg2.3-skills.txt` — confirm 4 PASS + final "ALL SKILL ENGINE: PASS"
Verdict: PASS → proceed to 2.4 | FAIL → fix skill_engine.py → re-run
Mock guard: No mocking skill discovery — real file system scan (even if no skills found)
</validation_gate>

---

<task id="2.4">
## Task 2.4: Add JSONL Session Logging

Extend `src/acli/core/session.py`:

1. Add `SessionLogger` class that writes JSONL to `.acli/sessions/`:
```python
class SessionLogger:
    """
    Writes agent session events to JSONL files.
    Matches Claude Code's native session format for compatibility.
    """
    
    def __init__(self, project_dir: Path, session_id: str): ...
    def log_event(self, event_type: str, data: dict) -> None: ...
    def close(self) -> None: ...
    
    @staticmethod
    def list_sessions(project_dir: Path) -> list[dict]: ...
    
    @staticmethod
    def load_session(project_dir: Path, session_id: str) -> list[dict]: ...
```

2. Each event is a JSON line:
```jsonl
{"type":"session_start","session_id":"s_001","agent_type":"analyst","model":"claude-opus-4-6","timestamp":"2026-03-18T14:00:00Z"}
{"type":"tool_use","tool":"Bash","input":{"command":"ls -la"},"duration_ms":120,"timestamp":"..."}
{"type":"assistant_text","text":"Analyzing...","tokens":42,"timestamp":"..."}
{"type":"decision","key":"architecture","value":"FastAPI REST API","confidence":0.95,"timestamp":"..."}
{"type":"session_end","session_id":"s_001","status":"completed","duration_s":180,"timestamp":"..."}
```

3. Wire into StreamingHandler — every event that goes through the handler also gets logged to JSONL

Files: `src/acli/core/session.py`
</task>

<validation_gate id="VG-2.4" blocking="true">
Prerequisites: VG-2.3 PASSED
Execute:
```bash
python -c "
from pathlib import Path
from acli.core.session import SessionLogger
import tempfile, json

with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    (p / '.acli' / 'sessions').mkdir(parents=True)
    
    # Create and log events
    logger = SessionLogger(p, 's_001')
    logger.log_event('session_start', {'agent_type': 'analyst', 'model': 'claude-opus-4-6'})
    logger.log_event('tool_use', {'tool': 'Bash', 'input': {'command': 'ls'}, 'duration_ms': 50})
    logger.log_event('assistant_text', {'text': 'Analyzing...', 'tokens': 42})
    logger.log_event('session_end', {'status': 'completed', 'duration_s': 60})
    logger.close()
    
    # Verify JSONL file exists
    session_files = list((p / '.acli' / 'sessions').glob('*.jsonl'))
    assert len(session_files) > 0, 'No JSONL session file created'
    
    # Read and verify content
    with open(session_files[0]) as f:
        lines = [json.loads(line) for line in f if line.strip()]
    
    assert len(lines) == 4, f'Expected 4 events, got {len(lines)}'
    assert lines[0]['type'] == 'session_start'
    assert lines[-1]['type'] == 'session_end'
    assert all('timestamp' in line for line in lines), 'All events should have timestamps'
    print(f'JSONL logging ({len(lines)} events): PASS')
    
    # Verify list_sessions
    sessions = SessionLogger.list_sessions(p)
    assert len(sessions) >= 1, 'Should list at least 1 session'
    print(f'Session listing ({len(sessions)} sessions): PASS')
    
    # Verify load_session
    loaded = SessionLogger.load_session(p, 's_001')
    assert len(loaded) == 4, f'Loaded session should have 4 events, got {len(loaded)}'
    print('Session loading: PASS')

print('ALL SESSION LOGGING: PASS')
" 2>&1 | tee evidence/vg2.4-sessions.txt
```
Pass criteria:
- JSONL file created with 4 events
- Events have correct types and timestamps
- list_sessions returns non-empty list
- load_session returns all 4 events
Review: `cat evidence/vg2.4-sessions.txt` — confirm 3 PASS + final "ALL SESSION LOGGING: PASS"
Verdict: PASS → proceed to Phase 2 Gate | FAIL → fix session.py → re-run
Mock guard: Real file I/O with temp directory — no mocking
</validation_gate>

---

<phase_gate id="PG-2" blocking="true">
## Phase 2 Gate — Agent Architecture Cumulative Validation

Prerequisites: PG-1 PASSED, VG-2.1 through VG-2.4 all PASSED

Execute:
```bash
python -c "
# Phase 1 regression check
from acli.core.client import MODEL_OPUS, MODEL_SONNET
from acli.core.streaming import EventType
from acli.routing.router import PromptRouter
from acli.context.store import ContextStore
from acli.context.memory import MemoryManager

# Phase 2 checks
from acli.agents.definitions import AgentType, AgentDefinition
from acli.agents.factory import AgentFactory
from acli.core.orchestrator_v2 import EnhancedOrchestrator
from acli.integration.skill_engine import SkillEngine
from acli.core.session import SessionLogger

# Verify full chain: Router → AgentDefinition → Factory
from acli.routing.workflows import WorkflowType
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    (p / 'app_spec.txt').write_text('Build a todo app')
    
    # Router classifies
    router = PromptRouter()
    workflow = router.classify('Build a todo app', p)
    assert workflow.workflow_type == WorkflowType.GREENFIELD_APP
    
    # Agent definition for planner
    planner_def = AgentDefinition.for_type(AgentType.PLANNER)
    assert 'opus' in planner_def.model
    
    # Orchestrator creates
    orch = EnhancedOrchestrator(project_dir=p)
    status = orch.get_status()
    assert isinstance(status, dict)
    
    # Skill engine detects
    engine = SkillEngine()
    skills = engine.get_skills_for_agent('validator')
    assert len(skills) > 0
    
    print('FULL CHAIN: Router → Definition → Factory → Orchestrator → Skills: PASS')

print('PHASE 2 GATE: ALL PASS')
" 2>&1 | tee evidence/pg2-cumulative.txt
```
Pass criteria: Full import chain works, classification → definition → orchestrator → skills, no regressions from Phase 1
Review: `cat evidence/pg2-cumulative.txt` — confirm "PHASE 2 GATE: ALL PASS"
Verdict: PASS → proceed to Phase 3 | FAIL → identify regression → fix → re-run
</phase_gate>

---

# PHASE 3: Validation Engine — Iron Rule Enforcement

**Objective**: Build the validation engine with evidence collection, platform-specific validators, mock detection hook, and phase gate logic.

**New files:**
- `src/acli/validation/__init__.py`
- `src/acli/validation/engine.py`
- `src/acli/validation/evidence.py`
- `src/acli/validation/gates.py`
- `src/acli/validation/mock_detector.py`
- `src/acli/validation/platforms/` (ios.py, web.py, api.py, cli.py, generic.py)

---

<task id="3.1">
## Task 3.1: Create Mock Detector Hook

Create `src/acli/validation/mock_detector.py`:

```python
import re

MOCK_PATTERNS = [
    r"mock\.", r"Mock\(", r"unittest\.mock", r"from unittest import mock",
    r"jest\.mock", r"jest\.fn", r"sinon\.", r"nock\(",
    r"@Mock", r"Mockito\.", r"@patch",
    r"\.stub\(", r"\.fake\(", r"monkeypatch",
    r"in.memory.*database", r":memory:", r"mongomock",
    r"TEST_MODE", r"test_mode", r"TESTING\s*=\s*[Tt]rue",
    r"\.test\.\w+$", r"\.spec\.\w+$", r"_test\.\w+$", r"test_\w+\.\w+$",
]

async def mock_detection_hook(input_data: dict, tool_use_id=None, context=None) -> dict:
    """
    Pre-tool-use hook that blocks creation of mock/stub/test code.
    
    Scans Write and Edit tool inputs for mock patterns.
    Returns block decision if pattern found.
    """

def scan_content_for_mocks(content: str) -> list[str]:
    """Scan content and return list of detected mock patterns."""

def scan_file_path_for_test(path: str) -> bool:
    """Check if file path matches test file patterns."""
```

Wire into the security hooks in `src/acli/core/client.py` — add `mock_detection_hook` to PreToolUse hooks for Write and Edit tools.

Files: `src/acli/validation/mock_detector.py`, `src/acli/core/client.py` (update hooks)
</task>

<validation_gate id="VG-3.1" blocking="true">
Prerequisites: Phase 2 Gate PASSED
Execute:
```bash
python -c "
from acli.validation.mock_detector import scan_content_for_mocks, scan_file_path_for_test

# Test pattern detection in content
mock_samples = [
    ('from unittest.mock import Mock', True),
    ('mock.patch(\"module.func\")', True),
    ('@patch(\"requests.get\")', True),
    ('jest.mock(\"./module\")', True),
    ('const db = new SQLite(:memory:)', True),
    ('TEST_MODE = True', True),
    ('def calculate(a, b): return a + b', False),
    ('import json', False),
    ('class UserService:', False),
]

passed = 0
for content, should_detect in mock_samples:
    patterns = scan_content_for_mocks(content)
    detected = len(patterns) > 0
    if detected == should_detect:
        passed += 1
    else:
        print(f'MISMATCH: \"{content[:40]}\" expected={should_detect} got={detected}')

print(f'Content detection: {passed}/{len(mock_samples)} correct')
assert passed >= 7, f'At least 7/9 should be correct, got {passed}'
print('Content detection: PASS')

# Test file path detection
path_samples = [
    ('test_auth.py', True),
    ('auth.test.ts', True),
    ('AuthTests.swift', True),
    ('auth_test.go', True),
    ('auth.py', False),
    ('src/services/auth.ts', False),
]

path_passed = 0
for path, should_detect in path_samples:
    detected = scan_file_path_for_test(path)
    if detected == should_detect:
        path_passed += 1

print(f'Path detection: {path_passed}/{len(path_samples)} correct')
assert path_passed >= 5, f'At least 5/6 should be correct'
print('Path detection: PASS')

print('ALL MOCK DETECTOR: PASS')
" 2>&1 | tee evidence/vg3.1-mocks.txt
```
Pass criteria:
- At least 7/9 content samples correctly classified
- At least 5/6 path samples correctly classified
Review: `cat evidence/vg3.1-mocks.txt` — confirm PASS lines
Verdict: PASS → proceed to 3.2 | FAIL → fix patterns → re-run
Mock guard: Ironic but correct — we're testing mock DETECTION, not using mocks
</validation_gate>

---

<task id="3.2">
## Task 3.2: Create Evidence Collector & Validation Engine

Create `src/acli/validation/evidence.py`:
```python
class EvidenceCollector:
    """Captures, saves, and catalogs validation evidence."""
    
    def __init__(self, evidence_dir: Path): ...
    def save_text(self, name: str, content: str) -> Path: ...
    def save_json(self, name: str, data: dict) -> Path: ...
    def save_command_output(self, name: str, command: str) -> tuple[Path, int]: ...  # Returns (path, exit_code)
    def list_evidence(self) -> list[dict]: ...
    def get_evidence(self, name: str) -> str | None: ...
```

Create `src/acli/validation/gates.py`:
```python
@dataclass
class GateCriterion:
    description: str
    check_command: str  # Shell command that exits 0 on pass
    evidence_name: str

@dataclass
class ValidationGate:
    gate_id: str
    task_id: str
    criteria: list[GateCriterion]
    blocking: bool = True

@dataclass  
class GateResult:
    gate_id: str
    status: str  # "PASS" or "FAIL"
    criteria_results: list[dict]  # {criterion, passed, evidence_path}
    timestamp: datetime

class GateRunner:
    """Executes validation gates with evidence collection and review."""
    
    def __init__(self, evidence_collector: EvidenceCollector, streaming: StreamingHandler): ...
    async def run_gate(self, gate: ValidationGate) -> GateResult: ...
    async def run_phase_gate(self, phase_gates: list[ValidationGate]) -> GateResult: ...
```

Create `src/acli/validation/engine.py`:
```python
class ValidationEngine:
    """
    Orchestrates validation across the entire build.
    
    Manages:
    - Per-task validation gates
    - Per-phase cumulative gates
    - Evidence directory management
    - PASS/FAIL tracking with streaming events
    """
    
    def __init__(self, project_dir: Path, streaming: StreamingHandler): ...
    async def validate_task(self, task: dict, implementation_result: str) -> GateResult: ...
    async def validate_phase(self, phase: dict) -> GateResult: ...
    def get_all_results(self) -> list[GateResult]: ...
    def get_phase_summary(self) -> dict: ...
```

Files: `src/acli/validation/__init__.py`, `src/acli/validation/evidence.py`, `src/acli/validation/gates.py`, `src/acli/validation/engine.py`
</task>

<validation_gate id="VG-3.2" blocking="true">
Prerequisites: VG-3.1 PASSED
Execute:
```bash
python -c "
from pathlib import Path
from acli.validation.evidence import EvidenceCollector
from acli.validation.gates import GateCriterion, ValidationGate, GateRunner, GateResult
from acli.validation.engine import ValidationEngine
import tempfile

# Test EvidenceCollector
with tempfile.TemporaryDirectory() as td:
    evidence_dir = Path(td) / 'evidence'
    collector = EvidenceCollector(evidence_dir)
    
    # Save text evidence
    path = collector.save_text('test-output', 'Hello World\nExit: 0')
    assert path.exists(), 'Text evidence file not created'
    assert path.read_text() == 'Hello World\nExit: 0'
    print('Evidence save_text: PASS')
    
    # Save JSON evidence
    path = collector.save_json('test-response', {'status': 200, 'body': {'id': 1}})
    assert path.exists(), 'JSON evidence file not created'
    print('Evidence save_json: PASS')
    
    # Save command output (real command)
    path, exit_code = collector.save_command_output('echo-test', 'echo hello')
    assert path.exists(), 'Command output file not created'
    assert exit_code == 0, f'Expected exit 0, got {exit_code}'
    content = path.read_text()
    assert 'hello' in content, f'Expected hello in output, got {content}'
    print('Evidence save_command_output: PASS')
    
    # List evidence
    all_evidence = collector.list_evidence()
    assert len(all_evidence) >= 3, f'Expected >= 3 evidence files, got {len(all_evidence)}'
    print(f'Evidence listing ({len(all_evidence)} files): PASS')

# Test GateCriterion and ValidationGate data structures
criterion = GateCriterion(
    description='Echo exits 0',
    check_command='echo hello',
    evidence_name='echo-test'
)
gate = ValidationGate(
    gate_id='VG-TEST',
    task_id='T-1',
    criteria=[criterion],
    blocking=True
)
assert gate.blocking == True
assert len(gate.criteria) == 1
print('Gate data structures: PASS')

# Test ValidationEngine imports
engine = ValidationEngine.__new__(ValidationEngine)
assert hasattr(engine, 'validate_task')
assert hasattr(engine, 'validate_phase')
assert hasattr(engine, 'get_all_results')
print('ValidationEngine interface: PASS')

print('ALL VALIDATION ENGINE: PASS')
" 2>&1 | tee evidence/vg3.2-engine.txt
```
Pass criteria:
- EvidenceCollector: creates files for text, JSON, command output; lists evidence
- Command output captures real `echo hello` with exit 0
- Gate data structures create correctly
- ValidationEngine has required interface
Review: `cat evidence/vg3.2-engine.txt` — confirm 6 PASS + final
Verdict: PASS → proceed to 3.3 | FAIL → fix validation module → re-run
Mock guard: Uses REAL `echo hello` command — not a mock
</validation_gate>

---

<task id="3.3">
## Task 3.3: Create Platform-Specific Validators

Create `src/acli/validation/platforms/` package with validators for each platform:

**`api.py`** — API validation:
```python
class APIValidator:
    """Validates API endpoints via curl against running servers."""
    async def validate_endpoint(self, url: str, method: str, body: dict | None, expected_status: int, evidence_dir: Path) -> dict: ...
    async def health_check_poll(self, url: str, timeout: int = 60) -> bool: ...
```

**`cli.py`** — CLI validation:
```python
class CLIValidator:
    """Validates CLI tools via binary/module execution."""
    async def validate_command(self, command: str, expected_exit: int, expected_output: str | None, evidence_dir: Path) -> dict: ...
```

**`web.py`** — Web frontend validation:
```python
class WebValidator:
    """Validates web frontends via Playwright screenshots."""
    async def validate_page(self, url: str, selector: str, evidence_dir: Path) -> dict: ...
```

**`ios.py`** — iOS validation:
```python
class IOSValidator:
    """Validates iOS apps via simulator screenshots."""
    async def validate_screen(self, scheme: str, bundle_id: str, evidence_dir: Path) -> dict: ...
```

**`generic.py`** — Generic validation:
```python
class GenericValidator:
    """Fallback validator for untyped platforms."""
    async def validate(self, command: str, evidence_dir: Path) -> dict: ...
```

Each validator returns a dict: `{"status": "PASS"|"FAIL", "evidence_path": str, "details": str}`

Files: `src/acli/validation/platforms/__init__.py`, `api.py`, `cli.py`, `web.py`, `ios.py`, `generic.py`
</task>

<validation_gate id="VG-3.3" blocking="true">
Prerequisites: VG-3.2 PASSED
Execute:
```bash
python -c "
from acli.validation.platforms.api import APIValidator
from acli.validation.platforms.cli import CLIValidator
from acli.validation.platforms.web import WebValidator
from acli.validation.platforms.ios import IOSValidator
from acli.validation.platforms.generic import GenericValidator
import asyncio
from pathlib import Path
import tempfile

# Test CLIValidator with real command
async def test_cli():
    with tempfile.TemporaryDirectory() as td:
        validator = CLIValidator()
        result = await validator.validate_command(
            command='echo VALIDATION_TEST',
            expected_exit=0,
            expected_output='VALIDATION_TEST',
            evidence_dir=Path(td)
        )
        assert result['status'] == 'PASS', f'CLI validation failed: {result}'
        assert Path(result['evidence_path']).exists(), 'Evidence file not created'
        return result

result = asyncio.run(test_cli())
print(f'CLIValidator (real echo): {result[\"status\"]}')

# Test GenericValidator with real command
async def test_generic():
    with tempfile.TemporaryDirectory() as td:
        validator = GenericValidator()
        result = await validator.validate(
            command='python -c \"print(42)\"',
            evidence_dir=Path(td)
        )
        assert result['status'] == 'PASS', f'Generic validation failed: {result}'
        return result

result = asyncio.run(test_generic())
print(f'GenericValidator (real python): {result[\"status\"]}')

# Verify all validators have required interface
for cls in [APIValidator, CLIValidator, WebValidator, IOSValidator, GenericValidator]:
    instance = cls.__new__(cls)
    assert any(hasattr(instance, m) for m in ['validate', 'validate_command', 'validate_endpoint', 'validate_page', 'validate_screen']), f'{cls.__name__} missing validate method'

print('ALL PLATFORM VALIDATORS: PASS')
" 2>&1 | tee evidence/vg3.3-platforms.txt
```
Pass criteria:
- CLIValidator executes real `echo VALIDATION_TEST`, captures evidence, returns PASS
- GenericValidator executes real `python -c "print(42)"`, returns PASS
- All 5 validator classes have validate-type methods
Review: `cat evidence/vg3.3-platforms.txt` — confirm 3 PASS lines
Verdict: PASS → proceed to Phase 3 Gate | FAIL → fix validators → re-run
Mock guard: Uses REAL echo and python commands — not mocks
</validation_gate>

---

<phase_gate id="PG-3" blocking="true">
## Phase 3 Gate — Validation Engine Cumulative

Prerequisites: PG-1 PASSED, PG-2 PASSED, VG-3.1 through VG-3.3 all PASSED

Execute:
```bash
python -c "
# Phase 1+2 regression
from acli.core.client import MODEL_OPUS, MODEL_SONNET
from acli.core.streaming import EventType
from acli.routing.router import PromptRouter
from acli.context.store import ContextStore
from acli.agents.definitions import AgentType
from acli.core.orchestrator_v2 import EnhancedOrchestrator

# Phase 3 checks
from acli.validation.mock_detector import scan_content_for_mocks
from acli.validation.evidence import EvidenceCollector
from acli.validation.gates import GateRunner, ValidationGate
from acli.validation.engine import ValidationEngine
from acli.validation.platforms.cli import CLIValidator
from acli.validation.platforms.api import APIValidator
import asyncio
from pathlib import Path
import tempfile

# End-to-end: create evidence, run CLI validation, check result
async def e2e():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        validator = CLIValidator()
        result = await validator.validate_command(
            command='python -c \"import json; print(json.dumps({\\\"test\\\": True}))\"',
            expected_exit=0,
            expected_output='test',
            evidence_dir=p
        )
        assert result['status'] == 'PASS', f'E2E failed: {result}'
        print('E2E CLI validation: PASS')
        
        # Mock detector catches mock code
        patterns = scan_content_for_mocks('from unittest.mock import Mock')
        assert len(patterns) > 0, 'Should detect mock pattern'
        print('Mock detector: PASS')

asyncio.run(e2e())
print('PHASE 3 GATE: ALL PASS')
" 2>&1 | tee evidence/pg3-cumulative.txt
```
Pass criteria: Full import chain, E2E CLI validation with real Python command, mock detector catches patterns
Review: `cat evidence/pg3-cumulative.txt` — confirm "PHASE 3 GATE: ALL PASS"
Verdict: PASS → proceed to Phase 4 | FAIL → identify regression → fix → re-run
</phase_gate>

---

# PHASE 4: Enhanced TUI — Full Visibility

**Objective**: Add 3 new TUI panels (Context Explorer, Validation Gates, Prompt Input), update the agent graph for multi-agent types, and extend the cyberpunk theme.

**Modified files:**
- `src/acli/tui/widgets.py` — 3 new widget classes
- `src/acli/tui/app.py` — 7-panel layout, new keybindings
- `src/acli/tui/bridge.py` — context store + validation engine connections
- `src/acli/tui/cyberpunk.tcss` — styles for new panels

**New files:**
- `src/acli/tui/prompt_input.py` — Inline prompt widget

---

<task id="4.1">
## Task 4.1: Create New TUI Widgets

Read existing `src/acli/tui/widgets.py` (589 lines). Add 3 new widget classes following existing patterns:

**ContextExplorer** — Shows detected tech stack, file count, LOC, memory facts:
```python
class ContextExplorer(Widget):
    """Displays project context from ContextStore and MemoryManager."""
    def compose(self) -> ComposeResult: ...
    def refresh_context(self) -> None: ...
```

**ValidationGatePanel** — Shows phase/task gates with PASS/FAIL/RUNNING/PENDING:
```python
class ValidationGatePanel(Widget):
    """Displays validation gate status for all phases and tasks."""
    def compose(self) -> ComposeResult: ...
    def update_gate(self, gate_id: str, status: str) -> None: ...
    def refresh_gates(self) -> None: ...
```

**PromptInput** — Inline text input for sending new tasks:
```python
class PromptInput(Widget):
    """Inline prompt input at bottom of TUI for sending new tasks."""
    def compose(self) -> ComposeResult: ...
    def on_input_submitted(self, event) -> None: ...
```

Follow the existing widget patterns:
- Inherit from Widget
- Use `compose()` for layout
- Use Static/RichLog for content
- Read data from OrchestratorBridge
- Style with cyberpunk theme CSS classes

Files: `src/acli/tui/widgets.py`, `src/acli/tui/prompt_input.py`
</task>

<validation_gate id="VG-4.1" blocking="true">
Prerequisites: Phase 3 Gate PASSED
Execute:
```bash
python -c "
from acli.tui.widgets import ContextExplorer, ValidationGatePanel
from acli.tui.prompt_input import PromptInput

# Verify widgets have compose methods (Textual requirement)
for widget_cls in [ContextExplorer, ValidationGatePanel, PromptInput]:
    assert hasattr(widget_cls, 'compose'), f'{widget_cls.__name__} missing compose()'
    print(f'{widget_cls.__name__}.compose: exists')

# Verify ContextExplorer has refresh method
assert hasattr(ContextExplorer, 'refresh_context'), 'Missing refresh_context'
print('ContextExplorer.refresh_context: exists')

# Verify ValidationGatePanel has update and refresh
assert hasattr(ValidationGatePanel, 'update_gate'), 'Missing update_gate'
assert hasattr(ValidationGatePanel, 'refresh_gates'), 'Missing refresh_gates'
print('ValidationGatePanel.update_gate + refresh_gates: exists')

# Verify PromptInput has submission handler
assert hasattr(PromptInput, 'on_input_submitted') or hasattr(PromptInput, '_on_input_submitted'), 'Missing input handler'
print('PromptInput.on_input_submitted: exists')

print('ALL NEW TUI WIDGETS: PASS')
" 2>&1 | tee evidence/vg4.1-widgets.txt
```
Pass criteria:
- All 3 widget classes exist and have compose()
- ContextExplorer has refresh_context
- ValidationGatePanel has update_gate and refresh_gates
- PromptInput has submission handler
Review: `cat evidence/vg4.1-widgets.txt` — confirm PASS
Verdict: PASS → proceed to 4.2 | FAIL → fix widgets → re-run
Mock guard: Testing real class structure — no mocking Textual
</validation_gate>

---

<task id="4.2">
## Task 4.2: Update TUI App Layout & Bridge

Read `src/acli/tui/app.py` and `src/acli/tui/bridge.py`.

**app.py changes:**
1. Add new widgets to `compose()` — 7-panel layout:
   - Left: AgentGraph + AgentDetail + ContextExplorer
   - Right: LogStream + ValidationGatePanel + StatsPanel
   - Bottom: PromptInput
2. Add new keybindings: `/` (prompt focus), `v` (validation view), `c` (context view)
3. Wire new widgets into `_refresh_all_widgets()`
4. Handle PROMPT_RECEIVED events from PromptInput → orchestrator

**bridge.py changes:**
1. Add ContextStore connection for ContextExplorer data
2. Add ValidationEngine connection for gate status data
3. Add `context_summary` and `gate_results` properties to `OrchestratorSnapshot`
4. Handle new event types (GATE_START, GATE_RESULT, CONTEXT_UPDATE, MEMORY_UPDATE)

**cyberpunk.tcss changes:**
1. Add styles for ContextExplorer, ValidationGatePanel, PromptInput
2. Gate status colors: PASS=#00ff41, FAIL=#ff003c, RUNNING=#0abdc6, PENDING=#4a6670

Files: `src/acli/tui/app.py`, `src/acli/tui/bridge.py`, `src/acli/tui/cyberpunk.tcss`
</task>

<validation_gate id="VG-4.2" blocking="true">
Prerequisites: VG-4.1 PASSED
Execute:
```bash
python -c "
# Verify TUI app imports without error (catches broken compose layout)
from acli.tui.app import AgentMonitorApp
from acli.tui.bridge import OrchestratorBridge, OrchestratorSnapshot

# Verify new snapshot fields
snap = OrchestratorSnapshot()
assert hasattr(snap, 'context_summary') or hasattr(snap, 'gate_results'), 'Snapshot should have new fields'
print('Snapshot fields: PASS')

# Verify new bindings in app
app = AgentMonitorApp.__new__(AgentMonitorApp)
binding_keys = [b.key for b in AgentMonitorApp.BINDINGS]
new_keys_present = any(k in binding_keys for k in ['slash', '/', 'v', 'c'])
print(f'New keybindings present: {new_keys_present}')

# Verify CSS file has new widget styles
from pathlib import Path
css_path = Path('src/acli/tui/cyberpunk.tcss')
if css_path.exists():
    css_content = css_path.read_text()
    has_context = 'ContextExplorer' in css_content or 'context-explorer' in css_content
    has_gates = 'ValidationGatePanel' in css_content or 'validation-gate' in css_content
    has_prompt = 'PromptInput' in css_content or 'prompt-input' in css_content
    print(f'CSS: context={has_context} gates={has_gates} prompt={has_prompt}')
else:
    print('CSS file not found at expected path')

# Verify bridge handles new event types
bridge = OrchestratorBridge.__new__(OrchestratorBridge)
assert hasattr(bridge, 'handle_event'), 'Bridge must have handle_event'
print('Bridge interface: PASS')

print('ALL TUI UPDATES: PASS')
" 2>&1 | tee evidence/vg4.2-tui.txt
```
Pass criteria:
- AgentMonitorApp imports without error
- OrchestratorSnapshot has new fields
- New keybindings present in BINDINGS
- CSS file contains styles for new widgets
- Bridge has handle_event method
Review: `cat evidence/vg4.2-tui.txt` — confirm PASS
Verdict: PASS → proceed to Phase 4 Gate | FAIL → fix TUI → re-run
Mock guard: Real imports, real file reads — no mocking Textual framework
</validation_gate>

---

<phase_gate id="PG-4" blocking="true">
## Phase 4 Gate — TUI Cumulative

Prerequisites: PG-1 through PG-3 PASSED, VG-4.1 and VG-4.2 PASSED

Execute:
```bash
python -c "
# Full regression: imports from ALL phases
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

# Verify CLI entry point still works (doesn't crash on import)
from acli.cli import app as cli_app
print('CLI import: PASS')

print('PHASE 4 GATE: ALL PASS — Full import chain from every phase')
" 2>&1 | tee evidence/pg4-cumulative.txt
```
Pass criteria: Every module from every phase imports without error
Review: `cat evidence/pg4-cumulative.txt` — confirm "PHASE 4 GATE: ALL PASS"
Verdict: PASS → proceed to Phase 5 | FAIL → identify broken import → fix → re-run
</phase_gate>

---

# PHASE 5: CLI Integration & Session Management

**Objective**: Update CLI commands, add new commands (onboard, prompt, validate, session, memory), wire everything together.

---

<task id="5.1">
## Task 5.1: Update CLI Commands & Add New Commands

Read `src/acli/cli.py`. Update and add commands:

1. **Update `run` command**: Accept `--prompt` option for arbitrary task text
2. **Update `init` command**: Add `--onboard` flag for brownfield projects
3. **Update `monitor` command**: Pass context/validation data to TUI
4. **Add `onboard` command**: Explicit brownfield onboarding
5. **Add `prompt` command**: Send single task without TUI
6. **Add `validate` command**: Run validation gates only
7. **Add `session` command**: `list`, `resume`, `replay` subcommands
8. **Add `memory` command**: `list`, `add`, `clear` subcommands
9. **Add `context` command**: Show/manage context store

Update default model strings to `claude-sonnet-4-6` everywhere.

Files: `src/acli/cli.py`
</task>

<validation_gate id="VG-5.1" blocking="true">
Prerequisites: Phase 4 Gate PASSED
Execute:
```bash
# Test CLI commands exist and show help
python -m acli --help 2>&1 | tee evidence/vg5.1-help.txt

# Verify new commands are registered
python -c "
from acli.cli import app
from typer.testing import CliRunner
runner = CliRunner()

# Test --help for each command (should not error)
commands = ['init', 'run', 'monitor', 'status', 'enhance', 'config', 'list-skills',
            'onboard', 'prompt', 'validate', 'session', 'memory', 'context']
for cmd in commands:
    result = runner.invoke(app, [cmd, '--help'])
    status = 'OK' if result.exit_code == 0 else f'FAIL({result.exit_code})'
    print(f'{cmd} --help: {status}')

# Verify model strings updated
import subprocess
old_refs = subprocess.run(['grep', '-r', 'claude-sonnet-4-20250514', 'src/acli/cli.py'], capture_output=True, text=True)
assert old_refs.stdout.strip() == '', f'Old model string in cli.py: {old_refs.stdout}'
print('No stale model strings in cli.py: PASS')

print('ALL CLI COMMANDS: PASS')
" 2>&1 | tee evidence/vg5.1-cli.txt
```
Pass criteria:
- `acli --help` shows all commands (exit 0)
- All 13 commands respond to `--help` without error
- No stale model strings in cli.py
Review: `cat evidence/vg5.1-cli.txt` — confirm all "OK" + final PASS
Verdict: PASS → proceed to Phase 5 Gate | FAIL → fix CLI → re-run
Mock guard: Using real CliRunner from typer — real invocation
</validation_gate>

---

<phase_gate id="PG-5" blocking="true">
## Phase 5 Gate — CLI & Session Cumulative

Prerequisites: PG-1 through PG-4 PASSED, VG-5.1 PASSED

Execute:
```bash
# Full system test: init a project and verify structure
python -c "
import subprocess, json, tempfile, os
from pathlib import Path

with tempfile.TemporaryDirectory() as td:
    project_dir = Path(td) / 'test_project'
    
    # Run acli init
    result = subprocess.run(
        ['python', '-m', 'acli', 'init', str(project_dir)],
        capture_output=True, text=True, cwd=td
    )
    print(f'acli init exit: {result.returncode}')
    
    if project_dir.exists():
        # Verify expected files
        expected = ['app_spec.txt', '.gitignore']
        for f in expected:
            exists = (project_dir / f).exists()
            print(f'  {f}: {\"exists\" if exists else \"MISSING\"}')
        
        # Verify acli status works
        result2 = subprocess.run(
            ['python', '-m', 'acli', 'status', str(project_dir)],
            capture_output=True, text=True
        )
        print(f'acli status exit: {result2.returncode}')
    else:
        print(f'Project dir not created at {project_dir}')

print('PHASE 5 GATE: PASS')
" 2>&1 | tee evidence/pg5-cumulative.txt
```
Pass criteria: `acli init` creates project, `acli status` runs, expected files present
Review: `cat evidence/pg5-cumulative.txt`
Verdict: PASS → proceed to Phase 6 | FAIL → fix → re-run
</phase_gate>

---

# PHASE 6: Integration, Polish & Documentation

**Objective**: Wire everything end-to-end, update documentation, bump version, run final validation.

---

<task id="6.1">
## Task 6.1: End-to-End Integration & Documentation

1. Ensure `EnhancedOrchestrator` is the default in CLI (backwards compat with v1 TUI)
2. Update `CLAUDE.md` with v2 architecture, new commands, new module structure
3. Update `README.md` with v2 features
4. Update `docs/ARCHITECTURE.md` to reflect v2
5. Bump version in `pyproject.toml` to `2.0.0`
6. Update `src/acli/__init__.py` with new version
7. Verify `ruff check src/` passes (linting)
8. Verify `mypy src/acli/` passes (type checking) — or document known issues

Files: Multiple documentation files, pyproject.toml, __init__.py
</task>

<validation_gate id="VG-6.1" blocking="true">
Prerequisites: Phase 5 Gate PASSED
Execute:
```bash
# Lint check
ruff check src/ 2>&1 | tee evidence/vg6.1-lint.txt
echo "LINT_EXIT: $?" >> evidence/vg6.1-lint.txt

# Version check
python -c "from acli import __version__; print(f'Version: {__version__}')" 2>&1 | tee evidence/vg6.1-version.txt

# Full import chain (every module)
python -c "
import acli
from acli.core.client import MODEL_OPUS, MODEL_SONNET
from acli.core.streaming import EventType, StreamBuffer, StreamingHandler
from acli.core.orchestrator_v2 import EnhancedOrchestrator
from acli.core.session import SessionLogger, ProjectState
from acli.routing.router import PromptRouter
from acli.routing.workflows import WorkflowType, WorkflowConfig
from acli.context.store import ContextStore
from acli.context.memory import MemoryManager
from acli.context.chunker import KnowledgeChunker
from acli.context.onboarder import BrownfieldOnboarder
from acli.agents.definitions import AgentType, AgentDefinition
from acli.agents.factory import AgentFactory
from acli.validation.engine import ValidationEngine
from acli.validation.evidence import EvidenceCollector
from acli.validation.gates import GateRunner, ValidationGate, GateResult
from acli.validation.mock_detector import scan_content_for_mocks, mock_detection_hook
from acli.validation.platforms.api import APIValidator
from acli.validation.platforms.cli import CLIValidator
from acli.validation.platforms.web import WebValidator
from acli.validation.platforms.ios import IOSValidator
from acli.validation.platforms.generic import GenericValidator
from acli.integration.skill_engine import SkillEngine
from acli.tui.app import AgentMonitorApp
from acli.tui.widgets import ContextExplorer, ValidationGatePanel
from acli.tui.prompt_input import PromptInput
from acli.tui.bridge import OrchestratorBridge
from acli.cli import app as cli_app
from acli.spec.enhancer import enhance_spec
from acli.security.hooks import bash_security_hook

print(f'ALL {30}+ IMPORTS: PASS')
" 2>&1 | tee evidence/vg6.1-imports.txt
```
Pass criteria:
- `ruff check` exits 0 (or only warnings, no errors)
- Version is `2.0.0`
- All 30+ module imports succeed without error
Review: `cat evidence/vg6.1-lint.txt` | `cat evidence/vg6.1-version.txt` | `cat evidence/vg6.1-imports.txt`
Verdict: PASS → proceed to Final Gate | FAIL → fix issues → re-run
Mock guard: Real lint, real imports — no skipping
</validation_gate>

---

<phase_gate id="PG-FINAL" blocking="true">
## FINAL GATE — Complete System Validation

Prerequisites: ALL phase gates PG-1 through PG-5 PASSED, VG-6.1 PASSED

This gate validates the entire ACLI v2 system end-to-end with real execution.

Execute:
```bash
mkdir -p evidence/final

# 1. Fresh init
python -m acli init /tmp/acli_v2_test 2>&1 | tee evidence/final/01-init.txt
echo "EXIT: $?" >> evidence/final/01-init.txt

# 2. Status check
python -m acli status /tmp/acli_v2_test 2>&1 | tee evidence/final/02-status.txt
echo "EXIT: $?" >> evidence/final/02-status.txt

# 3. Verify router classifies correctly
python -c "
from acli.routing.router import PromptRouter
from acli.routing.workflows import WorkflowType
from pathlib import Path

router = PromptRouter()

# Greenfield
r1 = router.classify('Build a todo app', Path('/tmp/acli_v2_test'))
print(f'Greenfield: {r1.workflow_type}')

# Brownfield (simulate)
import tempfile
with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    for i in range(5):
        (p / f'mod{i}.py').write_text(f'x={i}')
    r2 = router.classify('Add auth', p)
    print(f'Brownfield: {r2.workflow_type}')

print('Router: PASS')
" 2>&1 | tee evidence/final/03-router.txt

# 4. Context store round-trip
python -c "
from acli.context.store import ContextStore
from acli.context.memory import MemoryManager
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    store = ContextStore(p)
    store.initialize()
    store.store_tech_stack({'language': 'Python'})
    assert store.get_tech_stack()['language'] == 'Python'
    
    mem = MemoryManager(p)
    mem.add_fact('test', 'ACLI v2 works')
    assert mem.fact_count == 1
    
    print('Context + Memory: PASS')
" 2>&1 | tee evidence/final/04-context.txt

# 5. Validation engine with real command
python -c "
from acli.validation.platforms.cli import CLIValidator
import asyncio
from pathlib import Path
import tempfile

async def test():
    with tempfile.TemporaryDirectory() as td:
        v = CLIValidator()
        r = await v.validate_command('python -c \"print(123)\"', 0, '123', Path(td))
        assert r['status'] == 'PASS', f'Failed: {r}'
        print(f'CLI Validation: {r[\"status\"]}')

asyncio.run(test())
" 2>&1 | tee evidence/final/05-validation.txt

# 6. Mock detector
python -c "
from acli.validation.mock_detector import scan_content_for_mocks
assert len(scan_content_for_mocks('from unittest.mock import Mock')) > 0
assert len(scan_content_for_mocks('def real_function(): pass')) == 0
print('Mock Detector: PASS')
" 2>&1 | tee evidence/final/06-mocks.txt

# 7. Session logging
python -c "
from acli.core.session import SessionLogger
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    (p / '.acli' / 'sessions').mkdir(parents=True)
    logger = SessionLogger(p, 'final_test')
    logger.log_event('test', {'data': 'final'})
    logger.close()
    sessions = SessionLogger.list_sessions(p)
    assert len(sessions) >= 1
    print('Session Logging: PASS')
" 2>&1 | tee evidence/final/07-sessions.txt

# 8. Full import chain (30+ modules)
python -c "
count = 0
modules = [
    'acli', 'acli.core.client', 'acli.core.streaming', 'acli.core.orchestrator_v2',
    'acli.core.session', 'acli.routing.router', 'acli.routing.workflows',
    'acli.context.store', 'acli.context.memory', 'acli.context.chunker',
    'acli.context.onboarder', 'acli.agents.definitions', 'acli.agents.factory',
    'acli.validation.engine', 'acli.validation.evidence', 'acli.validation.gates',
    'acli.validation.mock_detector', 'acli.validation.platforms.api',
    'acli.validation.platforms.cli', 'acli.validation.platforms.web',
    'acli.validation.platforms.ios', 'acli.validation.platforms.generic',
    'acli.integration.skill_engine', 'acli.tui.app', 'acli.tui.widgets',
    'acli.tui.prompt_input', 'acli.tui.bridge', 'acli.cli',
    'acli.spec.enhancer', 'acli.security.hooks',
]
import importlib
for mod in modules:
    importlib.import_module(mod)
    count += 1
print(f'All {count} modules imported: PASS')
" 2>&1 | tee evidence/final/08-imports.txt

# Compile final verdict
echo "=== FINAL GATE SUMMARY ===" | tee evidence/final/VERDICT.txt
for f in evidence/final/0*.txt; do
    name=$(basename $f)
    last_line=$(tail -1 $f)
    echo "$name: $last_line" | tee -a evidence/final/VERDICT.txt
done
```

Pass criteria — ALL of these must PASS:
1. `acli init` creates project (exit 0)
2. `acli status` runs (exit 0)
3. Router classifies greenfield + brownfield correctly
4. Context store round-trip (store → retrieve)
5. CLI validation with real `python -c` command → PASS
6. Mock detector catches mocks, passes clean code
7. Session logging creates + lists sessions
8. All 30+ module imports succeed

Review: `cat evidence/final/VERDICT.txt` — every line should end with "PASS"
Verdict: **ALL PASS** → ACLI v2 build complete | **ANY FAIL** → identify failure → fix → re-run from failed check
</phase_gate>

---

<gate_manifest>
## Gate Manifest

| Gate | Phase | Type | Blocking | What It Validates |
|------|-------|------|----------|-------------------|
| VG-1.1 | 1 | Task | ✅ | Model IDs updated, no stale references |
| VG-1.2 | 1 | Task | ✅ | 13 new event types, 8 new handlers |
| VG-1.3 | 1 | Task | ✅ | Router classifies 4 workflow types correctly |
| VG-1.4 | 1 | Task | ✅ | Context store, memory, chunker, onboarder |
| PG-1 | 1 | Phase | ✅ | Cumulative Phase 1 + regression check |
| VG-2.1 | 2 | Task | ✅ | 7 agent types, model routing, context injection |
| VG-2.2 | 2 | Task | ✅ | EnhancedOrchestrator with 12 methods, v1 preserved |
| VG-2.3 | 2 | Task | ✅ | Skill engine auto-detection and injection |
| VG-2.4 | 2 | Task | ✅ | JSONL session logging, list, load |
| PG-2 | 2 | Phase | ✅ | Full chain: Router → Definition → Orchestrator → Skills |
| VG-3.1 | 3 | Task | ✅ | Mock detector catches patterns, passes clean code |
| VG-3.2 | 3 | Task | ✅ | Evidence collector, gate runner, validation engine |
| VG-3.3 | 3 | Task | ✅ | Platform validators with real command execution |
| PG-3 | 3 | Phase | ✅ | E2E validation with real CLI command |
| VG-4.1 | 4 | Task | ✅ | 3 new TUI widgets with compose() |
| VG-4.2 | 4 | Task | ✅ | 7-panel layout, new bindings, CSS styles |
| PG-4 | 4 | Phase | ✅ | Full import chain from every phase |
| VG-5.1 | 5 | Task | ✅ | 13 CLI commands respond to --help |
| PG-5 | 5 | Phase | ✅ | acli init + status work end-to-end |
| VG-6.1 | 6 | Task | ✅ | Lint, version, 30+ imports |
| PG-FINAL | 6 | Final | ✅ | 8-point end-to-end system validation |

**Total gates: 21**
**Sequence: VG-1.1 → VG-1.2 → VG-1.3 → VG-1.4 → PG-1 → VG-2.1 → VG-2.2 → VG-2.3 → VG-2.4 → PG-2 → VG-3.1 → VG-3.2 → VG-3.3 → PG-3 → VG-4.1 → VG-4.2 → PG-4 → VG-5.1 → PG-5 → VG-6.1 → PG-FINAL**
**All gates: BLOCKING (no advancement on FAIL)**
**Evidence directory: `evidence/` (task gates) + `evidence/final/` (final gate)**
**If ANY gate FAILS: Fix real system → re-run from FAILED gate → do NOT skip**
**Mock detection: Active at prompt level + runtime hook level**
</gate_manifest>
