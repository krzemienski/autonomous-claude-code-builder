# Phase 5: CLI Integration & Session Management

## Priority: P1 | Depends: Phase 4 (PG-4 PASSED) | Gates: G15, G16, G17, G18

**Objective**: Add 6 new CLI commands (onboard, prompt, validate, session, memory, context), update existing commands to use v2 orchestrator, wire everything together.

**Skills to invoke before starting**: `/functional-validation`, `/gate-validation-discipline`

---

## Task 5.1: Update Existing CLI Commands

### Modified File: `src/acli/cli.py` (626 lines)

**Step 1**: Update `run` command (line 202-297) — add `--prompt` option:
```python
@app.command()
def run(
    project_dir: Annotated[Path, typer.Argument(...)] = Path("."),
    model: Annotated[str, typer.Option("--model", "-m", ...)] = "claude-sonnet-4-6-20250514",
    max_iterations: Annotated[Optional[int], typer.Option(...)] = None,
    prompt: Annotated[Optional[str], typer.Option("--prompt", "-p", help="Task prompt (any text)")] = None,
    dashboard: Annotated[bool, typer.Option(...)] = True,
    headless: Annotated[bool, typer.Option(...)] = False,
    verbose: Annotated[bool, typer.Option(...)] = False,
) -> None:
```

When `prompt` is provided, use `EnhancedOrchestrator.run(prompt)` instead of `run_loop()`.

**Step 2**: Update `init` command (line 100-199) — add `--onboard` flag:
```python
    onboard: Annotated[bool, typer.Option("--onboard", help="Run brownfield onboarding after init")] = False,
```

**Step 3**: Update `monitor` command (line 556-622) — import from orchestrator_v2:
```python
from .core.orchestrator_v2 import EnhancedOrchestrator as AgentOrchestrator
```

---

## Task 5.2: Add New CLI Commands

Add 6 new commands after `monitor` command (after line 622):

**`onboard` command**:
```python
@app.command()
def onboard(
    project_dir: Annotated[Path, typer.Argument(help="Project directory to onboard")] = Path("."),
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Run brownfield codebase onboarding — analyze existing project."""
    project_dir = project_dir.resolve()
    if not project_dir.exists():
        console.print(f"[red]Error:[/] Directory not found: {project_dir}")
        raise typer.Exit(1)

    from .context.onboarder import BrownfieldOnboarder
    from .core.streaming import StreamBuffer, StreamingHandler

    async def _onboard():
        buffer = StreamBuffer()
        streaming = StreamingHandler(buffer)
        onboarder = BrownfieldOnboarder()
        result = await onboarder.onboard(project_dir, streaming)
        console.print(f"[green]Onboarded:[/] {result}")

    asyncio.run(_onboard())
```

**`prompt` command**:
```python
@app.command()
def prompt(
    project_dir: Annotated[Path, typer.Argument(help="Project directory")] = Path("."),
    text: Annotated[str, typer.Argument(help="Task prompt")] = "",
    model: Annotated[str, typer.Option("--model", "-m")] = "claude-sonnet-4-6-20250514",
    max_iterations: Annotated[Optional[int], typer.Option("--max-iterations")] = None,
) -> None:
    """Send a single task prompt (headless, no TUI)."""
    # Uses EnhancedOrchestrator.run(text) headless
```

**`validate` command**:
```python
@app.command()
def validate(
    project_dir: Annotated[Path, typer.Argument(help="Project to validate")] = Path("."),
) -> None:
    """Run validation gates on project."""
    # Uses ValidationEngine to check existing evidence
```

**`session` command** (Typer subcommand group):
```python
session_app = typer.Typer(help="Session management")
app.add_typer(session_app, name="session")

@session_app.command("list")
def session_list(project_dir: Annotated[Path, typer.Argument(...)] = Path(".")):
    """List all sessions."""
    from .core.session import SessionLogger
    sessions = SessionLogger.list_sessions(project_dir.resolve())
    # Display sessions table

@session_app.command("replay")
def session_replay(session_id: str, project_dir: Annotated[Path, typer.Argument(...)] = Path(".")):
    """Replay session events."""
    from .core.session import SessionLogger
    events = SessionLogger.load_session(project_dir.resolve(), session_id)
    # Display events
```

