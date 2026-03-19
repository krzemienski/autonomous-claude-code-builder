# Claude Agent SDK v0.1.49 — Complete API Reference

**Research Date:** 2026-03-18
**SDK Version:** 0.1.49
**Parent Package:** anthropic 0.75.0
**Python Target:** >=3.11
**Repository:** https://github.com/anthropics/claude-agent-sdk-python

---

## Executive Summary

The Claude Agent SDK is a thin Python wrapper over the Claude Code CLI. It does NOT directly call the Anthropic API; instead, it spawns a subprocess (claude or claude-dev) and communicates via JSON-JSONL over stdin/stdout using a bidirectional control protocol.

**Key architectural facts for ACLI v2 planning:**
- **Streaming model:** All SDK calls internally use streaming mode (bidirectional stdin/stdout)
- **Session lifecycle:** Options + connect() → query() → receive_response() → disconnect()
- **MCP integration:** SDK supports 3 server types (stdio, SSE, HTTP) + 1 in-process SDK type
- **Hooks system:** Pre/Post tool execution, before user submit, on stop/compact, on subagent start
- **Cost tracking:** ResultMessage includes `total_cost_usd` and token usage
- **Model IDs:** Full string IDs (e.g., "claude-opus-4-6-20250514"), not aliases
- **Thinking config:** Adaptive (default) or explicit budget in tokens

---

## 1. ClaudeSDKClient — Bidirectional Interactive Sessions

### Constructor

```python
def __init__(
    self,
    options: ClaudeAgentOptions | None = None,
    transport: Transport | None = None,
) -> None:
```

**Parameters:**
- `options`: ClaudeAgentOptions instance (see § 2). Defaults to empty if None.
- `transport`: Advanced—custom Transport implementation. Defaults to SubprocessCLITransport.

**Lifetime:** Initialize → connect() → query() → receive_response() → disconnect()

**Example — Basic bidirectional session:**
```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        model="claude-opus-4-6-20250514",
        cwd="/path/to/project",
        permission_mode="acceptEdits",
    )
    async with ClaudeSDKClient(options) as client:
        # Send first query
        await client.query("Analyze this codebase")
        async for msg in client.receive_response():
            print(type(msg).__name__, msg)

        # Follow-up query (same session)
        await client.query("Now implement the fix")
        async for msg in client.receive_response():
            print(type(msg).__name__, msg)

asyncio.run(main())
```

### Methods

#### async connect(prompt=None) → None
Opens connection. Auto-connects with empty stream if prompt is None.

```python
await client.connect()  # Interactive, no initial prompt
# OR
await client.connect("Initial prompt string")
# OR
async def prompts():
    yield {"type": "user", "message": {"role": "user", "content": "..."}}
await client.connect(prompts())
```

**Validation:**
- If `can_use_tool` callback is set, requires AsyncIterable prompt (not string).
- `can_use_tool` and `permission_prompt_tool_name` are mutually exclusive.

#### async query(prompt: str | AsyncIterable, session_id="default") → None
Send a request in streaming mode.

```python
await client.query("What's the capital of France?", session_id="chat-1")
```

**Parameters:**
- `prompt`: Message as string or async iterable of dicts
- `session_id`: Default "default". Used to group messages in conversation.

#### async receive_response() → AsyncIterator[Message]
**Recommended pattern for single-response workflows.** Yields all messages until ResultMessage (inclusive), then stops.

```python
async for msg in client.receive_response():
    if isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"Claude: {block.text}")
    elif isinstance(msg, ResultMessage):
        print(f"Cost: ${msg.total_cost_usd:.4f}")
        # Iterator stops here automatically
```

#### async receive_messages() → AsyncIterator[Message]
Lower-level alternative. Yields all messages indefinitely (caller must manage termination).

```python
async for msg in client.receive_messages():
    if isinstance(msg, ResultMessage):
        break  # Manual termination needed
```

#### async interrupt() → None
Send interrupt signal (streaming mode only). Stops Claude mid-execution.

```python
await client.interrupt()
```

#### async set_permission_mode(mode: str) → None
Change permissions during conversation.

```python
await client.set_permission_mode("bypassPermissions")  # Accept all tools
```

**Valid modes:**
- `"default"`: Prompt for dangerous tools
- `"acceptEdits"`: Auto-accept file edits
- `"plan"`: Review/planning mode (prompt for actions)
- `"bypassPermissions"`: Allow all (use caution)

#### async set_model(model: str | None) → None
Switch models mid-conversation.

```python
await client.set_model("claude-sonnet-4-6-20250514")
```

