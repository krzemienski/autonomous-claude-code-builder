# Phase 1: Core Infrastructure — Routing, Context, Model Updates

## Priority: P0 | Depends: None | Gates: G1, G2, G3

**Objective**: Update SDK client for Claude 4.6 models, extend streaming events, create routing module, create context/memory store.

**Skills to invoke before starting**: `/functional-validation`, `/gate-validation-discipline`

---

## Task 1.1: Update SDK Client for Claude 4.6

### Files Modified

**`src/acli/core/client.py`** (149 lines currently)

**Step 1**: Add model constants after line 16 (after imports, before PUPPETEER_TOOLS):
```python
# Model routing constants (Claude 4.6)
MODEL_OPUS = "claude-opus-4-6-20250514"
MODEL_SONNET = "claude-sonnet-4-6-20250514"

# Thinking configuration per tier
THINKING_CONFIG = {
    "opus": {"type": "adaptive"},
    "sonnet": {"type": "adaptive"},
}

# Effort level per tier (separate field on ClaudeAgentOptions)
EFFORT_CONFIG = {
    "opus": "high",
    "sonnet": None,  # Default adaptive
}
```

**Step 2**: Update `create_sdk_client()` signature at line 71:
```python
# BEFORE (line 71-75):
def create_sdk_client(
    project_dir: Path,
    model: str,
    system_prompt: str | None = None,
) -> ClaudeSDKClient:

# AFTER:
def create_sdk_client(
    project_dir: Path,
    model: str | None = None,
    system_prompt: str | None = None,
    model_tier: Literal["opus", "sonnet"] = "sonnet",
) -> ClaudeSDKClient:
```

**Step 3**: Update the ClaudeSDKClient constructor call at line 137-148:
```python
# BEFORE:
    return ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=model,
            ...
            max_turns=100,
            ...
        )
    )

# AFTER:
    resolved_model = model or (MODEL_OPUS if model_tier == "opus" else MODEL_SONNET)
    thinking = THINKING_CONFIG.get(model_tier, {"type": "adaptive"})
    effort = EFFORT_CONFIG.get(model_tier)

    return ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=resolved_model,
            thinking=thinking,
            effort=effort,
            system_prompt=system_prompt or default_system,
            allowed_tools=[*BUILTIN_TOOLS, *PUPPETEER_TOOLS, *PLAYWRIGHT_TOOLS],
            mcp_servers=mcp_servers,
            hooks=hooks,
            max_turns=200,  # Increased for v2 longer sessions
            cwd=str(project_dir),
            settings=str(settings_file),
        )
    )
```

**Step 4**: Add `Literal` to imports at line 12:
```python
# BEFORE:
from typing import Any, Literal, cast

# Already has Literal — no change needed
```

### Model String Migration (6 files, 11 references)

**`src/acli/cli.py`**:
- Line 211: `] = "claude-sonnet-4-20250514",` → `] = "claude-sonnet-4-6-20250514",`
- Line 454: `"model": "claude-sonnet-4-20250514",` → `"model": "claude-sonnet-4-6-20250514",`
- Line 565: `] = "claude-sonnet-4-20250514",` → `] = "claude-sonnet-4-6-20250514",`

**`src/acli/core/orchestrator.py`**:
- Line 38: `model: str = "claude-sonnet-4-20250514",` → `model: str = "claude-sonnet-4-6-20250514",`
- Line 261: `model: str = "claude-opus-46",` → `model: str = "claude-opus-4-6-20250514",` (TYPO FIX)

**`src/acli/spec/enhancer.py`**:
- Line 60: `model: str = "claude-sonnet-4-20250514",` → `model: str = "claude-sonnet-4-6-20250514",`
- Line 110: `model: str = "claude-sonnet-4-20250514",` → `model: str = "claude-sonnet-4-6-20250514",`
- Line 187: `model: str = "claude-sonnet-4-20250514",` → `model: str = "claude-sonnet-4-6-20250514",`

**`src/acli/spec/refinement.py`**:
- Line 89: `model: str = "claude-sonnet-4-20250514",` → `model: str = "claude-sonnet-4-6-20250514",`

