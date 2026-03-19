"""
Agent Session Logic
===================

Core agent interaction using Claude Agent SDK.
Handles message streaming and tool execution tracking.
"""

from pathlib import Path

from claude_agent_sdk import ClaudeSDKClient
from claude_agent_sdk.types import (
    AssistantMessage,
    RateLimitEvent,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    UserMessage,
)

from ..utils import logger
from .streaming import StreamingHandler


async def run_agent_session(
    client: ClaudeSDKClient,
    prompt: str,
    streaming: StreamingHandler,
) -> tuple[str, str]:
    """
    Run a single agent session with streaming.

    Args:
        client: Claude SDK client
        prompt: Prompt to send
        streaming: Streaming handler for events

    Returns:
        (status, response_text) where status is "continue" or "error"
    """
    logger.info("Starting agent session...")

    try:
        await client.query(prompt)

        response_text = ""
        result_info: dict = {}

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    block_type = type(block).__name__

                    if block_type == "TextBlock" and hasattr(block, "text"):
                        response_text += block.text
                        await streaming.handle_text(block.text)

                    elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                        await streaming.handle_tool_start(
                            block.name, getattr(block, "input", {}),
                        )

            elif isinstance(msg, UserMessage):
                content = msg.content
                if isinstance(content, list):
                    for block in content:
                        block_type = type(block).__name__
                        if block_type == "ToolResultBlock":
                            tc = getattr(block, "content", "")
                            is_error = getattr(block, "is_error", False)

                            if "blocked" in str(tc).lower():
                                await streaming.handle_tool_blocked(
                                    "Bash", str(tc),
                                )
                            elif is_error:
                                await streaming.handle_tool_end(
                                    "", error=str(tc)[:500],
                                )
                            else:
                                await streaming.handle_tool_end(
                                    "", result="Success",
                                )

            elif isinstance(msg, ResultMessage):
                result_info = {
                    "turns": msg.num_turns,
                    "cost_usd": msg.total_cost_usd,
                    "stop_reason": msg.stop_reason,
                    "is_error": msg.is_error,
                }
                logger.info(
                    f"Session result: {msg.num_turns} turns, "
                    f"${msg.total_cost_usd:.4f}, stop={msg.stop_reason}",
                )

            elif isinstance(msg, RateLimitEvent):
                logger.debug("Rate limit event received, continuing...")

            elif isinstance(msg, SystemMessage):
                logger.debug(f"System message: {msg.subtype}")

            elif isinstance(msg, StreamEvent):
                pass  # Low-level stream events — skip

            else:
                logger.debug(f"Unhandled message type: {type(msg).__name__}")

        if result_info.get("is_error"):
            return "error", response_text or "Session ended with error"

        return "continue", response_text

    except Exception as e:
        error_msg = str(e)
        await streaming.handle_error(error_msg)
        logger.error(f"Agent session error: {error_msg}")
        return "error", error_msg


def load_prompt_template(name: str) -> str:
    """Load prompt template from prompts directory."""
    prompts_dir = Path(__file__).parent.parent / "prompts" / "templates"
    template_path = prompts_dir / f"{name}.md"

    if template_path.exists():
        return template_path.read_text()

    # Fallback prompts
    if name == "initializer":
        return """Read app_spec.txt and create:

1. feature_list.json with 100-200 testable features
   - Each feature: {id, component, description, passes: false}
   - Cover all functionality, edge cases, error handling
   - Group by component/module
   - Order from foundational to advanced

2. init.sh setup script (detect tech stack from spec)
   - Python: pip install -e . or poetry install
   - Node: npm install
   - Adapt to what the spec requires

3. Project structure appropriate for the tech stack
   - Python: src/ package, pyproject.toml
   - Node: src/, package.json
   - Create source dirs and config files

Start by reading app_spec.txt."""

    elif name == "coding":
        return """Continue development:

1. Read feature_list.json to see progress
2. Check git status and existing code
3. Set up environment if needed (./init.sh or equivalent)
4. Pick ONE incomplete feature (passes: false)
5. Implement the feature
6. Test by running the project (CLI, API, or script execution)
7. Update feature_list.json (passes: true)
8. Commit changes

Focus on one feature at a time. Test before marking as passing."""

    return f"Error: Unknown prompt template '{name}'"