#### async rewind_files(user_message_id: str) → None
Rewind tracked files to state at a specific user message.

**Requires:**
- `enable_file_checkpointing=True` in options
- `extra_args={"replay-user-messages": None}` to receive UserMessage UUIDs

```python
options = ClaudeAgentOptions(
    enable_file_checkpointing=True,
    extra_args={"replay-user-messages": None},
)
async with ClaudeSDKClient(options) as client:
    await client.query("Make changes")
    checkpoint_id = None
    async for msg in client.receive_response():
        if isinstance(msg, UserMessage) and msg.uuid:
            checkpoint_id = msg.uuid

    # Later, rewind
    if checkpoint_id:
        await client.rewind_files(checkpoint_id)
```

#### async get_mcp_status() → McpStatusResponse
Query live MCP server connection status.

```python
status = await client.get_mcp_status()
for server in status["mcpServers"]:
    print(f"{server['name']}: {server['status']}")  # "connected", "failed", "pending", etc.
    if server["status"] == "failed":
        print(f"  Error: {server.get('error')}")
```

**Response structure:**
```python
{
    "mcpServers": [
        {
            "name": "puppeteer",
            "status": "connected",  # | "failed" | "pending" | "needs-auth" | "disabled"
            "serverInfo": {"name": "...", "version": "..."},  # When connected
            "error": "...",  # When failed
            "config": {...},  # Server config (stdio/sse/http/sdk)
            "scope": "project",
            "tools": [
                {"name": "tool_name", "description": "..."}
            ]
        }
    ]
}
```

#### async reconnect_mcp_server(server_name: str) → None
Retry a failed MCP server.

```python
await client.reconnect_mcp_server("puppeteer")
```

#### async toggle_mcp_server(server_name: str, enabled: bool) → None
Enable/disable an MCP server.

```python
await client.toggle_mcp_server("puppeteer", enabled=False)
await client.query("Work without browser automation")
await client.toggle_mcp_server("puppeteer", enabled=True)
```

#### async stop_task(task_id: str) → None
Stop a running background task.

```python
await client.stop_task("task-abc123")
```

#### async get_server_info() → dict[str, Any] | None
Get CLI initialization info (commands, output styles, server capabilities).

```python
info = await client.get_server_info()
print(f"Output style: {info.get('output_style', 'default')}")
```

#### async disconnect() → None
Explicitly close connection. Auto-called by `async with`.

```python
await client.disconnect()
```

### Context Manager Protocol

```python
async with ClaudeSDKClient(options) as client:
    await client.query("...")
    async for msg in client.receive_response():
        ...
# disconnect() auto-called
```

**Caveat:** As of v0.0.20, client cannot be reused across different async runtime contexts. Must complete all operations within the same context where connect() was called.

---

## 2. ClaudeAgentOptions — Configuration Dataclass

### Full Field Listing

```python
@dataclass
class ClaudeAgentOptions:
    # Model selection
    model: str | None = None  # Full ID: "claude-opus-4-6-20250514"
    fallback_model: str | None = None  # Fallback if primary unavailable

    # Thinking configuration
    thinking: ThinkingConfig | None = None  # Adaptive/enabled/disabled
    effort: Literal["low", "medium", "high", "max"] | None = None  # Thinking effort
    max_thinking_tokens: int | None = None  # DEPRECATED: use thinking instead

    # Tool & permission configuration
    tools: list[str] | ToolsPreset | None = None  # Deprecated preset system
    allowed_tools: list[str] = field(default_factory=list)  # Specific tools to allow
    disallowed_tools: list[str] = field(default_factory=list)  # Explicit denials
    permission_mode: PermissionMode | None = None  # "default"|"acceptEdits"|"plan"|"bypassPermissions"
    permission_prompt_tool_name: str | None = None  # Use "stdio" for can_use_tool callback
    can_use_tool: CanUseTool | None = None  # Tool permission callback

    # System prompt & agents
    system_prompt: str | SystemPromptPreset | None = None
    agents: dict[str, AgentDefinition] | None = None  # Custom agent definitions

    # MCP servers
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)

    # Session control
    continue_conversation: bool = False  # Continue previous session ID
    resume: str | None = None  # Resume from specific session ID
    fork_session: bool = False  # Fork instead of continue when resuming
    enable_file_checkpointing: bool = False  # Track file changes per user message

    # Execution limits
    max_turns: int | None = None  # Max back-and-forth turns
    max_budget_usd: float | None = None  # Max spend in USD

    # Hooks & callbacks
    hooks: dict[HookEvent, list[HookMatcher]] | None = None

    # Environment
    cwd: str | Path | None = None  # Working directory
    cli_path: str | Path | None = None  # Path to claude/claude-dev CLI
    settings: str | None = None  # Path to .claude_settings.json
    add_dirs: list[str | Path] = field(default_factory=list)  # Additional dirs to include
    env: dict[str, str] = field(default_factory=dict)  # Env vars for CLI process
    extra_args: dict[str, str | None] = field(default_factory=dict)  # Arbitrary CLI flags

    # Beta features
    betas: list[SdkBeta] = field(default_factory=list)  # ["context-1m-2025-08-07"]
    user: str | None = None  # User identifier
    setting_sources: list[SettingSource] | None = None  # ["user", "project", "local"]

    # Output & streaming
    include_partial_messages: bool = False  # Stream partial assistant messages
    output_format: dict[str, Any] | None = None  # Structured output (JSON schema, etc.)

    # Sandbox & plugins
    sandbox: SandboxSettings | None = None  # Bash command isolation config
    plugins: list[SdkPluginConfig] = field(default_factory=list)  # Custom plugins

    # Debug
    max_buffer_size: int | None = None  # Max bytes buffering CLI stdout
    debug_stderr: Any = sys.stderr  # DEPRECATED
    stderr: Callable[[str], None] | None = None  # Callback for CLI stderr
```

