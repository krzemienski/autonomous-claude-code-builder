# API Reference

Python API reference for Autonomous CLI.

## Table of Contents

- [Core](#core)
  - [Orchestrator](#orchestrator)
  - [Session](#session)
  - [Client](#client)
- [Security](#security)
  - [Hooks](#security-hooks)
  - [Validators](#validators)
- [Progress](#progress)
  - [Tracker](#progresstracker)
  - [FeatureList](#featurelist)
- [Browser](#browser)
  - [Manager](#browsermanager)
  - [Wrappers](#browser-wrappers)
- [Spec](#spec)
  - [Enhancer](#specenhancer)
  - [Validator](#specvalidator)
- [UI](#ui)
  - [Dashboard](#dashboard)
  - [ToolBoard](#toolboard)

---

## Core

### Orchestrator

**Module**: `acli.core.orchestrator`

Main orchestration class that coordinates agent sessions.

```python
from acli.core.orchestrator import Orchestrator

orchestrator = Orchestrator(
    project_dir=Path("/path/to/project"),
    client=client,
    model="claude-sonnet-4-20250514",
    max_iterations=None,
    dashboard=True,
)

await orchestrator.run()
```

#### Constructor

```python
def __init__(
    self,
    project_dir: Path,
    client: AgentClient,
    model: str = "claude-sonnet-4-20250514",
    max_iterations: int | None = None,
    dashboard: bool = True,
) -> None
```

**Parameters**:
- `project_dir`: Project directory path
- `client`: Claude Code SDK client instance
- `model`: Claude model identifier
- `max_iterations`: Maximum number of sessions (None = unlimited)
- `dashboard`: Whether to show TUI dashboard

#### Methods

##### `async run() -> None`

Run the orchestration loop.

```python
await orchestrator.run()
```

Automatically detects first run vs continuation and selects appropriate agent.

##### `is_first_run() -> bool`

Check if this is the first run (no feature_list.json exists).

```python
if orchestrator.is_first_run():
    print("Running initializer...")
```

---

### Session

**Module**: `acli.core.session`

Represents a single agent session.

```python
from acli.core.session import Session

session = Session(
    client=client,
    project_dir=Path("/path/to/project"),
    prompt_template="initializer",
    session_type="initializer",
)

await session.run()
```

#### Constructor

```python
def __init__(
    self,
    client: AgentClient,
    project_dir: Path,
    prompt_template: str,
    session_type: Literal["initializer", "coding"],
) -> None
```

#### Methods

##### `async run() -> None`

Execute the session.

```python
await session.run()
```

Streams responses and executes tool calls.

---

### Client

**Module**: `acli.core.client`

Wrapper around Claude Code SDK client.

```python
from acli.core.client import create_client

client = create_client(
    api_key="sk-ant-...",
    model="claude-sonnet-4-20250514",
)
```

#### Functions

##### `create_client(api_key: str, model: str) -> AgentClient`

Create a configured Claude Code SDK client.

```python
client = create_client(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    model="claude-opus-4",
)
```

---

## Security

### Security Hooks

**Module**: `acli.security.hooks`

Pre-tool-use hooks for bash command validation.

```python
from acli.security.hooks import bash_security_hook

result = await bash_security_hook(
    input_data={
        "tool_name": "Bash",
        "tool_input": {"command": "ls -la"},
    }
)

if result.get("decision") == "block":
    print(f"Blocked: {result['reason']}")
```

#### Functions

##### `async bash_security_hook(input_data, tool_use_id=None, context=None) -> dict`

Validate bash commands using allowlist.

**Returns**:
- Empty dict `{}` to allow
- `{"decision": "block", "reason": "..."}` to block

##### `extract_commands(command_string: str) -> list[str]`

Extract command names from shell string.

```python
commands = extract_commands("ls | grep txt")
# Returns: ["ls", "grep"]
```

##### `split_command_segments(command_string: str) -> list[str]`

Split compound command into segments.

```python
segments = split_command_segments("ls && cat file")
# Returns: ["ls", "cat file"]
```

---

### Validators

**Module**: `acli.security.validators`

Per-command validators for sensitive operations.

```python
from acli.security.validators import (
    validate_pkill,
    validate_chmod,
    validate_init_script,
)
```

#### Classes

##### `ValidationResult`

Named tuple for validation results.

```python
ValidationResult(allowed: bool, reason: str = "")
```

#### Functions

##### `validate_pkill(command: str) -> ValidationResult`

Validate pkill commands.

```python
result = validate_pkill("pkill node")
assert result.allowed is True

result = validate_pkill("pkill bash")
assert result.allowed is False
```

##### `validate_chmod(command: str) -> ValidationResult`

Validate chmod commands (only +x allowed).

```python
result = validate_chmod("chmod +x init.sh")
assert result.allowed is True

result = validate_chmod("chmod 777 file")
assert result.allowed is False
```

##### `validate_init_script(command: str) -> ValidationResult`

Validate init.sh execution (only ./init.sh allowed).

```python
result = validate_init_script("./init.sh")
assert result.allowed is True

result = validate_init_script("/etc/init.sh")
assert result.allowed is False
```

##### `get_validator(command_name: str) -> Callable | None`

Get validator function for a command.

```python
validator = get_validator("pkill")
if validator:
    result = validator("pkill node")
```

---

## Progress

### ProgressTracker

**Module**: `acli.progress.tracker`

Track feature implementation progress.

```python
from acli.progress.tracker import ProgressTracker

tracker = ProgressTracker(project_dir=Path("/path/to/project"))

print(f"Total: {tracker.get_total_count()}")
print(f"Complete: {tracker.get_completed_count()}")
print(f"Progress: {tracker.get_progress_percentage()}%")
```

#### Constructor

```python
def __init__(self, project_dir: Path) -> None
```

#### Methods

##### `is_first_run() -> bool`

Check if feature_list.json exists.

```python
if tracker.is_first_run():
    print("No progress file found")
```

##### `get_total_count() -> int`

Get total number of features.

```python
total = tracker.get_total_count()
```

##### `get_completed_count() -> int`

Get number of passing features.

```python
completed = tracker.get_completed_count()
```

##### `get_incomplete_count() -> int`

Get number of incomplete features.

```python
remaining = tracker.get_incomplete_count()
```

##### `get_progress_percentage() -> float`

Get progress as percentage (0-100).

```python
progress = tracker.get_progress_percentage()
print(f"{progress:.1f}% complete")
```

---

### FeatureList

**Module**: `acli.progress.feature_list`

Manage feature_list.json file.

```python
from acli.progress.feature_list import FeatureList

features = FeatureList.load(Path("/path/to/project"))
features.mark_complete(feature_id=1)
features.save()
```

#### Methods

##### `@classmethod load(cls, project_dir: Path) -> FeatureList`

Load feature list from JSON file.

```python
features = FeatureList.load(project_dir)
```

##### `save(self) -> None`

Save feature list to JSON file.

```python
features.save()
```

##### `mark_complete(self, feature_id: int) -> None`

Mark a feature as passing.

```python
features.mark_complete(feature_id=5)
```

---

## Browser

### BrowserManager

**Module**: `acli.browser.manager`

Manage browser automation provider.

```python
from acli.browser.manager import BrowserManager

manager = BrowserManager(provider="puppeteer")
wrapper = manager.get_wrapper()
```

#### Constructor

```python
def __init__(self, provider: Literal["puppeteer", "playwright"] = "puppeteer") -> None
```

**Raises**: `ValueError` if provider is invalid

#### Methods

##### `get_wrapper() -> BrowserWrapper`

Get browser wrapper instance.

```python
wrapper = manager.get_wrapper()
commands = [
    wrapper.navigate("https://example.com"),
    wrapper.click("button#submit"),
]
```

---

### Browser Wrappers

#### PuppeteerWrapper

**Module**: `acli.browser.puppeteer`

```python
from acli.browser.puppeteer import PuppeteerWrapper

wrapper = PuppeteerWrapper(tools=mcp_tools)
```

##### Methods

```python
def navigate(self, url: str) -> dict
def click(self, selector: str) -> dict
def fill(self, selector: str, value: str) -> dict
def screenshot(self, name: str) -> dict
```

**Example**:

```python
commands = [
    wrapper.navigate("https://example.com"),
    wrapper.fill("input[name='email']", "test@example.com"),
    wrapper.click("button[type='submit']"),
    wrapper.screenshot("result.png"),
]
```

#### PlaywrightWrapper

**Module**: `acli.browser.playwright`

```python
from acli.browser.playwright import PlaywrightWrapper

wrapper = PlaywrightWrapper(tools=mcp_tools)
```

##### Methods

```python
def navigate(self, url: str) -> dict
def snapshot(self) -> dict
def click(self, uid: str, element: str) -> dict
def fill(self, uid: str, element: str, value: str) -> dict
```

**Example**:

```python
commands = [
    wrapper.navigate("https://example.com"),
    wrapper.snapshot(),  # Get element refs
    wrapper.fill(uid="input-123", element="Email", value="test@example.com"),
    wrapper.click(uid="btn-456", element="Submit"),
]
```

---

## Spec

### SpecEnhancer

**Module**: `acli.spec.enhancer`

Enhance plain text specs to structured JSON.

```python
from acli.spec.enhancer import SpecEnhancer

enhancer = SpecEnhancer(client=client)
enhanced = await enhancer.enhance(
    spec_text="Build a todo app",
    output_path=Path("enhanced_spec.json"),
)
```

#### Methods

##### `async enhance(self, spec_text: str, output_path: Path) -> dict`

Enhance specification interactively.

```python
result = await enhancer.enhance(
    spec_text=Path("app_spec.txt").read_text(),
    output_path=Path("enhanced.json"),
)
```

---

### SpecValidator

**Module**: `acli.spec.validator`

Validate specification schemas.

```python
from acli.spec.validator import SpecValidator

validator = SpecValidator()
is_valid = validator.validate(spec_dict)
```

#### Methods

##### `validate(self, spec: dict) -> bool`

Validate spec against schema.

```python
if validator.validate(spec):
    print("Valid spec")
else:
    print("Invalid spec")
    print(validator.errors)
```

---

## UI

### Dashboard

**Module**: `acli.ui.dashboard`

Real-time TUI dashboard.

```python
from acli.ui.dashboard import Dashboard

dashboard = Dashboard()
dashboard.start()

# Update from orchestrator
dashboard.add_tool_execution("Bash", duration=1.2, success=True)
dashboard.add_log("[INF] Session started")
dashboard.update_progress(completed=15, total=200)

dashboard.stop()
```

#### Methods

##### `start(self) -> None`

Start the dashboard.

```python
dashboard.start()
```

##### `stop(self) -> None`

Stop the dashboard.

```python
dashboard.stop()
```

##### `add_tool_execution(self, tool_name: str, duration: float, success: bool) -> None`

Add tool execution to board.

```python
dashboard.add_tool_execution("Write", duration=0.5, success=True)
```

##### `add_log(self, message: str, level: str = "INFO") -> None`

Add log message.

```python
dashboard.add_log("[INF] Processing feature 1", level="INFO")
```

##### `update_progress(self, completed: int, total: int) -> None`

Update progress bar.

```python
dashboard.update_progress(completed=50, total=200)
```

---

### ToolBoard

**Module**: `acli.ui.tool_board`

Tool execution display.

```python
from acli.ui.tool_board import ToolBoard

board = ToolBoard()
board.add_tool("Bash", duration=1.2, success=True)
```

#### Methods

##### `add_tool(self, name: str, duration: float, success: bool) -> None`

Add tool execution.

```python
board.add_tool("Read", duration=0.3, success=True)
```

##### `render(self) -> str`

Render tool board as text.

```python
output = board.render()
print(output)
```

---

## Examples

### Complete Workflow

```python
from pathlib import Path
from acli.core.orchestrator import Orchestrator
from acli.core.client import create_client

# Setup
client = create_client(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    model="claude-sonnet-4-20250514",
)

# Run orchestrator
orchestrator = Orchestrator(
    project_dir=Path("my_app"),
    client=client,
    max_iterations=5,
    dashboard=True,
)

await orchestrator.run()
```

### Custom Security Validator

```python
from acli.security.validators import ValidationResult, VALIDATORS

def validate_custom_command(command: str) -> ValidationResult:
    """Custom validator."""
    if "dangerous" in command:
        return ValidationResult(False, "Dangerous command detected")
    return ValidationResult(True)

# Register
VALIDATORS["custom"] = validate_custom_command
```

### Progress Monitoring

```python
from acli.progress.tracker import ProgressTracker

tracker = ProgressTracker(Path("my_app"))

while tracker.get_incomplete_count() > 0:
    progress = tracker.get_progress_percentage()
    print(f"Progress: {progress:.1f}%")
    await asyncio.sleep(10)  # Check every 10 seconds

print("Complete!")
```
