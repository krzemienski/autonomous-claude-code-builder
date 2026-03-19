# Phase 2: Agent Architecture — Factory, Orchestrator, Skill Engine, JSONL

## Priority: P0 | Depends: Phase 1 (PG-1 PASSED) | Gates: G4, G5, G6, G7

**Objective**: Create agent factory with typed agents, replace v1 orchestrator with EnhancedOrchestrator, build skill engine, add JSONL session logging.

**Skills to invoke before starting**: `/functional-validation`, `/gate-validation-discipline`

---

## Task 2.1: Create Agent Definitions & Factory

### New Files

**`src/acli/agents/__init__.py`**:
```python
"""Agent definitions and factory for multi-agent orchestration."""
from .definitions import AgentDefinition, AgentType
from .factory import AgentFactory
__all__ = ["AgentType", "AgentDefinition", "AgentFactory"]
```

**`src/acli/agents/definitions.py`** (~130 lines):

Define `AgentType` enum with 7 values matching ARCHITECTURE_V2.md § 3.1.

Define `AgentDefinition` dataclass with:
- `agent_type: AgentType`
- `model: str` — full model ID from `core.client.MODEL_OPUS` or `MODEL_SONNET`
- `system_prompt_template: str` — XML-structured prompt per ARCHITECTURE_V2.md § 11
- `allowed_tools: list[str]` — tool allowlist per agent type
- `max_turns: int` — session turn limit
- `thinking_config: dict` — `{"type": "adaptive"}` for all agents
- `effort: str | None` — `"high"` for Opus agents, `None` for Sonnet
- `@classmethod for_type(cls, agent_type, context="", skills="", memory="")` — factory method

Model assignments (from ARCHITECTURE_V2.md § 3.1):
- Router → Sonnet (`MODEL_SONNET`)
- Analyst → Opus (`MODEL_OPUS`), effort="high"
- Planner → Opus (`MODEL_OPUS`), effort="high"
- Implementer → Sonnet (`MODEL_SONNET`)
- Validator → Sonnet (`MODEL_SONNET`)
- ContextManager → Sonnet (`MODEL_SONNET`)
- Reporter → Sonnet (`MODEL_SONNET`)

System prompt templates follow XML structure from ARCHITECTURE_V2.md § 11 with `<context>`, `<skills>`, `<iron_rule>`, `<task>`, `<validation_criteria>`, `<constraints>` sections.

**`src/acli/agents/factory.py`** (~100 lines):

`AgentFactory` class:
- `__init__(self, project_dir, context_store, memory_manager)` — stores references
- `create_agent(self, agent_type, task_context="")` — returns configured `ClaudeSDKClient` using `create_sdk_client()` from `core.client`
- `_build_system_prompt(self, definition, task_context)` — builds full prompt by:
  1. Taking `definition.system_prompt_template`
  2. Injecting `context_store.get_context_summary()` into `<context>` section
  3. Injecting `memory_manager.get_injection_prompt()` into `<memory>` section
  4. Injecting `task_context` into `<task>` section
  5. Adding Iron Rule block from `/functional-validation` skill

Uses real SDK patterns from research:
```python
from ..core.client import create_sdk_client, MODEL_OPUS, MODEL_SONNET
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
```

---

## Task 2.2: Create EnhancedOrchestrator

### File Changes

**Step 1**: Rename `src/acli/core/orchestrator.py` → `src/acli/core/orchestrator_v1.py` (git mv, preserve v1)

**Step 2**: Create `src/acli/core/orchestrator_v2.py` (~200 lines):

`EnhancedOrchestrator` class with 12 methods per ARCHITECTURE_V2.md § 5.1:

```python
class EnhancedOrchestrator:
    def __init__(self, project_dir: Path, model: str = "claude-sonnet-4-6-20250514", max_iterations: int | None = None):
        self.project_dir = project_dir.resolve()
        self.model = model
        self.max_iterations = max_iterations
        self.state = get_project_state(self.project_dir)
        self.buffer = StreamBuffer()
        self.streaming = StreamingHandler(self.buffer)
        self.context_store = ContextStore(self.project_dir)
        self.memory_manager = MemoryManager(self.project_dir)
        self.router = PromptRouter()
        self.factory = AgentFactory(self.project_dir, self.context_store, self.memory_manager)
        self._running = False
        self._pause_requested = False
        self._stop_requested = False

    async def run(self, prompt: str) -> None: ...
    async def run_loop(self, on_session_start=None, on_session_end=None) -> None: ...
    async def route_prompt(self, prompt: str) -> WorkflowConfig: ...
    async def run_analyst(self) -> dict: ...
    async def run_planner(self, workflow, prompt) -> dict: ...
    async def run_implementer(self, task, context) -> tuple[str, str]: ...
    async def run_validator(self, task, result) -> dict: ...
    async def run_reporter(self, phase) -> str: ...
    def request_pause(self) -> None: ...
    def request_stop(self) -> None: ...
    def resume(self) -> None: ...
    def get_status(self) -> dict: ...
```