### ThinkingConfig Types

**Adaptive (default behavior):**
```python
thinking = {"type": "adaptive"}  # Claude decides thinking depth
```

**Explicitly enabled:**
```python
thinking = {"type": "enabled", "budget_tokens": 10000}  # Fixed token budget
```

**Disabled:**
```python
thinking = {"type": "disabled"}  # No thinking blocks
```

**Example:**
```python
options = ClaudeAgentOptions(
    thinking={"type": "adaptive"},  # Type-safe typing
    model="claude-opus-4-6-20250514",
)
```

### Preset System (Legacy)

**SystemPromptPreset:**
```python
system_prompt = {"type": "preset", "preset": "claude_code", "append": "Additional context"}
```

**ToolsPreset:**
```python
tools = {"type": "preset", "preset": "claude_code"}
```

### AgentDefinition — Custom Agents

```python
@dataclass
class AgentDefinition:
    description: str  # What this agent does
    prompt: str  # System/instruction prompt
    tools: list[str] | None = None  # Specific tools for this agent
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
    skills: list[str] | None = None  # Skill references
    memory: Literal["user", "project", "local"] | None = None
    mcpServers: list[str | dict[str, Any]] | None = None  # Server refs or inline configs

agents = {
    "researcher": AgentDefinition(
        description="Researches technical topics",
        prompt="You are a technical researcher...",
        model="opus",
        tools=["Read", "Grep", "WebFetch"],
    )
}
```

---

## 3. Message Types — Response Parsing

### Message Union

All message types inherit from base types:

```python
Message = (
    UserMessage
    | AssistantMessage
    | SystemMessage
    | ResultMessage
    | StreamEvent
    | RateLimitEvent
)
```

### UserMessage

```python
@dataclass
class UserMessage:
    content: str | list[ContentBlock]
    uuid: str | None = None  # UUIDs only with replay-user-messages
    parent_tool_use_id: str | None = None  # For tool-use sidechain messages
    tool_use_result: dict[str, Any] | None = None
```

**Example:** User-initiated messages in the transcript.

### AssistantMessage

```python
@dataclass
class AssistantMessage:
    content: list[ContentBlock]  # Text, thinking, tool use, etc.
    model: str  # The actual model ID used ("claude-opus-4-6-...")
    parent_tool_use_id: str | None = None
    error: AssistantMessageError | None = None  # "authentication_failed", "rate_limit", etc.
    usage: dict[str, Any] | None = None  # Token counts
```

**ContentBlock types in content list:**
```python
ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock
```

### TextBlock

```python
@dataclass
class TextBlock:
    text: str
```

### ThinkingBlock

```python
@dataclass
class ThinkingBlock:
    thinking: str  # Internal reasoning
    signature: str  # Unique ID for thinking block
```

### ToolUseBlock

```python
@dataclass
class ToolUseBlock:
    id: str  # Tool use ID, referenced in results
    name: str  # Tool name ("Bash", "Read", etc.)
    input: dict[str, Any]  # Tool parameters
```

### ToolResultBlock

```python
@dataclass
class ToolResultBlock:
    tool_use_id: str  # References ToolUseBlock.id
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None
```

### ResultMessage — End-of-Response Marker

**CRITICAL:** Marks end of a single response.