**`src/acli/integration/claude_config.py`**:
- Line 115: `return config.default_model or "claude-sonnet-4-20250514"` → `return config.default_model or "claude-sonnet-4-6-20250514"`

---

## Task 1.2: Extend Streaming Event Types

### File Modified: `src/acli/core/streaming.py` (198 lines)

**Step 1**: Add 13 new values to `EventType` enum after line 28 (after `PROGRESS = "progress"`):
```python
    # v2 additions — multi-agent orchestration events
    AGENT_SPAWN = "agent_spawn"
    AGENT_COMPLETE = "agent_complete"
    ANALYSIS_UPDATE = "analysis_update"
    PLAN_CREATED = "plan_created"
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    GATE_START = "gate_start"
    GATE_RESULT = "gate_result"
    CONTEXT_UPDATE = "context_update"
    MEMORY_UPDATE = "memory_update"
    THINKING = "thinking"
    MOCK_DETECTED = "mock_detected"
    PROMPT_RECEIVED = "prompt_received"
```

**Step 2**: Add new fields to `StreamEvent` dataclass after line 55 (after `features_total`):
```python
    # v2 agent fields
    agent_id: str = ""
    agent_type: str = ""
    model: str = ""

    # v2 gate fields
    gate_id: str = ""
    gate_status: str = ""
    evidence_path: str = ""

    # v2 phase fields
    phase_id: str = ""
    phase_name: str = ""

    # v2 memory fields
    memory_fact: str = ""
```

**Step 3**: Add 8 new handler methods to `StreamingHandler` after line 197 (after `handle_progress`):
```python
    async def handle_agent_spawn(self, agent_id: str, agent_type: str, model: str) -> None:
        """Handle new agent creation."""
        event = StreamEvent(
            type=EventType.AGENT_SPAWN,
            agent_id=agent_id,
            agent_type=agent_type,
            model=model,
        )
        await self.emit(event)

    async def handle_agent_complete(self, agent_id: str, status: str) -> None:
        """Handle agent completion."""
        event = StreamEvent(
            type=EventType.AGENT_COMPLETE,
            agent_id=agent_id,
            gate_status=status,
        )
        await self.emit(event)

    async def handle_gate_start(self, gate_id: str, criteria: str) -> None:
        """Handle validation gate start."""
        event = StreamEvent(
            type=EventType.GATE_START,
            gate_id=gate_id,
            text=criteria,
        )
        await self.emit(event)

    async def handle_gate_result(self, gate_id: str, status: str, evidence_path: str) -> None:
        """Handle validation gate result."""
        event = StreamEvent(
            type=EventType.GATE_RESULT,
            gate_id=gate_id,
            gate_status=status,
            evidence_path=evidence_path,
        )
        await self.emit(event)

    async def handle_context_update(self, key: str, summary: str) -> None:
        """Handle context store update."""
        event = StreamEvent(
            type=EventType.CONTEXT_UPDATE,
            text=f"{key}: {summary}",
        )
        await self.emit(event)

    async def handle_memory_update(self, fact: str) -> None:
        """Handle memory fact addition."""
        event = StreamEvent(
            type=EventType.MEMORY_UPDATE,
            memory_fact=fact,
        )
        await self.emit(event)

    async def handle_phase_start(self, phase_id: str, phase_name: str) -> None:
        """Handle phase start."""
        event = StreamEvent(
            type=EventType.PHASE_START,
            phase_id=phase_id,
            phase_name=phase_name,
        )
        await self.emit(event)

    async def handle_phase_end(self, phase_id: str, status: str) -> None:
        """Handle phase completion."""
        event = StreamEvent(
            type=EventType.PHASE_END,
            phase_id=phase_id,
            gate_status=status,
        )
        await self.emit(event)
```

---

## Task 1.3: Create Routing Module

### New Files

**`src/acli/routing/__init__.py`**:
```python
"""Prompt routing and workflow classification."""

from .router import PromptRouter
from .workflows import WorkflowConfig, WorkflowType

__all__ = ["PromptRouter", "WorkflowType", "WorkflowConfig"]
```