**`memory` command** (Typer subcommand group):
```python
memory_app = typer.Typer(help="Memory management")
app.add_typer(memory_app, name="memory")

@memory_app.command("list")
def memory_list(project_dir: Annotated[Path, typer.Argument(...)] = Path(".")):
    """List memory facts."""
    from .context.memory import MemoryManager
    mem = MemoryManager(project_dir.resolve())
    # Display facts

@memory_app.command("add")
def memory_add(category: str, fact: str, project_dir: Annotated[Path, typer.Option(...)] = Path(".")):
    """Add a memory fact."""
    from .context.memory import MemoryManager
    mem = MemoryManager(project_dir.resolve())
    mem.add_fact(category, fact)

@memory_app.command("clear")
def memory_clear(project_dir: Annotated[Path, typer.Argument(...)] = Path(".")):
    """Clear all memory."""
```

**`context` command**:
```python
@app.command()
def context(
    project_dir: Annotated[Path, typer.Argument(help="Project directory")] = Path("."),
) -> None:
    """Show project context store."""
    from .context.store import ContextStore
    store = ContextStore(project_dir.resolve())
    summary = store.get_context_summary()
    console.print(summary)
    tech = store.get_tech_stack()
    if tech:
        console.print(f"\n[cyan]Tech Stack:[/] {tech}")
    console.print(f"\n[cyan]Onboarded:[/] {store.is_onboarded()}")
```

---

## Gate G15: All 13 Commands Respond to --help

```bash
mkdir -p evidence/G15

pip install -e ".[dev]" 2>&1 | tail -3

# Test every command
python -c "
from acli.cli import app
from typer.testing import CliRunner
runner = CliRunner()

commands = ['init','run','monitor','status','enhance','config','list-skills',
            'onboard','prompt','validate','session','memory','context']
results = []
for cmd in commands:
    result = runner.invoke(app, [cmd, '--help'])
    status = 'OK' if result.exit_code == 0 else f'FAIL(exit={result.exit_code})'
    results.append(f'{cmd:15s} --help: {status}')
    print(f'{cmd:15s} --help: {status}')

ok_count = sum(1 for r in results if 'OK' in r)
print(f'\nTotal: {ok_count}/{len(commands)} commands respond to --help')
assert ok_count == len(commands), f'Expected all {len(commands)} to pass'
print('ALL CLI COMMANDS: PASS')
" 2>&1 | tee evidence/G15/commands-help.txt

# No stale model strings
grep -rn "claude-sonnet-4-20250514" src/acli/cli.py 2>&1 | tee evidence/G15/stale-models.txt
```

**PASS criteria**:
- [ ] All 13 commands respond to `--help` with exit 0
- [ ] No stale model strings in cli.py

---

## Gate G16: Session/Memory/Context Commands Work

```bash
mkdir -p evidence/G16

# Setup: create project with context
rm -rf /tmp/acli-g16-test
python -m acli init /tmp/acli-g16-test --no-interactive 2>&1 | tee evidence/G16/init.txt

# Memory: add facts
python -m acli memory add architecture "Uses Claude Agent SDK" --project-dir /tmp/acli-g16-test 2>&1 | tee evidence/G16/memory-add.txt
python -m acli memory add tools "Custom MCP tools for web search" --project-dir /tmp/acli-g16-test 2>&1 | tee evidence/G16/memory-add2.txt

# Memory: list facts
python -m acli memory list /tmp/acli-g16-test 2>&1 | tee evidence/G16/memory-list.txt

# Context: show store
python -m acli context /tmp/acli-g16-test 2>&1 | tee evidence/G16/context.txt

# Session: list (should show empty or previous sessions)
python -m acli session list /tmp/acli-g16-test 2>&1 | tee evidence/G16/session-list.txt
```