```python
@dataclass
class ResultMessage:
    subtype: str  # "final_result"
    duration_ms: int  # Total time for response
    duration_api_ms: int  # API call time
    is_error: bool  # Error occurred?
    num_turns: int  # Claude back-and-forth turns
    session_id: str
    stop_reason: str | None  # "tool_use", "end_turn", "max_tokens"
    total_cost_usd: float | None  # TOTAL cost so far
    usage: dict[str, Any] | None  # Token breakdown
    result: str | None  # Final text result
    structured_output: Any = None  # For JSON-schema outputs
```

**Example — Cost tracking:**
```python
async for msg in client.receive_response():
    if isinstance(msg, ResultMessage):
        print(f"Session cost: ${msg.total_cost_usd:.4f}")
        print(f"Turns: {msg.num_turns}")
        print(f"Duration: {msg.duration_ms}ms")
```

### SystemMessage — Metadata Events

```python
@dataclass
class SystemMessage:
    subtype: str  # "task_started", "task_progress", "task_notification", rate_limit", etc.
    data: dict[str, Any]  # Raw payload
```

**Subtypes:**
- `"task_started"` → TaskStartedMessage
- `"task_progress"` → TaskProgressMessage
- `"task_notification"` → TaskNotificationMessage
- `"rate_limit"` → RateLimitEvent (separate type)

### TaskStartedMessage

```python
@dataclass
class TaskStartedMessage(SystemMessage):
    task_id: str
    description: str
    uuid: str
    session_id: str
    tool_use_id: str | None = None
    task_type: str | None = None
```

### TaskProgressMessage

```python
@dataclass
class TaskProgressMessage(SystemMessage):
    task_id: str
    description: str
    usage: TaskUsage  # {"total_tokens": int, "tool_uses": int, "duration_ms": int}
    uuid: str
    session_id: str
    tool_use_id: str | None = None
    last_tool_name: str | None = None
```

### TaskNotificationMessage

```python
@dataclass
class TaskNotificationMessage(SystemMessage):
    task_id: str
    status: TaskNotificationStatus  # "completed" | "failed" | "stopped"
    output_file: str  # Path to task output
    summary: str
    uuid: str
    session_id: str
    usage: TaskUsage | None = None
```

### RateLimitEvent

```python
@dataclass
class RateLimitEvent:
    rate_limit_info: RateLimitInfo
    uuid: str
    session_id: str

@dataclass
class RateLimitInfo:
    status: RateLimitStatus  # "allowed" | "allowed_warning" | "rejected"
    resets_at: int | None  # Unix timestamp
    rate_limit_type: RateLimitType | None  # "five_hour", "seven_day", etc.
    utilization: float | None  # 0.0-1.0
    overage_status: RateLimitStatus | None
    overage_resets_at: int | None
    overage_disabled_reason: str | None
    raw: dict[str, Any]  # Full dict from CLI
```

### StreamEvent — Partial Streaming

When `include_partial_messages=True`:

```python
@dataclass
class StreamEvent:
    uuid: str
    session_id: str
    event: dict[str, Any]  # Raw Anthropic API streaming event
    parent_tool_use_id: str | None = None
```

---

## 4. Hooks System — Execution Interception

### Hook Events

```python
HookEvent = (
    Literal["PreToolUse"]
    | Literal["PostToolUse"]
    | Literal["PostToolUseFailure"]
    | Literal["UserPromptSubmit"]
    | Literal["Stop"]
    | Literal["SubagentStop"]
    | Literal["PreCompact"]
    | Literal["Notification"]
    | Literal["SubagentStart"]
    | Literal["PermissionRequest"]
)
```

### HookMatcher Configuration

```python
@dataclass
class HookMatcher:
    matcher: str | None = None  # Pattern matching (e.g., "Bash", "Write|Edit")
    hooks: list[HookCallback] = field(default_factory=list)
    timeout: float | None = None  # Seconds (default: 60)
```

**Example:**
```python
hooks = {
    "PreToolUse": [
        HookMatcher(matcher="Bash", hooks=[my_bash_hook]),
        HookMatcher(matcher="Write|Edit|MultiEdit", hooks=[my_file_hook]),
    ]
}
```

### HookCallback Type Signature

```python
HookCallback = Callable[
    [HookInput, str | None, HookContext],
    Awaitable[HookJSONOutput]
]
```

**Parameters:**
1. **HookInput** (discriminated union):
   - PreToolUseHookInput
   - PostToolUseHookInput
   - PostToolUseFailureHookInput
   - UserPromptSubmitHookInput
   - StopHookInput
   - SubagentStopHookInput
   - PreCompactHookInput
   - NotificationHookInput
   - SubagentStartHookInput
   - PermissionRequestHookInput

