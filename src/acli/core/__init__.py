"""Core module exports."""

from .agent import load_prompt_template, run_agent_session
from .client import (
    BUILTIN_TOOLS,
    PLAYWRIGHT_TOOLS,
    PUPPETEER_TOOLS,
    create_sdk_client,
)
from .orchestrator_v1 import AgentOrchestrator, run_autonomous_agent
from .orchestrator_v2 import EnhancedOrchestrator
from .session import ProjectState, SessionLogger, SessionState, get_project_state
from .streaming import EventType, StreamBuffer, StreamEvent, StreamingHandler

__all__ = [
    # Session
    "SessionState",
    "SessionLogger",
    "ProjectState",
    "get_project_state",
    # Streaming
    "StreamEvent",
    "EventType",
    "StreamBuffer",
    "StreamingHandler",
    # Client
    "create_sdk_client",
    "BUILTIN_TOOLS",
    "PUPPETEER_TOOLS",
    "PLAYWRIGHT_TOOLS",
    # Agent
    "run_agent_session",
    "load_prompt_template",
    # Orchestrator (v1 — backwards compat)
    "AgentOrchestrator",
    "run_autonomous_agent",
    # Orchestrator (v2 — default)
    "EnhancedOrchestrator",
]