**`src/acli/routing/workflows.py`** (~50 lines):
```python
"""Workflow type definitions for prompt classification."""

from dataclasses import dataclass, field
from enum import Enum


class WorkflowType(str, Enum):
    """Classification of user prompts into workflow patterns."""

    GREENFIELD_APP = "greenfield_app"
    BROWNFIELD_ONBOARD = "brownfield_onboard"
    BROWNFIELD_TASK = "brownfield_task"
    REFACTOR = "refactor"
    DEBUG = "debug"
    CLI_TOOL = "cli_tool"
    IOS_APP = "ios_app"
    FREE_TASK = "free_task"


@dataclass
class WorkflowConfig:
    """Configuration for a classified workflow."""

    workflow_type: WorkflowType
    requires_onboarding: bool
    agent_sequence: list[str] = field(default_factory=list)
    model_tier: str = "sonnet"
    platform: str = "generic"
```

**`src/acli/routing/router.py`** (~120 lines):
```python
"""Prompt classification into workflow types."""

import re
from pathlib import Path

from .workflows import WorkflowConfig, WorkflowType

# Source file extensions that indicate a real codebase
SOURCE_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".swift", ".rs", ".go", ".java", ".kt", ".rb"}

# Intent patterns for classification
DEBUG_PATTERNS = re.compile(r"\b(fix|debug|broken|crash|error|bug|fail|issue)\b", re.IGNORECASE)
REFACTOR_PATTERNS = re.compile(r"\b(refactor|migrate|convert|upgrade|modernize|rewrite)\b", re.IGNORECASE)
ADD_PATTERNS = re.compile(r"\b(add|implement|create|build|make|develop|set up|integrate)\b", re.IGNORECASE)


class PromptRouter:
    """Classifies any user prompt into a WorkflowType with config."""

    def classify(self, prompt: str, project_dir: Path) -> WorkflowConfig:
        """Classify prompt + project state into workflow config."""
        has_xcodeproj = self._has_ios_project(project_dir)
        has_cargo = (project_dir / "Cargo.toml").exists()
        has_spec = (project_dir / "app_spec.txt").exists()
        source_count = self._count_source_files(project_dir)
        is_onboarded = (project_dir / ".acli" / "context" / "codebase_analysis.json").exists()

        # Priority 1: iOS project
        if has_xcodeproj:
            return WorkflowConfig(
                workflow_type=WorkflowType.IOS_APP,
                requires_onboarding=not is_onboarded and source_count > 3,
                agent_sequence=["analyst", "planner", "implementer", "validator"],
                model_tier="sonnet",
                platform="ios",
            )

        # Priority 2: CLI/Rust project
        if has_cargo:
            return WorkflowConfig(
                workflow_type=WorkflowType.CLI_TOOL,
                requires_onboarding=not is_onboarded and source_count > 3,
                agent_sequence=["planner", "implementer", "validator"],
                model_tier="sonnet",
                platform="cli",
            )

        # Priority 3: Greenfield (spec present, no significant source)
        if has_spec and source_count <= 3:
            return WorkflowConfig(
                workflow_type=WorkflowType.GREENFIELD_APP,
                requires_onboarding=False,
                agent_sequence=["planner", "implementer", "validator", "reporter"],
                model_tier="sonnet",
                platform="generic",
            )

        # Priority 4-6: Brownfield variants (significant source files)
        if source_count > 3:
            # Debug intent
            if DEBUG_PATTERNS.search(prompt):
                return WorkflowConfig(
                    workflow_type=WorkflowType.DEBUG,
                    requires_onboarding=not is_onboarded,
                    agent_sequence=["analyst", "planner", "implementer", "validator"],
                    model_tier="opus",
                    platform="generic",
                )

            # Refactor intent
            if REFACTOR_PATTERNS.search(prompt):
                return WorkflowConfig(
                    workflow_type=WorkflowType.REFACTOR,
                    requires_onboarding=not is_onboarded,
                    agent_sequence=["analyst", "planner", "implementer", "validator"],
                    model_tier="opus",
                    platform="generic",
                )

            # Add/implement intent (brownfield task)
            if ADD_PATTERNS.search(prompt):
                return WorkflowConfig(
                    workflow_type=WorkflowType.BROWNFIELD_TASK,
                    requires_onboarding=not is_onboarded,
                    agent_sequence=["analyst", "planner", "implementer", "validator"],
                    model_tier="sonnet",
                    platform="generic",
                )

            # Source files but no clear intent → needs onboarding
            return WorkflowConfig(
                workflow_type=WorkflowType.BROWNFIELD_ONBOARD,
                requires_onboarding=True,
                agent_sequence=["analyst", "planner"],
                model_tier="opus",
                platform="generic",
            )

        # Default: free task
        return WorkflowConfig(
            workflow_type=WorkflowType.FREE_TASK,
            requires_onboarding=False,
            agent_sequence=["planner", "implementer"],
            model_tier="sonnet",
            platform="generic",
        )

    def _has_ios_project(self, project_dir: Path) -> bool:
        """Check for iOS project indicators."""
        for item in project_dir.iterdir():
            if item.suffix in (".xcodeproj", ".xcworkspace"):
                return True
        return False

    def _count_source_files(self, project_dir: Path, max_depth: int = 4) -> int:
        """Count non-config source files recursively."""
        count = 0
        for path in project_dir.rglob("*"):
            if path.is_file() and path.suffix in SOURCE_EXTENSIONS:
                # Skip node_modules, .git, __pycache__, etc.
                parts = path.parts
                if any(p.startswith(".") or p in ("node_modules", "__pycache__", "venv", ".venv") for p in parts):
                    continue
                count += 1
                if count > 10:  # Early exit — clearly a codebase
                    return count
        return count
```