2. **tool_use_id: str | None** — Reference to ToolUseBlock.id (present in tool-lifecycle hooks)

3. **HookContext** — `{"signal": None}` (placeholder for future abort signals)

### PreToolUseHookInput

```python
@dataclass
class PreToolUseHookInput(BaseHookInput, _SubagentContextMixin):
    hook_event_name: Literal["PreToolUse"]
    tool_name: str  # "Bash", "Read", "Write", etc.
    tool_input: dict[str, Any]  # Parameters
    tool_use_id: str  # Unique ID
    # From BaseHookInput:
    session_id: str
    transcript_path: str
    cwd: str
    permission_mode: str | None = None
    # From _SubagentContextMixin:
    agent_id: str | None = None  # Present only in sub-agent
    agent_type: str | None = None
```

**Example — Bash security hook:**
```python
async def bash_security_hook(
    input: PreToolUseHookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    if input.tool_name != "Bash":
        return {"continue_": True}

    cmd = input.tool_input.get("command", "")
    if "rm -rf" in cmd:
        return {
            "continue_": False,
            "decision": "block",
            "reason": "Dangerous command blocked",
        }

    return {"continue_": True}
```

### PostToolUseHookInput

```python
@dataclass
class PostToolUseHookInput(BaseHookInput, _SubagentContextMixin):
    hook_event_name: Literal["PostToolUse"]
    tool_name: str
    tool_input: dict[str, Any]
    tool_response: Any  # The result
    tool_use_id: str
```

### PostToolUseFailureHookInput

```python
@dataclass
class PostToolUseFailureHookInput(BaseHookInput, _SubagentContextMixin):
    hook_event_name: Literal["PostToolUseFailure"]
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str
    error: str
    is_interrupt: bool | None = None
```

### HookJSONOutput — Return Type

**Async deferred:**
```python
HookJSONOutput = {
    "async_": True,  # Note: use async_ (underscore), converted to "async" for CLI
    "asyncTimeout": 5000,  # Optional, in milliseconds
}
```

**Sync with control:**
```python
HookJSONOutput = {
    # Control flow
    "continue_": True,  # Use underscore, converted to "continue" for CLI
    "suppressOutput": False,
    "stopReason": "Custom stop reason",

    # Decision (if blocking)
    "decision": "block",  # Enum: "block" (only meaningful value)
    "systemMessage": "Warning shown to user",
    "reason": "Why this decision",

    # Hook-specific output
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",  # "allow" | "deny" | "ask"
        "permissionDecisionReason": "...",
        "updatedInput": {...},  # Modified tool input
        "additionalContext": "Info for Claude",
    }
}
```

### UserPromptSubmitHookInput

```python
@dataclass
class UserPromptSubmitHookInput(BaseHookInput):
    hook_event_name: Literal["UserPromptSubmit"]
    prompt: str
```

### SubagentStartHookInput

```python
@dataclass
class SubagentStartHookInput(BaseHookInput):
    hook_event_name: Literal["SubagentStart"]
    agent_id: str  # Unique per subagent
    agent_type: str  # Agent type name
```

### Example — Full Hook Setup

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, HookMatcher

async def my_hook(input, tool_use_id, context):
    if input.hook_event_name == "PreToolUse":
        if input.tool_name == "Bash" and "sudo" in str(input.tool_input):
            return {
                "continue_": False,
                "decision": "block",
                "reason": "sudo not allowed",
            }
    return {"continue_": True}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[my_hook])
        ]
    }
)
async with ClaudeSDKClient(options) as client:
    await client.query("Run some bash")
    async for msg in client.receive_response():
        print(msg)
```

---

## 5. Tool Callbacks — can_use_tool Permission

### CanUseTool Type

```python
CanUseTool = Callable[
    [str, dict[str, Any], ToolPermissionContext],
    Awaitable[PermissionResult]
]
```

**Parameters:**
1. **tool_name: str** — Name of tool
2. **tool_input: dict[str, Any]** — Parameters
3. **ToolPermissionContext** — `{"signal": None, "suggestions": [...]}`

**Returns:** PermissionResult (union of allow/deny)

### PermissionResultAllow

```python
@dataclass
class PermissionResultAllow:
    behavior: Literal["allow"] = "allow"
    updated_input: dict[str, Any] | None = None  # Modified parameters
    updated_permissions: list[PermissionUpdate] | None = None
```

### PermissionResultDeny

```python
@dataclass
class PermissionResultDeny:
    behavior: Literal["deny"] = "deny"
    message: str = ""
    interrupt: bool = False  # Stop execution?
