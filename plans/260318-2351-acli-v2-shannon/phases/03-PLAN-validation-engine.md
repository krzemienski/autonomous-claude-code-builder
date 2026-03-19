# Phase 3: Validation Engine — Iron Rule Enforcement

## Priority: P0 | Depends: Phase 2 (PG-2 PASSED) | Gates: G8, G9, G10

**Objective**: Build mock detector hook, evidence collector, validation gate runner, and platform-specific validators. Wire mock detection into SDK client hooks.

**Skills to invoke before starting**: `/functional-validation`, `/gate-validation-discipline`

---

## Task 3.1: Create Mock Detector Hook

### New File: `src/acli/validation/__init__.py`
```python
"""Validation engine — Iron Rule enforcement, evidence collection, platform validators."""
from .mock_detector import mock_detection_hook, scan_content_for_mocks, scan_file_path_for_test
__all__ = ["mock_detection_hook", "scan_content_for_mocks", "scan_file_path_for_test"]
```

### New File: `src/acli/validation/mock_detector.py` (~90 lines)

16+ regex patterns covering Python/JS/Java mocks, in-memory DBs, test mode flags, test file extensions.

Functions:
- `scan_content_for_mocks(content: str) -> list[str]` — returns list of matched pattern strings
- `scan_file_path_for_test(path: str) -> bool` — returns True if path matches test file patterns (`.test.`, `_test.`, `test_`, `Tests.`)
- `async mock_detection_hook(input_data, tool_use_id=None, context=None) -> dict` — PreToolUse hook for Write/Edit that returns `{"continue_": False, "decision": "block", "reason": "..."}` if mock patterns detected

### Modified File: `src/acli/core/client.py`

Add mock detection hook to PreToolUse hooks at line 126-130:

```python
# BEFORE (line 125-130):
        {
            "PreToolUse": [
                HookMatcher(matcher="Bash", hooks=[bash_security_hook]),
            ],
        },

# AFTER:
        {
            "PreToolUse": [
                HookMatcher(matcher="Bash", hooks=[bash_security_hook]),
                HookMatcher(matcher="Write|Edit|MultiEdit", hooks=[mock_detection_hook]),
            ],
        },
```

Add import at top of client.py:
```python
from ..validation.mock_detector import mock_detection_hook
```

---

## Task 3.2: Create Evidence Collector & Validation Engine

### New File: `src/acli/validation/evidence.py` (~80 lines)

`EvidenceCollector` class:
- `__init__(self, evidence_dir: Path)` — creates dir if needed
- `save_text(self, name: str, content: str) -> Path` — saves to `{evidence_dir}/{name}.txt`
- `save_json(self, name: str, data: dict) -> Path` — saves to `{evidence_dir}/{name}.json`
- `save_command_output(self, name: str, command: str) -> tuple[Path, int]` — runs REAL subprocess, captures stdout+stderr, returns (path, exit_code)
- `list_evidence(self) -> list[dict]` — lists all files in evidence_dir with name/size/path
- `get_evidence(self, name: str) -> str | None` — reads evidence file content

`save_command_output` uses `subprocess.run(command, shell=True, capture_output=True, text=True)` — REAL execution, no mocks.

### New File: `src/acli/validation/gates.py` (~100 lines)

Dataclasses:
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
    criteria_results: list[dict]
    timestamp: datetime = field(default_factory=datetime.now)
