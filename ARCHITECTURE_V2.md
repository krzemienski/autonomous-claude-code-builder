# ACLI v2 — Full-Fledged Autonomous Claude Code Builder
## System Architecture Design & Execution Blueprint

> **Codename**: Shannon-ACLI (after Claude Shannon — information theory meets autonomous orchestration)
> **Target**: Production-grade autonomous coding system that handles ANY prompt, ANY project type (greenfield + brownfield), with meticulous validation, full TUI visibility, and deep context/memory management.

---

## 1. EXECUTIVE VISION

The current ACLI v1 is a solid foundation: a two-agent pattern (Initializer + Coding), cyberpunk TUI, security hooks, spec enhancement, and progress tracking across ~7,300 LOC. But it's constrained to a narrow flow — greenfield web apps with feature_list.json progression and browser-based testing.

**ACLI v2 transforms this into a universal autonomous coding system** that:

1. **Accepts any prompt** — not just "build an app from spec" but "refactor this codebase," "add auth to my existing API," "migrate from React to Svelte," "fix these 12 bugs," "write a CLI tool," "build an iOS app"
2. **Handles brownfield projects** — onboards existing codebases with deep analysis, context extraction, memory population, and dependency mapping before touching a single line
3. **Uses multi-agent orchestration** — not just 2 agents but a dynamic agent graph: Analyst → Planner → Implementer → Validator → Reporter, with sub-agents spawned per-task
4. **Enforces functional validation** — the Iron Rule throughout: no mocks, no stubs, real-system evidence at every gate
5. **Shows everything in the TUI** — every agent decision, every SDK call, every validation gate, every context update, streaming in real-time
6. **Maintains deep context/memory** — session persistence, cross-session memory, codebase knowledge graphs, decision logs
7. **Uses latest models** — `claude-opus-4-6` for planning/analysis, `claude-sonnet-4-6` for implementation, with adaptive thinking

---

## 2. HIGH-LEVEL SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ACLI v2 — Shannon Architecture                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────────────────────────────────────────┐  │
│  │  TUI Layer   │    │             Prompt Router                        │  │
│  │  (Textual)   │◄──►│  Classifies ANY input → agent graph selection    │  │
│  │              │    │  greenfield | brownfield | task | debug | free   │  │
│  │  ┌─────────┐│    └──────────────────────────────────────────────────┘  │
│  │  │Agent    ││              │                                           │
│  │  │Graph    ││              ▼                                           │
│  │  │Viz      ││    ┌──────────────────────────────────────────────────┐  │
│  │  ├─────────┤│    │         Orchestration Engine                     │  │
│  │  │Log      ││    │                                                  │  │
│  │  │Stream   ││◄───│  Dynamic agent graph execution with:             │  │
│  │  ├─────────┤│    │  • Phase-gated progression                       │  │
│  │  │Context  ││    │  • Sub-agent spawning per task                   │  │
│  │  │Explorer ││    │  • Parallel execution where safe                 │  │
│  │  ├─────────┤│    │  • Validation gates between phases               │  │
│  │  │Validate ││    │  • Error recovery with backtracking              │  │
│  │  │Gates    ││    └──────────────────────────────────────────────────┘  │
│  │  ├─────────┤│              │                                           │
│  │  │Prompt   ││              ▼                                           │
│  │  │Input    ││    ┌──────────────────────────────────────────────────┐  │
│  │  └─────────┘│    │              Agent Pool                          │  │
│  └──────────────┘    │                                                  │  │
│                      │  ┌─────────┐ ┌──────────┐ ┌──────────────────┐ │  │
│                      │  │Analyst  │ │Planner   │ │Implementer       │ │  │
│                      │  │Agent    │ │Agent     │ │Agent(s)          │ │  │
│                      │  │(Opus)   │ │(Opus)    │ │(Sonnet)          │ │  │
│                      │  └─────────┘ └──────────┘ └──────────────────┘ │  │
│                      │  ┌─────────┐ ┌──────────┐ ┌──────────────────┐ │  │
│                      │  │Validator│ │Reporter  │ │Context           │ │  │
│                      │  │Agent    │ │Agent     │ │Manager Agent     │ │  │
│                      │  │(Sonnet) │ │(Sonnet)  │ │(Sonnet)          │ │  │
│                      │  └─────────┘ └──────────┘ └──────────────────┘ │  │
│                      └──────────────────────────────────────────────────┘  │
│                                    │                                       │
│                      ┌─────────────┼───────────────────┐                  │
│                      ▼             ▼                   ▼                  │
│            ┌──────────────┐ ┌──────────────┐  ┌──────────────────┐       │
│            │  Context     │ │  Session     │  │  Skill           │       │
│            │  Store       │ │  Manager     │  │  Engine          │       │
│            │              │ │              │  │                  │       │
│            │ • Codebase   │ │ • JSONL logs │  │ • Auto-detect    │       │
│            │   knowledge  │ │ • Resume     │  │ • Load & inject  │       │
│            │ • Decisions  │ │ • Handoff    │  │ • Validate with  │       │
│            │ • Memory     │ │ • Checkpoints│  │ • Chain skills   │       │
│            └──────────────┘ └──────────────┘  └──────────────────┘       │
│                                    │                                       │
│                      ┌─────────────┼───────────────────┐                  │
│                      ▼             ▼                   ▼                  │
│            ┌──────────────┐ ┌──────────────┐  ┌──────────────────┐       │
│            │  Security    │ │  Validation  │  │  MCP             │       │
│            │  Layer       │ │  Engine      │  │  Integration     │       │
│            │              │ │              │  │                  │       │
│            │ • Allowlist  │ │ • Iron Rule  │  │ • Puppeteer      │       │
│            │ • Hooks      │ │ • Evidence   │  │ • Playwright     │       │
│            │ • Sandbox    │ │ • Screenshots│  │ • Filesystem     │       │
│            │ • Validators │ │ • cURL/CLI   │  │ • Git            │       │
│            └──────────────┘ └──────────────┘  └──────────────────┘       │
│                                                                           │
│                      ┌────────────────────────────────────┐               │
│                      │         Claude Agent SDK            │               │
│                      │  claude-opus-4-6 | claude-sonnet-4-6│               │
│                      │  Adaptive Thinking | 1M Context     │               │
│                      │  128k Output (Opus) | 64k (Sonnet)  │               │
│                      └────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. AGENT ARCHITECTURE — DYNAMIC MULTI-AGENT GRAPH