```

### Example

```python
async def my_permission_callback(tool_name, tool_input, context):
    if tool_name == "Bash" and "rm -rf" in tool_input.get("command", ""):
        return PermissionResultDeny(
            message="Dangerous command blocked",
            interrupt=True
        )
    return PermissionResultAllow()

options = ClaudeAgentOptions(
    can_use_tool=my_permission_callback,
)
# Note: requires AsyncIterable prompt, not string prompt
async with ClaudeSDKClient(options) as client:
    async def prompts():
        yield {"type": "user", "message": {"role": "user", "content": "Run bash"}}

    await client.connect(prompts())
    async for msg in client.receive_messages():
        print(msg)
```

**Validation:**
- `can_use_tool` **requires streaming mode** (AsyncIterable prompt)
- `can_use_tool` and `permission_prompt_tool_name` are mutually exclusive

---

## 6. MCP Servers — Configuration & Discovery

### Server Configuration Types

**Standard (stdio subprocess):**
```python
McpStdioServerConfig = {
    "type": "stdio",  # Optional, inferred from command
    "command": "npx",
    "args": ["puppeteer-mcp-server"],
    "env": {"NODE_ENV": "production"},  # Optional
}
```

**Server-Sent Events (HTTP):**
```python
McpSSEServerConfig = {
    "type": "sse",
    "url": "https://example.com/sse",
    "headers": {"Authorization": "Bearer token"},  # Optional
}
```

**HTTP/JSON-RPC:**
```python
McpHttpServerConfig = {
    "type": "http",
    "url": "https://example.com/rpc",
    "headers": {...},
}
```

**In-process SDK MCP (v0.1.49 only):**
```python
McpSdkServerConfig = {
    "type": "sdk",
    "name": "my-server",
    "instance": mcp_server_instance,  # From create_sdk_mcp_server()
}
```

### Using MCP Servers

```python
mcp_servers = {
    "puppeteer": {
        "command": "npx",
        "args": ["puppeteer-mcp-server"],
    },
    "custom": {
        "command": "python",
        "args": ["-m", "my_mcp_server"],
        "env": {"API_KEY": "..."}
    }
}

options = ClaudeAgentOptions(
    mcp_servers=mcp_servers,
    allowed_tools=["mcp__puppeteer__*"],
)
```

### Status Discovery

```python
status = await client.get_mcp_status()
for server in status["mcpServers"]:
    print(f"{server['name']}: {server['status']}")
    if server["status"] == "connected":
        for tool in server.get("tools", []):
            print(f"  - {tool['name']}: {tool.get('description', '')}")
```

---

## 7. SDK MCP Tools — In-Process Tools

### @tool Decorator

```python
from claude_agent_sdk import tool

@tool(
    name="my_tool",
    description="What this tool does",
    input_schema={"param1": str, "param2": int}
)
async def my_tool(args):
    """Implement the tool."""
    param1 = args["param1"]
    param2 = args["param2"]

    result = do_something(param1, param2)

    return {
        "content": [{"type": "text", "text": str(result)}],
        "is_error": False,  # Optional
    }
```

### create_sdk_mcp_server

```python
from claude_agent_sdk import create_sdk_mcp_server, tool

@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    return {
        "content": [{"type": "text", "text": f"Sum: {args['a'] + args['b']}"}]
    }

@tool("multiply", "Multiply two numbers", {"a": float, "b": float})
async def multiply(args):
    return {
        "content": [{"type": "text", "text": f"Product: {args['a'] * args['b']}"}]
    }

server = create_sdk_mcp_server(
    name="calculator",
    version="1.0.0",
    tools=[add, multiply]
)

options = ClaudeAgentOptions(
    mcp_servers={"calc": server},
    allowed_tools=["add", "multiply"],
)
```

### Input Schema Format

**Simple dict mapping (auto-converted to JSON schema):**
```python
@tool("divide", "Divide", {"dividend": float, "divisor": float})
async def divide(args):
    ...
```

**Explicit JSON Schema:**
```python
@tool("grep", "Search text", {
    "type": "object",
    "properties": {
        "pattern": {"type": "string"},
        "text": {"type": "string"},
        "case_sensitive": {"type": "boolean", "default": False}
    },
    "required": ["pattern", "text"]
})
async def grep(args):
    ...
```

**TypedDict (complex schemas):**
```python
from typing_extensions import TypedDict

class GrepInput(TypedDict):
    pattern: str
    text: str
    case_sensitive: bool

@tool("grep", "Search text", GrepInput)
async def grep(args):
    ...