```

`GateRunner` class:
- `__init__(self, evidence_collector, streaming)` — stores refs
- `async run_gate(self, gate: ValidationGate) -> GateResult` — executes each criterion's check_command via evidence_collector.save_command_output, emits GATE_START/GATE_RESULT events
- `async run_phase_gate(self, gates: list[ValidationGate]) -> GateResult` — runs all gates, returns composite result

### New File: `src/acli/validation/engine.py` (~80 lines)

`ValidationEngine` class:
- `__init__(self, project_dir, streaming)` — creates EvidenceCollector and GateRunner
- `async validate_task(self, task, implementation_result) -> GateResult` — creates gate from task criteria, runs it
- `async validate_phase(self, phase) -> GateResult` — creates phase gate, runs cumulative validation
- `get_all_results(self) -> list[GateResult]` — returns all stored results
- `get_phase_summary(self) -> dict` — summary with pass/fail counts

---

## Task 3.3: Create Platform Validators

### New Files in `src/acli/validation/platforms/`

**`__init__.py`**:
```python
"""Platform-specific validators."""
from .api import APIValidator
from .cli import CLIValidator
from .generic import GenericValidator
from .ios import IOSValidator
from .web import WebValidator
__all__ = ["APIValidator", "CLIValidator", "WebValidator", "IOSValidator", "GenericValidator"]
```

**`cli.py`** (~50 lines): `CLIValidator.validate_command(command, expected_exit, expected_output, evidence_dir)` — runs real subprocess, saves output, checks exit code + output pattern. Returns `{"status": "PASS"|"FAIL", "evidence_path": str, "details": str}`.

**`api.py`** (~60 lines): `APIValidator.validate_endpoint(url, method, body, expected_status, evidence_dir)` — runs real `curl` command via subprocess. `health_check_poll(url, timeout)` — polls with retries.

**`web.py`** (~40 lines): `WebValidator.validate_page(url, selector, evidence_dir)` — delegates to Playwright MCP if available, otherwise notes unavailability.

**`ios.py`** (~40 lines): `IOSValidator.validate_screen(scheme, bundle_id, evidence_dir)` — delegates to xcrun simctl if available.

**`generic.py`** (~30 lines): `GenericValidator.validate(command, evidence_dir)` — runs any command via subprocess, captures output. Fallback for any platform.

All validators use REAL subprocess execution. No mocks.

---

## Gate G8: Mock Detector Blocks Test Code

```bash
mkdir -p evidence/G8

python -c "
from acli.validation.mock_detector import scan_content_for_mocks, scan_file_path_for_test

