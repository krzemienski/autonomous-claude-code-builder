# Agent Orchestration Engine

Complete implementation of the 2-agent pattern with Claude Code SDK.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AgentOrchestrator                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Session Loop (max_iterations control)                │  │
│  │  ├─ Pause/Resume/Stop controls                        │  │
│  │  ├─ Auto-continue (3s delay)                          │  │
│  │  └─ Error recovery (max 3 errors)                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ ProjectState│  │ StreamBuffer │  │ StreamingHandler │   │
│  │ (.acli_state│  │ (1000 events)│  │ (event emitter)  │   │
│  │  .json)     │  └──────────────┘  └──────────────────┘   │
│  └─────────────┘                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ├─► run_agent_session()
         │   ├─ Create SDK client with security
         │   ├─ Send prompt (initializer or coding)
         │   ├─ Stream responses
         │   └─ Track tool execution
         │
         └─► ClaudeSDKClient
             ├─ Model: claude-sonnet-4-20250514
             ├─ Security hooks (bash validation)
             ├─ MCP servers (Puppeteer + Playwright)
             └─ Tools: Read, Write, Edit, Glob, Grep, Bash
```

## Components

### 1. StreamingHandler

Real-time event streaming from Claude SDK.

**Events:**
- `TEXT`: Assistant text chunks
- `TOOL_START`: Tool execution begins
- `TOOL_END`: Tool execution completes
- `TOOL_BLOCKED`: Security hook blocked tool
- `ERROR`: Error occurred
- `SESSION_START`: Session begins
- `SESSION_END`: Session ends
- `PROGRESS`: Feature completion update

**Usage:**
```python
buffer = StreamBuffer()
handler = StreamingHandler(buffer)

# Register event listener
handler.on("text", lambda event: print(event.text))

# Emit events
await handler.handle_text("Building feature...")
await handler.handle_tool_start("Bash", {"command": "npm install"})
await handler.handle_tool_end("Bash", result="Success")
```

### 2. ClaudeSDKClient

Configured SDK client with security and MCPs.

**Security:**
- Sandbox enabled with auto-allow Bash
- Bash commands validated by security hook
- Permissions: Read, Write, Edit, Glob, Grep, Bash + MCPs

**MCP Servers:**
- **Puppeteer**: Browser automation (7 tools)
- **Playwright**: Advanced browser testing (7 tools)

**Usage:**
```python
from acli.core import create_sdk_client

client = create_sdk_client(
    project_dir=Path("./my-project"),
    model="claude-sonnet-4-20250514",
)

async with client:
    # Use client
    pass
```

### 3. AgentOrchestrator

Multi-session autonomous agent loop.

**Features:**
- 2-agent pattern (initializer → coding)
- Auto-continue with delay
- Pause/resume/stop controls
- Error recovery (3 max consecutive errors)
- Progress tracking (feature_list.json)
- Session state persistence

**Usage:**
```python
from acli.core import AgentOrchestrator

orch = AgentOrchestrator(
    project_dir=Path("./my-project"),
    model="claude-sonnet-4-20250514",
    max_iterations=10,
)

# Register event handlers
orch.on_event("progress", lambda event: print(f"{event.features_done}/{event.features_total}"))

# Run autonomous loop
await orch.run_loop()

# Or run single session
status, response = await orch.run_single_session()
```

### 4. Prompt Templates

**Initializer** (`prompts/templates/initializer.md`):
- Read app_spec.txt
- Generate ~200 features in feature_list.json
- Create init.sh setup script
- Initialize project structure
- Git init + initial commit

**Coding** (`prompts/templates/coding.md`):
- Read feature_list.json
- Start dev server
- Verify existing features
- Pick ONE incomplete feature
- Implement and test (Puppeteer/Playwright)
- Update feature_list.json
- Git commit

## Session Lifecycle

```
1. START SESSION
   ├─ Determine type (initializer or coding)
   ├─ Emit SESSION_START event
   └─ Create fresh SDK client

2. RUN SESSION
   ├─ Load prompt template
   ├─ Send to Claude SDK
   ├─ Stream responses
   │  ├─ TEXT chunks
   │  ├─ TOOL_START (name, input)
   │  └─ TOOL_END (result or error)
   └─ Return (status, response)