---

## Task 1.4: Create Context Store & Memory Manager

### New Files

**`src/acli/context/__init__.py`**:
```python
"""Context and memory management for brownfield projects."""

from .chunker import KnowledgeChunker
from .memory import MemoryManager
from .onboarder import BrownfieldOnboarder
from .store import ContextStore

__all__ = ["ContextStore", "MemoryManager", "KnowledgeChunker", "BrownfieldOnboarder"]
```

**`src/acli/context/store.py`** (~120 lines):
```python
"""Persistent codebase knowledge store."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ContextStore:
    """Reads/writes codebase knowledge to .acli/context/ directory."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.context_dir = project_dir / ".acli" / "context"

    def initialize(self) -> None:
        """Create .acli/context/ directory structure."""
        self.context_dir.mkdir(parents=True, exist_ok=True)
        (self.context_dir / "knowledge_chunks").mkdir(exist_ok=True)

    def store_analysis(self, analysis: dict[str, Any]) -> None:
        """Save full codebase analysis."""
        self._write_json("codebase_analysis.json", analysis)

    def store_tech_stack(self, tech_stack: dict[str, Any]) -> None:
        """Save detected technology stack."""
        self._write_json("tech_stack.json", tech_stack)

    def store_conventions(self, conventions: dict[str, Any]) -> None:
        """Save detected code conventions."""
        self._write_json("conventions.json", conventions)

    def log_decision(self, key: str, value: str, confidence: float) -> None:
        """Append decision to JSONL log."""
        entry = {
            "key": key,
            "value": value,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }
        decisions_file = self.context_dir / "decisions.jsonl"
        with open(decisions_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_analysis(self) -> dict[str, Any] | None:
        """Retrieve codebase analysis."""
        return self._read_json("codebase_analysis.json")

    def get_tech_stack(self) -> dict[str, Any] | None:
        """Retrieve tech stack."""
        return self._read_json("tech_stack.json")

    def get_context_summary(self) -> str:
        """Human-readable summary for agent system prompts."""
        parts: list[str] = []
        tech = self.get_tech_stack()
        if tech:
            parts.append(f"Tech Stack: {json.dumps(tech)}")
        analysis = self.get_analysis()
        if analysis:
            parts.append(f"Architecture: {json.dumps(analysis)}")
        decisions = self._read_decisions()
        if decisions:
            parts.append(f"Decisions: {len(decisions)} logged")
            for d in decisions[-5:]:
                parts.append(f"  - {d['key']}: {d['value']} (conf: {d['confidence']})")
        return "\n".join(parts) if parts else "No context available yet."

    def is_onboarded(self) -> bool:
        """True if codebase_analysis.json exists and is non-empty."""
        analysis_file = self.context_dir / "codebase_analysis.json"
        if not analysis_file.exists():
            return False
        content = analysis_file.read_text().strip()
        return content not in ("", "{}", "null")

    def _write_json(self, filename: str, data: dict[str, Any]) -> None:
        self.context_dir.mkdir(parents=True, exist_ok=True)
        with open(self.context_dir / filename, "w") as f:
            json.dump(data, f, indent=2)

    def _read_json(self, filename: str) -> dict[str, Any] | None:
        path = self.context_dir / filename
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def _read_decisions(self) -> list[dict[str, Any]]:
        path = self.context_dir / "decisions.jsonl"
        if not path.exists():
            return []
        decisions = []
        with open(path) as f:
            for line in f:
                if line.strip():
                    decisions.append(json.loads(line))
        return decisions
```