```

### Response Format

**Success (text):**
```python
return {
    "content": [{"type": "text", "text": "Result here"}]
}
```

**Error:**
```python
return {
    "content": [{"type": "text", "text": "Error message"}],
    "is_error": True
}
```

**Image response:**
```python
return {
    "content": [
        {"type": "image", "data": "base64-encoded", "mimeType": "image/png"}
    ]
}
```

---

## 8. Session Management

### list_sessions() — Enumerate Sessions

```python
from claude_agent_sdk import list_sessions

sessions = await list_sessions()  # Returns list[SDKSessionInfo]
for session in sessions:
    print(f"ID: {session.session_id}")
    print(f"Summary: {session.summary}")
    print(f"Modified: {session.last_modified}ms ago")
    print(f"Size: {session.file_size} bytes")
    if session.custom_title:
        print(f"Title: {session.custom_title}")
    if session.git_branch:
        print(f"Branch: {session.git_branch}")
```

### get_session_messages() — Read History

```python
from claude_agent_sdk import get_session_messages

messages = await get_session_messages(session_id="abc-123")
for msg in messages:
    print(f"Type: {msg.type}")  # "user" | "assistant"
    print(f"UUID: {msg.uuid}")
    print(f"Content: {msg.message}")  # Anthropic API message dict
```

### rename_session() & tag_session()

```python
from claude_agent_sdk import rename_session, tag_session

await rename_session(session_id="abc-123", new_title="My Project Setup")
await tag_session(session_id="abc-123", tags=["project", "setup"])
```

---

## 9. Model IDs & Thinking Configuration

### Valid Model IDs (March 2026)

**Opus (Most capable):**
- `"claude-opus-4-6-20250514"` (Default for opus)
- `"claude-opus-4-1-20250805"`

**Sonnet (Balanced):**
- `"claude-sonnet-4-6-20250514"` (Default for sonnet)
- `"claude-sonnet-4-5-20250415"`

**Haiku (Fast, cheap):**
- `"claude-haiku-4-5-20251001"`

**Note:** Model strings are FULL IDs, not aliases like "sonnet" or "opus". However, AgentDefinition supports `model="sonnet"` as shorthand, which means "use the project's sonnet model".

### Thinking Configuration

**Adaptive (recommended for most cases):**
```python
thinking = {"type": "adaptive"}
```

**Explicit token budget:**
```python
thinking = {"type": "enabled", "budget_tokens": 10000}
```

**Disabled:**
```python
thinking = {"type": "disabled"}
```

**With effort level:**
```python
options = ClaudeAgentOptions(
    thinking={"type": "adaptive"},
    effort="high",  # "low" | "medium" | "high" | "max"
)
```

---

## 10. Output Format — Structured Outputs

### JSON Schema Output

```python
output_format = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "analysis": {"type": "string"},
            "score": {"type": "number", "minimum": 0, "maximum": 10},
            "items": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["analysis", "score"]
    }
}

options = ClaudeAgentOptions(output_format=output_format)
```

**Access in ResultMessage:**
```python
async for msg in client.receive_response():
    if isinstance(msg, ResultMessage):
        parsed = msg.structured_output  # dict matching schema
```

---

## 11. Error Types

```python
class ClaudeSDKError(Exception):
    """Base exception."""

class CLIConnectionError(ClaudeSDKError):
    """Cannot connect to Claude Code."""

class CLINotFoundError(CLIConnectionError):
    """CLI not installed or not found."""

class ProcessError(ClaudeSDKError):
    """CLI process failed."""
    exit_code: int | None
    stderr: str | None

class CLIJSONDecodeError(ClaudeSDKError):
    """Cannot parse JSON from CLI."""
    line: str
    original_error: Exception
```

---

## 12. Streaming Mode vs. Non-Streaming

**CRITICAL FACT:** The Python SDK internally always uses streaming mode (bidirectional stdin/stdout). This is important for ACLI v2:

- `query(prompt="string")` → internally converts to streaming with single message
- `query(prompt=async_iterable)` → true streaming
- Both use the same control protocol via stdin/stdout
- Agents are sent via initialize request (not directly in query)
- Session lifecycle: connect → initialize → stream input → receive output

---

## 13. Cost Tracking & Usage

### Cost Fields in ResultMessage

```python
@dataclass
class ResultMessage:
    total_cost_usd: float | None  # CUMULATIVE cost for entire session
    usage: dict[str, Any] | None  # Token breakdown
    # Typical usage dict:
    # {
    #     "input_tokens": 5000,
    #     "output_tokens": 1200,
    #     "cache_creation_input_tokens": 0,
    #     "cache_read_input_tokens": 0
    # }