3. END SESSION
   ├─ Update session state (completed/error)
   ├─ Emit SESSION_END event
   ├─ Save state to .acli_state.json
   └─ Update progress if feature_list.json exists

4. AUTO-CONTINUE
   ├─ Check max_iterations
   ├─ Check pause/stop flags
   ├─ Wait 3 seconds
   └─ Start next session
```

## Error Handling

**Consecutive Errors:**
- Track consecutive errors
- Stop after 3 consecutive failures
- Reset counter on successful session

**Recovery:**
```python
try:
    status, response = await run_agent_session(...)
    if status == "error":
        consecutive_errors += 1
        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            logger.error("Too many errors, stopping")
            break
    else:
        consecutive_errors = 0
except Exception as e:
    # Handle exception
    pass
```

## State Persistence

**ProjectState** (`.acli_state.json`):
```json
{
  "project_dir": "/path/to/project",
  "created_at": "2025-12-08T17:00:00",
  "sessions": [
    {
      "session_id": 1,
      "session_type": "initializer",
      "start_time": "2025-12-08T17:00:00",
      "end_time": "2025-12-08T17:15:00",
      "status": "completed",
      "features_completed": [],
      "errors": [],
      "tool_calls": 42,
      "tokens_used": 15000
    }
  ]
}
```

## Progress Tracking

Reads `feature_list.json` to track completion:

```json
[
  {"id": 1, "component": "Login", "description": "Email field", "passes": true},
  {"id": 2, "component": "Login", "description": "Password field", "passes": false}
]
```

**Metrics:**
- `features_done`: Count where `passes: true`
- `features_total`: Total feature count
- Emits `PROGRESS` event after each session

## API

### Core Functions

```python
# Convenience function
await run_autonomous_agent(
    project_dir=Path("./project"),
    model="claude-sonnet-4-20250514",
    max_iterations=None,  # Unlimited
)

# Advanced control
orchestrator = AgentOrchestrator(project_dir, model, max_iterations)
await orchestrator.run_loop()
```

### Orchestrator Methods

```python
# Control
orchestrator.request_pause()
orchestrator.request_stop()
orchestrator.resume()

# State
orchestrator.is_running
orchestrator.is_first_run
orchestrator.get_status()

# Events
orchestrator.on_event("text", handler)
orchestrator.on_event("progress", handler)
```

## Configuration

**AUTO_CONTINUE_DELAY**: 3.0 seconds
**MAX_CONSECUTIVE_ERRORS**: 3
**STREAM_BUFFER_MAX_SIZE**: 1000 events
**MAX_TURNS**: 1000 per session

## Testing

Run verification:
```bash
python examples/test_orchestrator.py
```

Tests:
- ✅ StreamBuffer event handling
- ✅ Orchestrator initialization
- ✅ State persistence
- ✅ Pause/resume controls
- ✅ Event handlers
- ✅ Progress tracking

## Integration

**CLI** (Phase 2):
```python
from acli.core import run_autonomous_agent

await run_autonomous_agent(project_dir, model, max_iterations)
```

**Dashboard** (Phase 5):
```python
from acli.core import StreamBuffer, EventType

buffer = orchestrator.buffer
async for event in buffer.iter_from(0):
    if event.type == EventType.TEXT:
        display_text(event.text)
    elif event.type == EventType.TOOL_START:
        display_tool(event.tool_name)
```

**Progress** (Phase 6):
```python
orchestrator.on_event("progress", lambda e: update_ui(e.features_done, e.features_total))
```

## Files

```
src/acli/core/
├── __init__.py          # Module exports
├── streaming.py         # StreamEvent, StreamBuffer, StreamingHandler
├── client.py            # create_sdk_client, security config
├── agent.py             # run_agent_session, prompt loading
├── orchestrator.py      # AgentOrchestrator, run_autonomous_agent
└── session.py           # SessionState, ProjectState (Phase 2)

src/acli/prompts/
├── __init__.py
└── templates/
    ├── initializer.md
    └── coding.md

src/acli/utils/
├── events.py            # AsyncEventEmitter
└── logger.py            # Logger (Phase 1)
```

## Examples

See `examples/test_orchestrator.py` for complete working examples.