### 3.1 Agent Types & Model Assignment

| Agent | Model | Role | When Spawned |
|-------|-------|------|-------------|
| **Prompt Router** | `claude-sonnet-4-6` | Classifies input, selects workflow | Always first |
| **Analyst Agent** | `claude-opus-4-6` | Deep codebase analysis, architecture mapping | Brownfield; complex greenfield |
| **Planner Agent** | `claude-opus-4-6` | Phase plans with validation gates, task decomposition | All workflows |
| **Implementer Agent(s)** | `claude-sonnet-4-6` | Code writing, one task per session, commit per feature | Per-task |
| **Validator Agent** | `claude-sonnet-4-6` | Functional validation — screenshots, cURL, CLI execution | After each implementation |
| **Context Manager** | `claude-sonnet-4-6` | Updates knowledge store, memory, decision log | Continuously |
| **Reporter Agent** | `claude-sonnet-4-6` | Progress summaries, SUMMARY.md, devlog | After phases |

### 3.2 Workflow Selection — The Prompt Router

The Prompt Router replaces the binary "initializer vs coding" decision with intelligent classification:

```python
class WorkflowType(str, Enum):
    GREENFIELD_APP = "greenfield_app"       # "Build a todo app"
    BROWNFIELD_ONBOARD = "brownfield_onboard" # "Here's my codebase, add auth"
    BROWNFIELD_TASK = "brownfield_task"       # "Fix bug #123 in my API"
    REFACTOR = "refactor"                     # "Migrate from X to Y"
    DEBUG = "debug"                           # "This is broken, fix it"
    CLI_TOOL = "cli_tool"                     # "Build a CLI that does X"
    IOS_APP = "ios_app"                       # "Build an iOS SwiftUI app"
    FREE_TASK = "free_task"                   # Any other coding prompt
```

**Classification signals:**
- Existing codebase present? → brownfield
- `app_spec.txt` present? → greenfield_app
- `.xcodeproj` / `.xcworkspace`? → ios_app
- `Cargo.toml` / CLI indicators? → cli_tool
- Explicit "fix" / "debug" language? → debug
- Explicit "refactor" / "migrate"? → refactor
- None of the above → free_task (Planner decides)

### 3.3 Agent Graph Execution Patterns

**Pattern A: Greenfield App Build**
```
Prompt Router → Planner → [Implementer → Validator]×N → Reporter
                  │
                  └─ Generates phased plan with ~200 features
                     Each Implementer session = 1 feature
                     Validator = browser automation (Puppeteer/Playwright)
```

**Pattern B: Brownfield Onboarding + Task**
```
Prompt Router → Analyst → Context Manager → Planner → [Implementer → Validator]×N → Reporter
                  │              │
                  │              └─ Populates codebase knowledge store:
                  │                 architecture, dependencies, patterns,
                  │                 file map, function graph, conventions
                  │
                  └─ Deep analysis via repomix --style xml:
                     Every file, every import, every function
                     Architecture decisions, tech stack, patterns
```

**Pattern C: Debug/Fix**
```
Prompt Router → Analyst → Planner → Implementer → Validator → Reporter
                  │
                  └─ Focused analysis: reproduce bug, identify root cause
                     Planner creates minimal fix plan
                     Single Implementer session with targeted fix
                     Validator confirms fix + regression check
```

**Pattern D: iOS App Build**
```
Prompt Router → Planner → [Implementer → Validator(iOS)]×N → Reporter
                                            │
                                            └─ iOS Validator:
                                               xcrun simctl boot
                                               xcodebuild + screenshot
                                               Accessibility test via XC-MCP
                                               Real simulator evidence
```

---

## 4. CONTEXT, MEMORY & SESSION MANAGEMENT

### 4.1 Context Store Architecture

```
.acli/
├── context/
│   ├── codebase_analysis.json     # Full architecture map (Analyst output)
│   ├── dependency_graph.json      # Import/dependency relationships
│   ├── conventions.json           # Detected code patterns & style
│   ├── tech_stack.json            # Detected/specified technology stack
│   ├── decisions.jsonl            # Append-only decision log
│   └── knowledge_chunks/          # Chunked codebase knowledge for retrieval
│       ├── chunk_001.md
│       ├── chunk_002.md
│       └── index.json             # Chunk metadata + embeddings ref
├── sessions/
│   ├── session_001.jsonl          # Full session transcript
│   ├── session_002.jsonl
│   └── session_index.json         # Session metadata, outcomes, links
├── plans/
│   ├── BRIEF.md                   # Project vision + platform + strategy
│   ├── ROADMAP.md                 # Phased roadmap with gate criteria
│   └── phases/
│       ├── 01-foundation/
│       │   ├── PLAN.md            # Gated execution plan
│       │   ├── VALIDATION.md      # Evidence-based gate results
│       │   └── evidence/          # Screenshots, cURL responses, CLI output
│       └── 02-features/
│           ├── PLAN.md
│           └── evidence/
├── memory/
│   ├── project_memory.json        # Cross-session facts and decisions
│   ├── user_preferences.json      # Learned user patterns
│   └── error_patterns.json        # Common errors and resolutions
└── state.json                     # Current orchestrator state
```

### 4.2 Brownfield Onboarding Protocol

When an existing codebase is detected, the Analyst Agent executes a mandatory onboarding sequence:

**Phase 1: Structural Analysis** (via `repomix --style xml --compress`)
- Generate single-file XML representation of entire codebase
- Parse file tree, dependencies, imports, exports
- Detect tech stack, framework, language, build system
- Map directory structure and architectural layers

**Phase 2: Deep Code Analysis** (via Claude Agent SDK with Opus)
- Analyze every module for: purpose, dependencies, public API
- Build function/class relationship graph
- Identify design patterns (MVC, repository, DI, etc.)
- Detect code conventions (naming, formatting, error handling)
- Catalog existing tests, CI/CD, deployment config

**Phase 3: Context Population**
- Write `codebase_analysis.json` with full architecture map
- Write `dependency_graph.json` with import chains
- Write `conventions.json` with style rules
- Chunk codebase into retrievable knowledge segments
- Store in `.acli/context/` for all subsequent agents

**Phase 4: Handoff**
- Context Manager creates a context summary prompt
- All subsequent agents receive this context as system prompt prefix
- Ensures no agent operates without full codebase awareness

