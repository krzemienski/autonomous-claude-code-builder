"""
Context & Memory Module
========================

Persistent codebase knowledge and cross-session memory.
"""

from .chunker import KnowledgeChunker
from .memory import MemoryManager
from .onboarder import BrownfieldOnboarder
from .store import ContextStore

__all__ = [
    "ContextStore",
    "MemoryManager",
    "KnowledgeChunker",
    "BrownfieldOnboarder",
]