**`src/acli/context/memory.py`** (~80 lines):
```python
"""Cross-session memory manager."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class MemoryManager:
    """Stores and retrieves cross-session facts."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.memory_dir = project_dir / ".acli" / "memory"
        self.memory_file = self.memory_dir / "project_memory.json"
        self._facts: list[dict[str, Any]] = self._load()

    def add_fact(self, category: str, fact: str) -> None:
        """Add a fact to memory."""
        entry = {
            "category": category,
            "fact": fact,
            "timestamp": datetime.now().isoformat(),
        }
        self._facts.append(entry)
        self._save()

    def get_facts(self, category: str | None = None) -> list[dict[str, Any]]:
        """Get facts, optionally filtered by category."""
        if category is None:
            return list(self._facts)
        return [f for f in self._facts if f["category"] == category]

    def get_injection_prompt(self) -> str:
        """Format facts for system prompt injection."""
        if not self._facts:
            return "No project memory yet."
        lines = ["## Project Memory"]
        by_category: dict[str, list[str]] = {}
        for f in self._facts:
            cat = f["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f["fact"])
        for cat, facts in by_category.items():
            lines.append(f"\n### {cat}")
            for fact in facts:
                lines.append(f"- {fact}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all facts."""
        self._facts = []
        self._save()

    @property
    def fact_count(self) -> int:
        return len(self._facts)

    def _load(self) -> list[dict[str, Any]]:
        if not self.memory_file.exists():
            return []
        with open(self.memory_file) as f:
            return json.load(f)

    def _save(self) -> None:
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, "w") as f:
            json.dump(self._facts, f, indent=2)
```

**`src/acli/context/chunker.py`** (~60 lines):
```python
"""Codebase knowledge chunking for retrieval."""

from pathlib import Path
from typing import Any

SOURCE_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".swift", ".rs", ".go", ".java"}
SKIP_DIRS = {"node_modules", "__pycache__", ".git", ".venv", "venv", ".acli"}


class KnowledgeChunker:
    """Chunks codebase into retrievable segments."""

    def chunk_codebase(self, project_dir: Path, max_chunk_size: int = 4000) -> list[dict[str, Any]]:
        """Segment all source files into chunks."""
        chunks: list[dict[str, Any]] = []
        for path in sorted(project_dir.rglob("*")):
            if not path.is_file() or path.suffix not in SOURCE_EXTENSIONS:
                continue
            if any(skip in path.parts for skip in SKIP_DIRS):
                continue
            content = path.read_text(errors="replace")
            rel_path = str(path.relative_to(project_dir))
            if len(content) <= max_chunk_size:
                chunks.append({"path": rel_path, "content": content, "chunk_index": 0})
            else:
                lines = content.splitlines(keepends=True)
                current_chunk: list[str] = []
                current_size = 0
                chunk_idx = 0
                for line in lines:
                    current_chunk.append(line)
                    current_size += len(line)
                    if current_size >= max_chunk_size:
                        chunks.append({
                            "path": rel_path,
                            "content": "".join(current_chunk),
                            "chunk_index": chunk_idx,
                        })
                        current_chunk = []
                        current_size = 0
                        chunk_idx += 1
                if current_chunk:
                    chunks.append({
                        "path": rel_path,
                        "content": "".join(current_chunk),
                        "chunk_index": chunk_idx,
                    })
        return chunks

    def get_relevant_chunks(self, query: str, top_k: int = 3) -> list[str]:
        """Simple keyword-based chunk retrieval (no embeddings)."""
        # Placeholder — returns empty until embeddings or BM25 added
        return []
```