**PASS criteria**:
- [ ] Memory add exits 0, fact stored
- [ ] Memory list shows added facts
- [ ] Context command runs without error
- [ ] Session list runs without error

---

## Gate G17: ALR Init + Status Workflow

```bash
mkdir -p evidence/G17

# Full ALR workflow
rm -rf /tmp/acli-g17-alr
python -m acli init /tmp/acli-g17-alr --no-interactive 2>&1 | tee evidence/G17/init.txt
echo "EXIT: $?" >> evidence/G17/init.txt

# Copy ALR spec
cp alr-claude.md /tmp/acli-g17-alr/app_spec.txt

# Verify project structure
ls -la /tmp/acli-g17-alr/ 2>&1 | tee evidence/G17/ls.txt

# Status check
python -m acli status /tmp/acli-g17-alr 2>&1 | tee evidence/G17/status.txt
echo "EXIT: $?" >> evidence/G17/status.txt

# Verify router classification
python -c "
from pathlib import Path
from acli.routing.router import PromptRouter
from acli.routing.workflows import WorkflowType
router = PromptRouter()
r = router.classify('Build the Awesome-List Researcher', Path('/tmp/acli-g17-alr'))
print(f'Classification: {r.workflow_type}')
print(f'Onboarding required: {r.requires_onboarding}')
assert r.workflow_type == WorkflowType.GREENFIELD_APP
print('ALR Router Classification: PASS')
" 2>&1 | tee evidence/G17/router.txt
```

**PASS criteria**:
- [ ] `acli init` creates ALR project (exit 0)
- [ ] Project has app_spec.txt with ALR content
- [ ] `acli status` runs without error
- [ ] Router classifies ALR as GREENFIELD_APP

---

## Gate G18: Onboard Existing Project

```bash
mkdir -p evidence/G18

# Use the ACLI codebase itself as brownfield test
python -m acli onboard /Users/nick/Desktop/claude-code-builder-agents-sdk 2>&1 | tee evidence/G18/onboard.txt
echo "EXIT: $?" >> evidence/G18/onboard.txt

# Verify context was created
ls -la /Users/nick/Desktop/claude-code-builder-agents-sdk/.acli/context/ 2>&1 | tee evidence/G18/context-dir.txt
cat /Users/nick/Desktop/claude-code-builder-agents-sdk/.acli/context/tech_stack.json 2>&1 | tee evidence/G18/tech-stack.txt

# Context command
python -m acli context /Users/nick/Desktop/claude-code-builder-agents-sdk 2>&1 | tee evidence/G18/context-show.txt
```

**PASS criteria**:
- [ ] `acli onboard` exits 0
- [ ] `.acli/context/tech_stack.json` created with Python detected
- [ ] `acli context` shows tech stack

---

## Phase 5 Cumulative Gate (PG-5)

```bash
mkdir -p evidence/PG5

# Full regression + new commands
python -m acli --help 2>&1 | tee evidence/PG5/help.txt
python -m acli init /tmp/acli-pg5-test --no-interactive 2>&1 | tee evidence/PG5/init.txt
python -m acli status /tmp/acli-pg5-test 2>&1 | tee evidence/PG5/status.txt

python -c "
# Full import chain
from acli.core.client import MODEL_OPUS, MODEL_SONNET
from acli.core.streaming import EventType
from acli.routing.router import PromptRouter
from acli.context.store import ContextStore
from acli.context.memory import MemoryManager
from acli.agents.definitions import AgentType
from acli.core.orchestrator_v2 import EnhancedOrchestrator
from acli.validation.engine import ValidationEngine
from acli.tui.app import AgentMonitorApp
from acli.tui.widgets import ContextExplorer, ValidationGatePanel
from acli.tui.prompt_input import PromptInput
from acli.integration.skill_engine import SkillEngine
from acli.core.session import SessionLogger
from acli.cli import app
print('PHASE 5 CUMULATIVE GATE: ALL PASS')
" 2>&1 | tee evidence/PG5/cumulative.txt
```