```

### Per-Task Usage

```python
@dataclass
class TaskUsage(TypedDict):
    total_tokens: int
    tool_uses: int
    duration_ms: int
```

### Tracking Pattern

```python
total_cost = 0.0
async for msg in client.receive_response():
    if isinstance(msg, ResultMessage):
        if msg.total_cost_usd:
            total_cost = msg.total_cost_usd
            print(f"Response cost: ${msg.total_cost_usd:.4f}")

        if msg.usage:
            print(f"Tokens: {msg.usage.get('input_tokens')} in, "
                  f"{msg.usage.get('output_tokens')} out")
```

---

## 14. Advanced Features (v0.1.49+)

### File Checkpointing

Track file state per user message:

```python
options = ClaudeAgentOptions(
    enable_file_checkpointing=True,
    extra_args={"replay-user-messages": None},  # Receive UUIDs
)
async with ClaudeSDKClient(options) as client:
    checkpoint_id = None
    await client.query("Make changes")
    async for msg in client.receive_response():
        if isinstance(msg, UserMessage) and msg.uuid:
            checkpoint_id = msg.uuid

    # Rewind to that point
    if checkpoint_id:
        await client.rewind_files(checkpoint_id)
```

### Sandbox Settings

```python
sandbox = {
    "enabled": True,
    "autoAllowBashIfSandboxed": True,
    "excludedCommands": ["git", "docker"],
    "allowUnsandboxedCommands": True,
    "network": {
        "allowUnixSockets": ["/var/run/docker.sock"],
        "allowLocalBinding": True,
    },
    "ignoreViolations": {
        "file": [".env"],
        "network": ["localhost"],
    },
}

options = ClaudeAgentOptions(sandbox=sandbox)
```

### Beta Features

```python
options = ClaudeAgentOptions(
    betas=["context-1m-2025-08-07"],  # 1M context window
)
```

### Plugins

```python
plugins = [
    {"type": "local", "path": "/path/to/plugin"}
]

options = ClaudeAgentOptions(plugins=plugins)
```

---

## 15. Key Differences from TypeScript SDK

| Aspect | Python | TypeScript |
|--------|--------|-----------|
| Constructor | `ClaudeSDKClient(options)` | `new Claude(options)` |
| Query | `await client.query()` | `client.query()` |
| Receive | `client.receive_response()` (stops at Result) | Manual iteration |
| Hooks | Dict + HookMatcher classes | Direct callback arrays |
| Python keywords | `async_`, `continue_` (convert to `async`, `continue`) | Direct field names |
| MCP Tools | `@tool` decorator + `create_sdk_mcp_server()` | Direct tool functions |
| Init | `async with client` | Implicit in ctor |
| Model IDs | Full strings ("claude-opus-4-6-...") | Aliases ("opus", "sonnet") |

---

## 16. Usage in ACLI v1 Codebase

**Current implementation patterns:**
- `ClaudeSDKClient` with `ClaudeAgentOptions`
- Hooks for Bash security validation
- Allowed-tool allowlisting (BUILTIN_TOOLS + PUPPETEER + PLAYWRIGHT)
- MCP stdio servers (puppeteer, playwright)
- Session persistence via ProjectState
- Message type guards (hasattr checks)

**ACLI v1 gaps for v2:**
- No thinking config (use adaptive by default)
- No structured output format
- No file checkpointing
- No agent definitions (needed for multi-agent orchestration)
- No permission callback (`can_use_tool`)
- Basic hook setup (Bash only)

---

## Unresolved Questions

1. **Model routing in Opus 4.6:** Does "claude-opus-4-6-20250514" auto-enable thinking? Or explicit `thinking={"type": "adaptive"}`?
2. **Subagent spawning:** How does Task/subagent protocol interact with ClaudeSDKClient? Are subagents spawned via hooks or via separate agent definitions?
3. **MCP tool naming convention:** Are tool names auto-prefixed with "mcp__<server>__" by SDK or by CLI?
4. **Session forking:** When `fork_session=True`, does Claude Code allocate new session ID or SDK?
5. **Cost tracking across sessions:** Is `ResultMessage.total_cost_usd` cumulative for the entire CLI process lifetime or per session?

---

## Research Methodology

- **Source:** Installed SDK v0.1.49 source (`/Users/nick/Library/Python/3.12/...`)
- **Secondary sources:** Current ACLI v1 usage patterns, docstrings in types.py & client.py
- **Cross-validation:** Field inspection, type annotations, example code in docstrings
- **Coverage:** All public APIs in __init__.py exports