**`src/acli/context/onboarder.py`** (~90 lines):
```python
"""Brownfield codebase onboarding."""

import os
from pathlib import Path
from typing import Any

from ..core.streaming import StreamingHandler
from .chunker import KnowledgeChunker, SOURCE_EXTENSIONS, SKIP_DIRS
from .store import ContextStore


class BrownfieldOnboarder:
    """Full codebase analysis and context population."""

    async def onboard(self, project_dir: Path, streaming: StreamingHandler) -> dict[str, Any]:
        """Run full onboarding sequence."""
        store = ContextStore(project_dir)
        store.initialize()

        await streaming.handle_context_update("onboarding", "Starting codebase analysis")

        tech_stack = self.detect_tech_stack(project_dir)
        store.store_tech_stack(tech_stack)
        await streaming.handle_context_update("tech_stack", str(tech_stack))

        conventions = self.detect_conventions(project_dir)
        store.store_conventions(conventions)

        architecture = self.map_architecture(project_dir)
        store.store_analysis(architecture)
        await streaming.handle_context_update("analysis", f"{architecture.get('total_files', 0)} files mapped")

        chunker = KnowledgeChunker()
        chunks = chunker.chunk_codebase(project_dir)
        await streaming.handle_context_update("chunks", f"{len(chunks)} knowledge chunks created")

        return {"tech_stack": tech_stack, "architecture": architecture, "chunks": len(chunks)}

    def detect_tech_stack(self, project_dir: Path) -> dict[str, Any]:
        """Detect technology stack from project files."""
        stack: dict[str, Any] = {}
        if (project_dir / "pyproject.toml").exists() or (project_dir / "setup.py").exists():
            stack["language"] = "Python"
        if (project_dir / "package.json").exists():
            stack["language"] = stack.get("language", "JavaScript")
            stack["runtime"] = "Node.js"
        if (project_dir / "Cargo.toml").exists():
            stack["language"] = "Rust"
        if (project_dir / "Dockerfile").exists():
            stack["containerization"] = "Docker"
        if (project_dir / "docker-compose.yml").exists() or (project_dir / "docker-compose.yaml").exists():
            stack["orchestration"] = "Docker Compose"
        if (project_dir / "poetry.lock").exists():
            stack["package_manager"] = "Poetry"
        if (project_dir / "requirements.txt").exists():
            stack["package_manager"] = stack.get("package_manager", "pip")
        return stack

    def detect_conventions(self, project_dir: Path) -> dict[str, Any]:
        """Detect code conventions from existing files."""
        conventions: dict[str, Any] = {}
        py_files = list(project_dir.rglob("*.py"))
        py_files = [f for f in py_files if not any(s in f.parts for s in SKIP_DIRS)]
        if py_files:
            sample = py_files[0].read_text(errors="replace")
            conventions["has_type_hints"] = ": " in sample and " -> " in sample
            conventions["has_docstrings"] = '"""' in sample or "'''" in sample
            conventions["uses_async"] = "async " in sample
        return conventions

    def map_architecture(self, project_dir: Path) -> dict[str, Any]:
        """Map file structure and architecture."""
        total_files = 0
        total_loc = 0
        file_types: dict[str, int] = {}
        directories: list[str] = []

        for path in project_dir.rglob("*"):
            if any(s in path.parts for s in SKIP_DIRS):
                continue
            if path.is_dir():
                rel = str(path.relative_to(project_dir))
                if rel != ".":
                    directories.append(rel)
            elif path.is_file() and path.suffix in SOURCE_EXTENSIONS:
                total_files += 1
                total_loc += sum(1 for _ in open(path, errors="replace"))
                ext = path.suffix
                file_types[ext] = file_types.get(ext, 0) + 1

        return {
            "total_files": total_files,
            "total_loc": total_loc,
            "file_types": file_types,
            "directories": directories[:50],
        }
```

---

## Gate G1: Install & Version Check