`run()` method implements the agent graph from ARCHITECTURE_V2.md § 5.1:
1. Route prompt → WorkflowConfig
2. If `requires_onboarding` → run analyst + context manager
3. Run planner with workflow
4. For each task: run implementer → run validator → handle failures
5. Run reporter after each phase
6. Emit events: AGENT_SPAWN, PHASE_START, GATE_RESULT, etc.

`run_loop()` provides v1 backwards compat — reads `app_spec.txt` as prompt, calls `run()`.

`get_status()` returns dict matching v1 structure: `{running, paused, project_dir, model, session_count, is_first_run, progress}`.

**Step 3**: Update `src/acli/core/__init__.py` (line 10):
```python
# BEFORE:
from .orchestrator import AgentOrchestrator, run_autonomous_agent

# AFTER:
from .orchestrator_v1 import AgentOrchestrator
from .orchestrator_v2 import EnhancedOrchestrator
from .orchestrator_v2 import EnhancedOrchestrator as run_autonomous_agent  # compat
```

**Step 4**: Update `src/acli/cli.py` imports:
- Line 263: `from .core.orchestrator import AgentOrchestrator` → `from .core.orchestrator_v2 import EnhancedOrchestrator as AgentOrchestrator`
- Line 603: same pattern for monitor command
- Keep backwards compat — `AgentOrchestrator` alias points to `EnhancedOrchestrator`

**Step 5**: Update `src/acli/tui/app.py` line 21:
```python
# BEFORE:
from ..core.orchestrator import AgentOrchestrator

# AFTER:
from ..core.orchestrator_v2 import EnhancedOrchestrator as AgentOrchestrator
```

**Step 6**: Update `src/acli/tui/bridge.py` line 17:
```python
# BEFORE:
from ..core.orchestrator import AgentOrchestrator

# AFTER:
from ..core.orchestrator_v2 import EnhancedOrchestrator as AgentOrchestrator
```

---

## Task 2.3: Create Skill Engine

### New File: `src/acli/integration/skill_engine.py` (~100 lines)

`SkillEngine` class with:
- `AGENT_SKILL_MAP` — maps agent types to default skills
- `PLATFORM_SKILL_MAP` — maps platforms to additional skills
- `KEYWORD_SKILL_MAP` — maps task keywords to skills
- `discover_skills()` — scans `~/.claude/skills/` for SKILL.md files
- `get_skills_for_agent(agent_type, platform="", task_context="")` — combines maps + keyword detection
- `load_skill_content(skill_name)` — reads SKILL.md content
- `get_combined_skill_prompt(skill_names)` — concatenates skill content for system prompt injection

Key mappings from ARCHITECTURE_V2.md § 5.3:
```python
AGENT_SKILL_MAP = {
    "validator": ["functional-validation"],
    "planner": ["create-validation-plan", "create-plans"],
    "implementer": ["python-agent-sdk"],
    "reporter": [],
    "analyst": [],
    "context_manager": [],
    "router": [],
}
```

---

## Task 2.4: Add JSONL Session Logging

### File Modified: `src/acli/core/session.py` (146 lines)

Add `SessionLogger` class after `ProjectState` class (after line 141):

```python
class SessionLogger:
    """Writes agent session events to JSONL files."""

    def __init__(self, project_dir: Path, session_id: str) -> None:
        self.session_id = session_id
        self.sessions_dir = project_dir / ".acli" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.sessions_dir / f"{session_id}.jsonl"
        self._file = open(self.log_file, "a")

    def log_event(self, event_type: str, data: dict) -> None:
        entry = {"type": event_type, "session_id": self.session_id, "timestamp": datetime.now().isoformat(), **data}
        self._file.write(json.dumps(entry) + "\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()

    @staticmethod
    def list_sessions(project_dir: Path) -> list[dict]:
        sessions_dir = project_dir / ".acli" / "sessions"
        if not sessions_dir.exists():
            return []
        results = []
        for f in sorted(sessions_dir.glob("*.jsonl")):
            results.append({"session_id": f.stem, "path": str(f), "size": f.stat().st_size})
        return results

    @staticmethod
    def load_session(project_dir: Path, session_id: str) -> list[dict]:
        path = project_dir / ".acli" / "sessions" / f"{session_id}.jsonl"
        if not path.exists():
            return []
        events = []
        with open(path) as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        return events
```