# Content detection
samples = [
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
correct = 0
for content, expected in samples:
    detected = len(scan_content_for_mocks(content)) > 0
    status = 'OK' if detected == expected else 'WRONG'
    if detected == expected: correct += 1
    print(f'  [{status}] \"{content[:40]}\" expected={expected} got={detected}')
print(f'Content detection: {correct}/{len(samples)}')
assert correct >= 7, f'Need >= 7/9 correct'
print('Content detection: PASS')

# Path detection
paths = [
    ('test_auth.py', True), ('auth.test.ts', True), ('AuthTests.swift', True),
    ('auth_test.go', True), ('auth.py', False), ('src/services/auth.ts', False),
]
path_correct = sum(1 for p, exp in paths if scan_file_path_for_test(p) == exp)
print(f'Path detection: {path_correct}/{len(paths)}')
assert path_correct >= 5
print('Path detection: PASS')
print('ALL MOCK DETECTOR: PASS')
" 2>&1 | tee evidence/G8/mock-detector.txt
```

---

## Gate G9: Evidence Collector Real Command Execution

```bash
mkdir -p evidence/G9

python -c "
from pathlib import Path
from acli.validation.evidence import EvidenceCollector
from acli.validation.gates import GateCriterion, ValidationGate, GateResult
from acli.validation.engine import ValidationEngine
import tempfile

with tempfile.TemporaryDirectory() as td:
    collector = EvidenceCollector(Path(td) / 'evidence')

    # Text evidence
    p = collector.save_text('test-output', 'Hello World')
    assert p.exists() and p.read_text() == 'Hello World'
    print(f'save_text: {p.name} — PASS')

    # JSON evidence
    p = collector.save_json('test-json', {'status': 200, 'ok': True})
    assert p.exists()
    print(f'save_json: {p.name} — PASS')

    # REAL command execution
    p, exit_code = collector.save_command_output('echo-test', 'echo REAL_EXECUTION_TEST')
    assert p.exists() and exit_code == 0
    content = p.read_text()
    assert 'REAL_EXECUTION_TEST' in content, f'Expected REAL_EXECUTION_TEST in output, got: {content}'
    print(f'save_command_output: exit={exit_code}, output contains REAL_EXECUTION_TEST — PASS')

    # List evidence
    all_ev = collector.list_evidence()
    assert len(all_ev) >= 3, f'Expected >= 3 files, got {len(all_ev)}'
    print(f'list_evidence: {len(all_ev)} files — PASS')

# Data structures
gate = ValidationGate(gate_id='TEST', task_id='T1', criteria=[
    GateCriterion('echo works', 'echo hello', 'echo-test')
], blocking=True)
assert gate.blocking and len(gate.criteria) == 1
print('Gate data structures: PASS')

# Engine interface
engine = ValidationEngine.__new__(ValidationEngine)
assert hasattr(engine, 'validate_task')
assert hasattr(engine, 'validate_phase')
assert hasattr(engine, 'get_all_results')
print('ValidationEngine interface: PASS')

print('ALL EVIDENCE + GATES: PASS')
" 2>&1 | tee evidence/G9/evidence-gates.txt
```

---

## Gate G10: Platform Validators with Real Commands

```bash
mkdir -p evidence/G10

python -c "
from acli.validation.platforms.cli import CLIValidator
from acli.validation.platforms.generic import GenericValidator
from acli.validation.platforms.api import APIValidator
from acli.validation.platforms.web import WebValidator
from acli.validation.platforms.ios import IOSValidator
import asyncio
from pathlib import Path
import tempfile

# CLIValidator — real echo command
async def test_cli():
    with tempfile.TemporaryDirectory() as td:
        v = CLIValidator()
        r = await v.validate_command('echo CLI_VALIDATOR_WORKS', 0, 'CLI_VALIDATOR_WORKS', Path(td))
        assert r['status'] == 'PASS', f'Failed: {r}'
        assert Path(r['evidence_path']).exists()
        content = Path(r['evidence_path']).read_text()
        assert 'CLI_VALIDATOR_WORKS' in content
        return r

r = asyncio.run(test_cli())
print(f'CLIValidator (real echo): {r[\"status\"]} — evidence at {r[\"evidence_path\"]}')

# GenericValidator — real python command
async def test_generic():
    with tempfile.TemporaryDirectory() as td:
        v = GenericValidator()
        r = await v.validate('python3 -c \"print(42)\"', Path(td))
        assert r['status'] == 'PASS', f'Failed: {r}'
        return r

r = asyncio.run(test_generic())
print(f'GenericValidator (real python): {r[\"status\"]}')

# All validators have required interface
for cls in [APIValidator, CLIValidator, WebValidator, IOSValidator, GenericValidator]:
    inst = cls.__new__(cls)
    has_method = any(hasattr(inst, m) for m in ['validate','validate_command','validate_endpoint','validate_page','validate_screen'])
    assert has_method, f'{cls.__name__} missing validate method'
print('All 5 validator interfaces: PASS')

print('ALL PLATFORM VALIDATORS: PASS')
" 2>&1 | tee evidence/G10/platform-validators.txt
```

---

## Phase 3 Cumulative Gate (PG-3)

```bash
mkdir -p evidence/PG3

python -c "
# Phase 1+2 regression
from acli.core.client import MODEL_OPUS, MODEL_SONNET
from acli.core.streaming import EventType
from acli.routing.router import PromptRouter
from acli.context.store import ContextStore
from acli.agents.definitions import AgentType
from acli.core.orchestrator_v2 import EnhancedOrchestrator

# Phase 3
from acli.validation.mock_detector import scan_content_for_mocks
from acli.validation.evidence import EvidenceCollector
from acli.validation.gates import GateRunner, ValidationGate
from acli.validation.engine import ValidationEngine
from acli.validation.platforms.cli import CLIValidator
from acli.validation.platforms.api import APIValidator
from acli.validation.platforms.generic import GenericValidator

import asyncio
from pathlib import Path
import tempfile

# E2E: real CLI validation
async def e2e():
    with tempfile.TemporaryDirectory() as td:
        v = CLIValidator()
        r = await v.validate_command(
            'python3 -c \"import json; print(json.dumps({\\\"acli_v2\\\": True}))\"',
            0, 'acli_v2', Path(td))
        assert r['status'] == 'PASS', f'E2E failed: {r}'
        print(f'E2E CLI validation: {r[\"status\"]}')

    # Mock detector works
    assert len(scan_content_for_mocks('from unittest.mock import Mock')) > 0
    assert len(scan_content_for_mocks('def real_function(): pass')) == 0
    print('Mock detector: PASS')

asyncio.run(e2e())
print('PHASE 3 CUMULATIVE GATE: ALL PASS')
" 2>&1 | tee evidence/PG3/cumulative.txt
```