**Protocol**: Follow [gate-protocol.md](../gate-protocol.md)

**Pre-gate**: Invoke `/functional-validation`, `/gate-validation-discipline`

**Execute**:
```bash
mkdir -p evidence/G1

# 1. Install package
cd /Users/nick/Desktop/claude-code-builder-agents-sdk
pip install -e ".[dev]" 2>&1 | tail -5 | tee evidence/G1/install.txt
echo "EXIT_CODE: $?" >> evidence/G1/install.txt

# 2. Verify CLI responds
python -m acli --version 2>&1 | tee evidence/G1/version.txt

# 3. Verify config shows new model
python -m acli config list 2>&1 | tee evidence/G1/config.txt

# 4. Verify imports work (supplementary, not primary)
python -c "from acli.core.client import MODEL_OPUS, MODEL_SONNET; print(f'OPUS={MODEL_OPUS}'); print(f'SONNET={MODEL_SONNET}')" 2>&1 | tee evidence/G1/models.txt
```

**PASS criteria**:
- [ ] pip install exits 0
- [ ] `acli --version` prints version string
- [ ] `acli config list` shows `model` key with `claude-sonnet-4-6-20250514`
- [ ] MODEL_OPUS = `claude-opus-4-6-20250514`, MODEL_SONNET = `claude-sonnet-4-6-20250514`

**Dual verification**: 2 agents read evidence/G1/ files, cite specific output lines, confirm PASS

---

## Gate G2: No Stale Model Strings

**Execute**:
```bash
mkdir -p evidence/G2

# Must return ZERO matches
grep -rn "claude-sonnet-4-20250514" src/ 2>&1 | tee evidence/G2/stale-sonnet.txt
grep -rn "claude-opus-46" src/ 2>&1 | tee evidence/G2/stale-opus-typo.txt

# Verify new event types exist
python -c "
from acli.core.streaming import EventType
new = ['AGENT_SPAWN','AGENT_COMPLETE','ANALYSIS_UPDATE','PLAN_CREATED','PHASE_START','PHASE_END','GATE_START','GATE_RESULT','CONTEXT_UPDATE','MEMORY_UPDATE','THINKING','MOCK_DETECTED','PROMPT_RECEIVED']
for t in new:
    assert hasattr(EventType, t), f'MISSING: {t}'
    print(f'EventType.{t}: OK')
print(f'All {len(new)} new event types: PASS')
" 2>&1 | tee evidence/G2/event-types.txt

# Verify router imports
python -c "
from acli.routing.router import PromptRouter
from acli.routing.workflows import WorkflowType, WorkflowConfig
print('Router imports: PASS')
" 2>&1 | tee evidence/G2/router-imports.txt
```

**PASS criteria**:
- [ ] `stale-sonnet.txt` is empty (0 matches)
- [ ] `stale-opus-typo.txt` is empty (0 matches)
- [ ] All 13 EventType values exist
- [ ] Router module imports cleanly

**Dual verification**: 2 agents read evidence/G2/ files, confirm empty grep output and PASS lines

---

## Gate G3: Context Store + Router Classification with ALR