### 4.3 Session Continuity

Each agent session is logged as JSONL (matching Claude Code's native format):

```jsonl
{"type":"session_start","session_id":"s_001","agent_type":"analyst","model":"claude-opus-4-6","timestamp":"2026-03-18T14:00:00Z"}
{"type":"tool_use","tool":"Bash","input":{"command":"find . -type f -name '*.py' | head -50"},"duration_ms":120}
{"type":"assistant_text","text":"I'll analyze the Python project structure...","tokens":42}
{"type":"tool_use","tool":"Read","input":{"path":"src/main.py"},"duration_ms":50}
{"type":"decision","key":"architecture","value":"FastAPI REST API with SQLAlchemy ORM","confidence":0.95}
{"type":"session_end","session_id":"s_001","status":"completed","duration_s":180}
```

**Session Resume**: Any interrupted session can be resumed from the last checkpoint. The orchestrator reads the session JSONL, reconstructs state, and continues from the last completed task.

**Cross-Session Memory**: The `project_memory.json` accumulates facts across sessions — architecture decisions, user corrections, discovered gotchas, resolved errors. Every new agent session gets this injected into its system prompt.

---

## 5. ORCHESTRATION ENGINE — ENHANCED FLOW

### 5.1 Core Orchestration Loop

```python
class EnhancedOrchestrator:
    """
    Dynamic multi-agent orchestrator with phase-gated progression.
    
    Replaces the simple 2-agent loop with:
    - Prompt routing → workflow selection
    - Dynamic agent graph construction
    - Phase-gated progression with validation
    - Sub-agent spawning per task
    - Error recovery with backtracking
    - Full TUI streaming of all events
    """
    
    async def run(self, prompt: str) -> None:
        # 1. Route prompt → workflow type
        workflow = await self.route_prompt(prompt)
        
        # 2. If brownfield, run onboarding first
        if workflow.requires_onboarding:
            await self.run_analyst_agent()
            await self.run_context_manager()
        
        # 3. Plan phase — always uses Opus
        plan = await self.run_planner_agent(workflow)
        
        # 4. Execute phases with gates
        for phase in plan.phases:
            # Pre-phase: inject cumulative context
            context = self.context_store.get_phase_context(phase)
            
            for task in phase.tasks:
                # Spawn implementer sub-agent
                result = await self.run_implementer_agent(task, context)
                
                # Run validator
                validation = await self.run_validator_agent(task, result)
                
                if validation.status == "FAIL":
                    # Backtrack: re-implement with error context
                    await self.handle_validation_failure(task, validation)
                
                # Update context store
                await self.run_context_manager_update(task, result)
            
            # Phase gate — cumulative validation
            gate_result = await self.run_phase_gate(phase)
            if gate_result.status == "FAIL":
                await self.handle_phase_gate_failure(phase, gate_result)
            
            # Reporter summarizes phase
            await self.run_reporter_agent(phase)
        
        # 5. Final report
        await self.run_final_report()
```

### 5.2 Model Configuration

```python
# Model routing — use Opus for thinking-heavy, Sonnet for execution-heavy
MODEL_CONFIG = {
    "prompt_router": "claude-sonnet-4-6",
    "analyst": "claude-opus-4-6",        # Deep analysis needs Opus
    "planner": "claude-opus-4-6",        # Planning needs Opus
    "implementer": "claude-sonnet-4-6",  # Code writing — Sonnet is fast + capable
    "validator": "claude-sonnet-4-6",    # Validation execution — Sonnet
    "context_manager": "claude-sonnet-4-6",
    "reporter": "claude-sonnet-4-6",
}

# Adaptive thinking configuration (Claude 4.6 feature)
THINKING_CONFIG = {
    "analyst": {"type": "adaptive", "effort": "high"},    # Think hard
    "planner": {"type": "adaptive", "effort": "high"},    # Think hard
    "implementer": {"type": "adaptive"},                   # Default
    "validator": {"type": "adaptive"},                     # Default
}

# Output token budgets
OUTPUT_CONFIG = {
    "analyst": 128_000,     # Opus max — full analysis
    "planner": 128_000,     # Opus max — detailed plans
    "implementer": 64_000,  # Sonnet max
    "validator": 16_000,    # Usually short
    "reporter": 32_000,     # Medium summaries
}
```

### 5.3 Skill Engine — Auto-Detection & Injection

Every agent session begins with skill detection based on the current task context:

```python
class SkillEngine:
    """
    Auto-detects and injects relevant skills into agent prompts.
    
    Scans available skills and matches against:
    - Project type (iOS → ios-validation-runner, functional-validation)
    - Task type (implement → python-agent-sdk; validate → functional-validation)
    - Technology (ElevenLabs → elevenlabs skill)
    - Phase (planning → create-validation-plan, create-plans)
    """
    
    SKILL_ROUTING = {
        # Validation skills — always loaded for Validator agents
        "validator": [
            "functional-validation",
            "ios-validation-runner",  # if iOS detected
        ],
        # Planning skills — loaded for Planner agents
        "planner": [
            "create-validation-plan",
            "create-plans",
            "create-meta-prompts",
        ],
        # Prompt optimization — loaded when generating sub-agent prompts
        "prompt_generation": [
            "optimize-prompt",
            "prompt-engineering-expert",
            "prompt-engineering-patterns",
        ],
        # Implementation skills — loaded per technology
        "implementer": [
            "python-agent-sdk",  # if Python
            "elevenlabs",        # if ElevenLabs API
        ],
    }
```

---

## 6. FUNCTIONAL VALIDATION ENGINE

### 6.1 The Iron Rule — Enforced Everywhere

The validation engine is not optional. It is a first-class citizen wired into the orchestration loop at three levels:

**Level 1: Task Validation** — After every Implementer session
- Did the code change actually work?
- Evidence: screenshots, cURL responses, CLI output, exit codes

**Level 2: Phase Gate** — Between phases
- Does everything from this phase still work?
- Cumulative: re-validates previous phase evidence too
- Evidence compounds — Phase 2 gate requires Phase 1 still passing

**Level 3: Final Validation** — After all phases complete
- Full system integration test through real user interfaces
- Every claimed feature verified end-to-end

### 6.2 Platform-Specific Validation Routing

The Validator Agent automatically detects the platform and applies the correct validation protocol:

| Platform Indicator | Validation Method | Evidence Type |
|---|---|---|
| `.xcodeproj`, `.xcworkspace` | `xcrun simctl` boot + screenshot + accessibility | PNG screenshots from real simulator |
| REST routes, FastAPI/Express | `curl -s` against running server | JSON responses saved to evidence/ |
| React/Vue/Svelte, `package.json` | Playwright MCP → navigate + screenshot | Browser screenshots |
| `Cargo.toml`, CLI binary | Binary execution with args | stdout/stderr captured to .txt |
| Python script/module | `python -m` execution | stdout/stderr + exit code |
| Full-stack (frontend + backend) | Bottom-up: API first, then UI | Both cURL + screenshots |

### 6.3 Mock Detection — Active Enforcement

The orchestrator includes a **Mock Detector** hook that scans every Implementer session's tool calls:

```python
MOCK_PATTERNS = [
    r"mock\.", r"Mock\(", r"unittest\.mock",        # Python mocks
    r"jest\.mock", r"jest\.fn", r"sinon\.",          # JS mocks
    r"@Mock", r"Mockito\.",                          # Java mocks
    r"\.stub\(", r"\.fake\(",                        # Generic stubs
    r"in.memory.*database", r":memory:",             # In-memory DBs
    r"TEST_MODE", r"test_mode",                      # Test mode flags
    r"\.test\.", r"\.spec\.", r"_test\.",             # Test files
]

async def mock_detection_hook(tool_name: str, tool_input: dict) -> dict:
    """Pre-tool hook that blocks mock/stub creation."""
    if tool_name in ("Write", "Edit"):
        content = tool_input.get("content", "")
        for pattern in MOCK_PATTERNS:
            if re.search(pattern, content):
                return {
                    "decision": "block",
                    "reason": f"IRON RULE VIOLATION: Detected mock pattern '{pattern}'. "
                              "Fix the real system instead."
                }
    return {}
```

### 6.4 Evidence Collection & Verification

```python
class EvidenceCollector:
    """
    Collects and verifies validation evidence.
    
    Evidence is NOT just "file exists." Evidence is reviewed:
    - Screenshots are opened and visually inspected by the Validator
    - JSON responses are parsed and checked against PASS criteria
    - CLI output is parsed for expected patterns
    - Exit codes are checked (0 = success)
    """
    
    async def collect_and_verify(
        self,
        evidence_type: str,
        evidence_path: Path,
        pass_criteria: list[str],
    ) -> ValidationResult:
        # 1. Capture evidence
        evidence = await self.capture(evidence_type)
        
        # 2. Save to evidence/ directory
        await self.save(evidence, evidence_path)
        
        # 3. VERIFY — the critical step
        #    Validator agent actually reads the evidence
        #    and checks against pre-defined PASS criteria
        verification = await self.verify(evidence, pass_criteria)
        
        # 4. Write verdict
        return ValidationResult(
            status="PASS" if verification.all_criteria_met else "FAIL",
            evidence_path=evidence_path,
            criteria_results=verification.results,
            discrepancies=verification.discrepancies,
        )
```

---

## 7. ENHANCED TUI — FULL VISIBILITY

### 7.1 New TUI Layout

The v2 TUI expands from 4 panels to 7, adding context visibility, validation gates, and an inline prompt input:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ⟁ SHANNON-ACLI │ ● RUNNING │ Phase 2/4 │ Task 3/12 │ Opus 4.6 │ 14:32  │
├─────────────────────┬────────────────────────────────────────────────────────┤
│  AGENT GRAPH        │ LIVE STREAM  │ F1:All F2:Tools F3:Errors F4:Thinking │
│  ◆ ORCHESTRATOR     │ 14:32:15 [ANL] Analyzing src/auth/...               │
│  ├─ ✓ Analyst       │ 14:32:16 [PLN] Phase 2: 4 tasks, 4 gates           │
│  ├─ ✓ Planner       │ 14:32:17 [IMP] ▶ Write src/auth/jwt.py             │
│  ├─ ◆ Impl #3       │ 14:32:18 [IMP] ▶ Bash npm install jose             │
│  │  ⚡ Write jwt.py  │ 14:32:19 [VAL] ⏳ Awaiting validation...           │
│  ╰─ ○ Validator     │ 14:32:20 [VAL] ▶ curl localhost:3000/auth/login    │
│     (pending)       │ 14:32:21 [VAL] ✓ PASS: 200 OK + JWT in response    │
│─────────────────────├────────────────────────────────────────────────────────┤
│  CONTEXT            │ VALIDATION GATES                                      │
│  ┌─ Tech: Python    │ Phase 1: Foundation          ✓ PASS (3/3 criteria)  │
│  ├─ FW: FastAPI     │ Phase 2: Auth [CURRENT]                              │
│  ├─ DB: PostgreSQL  │   Gate 2.1: JWT creation     ✓ PASS                 │
│  ├─ Files: 47       │   Gate 2.2: Token refresh    ✓ PASS                 │
│  ├─ LOC: 3,200      │   Gate 2.3: Protected route  ◆ RUNNING              │
│  └─ Memory: 12 facts│   Gate 2.4: Phase gate       ○ PENDING              │
│─────────────────────│ Phase 3: Features            ○ PENDING               │
│  PROGRESS           │ Phase 4: Polish              ○ PENDING               │
│  ██████████░░░░░░░  ├────────────────────────────────────────────────────────┤
│  28% (12/42 tasks)  │ PROMPT INPUT                                          │
│  Sessions: 8        │ > Add rate limiting to the auth endpoints_            │
│  Tools: 145         │                                                        │
│  Errors: 1          │ [Enter] Send  [Ctrl+P] Paste spec  [Ctrl+S] Stop     │
├─────────────────────┴────────────────────────────────────────────────────────┤
│ q Quit  p Pause  s Stop  j/k Navigate  Enter Detail  Tab Focus  / Search   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 New TUI Panels

| Panel | Purpose | Data Source |
|-------|---------|-------------|
| **Agent Graph** (existing, enhanced) | Shows full agent tree with types, models, status | OrchestratorBridge |
| **Live Stream** (existing, enhanced) | All events + new agent type labels [ANL]/[PLN]/[IMP]/[VAL] | StreamBuffer |
| **Context Explorer** (NEW) | Shows detected tech stack, file count, LOC, memory facts | ContextStore |
| **Validation Gates** (NEW) | Phase/task gates with PASS/FAIL/RUNNING/PENDING status | ValidationEngine |
| **Progress** (existing, enhanced) | Phase-aware progress (not just feature count) | PlanExecutor |
| **Prompt Input** (NEW) | Inline prompt input — send new tasks without leaving TUI | Orchestrator |
| **Stats** (existing, enhanced) | Expanded with model usage, token costs, timing | SessionManager |

### 7.3 New TUI Keybindings

| Key | Action |
|-----|--------|
| `/` | Focus prompt input for new task |
| `v` | Toggle validation gate detail view |
| `c` | Toggle context explorer |
| `m` | Show memory/decision log |
| `t` | Show thinking/reasoning (adaptive thinking stream) |
| `e` | Show evidence viewer (opens screenshots/responses) |
| `Ctrl+P` | Paste multi-line spec into prompt |

---

## 8. CLI COMMANDS — EXPANDED

```bash
# Existing commands (enhanced)
acli init <project-dir>              # Now supports brownfield: acli init . --onboard
acli run [dir]                       # Now accepts ANY prompt via --prompt
acli monitor [dir]                   # Enhanced TUI with all new panels
acli status [dir]                    # Phase-aware status with gate results
acli enhance <spec-file>             # Now powered by Opus 4.6

# New commands
acli onboard [dir]                   # Explicit brownfield onboarding
acli prompt <text>                   # Send a single task (no TUI)
acli plan [dir]                      # Generate plan without executing
acli validate [dir]                  # Run validation gates only
acli context [dir]                   # Show/manage context store
acli session list|resume|replay      # Session management
acli memory list|add|clear           # Memory management
```

---

## 9. DESIRED OUTCOMES — TUI SCREEN FLOWS

### 9.1 Greenfield Build Flow

**Screen 1: Initialization**
```
User runs: acli init my_app --spec "Build a real-time chat app with rooms"

TUI shows:
  Agent Graph: ◆ Prompt Router → classifying...
  Live Stream: [RTR] Classified as: greenfield_app
               [RTR] Tech stack inference: TypeScript, React, Socket.IO
               [PLN] Spawning Planner Agent (claude-opus-4-6)...
```

**Screen 2: Planning**
```
  Agent Graph: ✓ Router → ◆ Planner (opus-4-6)
  Live Stream: [PLN] Generating phased plan with validation gates...
               [PLN] Phase 1: Foundation (5 tasks, 5 gates)
               [PLN] Phase 2: Chat Core (8 tasks, 8 gates)
               [PLN] Phase 3: Rooms (6 tasks, 6 gates)
               [PLN] Phase 4: Polish (4 tasks, 4 gates)
  Validation:  Phase 1: Foundation  ○ PENDING (0/5)
               Phase 2: Chat Core   ○ PENDING (0/8)
               ...
```

**Screen 3: Implementation + Validation**
```
  Agent Graph: ✓ Router → ✓ Planner → ◆ Impl #1 (sonnet-4-6)
  Live Stream: [IMP] Task 1.1: Initialize Next.js project
               [IMP] ▶ Bash npx create-next-app@latest
               [IMP] ▶ Write src/app/page.tsx
               [VAL] ▶ Bash npm run build
               [VAL] ✓ PASS: Build successful (exit 0)
  Validation:  Phase 1: Foundation
                 1.1: Project init       ✓ PASS
                 1.2: Socket.IO setup    ◆ RUNNING
```

### 9.2 Brownfield Onboarding Flow

**Screen 1: Analysis**
```
User runs: acli run . --prompt "Add JWT authentication to all API routes"

TUI shows:
  Agent Graph: ◆ Router → ◆ Analyst (opus-4-6)
  Live Stream: [RTR] Detected brownfield: 47 Python files, FastAPI project
               [ANL] Running repomix --style xml --compress...
               [ANL] Analyzing architecture: FastAPI + SQLAlchemy + Alembic
               [ANL] Mapping 23 route handlers across 8 routers
               [ANL] Detecting patterns: repository pattern, Pydantic models
               [ANL] Writing codebase_analysis.json (47 files mapped)
  Context:     Tech: Python 3.12 | FW: FastAPI | DB: PostgreSQL
               Files: 47 | LOC: 3,200 | Routes: 23
               Patterns: Repository, Dependency Injection
```

**Screen 2: Context Population + Planning**
```
  Agent Graph: ✓ Router → ✓ Analyst → ◆ Context Mgr → ◆ Planner
  Live Stream: [CTX] Stored 12 architecture facts to memory
               [CTX] Chunked codebase into 8 retrievable segments
               [PLN] Planning JWT auth integration...
               [PLN] Phase 1: Auth foundation (jwt.py, deps, config)
               [PLN] Phase 2: Route protection (middleware + guards)
               [PLN] Phase 3: Token refresh + error handling
  Memory:      12 facts stored
               "FastAPI app uses dependency injection via Depends()"
               "All routes in src/api/v1/ follow router pattern"
               "Existing auth: none (no auth middleware detected)"
```

### 9.3 iOS App Validation Flow

```
  Agent Graph: ✓ Planner → ◆ Impl #4 → ◆ Validator(iOS)
  Live Stream: [IMP] Task 2.3: Login screen with email/password
               [IMP] ▶ Write Sources/Views/LoginView.swift
               [VAL] ▶ Booting iPhone 16 simulator...
               [VAL] ▶ xcodebuild -scheme MyApp -destination 'iPhone 16'
               [VAL] ▶ xcrun simctl io booted screenshot evidence/login.png
               [VAL] ✓ Screenshot captured: login.png
               [VAL] ▶ Inspecting screenshot...
               [VAL] ✓ Email field visible: YES
               [VAL] ✓ Password field visible: YES
               [VAL] ✓ Login button visible: YES
               [VAL] ✓ PASS: All 3 criteria met
  Validation:  Phase 2: Auth UI
                 2.1: Login screen      ✓ PASS (3/3 criteria)
                 2.2: Registration      ◆ RUNNING
                 2.3: Password reset    ○ PENDING
```

---

## 10. TECHNICAL IMPLEMENTATION PLAN

### 10.1 Migration from v1 → v2

The v2 build is **additive** — v1's codebase is preserved and extended:

| v1 Component | v2 Status | Changes |
|---|---|---|
| `core/orchestrator.py` | **Replaced** | New `EnhancedOrchestrator` with dynamic agent graph |
| `core/agent.py` | **Extended** | Add agent type routing, skill injection, context loading |
| `core/client.py` | **Updated** | Model IDs → `claude-opus-4-6` / `claude-sonnet-4-6`, adaptive thinking |
| `core/session.py` | **Extended** | JSONL logging, session resume, cross-session memory |
| `core/streaming.py` | **Extended** | New event types: ANALYSIS, PLANNING, VALIDATION_GATE, CONTEXT_UPDATE |
| `tui/app.py` | **Extended** | 3 new panels, prompt input, validation gate view |
| `tui/bridge.py` | **Extended** | Context store connection, validation engine connection |
| `tui/widgets.py` | **Extended** | ContextExplorer, ValidationGatePanel, PromptInput widgets |
| `security/hooks.py` | **Extended** | Mock detection hook added |
| `spec/enhancer.py` | **Updated** | Model ID update, output_config migration |
| `integration/` | **Extended** | Skill engine auto-detection, repomix integration |
| — | **NEW** | `context/` module — ContextStore, KnowledgeChunker, MemoryManager |
| — | **NEW** | `validation/` module — ValidationEngine, EvidenceCollector, GateRunner |
| — | **NEW** | `routing/` module — PromptRouter, WorkflowSelector |
| — | **NEW** | `agents/` module — AgentFactory with typed agent definitions |

### 10.2 New Module Structure

```
src/acli/
├── agents/                         # NEW — Agent definitions and factory
│   ├── __init__.py
│   ├── factory.py                  # AgentFactory — creates typed agents
│   ├── analyst.py                  # Analyst agent prompt + tools
│   ├── planner.py                  # Planner agent prompt + tools
│   ├── implementer.py              # Implementer agent prompt + tools
│   ├── validator.py                # Validator agent prompt + tools
│   ├── context_manager.py          # Context manager agent
│   └── reporter.py                 # Reporter agent
├── context/                        # NEW — Context and memory management
│   ├── __init__.py
│   ├── store.py                    # ContextStore — codebase knowledge
│   ├── memory.py                   # MemoryManager — cross-session facts
│   ├── chunker.py                  # KnowledgeChunker — codebase → chunks
│   └── onboarder.py                # BrownfieldOnboarder — full analysis
├── validation/                     # NEW — Functional validation engine
│   ├── __init__.py
│   ├── engine.py                   # ValidationEngine — orchestrates gates
│   ├── evidence.py                 # EvidenceCollector — capture + save
│   ├── gates.py                    # GateRunner — phase/task gate logic
│   ├── mock_detector.py            # MockDetector — Iron Rule enforcement
│   └── platforms/                  # Platform-specific validators
│       ├── ios.py
│       ├── web.py
│       ├── api.py
│       ├── cli.py
│       └── generic.py
├── routing/                        # NEW — Prompt classification
│   ├── __init__.py
│   ├── router.py                   # PromptRouter — classify input
│   └── workflows.py                # WorkflowType definitions
├── core/                           # ENHANCED
│   ├── orchestrator.py             # EnhancedOrchestrator (replaces v1)
│   ├── orchestrator_v1.py          # Original preserved for reference
│   ├── agent.py                    # Enhanced with typing + skill injection
│   ├── client.py                   # Updated models + adaptive thinking
│   ├── session.py                  # JSONL logging + resume + memory
│   └── streaming.py                # New event types
├── tui/                            # ENHANCED
│   ├── app.py                      # 7-panel layout
│   ├── bridge.py                   # Context + validation connections
│   ├── widgets.py                  # 3 new widget classes
│   ├── prompt_input.py             # NEW — Inline prompt widget
│   └── cyberpunk.tcss              # Extended theme
├── [existing modules preserved]
```

### 10.3 Key Dependencies Update

```toml
[project]
dependencies = [
    "claude-agent-sdk>=0.2.0",       # Updated for 4.6 support
    "rich>=13.7.0",
    "typer>=0.9.0",
    "pydantic>=2.5.0",
    "httpx>=0.25.0",
    "textual>=1.0.0",
    # New dependencies
    "repomix>=0.2.0",                # Codebase → XML for analysis
    "aiofiles>=24.1.0",              # Async file operations
]
```

---

## 11. PROMPT ENGINEERING — META-PROMPT STRUCTURE

Every agent receives a carefully structured system prompt following the optimize-prompt skill guidelines:

```xml
<system_prompt agent="{agent_type}">
  <context>
    <project_type>{greenfield|brownfield}</project_type>
    <tech_stack>{detected or specified}</tech_stack>
    <current_phase>{phase name and number}</current_phase>
    <codebase_summary>{from context store, if brownfield}</codebase_summary>
    <memory>{cross-session facts}</memory>
    <previous_decisions>{relevant decisions from log}</previous_decisions>
  </context>

  <skills>
    {auto-detected and loaded skill content}
  </skills>

  <iron_rule>
    IF the real system doesn't work, FIX THE REAL SYSTEM.
    NEVER create mocks, stubs, test doubles, or test files.
    ALWAYS validate through the same interfaces real users experience.
  </iron_rule>

  <task>
    {specific task description with PASS criteria}
  </task>

  <validation_criteria>
    <criterion id="1">{specific observable condition}</criterion>
    <criterion id="2">{specific observable condition}</criterion>
  </validation_criteria>

  <constraints>
    <model>{claude-opus-4-6 or claude-sonnet-4-6}</model>
    <thinking>{adaptive thinking config}</thinking>
    <max_output>{token budget}</max_output>
    <tools>{allowed tool list}</tools>
  </constraints>
</system_prompt>
```

---

## 12. EXECUTION GUARANTEE — HOW IT ALL WORKS TOGETHER

### 12.1 End-to-End Flow: User Types a Prompt

```
1. USER types "Add JWT auth to my FastAPI app" in TUI prompt input
   │
2. PROMPT ROUTER (Sonnet 4.6, ~2s)
   │  Detects: brownfield (existing .py files), task type: feature addition
   │  Output: WorkflowType.BROWNFIELD_TASK
   │
3. ANALYST AGENT (Opus 4.6, ~30-60s)
   │  Runs repomix, analyzes every file
   │  Outputs: codebase_analysis.json, dependency_graph.json
   │  TUI: Context Explorer populates with tech stack, file count, etc.
   │
4. CONTEXT MANAGER (Sonnet 4.6, ~5s)
   │  Stores analysis, creates knowledge chunks
   │  Updates project_memory.json with 12 architecture facts
   │
5. PLANNER AGENT (Opus 4.6, ~15-30s)
   │  Creates 3-phase plan with validation gates:
   │  Phase 1: JWT foundation (jwt.py, config, deps) — 3 tasks, 3 gates
   │  Phase 2: Route protection (middleware) — 4 tasks, 4 gates
   │  Phase 3: Refresh + error handling — 3 tasks, 3 gates
   │  TUI: Validation Gates panel populates
   │
6. IMPLEMENTER #1 (Sonnet 4.6, ~30-60s per task)
   │  Task 1.1: Create src/auth/jwt.py with JWT creation/verification
   │  Receives full codebase context in system prompt
   │  Writes code following detected conventions
   │
7. VALIDATOR (Sonnet 4.6, ~10-20s per gate)
   │  Starts FastAPI server
   │  curl -X POST localhost:8000/auth/token -d '{"email":"test@test.com"}'
   │  Checks: 200 status, JWT in response, valid JWT structure
   │  Saves evidence to .acli/plans/phases/01/evidence/
   │  TUI: Gate 1.1 → ✓ PASS
   │
8. [REPEAT 6-7 for each task in each phase]
   │
9. PHASE GATE (Sonnet 4.6, ~15s)
   │  Re-validates ALL phase criteria cumulatively
   │  Phase 1 gate: JWT create ✓, JWT verify ✓, config ✓
   │  TUI: Phase 1 → ✓ PASS
   │
10. REPORTER (Sonnet 4.6, ~5s)
    │  Writes SUMMARY.md for phase
    │  Updates progress display
    │
11. [REPEAT 6-10 for phases 2 and 3]
    │
12. FINAL VALIDATION
    │  Full integration: create token → use on protected route → refresh
    │  All evidence reviewed, all criteria met
    │
13. DONE
    TUI: Progress 100%, all gates ✓ PASS
    Git: All changes committed with conventional commit messages
```

### 12.2 Failure Recovery

When a validation gate FAILS:

```
1. Validator reports FAIL with specific discrepancy
2. Orchestrator creates "fix context" from:
   - Original task description
   - Code that was written
   - Validation evidence (what went wrong)
   - Error messages / screenshots
3. New Implementer session spawned with fix context
4. Re-validation runs from scratch (not partial)
5. If 3 consecutive failures: escalate to Opus for re-planning
6. TUI shows: Gate 2.1 → ✗ FAIL → ◆ RETRY #1 → ✓ PASS
```

---

## 13. FUNCTIONAL VALIDATION — HOW TO VERIFY THE SYSTEM ITSELF

### 13.1 ACLI v2's Own Validation Plan

ACLI v2 must validate itself through real execution, not tests:

**Gate 1: Core Infrastructure**
- `acli init test_project` creates directory with all expected files
- `acli run test_project --prompt "Build hello world"` starts TUI, spawns agents
- Evidence: TUI screenshot, session JSONL exists, git log shows commits

**Gate 2: Brownfield Onboarding**
- Clone a real open-source Python project (e.g., httpie)
- `acli onboard .` generates codebase_analysis.json
- Verify: analysis contains correct tech stack, file count, architecture
- Evidence: codebase_analysis.json content, context store populated

**Gate 3: Multi-Agent Orchestration**
- `acli run . --prompt "Add a /health endpoint"` on brownfield project
- Verify: Analyst → Planner → Implementer → Validator chain executes
- Verify: Validator runs `curl localhost:PORT/health` and gets 200
- Evidence: session JSONL, validation evidence, git diff

**Gate 4: TUI Visibility**
- Launch `acli monitor` on running orchestrator
- Verify: All 7 panels render, events stream in real-time
- Verify: Agent graph updates as agents spawn/complete
- Verify: Validation gates show PASS/FAIL status
- Evidence: TUI screenshots at each phase

**Gate 5: iOS Validation Path** (if iOS project)
- Build SwiftUI app via ACLI
- Verify: Simulator boots, screenshots captured, accessibility verified
- Evidence: Simulator screenshots in evidence/ directory

**Gate 6: Session Continuity**
- Start a multi-phase build, interrupt after Phase 1
- Resume with `acli session resume`
- Verify: Phase 2 starts correctly with Phase 1 context preserved
- Evidence: Session JSONL shows resume, no re-execution of Phase 1

### 13.2 Validation Execution Methods

| What | How | Evidence |
|------|-----|----------|
| CLI commands work | `acli <command>` execution + exit code | stdout captured |
| TUI renders | `acli monitor` + screenshot | PNG of terminal |
| Agents execute | Check session JSONL for expected event types | JSONL content |
| Validation gates fire | Check `.acli/plans/phases/*/VALIDATION.md` | VALIDATION.md content |
| Context persists | Check `.acli/context/` files exist and are populated | JSON file content |
| Memory works | Start session, check memory injection in next session | System prompt inspection |
| Mock detection works | Attempt to write mock code, verify block | Hook error message |
| Browser validation works | Validator runs Playwright, check evidence/ | Screenshot files |
| API validation works | Validator runs curl, check evidence/ | JSON response files |

---

## 14. SECURITY MODEL — ENHANCED

### 14.1 Extended Allowlist

v2 adds commands needed for broader project types:

```python
ALLOWED_COMMANDS_V2 = {
    # v1 commands (preserved)
    "ls", "cat", "head", "tail", "wc", "grep",
    "cp", "mkdir", "chmod", "pwd",
    "npm", "node", "git",
    "ps", "lsof", "sleep", "pkill",
    "init.sh",
    
    # v2 additions
    "python", "pip", "python3",       # Python projects
    "cargo", "rustc",                  # Rust projects
    "go",                              # Go projects
    "swift", "xcodebuild", "xcrun",   # iOS projects
    "curl", "wget",                    # API validation
    "docker", "docker-compose",        # Containerized projects
    "make",                            # Build systems
    "repomix",                         # Codebase analysis
    "find", "sort", "uniq",           # File discovery
    "jq",                              # JSON processing
    "tee",                             # Evidence capture
}
```

### 14.2 New Validators

```python
VALIDATORS_V2 = {
    **VALIDATORS,  # Inherit v1
    "docker": validate_docker,        # Only allow build, up, down, ps
    "xcodebuild": validate_xcode,     # Only allow -scheme builds
    "xcrun": validate_xcrun,          # Only simctl subcommands
    "curl": validate_curl,            # Block non-localhost unless explicit
    "pip": validate_pip,              # Only install, no --user system mods
}
```

---

## 15. IMPLEMENTATION ROADMAP

### Phase 1: Core Infrastructure (Est. 3-4 Implementer sessions)
- Routing module (PromptRouter, WorkflowType)
- Context module (ContextStore, MemoryManager, KnowledgeChunker)
- Updated client.py with claude-opus-4-6 / claude-sonnet-4-6 + adaptive thinking
- New streaming event types
- **Gate**: PromptRouter classifies 5 test prompts correctly; ContextStore persists and retrieves

### Phase 2: Agent Architecture (Est. 4-5 sessions)
- Agent factory with typed agents (Analyst, Planner, Implementer, Validator, etc.)
- EnhancedOrchestrator replacing v1 loop
- Skill engine auto-detection and injection
- Session JSONL logging
- **Gate**: Full agent chain executes for a simple greenfield prompt; JSONL captured

### Phase 3: Brownfield Onboarding (Est. 3-4 sessions)
- BrownfieldOnboarder with repomix integration
- Analyst agent prompt engineering
- Codebase analysis → context population pipeline
- Cross-session memory injection
- **Gate**: Onboard a real Python project; verify analysis accuracy

### Phase 4: Validation Engine (Est. 3-4 sessions)
- ValidationEngine, EvidenceCollector, GateRunner
- Platform-specific validators (web, API, CLI, iOS)
- Mock detection hook
- Phase gate logic with cumulative validation
- **Gate**: Validator correctly PASS/FAIL on real API endpoint

### Phase 5: Enhanced TUI (Est. 3-4 sessions)
- ContextExplorer widget
- ValidationGatePanel widget
- PromptInput widget
- Updated agent graph with agent types
- Extended cyberpunk.tcss for new panels
- **Gate**: TUI screenshot shows all 7 panels with real data

### Phase 6: Integration & Polish (Est. 2-3 sessions)
- CLI command updates (onboard, prompt, plan, validate, context, session, memory)
- Session resume functionality
- Error recovery with backtracking
- Documentation update
- **Gate**: Full end-to-end brownfield workflow passes all gates

---

## 16. KEY DESIGN DECISIONS

| Decision | Rationale |
|----------|-----------|
| **Opus for analysis/planning, Sonnet for implementation** | Opus's 128k output and deeper reasoning are essential for architecture analysis and multi-phase planning. Sonnet is faster and cheaper for the volume of implementation sessions. |
| **Adaptive thinking over manual budget_tokens** | Claude 4.6's adaptive thinking automatically calibrates reasoning depth. Manual budgets are deprecated on 4.6. |
| **JSONL session format** | Matches Claude Code's native session format. Enables replay, resume, and SessionForge content mining. |
| **repomix for brownfield analysis** | Single-file XML representation is the most efficient way to give an LLM complete codebase context. |
| **Phase gates are blocking** | Non-blocking gates allow broken code to accumulate. Blocking gates catch problems early when they're cheap to fix. |
| **Mock detection as pre-tool hook** | Catching mocks at write-time is more reliable than post-hoc scanning. The hook fires before the file is created. |
| **Skill auto-injection** | Agents shouldn't need to be told which skills to use. The engine matches task type → skills automatically. |
| **TUI prompt input** | Users shouldn't exit the TUI to send new tasks. Inline input keeps the flow unbroken. |
| **Context chunking** | Full codebase analysis can exceed context windows. Chunking with retrieval keeps relevant context available without overflow. |

---

## APPENDIX A: Model ID Reference (March 2026)

| Model | API String | Max Output | Context | Use In ACLI |
|-------|-----------|------------|---------|-------------|
| Claude Opus 4.6 | `claude-opus-4-6` | 128k tokens | 1M tokens | Analyst, Planner |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | 64k tokens | 1M tokens | Implementer, Validator, Router |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | 8k tokens | 200k tokens | (not used — too limited) |

## APPENDIX B: Skill → Agent Mapping

| Skill | Agent(s) | Purpose |
|-------|----------|---------|
| `functional-validation` | Validator | Iron Rule enforcement, evidence protocols |
| `ios-validation-runner` | Validator (iOS) | Simulator boot, screenshot, accessibility |
| `create-validation-plan` | Planner | Phase-gated plan generation |
| `create-plans` | Planner | Hierarchical plan structure |
| `create-meta-prompts` | Orchestrator | Multi-stage prompt pipeline |
| `optimize-prompt` | Agent Factory | System prompt optimization for each agent |
| `prompt-engineering-expert` | Agent Factory | Prompt quality assurance |
| `prompt-engineering-patterns` | Agent Factory | Advanced prompting techniques |
| `python-agent-sdk` | Implementer (Python) | SDK usage patterns |
| `elevenlabs` | Implementer (TTS) | Voice/audio integration |
| `create-agent-skills` | Reporter | Skill creation from session insights |

## APPENDIX C: Event Type Registry (v2)

```python
class EventType(str, Enum):
    # v1 events (preserved)
    TEXT = "text"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    TOOL_BLOCKED = "tool_blocked"
    ERROR = "error"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    PROGRESS = "progress"
    
    # v2 additions
    AGENT_SPAWN = "agent_spawn"           # New agent created
    AGENT_COMPLETE = "agent_complete"     # Agent finished
    ANALYSIS_UPDATE = "analysis_update"   # Codebase analysis progress
    PLAN_CREATED = "plan_created"         # Plan generated
    PHASE_START = "phase_start"           # Phase begins
    PHASE_END = "phase_end"              # Phase completes
    GATE_START = "gate_start"            # Validation gate begins
    GATE_RESULT = "gate_result"          # PASS/FAIL
    CONTEXT_UPDATE = "context_update"    # Context store changed
    MEMORY_UPDATE = "memory_update"      # Memory fact added
    THINKING = "thinking"                # Adaptive thinking stream
    MOCK_DETECTED = "mock_detected"      # Iron Rule violation caught
    PROMPT_RECEIVED = "prompt_received"  # New user prompt from TUI
```