---

## Gate G4: Agent Factory Creates Agents

```bash
mkdir -p evidence/G4

python -c "
from acli.agents.definitions import AgentType, AgentDefinition
from acli.agents.factory import AgentFactory
from acli.context.store import ContextStore
from acli.context.memory import MemoryManager
from pathlib import Path
import tempfile

# All 7 types exist
for t in ['ROUTER','ANALYST','PLANNER','IMPLEMENTER','VALIDATOR','CONTEXT_MANAGER','REPORTER']:
    assert hasattr(AgentType, t), f'Missing: {t}'
print('All 7 AgentTypes: PASS')

# Model assignments correct
analyst = AgentDefinition.for_type(AgentType.ANALYST)
assert 'opus' in analyst.model, f'Analyst model: {analyst.model}'
planner = AgentDefinition.for_type(AgentType.PLANNER)
assert 'opus' in planner.model, f'Planner model: {planner.model}'
impl = AgentDefinition.for_type(AgentType.IMPLEMENTER)
assert 'sonnet' in impl.model, f'Impl model: {impl.model}'
print('Model assignments: PASS')

# Factory injects context
with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    store = ContextStore(p); store.initialize()
    store.store_tech_stack({'language': 'Python', 'framework': 'Claude Agent SDK'})
    mem = MemoryManager(p)
    mem.add_fact('arch', 'Docker-first execution')
    factory = AgentFactory(p, store, mem)
    prompt = factory._build_system_prompt(analyst, 'Analyze ALR')
    assert 'Python' in prompt or 'Claude Agent SDK' in prompt, 'Missing context in prompt'
    assert 'Docker' in prompt or 'execution' in prompt, 'Missing memory in prompt'
    print(f'System prompt length: {len(prompt)} chars')
    print('Context injection: PASS')

print('ALL AGENT ARCHITECTURE: PASS')
" 2>&1 | tee evidence/G4/agent-factory.txt
```

**PASS criteria**: All 7 types, correct model assignments, context/memory injected into prompts

---

## Gate G5: JSONL Session Logging

```bash
mkdir -p evidence/G5

python -c "
from pathlib import Path
from acli.core.session import SessionLogger
import tempfile, json

with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    logger = SessionLogger(p, 'test_session')
    logger.log_event('session_start', {'agent_type': 'analyst', 'model': 'claude-opus-4-6-20250514'})
    logger.log_event('tool_use', {'tool': 'Bash', 'input': {'command': 'ls'}, 'duration_ms': 50})
    logger.log_event('assistant_text', {'text': 'Analyzing...', 'tokens': 42})
    logger.log_event('session_end', {'status': 'completed', 'duration_s': 60})
    logger.close()

    # Verify file exists
    files = list((p / '.acli' / 'sessions').glob('*.jsonl'))
    assert len(files) == 1, f'Expected 1 JSONL file, got {len(files)}'
    print(f'JSONL file: {files[0].name}')

    # Verify content
    with open(files[0]) as f:
        lines = [json.loads(l) for l in f if l.strip()]
    assert len(lines) == 4, f'Expected 4 events, got {len(lines)}'
    assert lines[0]['type'] == 'session_start'
    assert lines[-1]['type'] == 'session_end'
    assert all('timestamp' in l for l in lines), 'Missing timestamps'
    assert all('session_id' in l for l in lines), 'Missing session_id'
    print(f'Events logged: {len(lines)}')
    for l in lines:
        print(f'  {l[\"type\"]}: {json.dumps({k:v for k,v in l.items() if k not in (\"timestamp\",\"session_id\")})[:80]}')

    # Verify list_sessions
    sessions = SessionLogger.list_sessions(p)
    assert len(sessions) >= 1
    print(f'Sessions listed: {len(sessions)}')

    # Verify load_session
    loaded = SessionLogger.load_session(p, 'test_session')
    assert len(loaded) == 4
    print(f'Session loaded: {len(loaded)} events')

print('ALL SESSION LOGGING: PASS')
" 2>&1 | tee evidence/G5/session-logging.txt
```

---

## Gate G6: Skill Engine

