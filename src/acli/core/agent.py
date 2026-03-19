"""
Agent Session Logic
===================

Core agent interaction using Claude Agent SDK.
Handles message streaming and tool execution tracking.
"""

from pathlib import Path

from claude_agent_sdk import ClaudeSDKClient

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

        async for msg in client.receive_response():
            msg_type = type(msg).__name__

            if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__

                    if block_type == "TextBlock" and hasattr(block, "text"):
                        text = block.text
                        response_text += text
                        await streaming.handle_text(text)

                    elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                        tool_name = block.name
                        tool_input = getattr(block, "input", {})
                        await streaming.handle_tool_start(tool_name, tool_input)

            elif msg_type == "UserMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__

                    if block_type == "ToolResultBlock":
                        content = getattr(block, "content", "")
                        is_error = getattr(block, "is_error", False)

                        if "blocked" in str(content).lower():
                            # Extract tool name from previous context
                            await streaming.handle_tool_blocked("Bash", str(content))
                        elif is_error:
                            await streaming.handle_tool_end("", error=str(content)[:500])
                        else:
                            await streaming.handle_tool_end("", result="Success")

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
        return """Read the app_spec.txt file and create:

1. feature_list.json with ~200 detailed test cases
   - Each feature: {id, component, description, passes: false}
   - Cover all UI components, interactions, edge cases
   - Group by component

2. init.sh script for environment setup
   - Install dependencies
   - Configure development server

3. Initial project structure
   - package.json
   - Source directories
   - Configuration files

Start by reading app_spec.txt, then generate the feature list."""

    elif name == "coding":
        return """Continue development:

1. Read feature_list.json to see progress
2. Check git status
3. Start dev server if not running
4. Pick ONE incomplete feature (passes: false)
5. Implement and test using browser automation
6. Update feature_list.json (passes: true)
7. Commit changes

Focus on one feature at a time. Test thoroughly."""

    return f"Error: Unknown prompt template '{name}'"