**Execute**:
```bash
mkdir -p evidence/G3

# 1. Init a real project with ALR spec
rm -rf /tmp/acli-g3-test
python -m acli init /tmp/acli-g3-test --no-interactive 2>&1 | tee evidence/G3/init.txt
echo "EXIT_CODE: $?" >> evidence/G3/init.txt

# 2. Copy ALR spec as app_spec.txt
cp alr-claude.md /tmp/acli-g3-test/app_spec.txt

# 3. Verify project structure
ls -la /tmp/acli-g3-test/ 2>&1 | tee evidence/G3/ls.txt

# 4. Test router classifies ALR as greenfield
python -c "
from pathlib import Path
from acli.routing.router import PromptRouter
from acli.routing.workflows import WorkflowType

router = PromptRouter()

# ALR with app_spec.txt → GREENFIELD_APP
r = router.classify('Build the Awesome-List Researcher', Path('/tmp/acli-g3-test'))
print(f'ALR classification: {r.workflow_type}')
print(f'Requires onboarding: {r.requires_onboarding}')
print(f'Agent sequence: {r.agent_sequence}')
assert r.workflow_type == WorkflowType.GREENFIELD_APP, f'Expected GREENFIELD_APP, got {r.workflow_type}'
print('ALR Router: PASS')
" 2>&1 | tee evidence/G3/router-alr.txt

# 5. Test context store round-trip
python -c "
from pathlib import Path
from acli.context.store import ContextStore
from acli.context.memory import MemoryManager

p = Path('/tmp/acli-g3-test')
store = ContextStore(p)
store.initialize()
store.store_tech_stack({'language': 'Python', 'framework': 'Claude Agent SDK', 'container': 'Docker'})
retrieved = store.get_tech_stack()
print(f'Stored tech stack: {retrieved}')
assert retrieved['language'] == 'Python'
store.store_analysis({'files': 15, 'architecture': 'multi-agent pipeline'})
assert store.is_onboarded()
summary = store.get_context_summary()
print(f'Context summary length: {len(summary)} chars')
assert len(summary) > 0
print('ContextStore: PASS')

mem = MemoryManager(p)
mem.add_fact('architecture', 'Uses Claude Agent SDK with 5 agent types')
mem.add_fact('architecture', 'Docker-first execution model')
mem.add_fact('tools', 'Custom MCP tools: web_search, browse_url, github_info, validate_url')
assert mem.fact_count == 3
prompt = mem.get_injection_prompt()
assert 'Claude Agent SDK' in prompt
print(f'Memory facts: {mem.fact_count}')
print('MemoryManager: PASS')
" 2>&1 | tee evidence/G3/context-memory.txt

# 6. Verify .acli directory was created
ls -la /tmp/acli-g3-test/.acli/context/ 2>&1 | tee evidence/G3/acli-context-dir.txt
cat /tmp/acli-g3-test/.acli/context/tech_stack.json 2>&1 | tee evidence/G3/tech-stack-content.txt
```

**PASS criteria**:
- [ ] `acli init` creates project (exit 0)
- [ ] Project has app_spec.txt, .gitignore
- [ ] Router classifies ALR as GREENFIELD_APP
- [ ] ContextStore stores and retrieves tech stack correctly
- [ ] MemoryManager stores 3 facts, produces injection prompt containing "Claude Agent SDK"
- [ ] `.acli/context/tech_stack.json` exists with real content
- [ ] `.acli/context/codebase_analysis.json` exists and `is_onboarded()` returns True

**Dual verification**: 2 agents read all evidence/G3/ files, cite specific output, confirm PASS

---

## Phase 1 Cumulative Gate (PG-1)

Re-run ALL G1 + G2 + G3 checks to catch regressions. If any fail, fix and re-run entire PG-1.

```bash
mkdir -p evidence/PG1

# Quick regression: all imports + no stale strings + router + context
python -c "
from acli.core.client import MODEL_OPUS, MODEL_SONNET, create_sdk_client
from acli.core.streaming import EventType, StreamEvent, StreamingHandler, StreamBuffer
from acli.routing.router import PromptRouter
from acli.routing.workflows import WorkflowType, WorkflowConfig
from acli.context.store import ContextStore
from acli.context.memory import MemoryManager
from acli.context.chunker import KnowledgeChunker
from acli.context.onboarder import BrownfieldOnboarder

assert MODEL_OPUS == 'claude-opus-4-6-20250514'
assert MODEL_SONNET == 'claude-sonnet-4-6-20250514'
assert hasattr(EventType, 'AGENT_SPAWN')
assert hasattr(EventType, 'GATE_RESULT')
assert hasattr(EventType, 'MOCK_DETECTED')

import subprocess
result = subprocess.run(['grep', '-r', 'claude-sonnet-4-20250514', 'src/'], capture_output=True, text=True)
assert result.stdout.strip() == '', f'STALE: {result.stdout}'

print('PHASE 1 CUMULATIVE GATE: ALL PASS')
" 2>&1 | tee evidence/PG1/cumulative.txt
```

**PASS criteria**: All imports succeed, all assertions pass, zero stale strings, exit 0

**Verdict**: PASS → proceed to Phase 2 | FAIL → fix → re-run PG-1