```bash
mkdir -p evidence/G6

python -c "
from acli.integration.skill_engine import SkillEngine

engine = SkillEngine()
available = engine.discover_skills()
print(f'Skills discovered: {len(available)}')

val_skills = engine.get_skills_for_agent('validator')
assert 'functional-validation' in val_skills, f'Missing functional-validation: {val_skills}'
print(f'Validator skills: {val_skills}')

plan_skills = engine.get_skills_for_agent('planner')
assert any(s in plan_skills for s in ['create-validation-plan', 'create-plans']), f'Missing planning skill: {plan_skills}'
print(f'Planner skills: {plan_skills}')

ios_skills = engine.get_skills_for_agent('validator', platform='ios')
assert 'functional-validation' in ios_skills
print(f'iOS validator skills: {ios_skills}')

kw_skills = engine.get_skills_for_agent('implementer', task_context='ElevenLabs TTS integration')
print(f'Keyword skills: {kw_skills}')

print('ALL SKILL ENGINE: PASS')
" 2>&1 | tee evidence/G6/skill-engine.txt
```

---

## Gate G7: EnhancedOrchestrator Single Iteration

```bash
mkdir -p evidence/G7

# Verify orchestrator instantiates and has all methods
python -c "
from pathlib import Path
from acli.core.orchestrator_v2 import EnhancedOrchestrator
import tempfile

with tempfile.TemporaryDirectory() as td:
    p = Path(td)
    (p / 'app_spec.txt').write_text('Build ALR')
    orch = EnhancedOrchestrator(project_dir=p)

    methods = ['run','run_loop','route_prompt','run_analyst','run_planner','run_implementer','run_validator','run_reporter','request_pause','request_stop','resume','get_status']
    for m in methods:
        assert hasattr(orch, m), f'Missing: {m}'
    print(f'All {len(methods)} methods: PASS')

    status = orch.get_status()
    assert 'running' in status and 'model' in status and 'project_dir' in status
    print(f'Status keys: {list(status.keys())}')
    print('Status structure: PASS')

    orch.request_pause(); orch.resume(); orch.request_stop()
    print('Control methods: PASS')

# Verify v1 preserved
from acli.core.orchestrator_v1 import AgentOrchestrator
print('V1 orchestrator preserved: PASS')

# Verify CLI still imports
from acli.cli import app
print('CLI import: PASS')

# Verify TUI still imports
from acli.tui.app import AgentMonitorApp
print('TUI import: PASS')

print('ALL ORCHESTRATOR V2: PASS')
" 2>&1 | tee evidence/G7/orchestrator-v2.txt

# Real CLI test: init + status
rm -rf /tmp/acli-g7-test
python -m acli init /tmp/acli-g7-test --no-interactive 2>&1 | tee evidence/G7/init.txt
python -m acli status /tmp/acli-g7-test 2>&1 | tee evidence/G7/status.txt
```

**PASS criteria for G7**: All 12 methods exist, status structure correct, v1 preserved, CLI and TUI import, `acli init` + `acli status` work

---

## Phase 2 Cumulative Gate (PG-2)

```bash
mkdir -p evidence/PG2

python -c "
# Phase 1 regression
from acli.core.client import MODEL_OPUS, MODEL_SONNET
from acli.core.streaming import EventType
from acli.routing.router import PromptRouter
from acli.context.store import ContextStore
from acli.context.memory import MemoryManager

# Phase 2
from acli.agents.definitions import AgentType, AgentDefinition
from acli.agents.factory import AgentFactory
from acli.core.orchestrator_v2 import EnhancedOrchestrator
from acli.integration.skill_engine import SkillEngine
from acli.core.session import SessionLogger

# Full chain test
from acli.routing.workflows import WorkflowType
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as td:
    p = Path(td); (p / 'app_spec.txt').write_text('Build ALR')
    router = PromptRouter()
    wf = router.classify('Build ALR', p)
    assert wf.workflow_type == WorkflowType.GREENFIELD_APP

    planner_def = AgentDefinition.for_type(AgentType.PLANNER)
    assert 'opus' in planner_def.model

    orch = EnhancedOrchestrator(project_dir=p)
    assert isinstance(orch.get_status(), dict)

    engine = SkillEngine()
    assert len(engine.get_skills_for_agent('validator')) > 0

    print('FULL CHAIN: Router → Definition → Factory → Orchestrator → Skills: PASS')

print('PHASE 2 CUMULATIVE GATE: ALL PASS')
" 2>&1 | tee evidence/PG2/cumulative.txt
```
