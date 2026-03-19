---
title: ALR Validation Design for ACLI v2
date: 2026-03-18
status: research complete
---

# ALR Validation Design: Using Awesome-List Researcher as ACLI v2 Test Payload

## Executive Summary

The **Awesome-List Researcher (ALR)** spec is an excellent real-world validation payload for ACLI v2. It's large (2,900+ lines), architecturally sophisticated (multi-agent, streaming, cost-controlled), and has measurable success criteria (lint compliance, HTTP validation, token tracking). This report extracts the ALR specification completely, maps it to ACLI capabilities, and designs 7 concrete validation scenarios using tmux automation for TUI verification.

**Key Finding**: ALR can be used to validate 6 ACLI subsystems in parallel:
- Project initialization & spec handling
- Router classification (GREENFIELD_APP detection)
- Progress tracking & persistence
- Tech stack detection
- Memory & configuration management
- TUI rendering & keyboard navigation

---

## 1. ALR Specification Extraction

### 1.1 Project Overview

**Name**: Awesome-List Researcher (ALR)
**Purpose**: Docker-first CLI tool using Claude Agents SDK to research, validate, and update GitHub Awesome-style repository lists
**Language**: Python 3.12
**Framework**: Claude Agent SDK (ClaudeSDKClient, ClaudeAgentOptions, structured outputs)
**Deployment**: Docker containers with Poetry dependency management

**Success Metrics**:
- Fetch and parse Awesome list into structured JSON
- Generate contextually relevant search queries
- Discover 10-50 new candidate links per category
- Filter duplicates with 99%+ accuracy (Bloom filters + exact matching)
- Validate links for HTTP 200 OK and GitHub star thresholds
- Produce `awesome-lint` compliant Markdown output (zero errors)
- Complete workflow within wall-time constraint (default 600s)
- Stay within cost ceiling (default $5.00 USD)
- Generate comprehensive structured logs with audit trail

### 1.2 Feature Enumeration

#### Core Infrastructure
- [x] Docker-only execution (Python 3.12-slim base)
- [x] Poetry dependency management (anthropic SDK + claude-agent-sdk)
- [x] CLI entrypoint via `./build-and-run.sh`
- [x] Environment variable config (ANTHROPIC_API_KEY)
- [x] Structured JSON logging (ISO 8601 timestamps)
- [x] Signal-based timeout handling (wall-time enforcement)
- [x] Exponential backoff retry logic for rate limits

#### Data Acquisition
- [x] GitHub API integration (default branch detection)
- [x] Fallback mechanism to HEAD for README retrieval
- [x] README parsing into structured JSON (original.json)
- [x] Bloom filter implementation (capacity 10K, error rate 0.001)
- [x] URL normalization & canonicalization
- [x] Description length validation (≤80 chars per Awesome spec)

#### Agent Orchestration
- [x] ClaudeSDKClient integration (stateful, multi-turn)
- [x] ClaudeAgentOptions config (budget enforcement, model selection)
- [x] Session management with fork capabilities
- [x] Streaming response handling (partial messages)
- [x] Structured message types (UserMessage, AssistantMessage, ResultMessage)
- [x] Cost tracking via ResultMessage.total_cost_usd
- [x] Token usage logging (input, output, thinking tokens)

#### Agent Types
- [x] **PlannerAgent**: Generates 3-5 search queries per category (Sonnet 4.5)
- [x] **CategoryResearchAgent**: Parallel instances, concurrent category research
- [x] **AggregatorAgent**: Merges & deduplicates candidate links
- [x] **ValidatorAgent**: HTTP checks + description cleanup (Haiku 4.5)
- [x] **RendererAgent**: Markdown generation + lint-fix loops

#### Custom Tools
- [x] **web_search**: Query results with titles, URLs, snippets
- [x] **browse_url**: Content extraction from URLs (BeautifulSoup)
- [x] **github_info**: Repository metadata (stars, description, topics, last_updated)
- [x] **validate_url**: HTTP 200 OK check with timeout handling

#### Quality Assurance
- [x] awesome-lint integration (Markdown validation)
- [x] Iterative fix loop (max 10 attempts)
- [x] ShellCheck validation for shell scripts
- [x] End-to-end testing framework

#### Output Artifacts
- [x] `original.json`: Parsed original list (categories, links, Bloom filter)
- [x] `plan.json`: Search query plan (categories, queries, estimated cost)
- [x] `candidate_*.json`: Per-category research results
- [x] `new_links.json`: Aggregated new links (deduped, deduplicated count)
- [x] `updated_list.md`: Final Markdown output (sorted, lint-compliant)
- [x] `agent.log`: Structured JSON logs (API calls, tokens, costs)
- [x] `summary.txt`: Human-readable statistics

### 1.3 CLI Interface Specification

**Entrypoint**: `./build-and-run.sh` (bash wrapper that builds Docker image + runs container)

**Flags**:
```bash
--repo_url <URL>              # GitHub repository URL (REQUIRED)
--cost_ceiling <USD>          # Max spend in dollars (default: 5.00)
--wall_time <SECONDS>         # Max execution time (default: 600)
--min_stars <COUNT>           # Min GitHub stars for candidates (default: 100)
--output_dir <PATH>           # Directory for run artifacts (default: ./runs)
--seed <INT>                  # Random seed for reproducibility (default: 42)
--model_planner <MODEL>       # Claude model for planning (default: claude-sonnet-4-5)
--model_research <MODEL>      # Claude model for research (default: claude-sonnet-4-5)
--model_validator <MODEL>     # Claude model for validation (default: claude-haiku-4-5)
--help                        # Show help message
```

**Execution Flow**:
1. Validate flags (repo_url required, ANTHROPIC_API_KEY env var required)
2. Build Docker image (`docker build -t awesome-list-researcher:latest .`)
3. Run container with mounted volumes (`-v ./runs:/app/runs`)
4. Execute orchestrator inside container

### 1.4 Agent Types Described

#### PlannerAgent
- **Input**: `original.json` (parsed list structure)
- **Model**: claude-sonnet-4-5
- **Budget**: $0.50 USD (10% of total)
- **Max Turns**: 5
- **Thinking Tokens**: 8000
- **Output**: `plan.json` (3-5 queries per category)
- **System Prompt**: Instructs to understand category themes, generate targeted queries, focus on recent projects (2024+), prioritize high-star repos

#### CategoryResearchAgent
- **Input**: Category name + search queries (from plan.json)
- **Model**: claude-sonnet-4-5
- **Budget**: $1.00 USD per category
- **Max Turns**: 20
- **Allowed Tools**: web_search, browse_url, github_info
- **Session**: Fork-enabled (independent per category)
- **Output**: `candidate_<category>.json` (title, url, description, stars, last_updated, source_query)
- **Parallelization**: Up to CPU core count concurrent agents

#### AggregatorAgent
- **Input**: All `candidate_*.json` files
- **Task**: Merge + deduplicate (Bloom filter + exact match check)
- **Output**: `new_links.json` (deduplicated count, deduplication ratio)
- **No Model Required**: Deterministic merging

#### ValidatorAgent
- **Input**: `new_links.json` (candidate URLs)
- **Model**: claude-haiku-4-5
- **Budget**: $0.10 USD
- **Task 1**: HTTP HEAD checks (async, timeout 10s per URL)
- **Task 2**: Description cleanup (batch LLM refinement, max 100 tokens)
- **Output**: Updated links (invalid URLs removed, descriptions cleaned)

#### RendererAgent
- **Input**: `original.json` + `new_links.json`
- **Task 1**: Merge + alphabetical sort
- **Task 2**: Generate Markdown
- **Task 3**: Lint loop (up to 10 attempts)
  - Run `npx awesome-lint updated_list.md`
  - Parse errors from stderr
  - Apply fixes
  - Regenerate
  - Retry
- **Output**: `updated_list.md` (lint-compliant)

### 1.5 Tool Definitions

#### web_search
```python
Input: {"query": str, "limit": int}
Output: {
  "content": [{"type": "text", "text": "Search results for '...':\n\n**Title**\nURL: ...\nDescription"}]
}
Provider: Brave Search API (or Tavily, Google, etc.)
Error Handling: Returns {"is_error": true} on failure
```

#### browse_url
```python
Input: {"url": str, "max_length": int}
Output: {
  "content": [{"type": "text", "text": "Content from {url}:\n\n{cleaned_text}"}]
}
Processing: BeautifulSoup parsing, script/style removal, whitespace cleanup
Error Handling: Catches httpx.HTTPStatusError, httpx.TimeoutException
```

#### github_info
```python
Input: {"repo_url": str}
Output: {
  "content": [{"type": "text", "text": "Repository: ...\nStars: ...\nDescription: ...\nLanguage: ...\nTopics: ...\nLast Updated: ...\nLicense: ...\nArchived: ..."}]
}
API: https://api.github.com/repos/{owner}/{repo}
Error Handling: Invalid URL detection, HTTP status errors
```

#### validate_url
```python
Input: {"url": str}
Output (200 OK): {
  "content": [{"type": "text", "text": "✓ {url} is accessible (200 OK)"}]
}
Output (non-200): {
  "content": [{"type": "text", "text": "✗ {url} returned {status_code}"}],
  "is_error": true
}
Method: HEAD request with timeout 10s, follow redirects
```

### 1.6 Output Artifacts Specification

#### original.json
```json
{
  "categories": [
    {
      "name": "Command-line Apps",
      "links": [
        {
          "title": "chalk",
          "url": "https://github.com/chalk/chalk",
          "description": "Terminal string styling done right"
        }
      ]
    }
  ],
  "total_links": 487,
  "bloom_filter_size": 10000
}
```

#### plan.json
```json
{
  "categories": [
    {
      "name": "Command-line Apps",
      "queries": [
        "nodejs cli tools 2024",
        "terminal apps github typescript",
        "command line utilities node"
      ]
    }
  ],
  "total_queries": 42,
  "estimated_cost": 0.15
}
```

#### candidate_<category>.json
```json
{
  "category": "Command-line Apps",
  "candidates": [
    {
      "title": "ink",
      "url": "https://github.com/vadimdemedes/ink",
      "description": "React for interactive command-line apps",
      "stars": 24500,
      "last_updated": "2024-11-10",
      "source_query": "nodejs cli tools 2024"
    }
  ],
  "total_candidates": 15,
  "cost_usd": 0.42
}
```

#### new_links.json
```json
{
  "new_links": [
    {
      "category": "Command-line Apps",
      "title": "ink",
      "url": "https://github.com/vadimdemedes/ink",
      "description": "React for interactive command-line apps",
      "stars": 24500
    }
  ],
  "total_new": 127,
  "duplicates_filtered": 43,
  "deduplication_ratio": 0.74
}
```

#### updated_list.md
```markdown
## Command-line Apps

- [chalk](https://github.com/chalk/chalk) - Terminal string styling done right.
- [ink](https://github.com/vadimdemedes/ink) - React for interactive command-line apps.
```

#### agent.log (structured JSON)
```json
{"timestamp": "2024-11-17T15:30:00Z", "level": "INFO", "module": "PlannerAgent", "event": "plan_generated", "categories": 12, "total_queries": 42}
{"timestamp": "2024-11-17T15:30:15Z", "level": "INFO", "module": "CategoryResearchAgent", "event": "research_started", "category": "Command-line Apps"}
{"timestamp": "2024-11-17T15:31:00Z", "level": "INFO", "module": "ResultMessage", "event": "cost_tracked", "cost_usd": 0.42, "tokens": {"input": 1234, "output": 567, "thinking": 89}}
```

#### summary.txt
```text
=== Awesome-List Researcher Summary ===
Repository: sindresorhus/awesome-nodejs
Execution Time: 487s
Total Cost: $3.42 USD

Original Links: 487
New Links Found: 127
Duplicates Filtered: 43
Final Total: 614

Token Usage:
- Input Tokens: 234,567
- Output Tokens: 45,678
- Thinking Tokens: 12,345

Validation:
- HTTP Checks: 127/127 passed
- awesome-lint: PASSED (0 errors)
```

### 1.7 Configuration Options

| Option | Default | Type | Required | Description |
|--------|---------|------|----------|-------------|
| `repo_url` | — | str | YES | GitHub repository URL |
| `cost_ceiling` | 5.00 | float | NO | Max USD spend |
| `wall_time` | 600 | int | NO | Max seconds |
| `min_stars` | 100 | int | NO | Min GitHub stars |
| `output_dir` | ./runs | str | NO | Artifact directory |
| `seed` | 42 | int | NO | Random seed |
| `model_planner` | claude-sonnet-4-5 | str | NO | Planner model |
| `model_research` | claude-sonnet-4-5 | str | NO | Research model |
| `model_validator` | claude-haiku-4-5 | str | NO | Validator model |

### 1.8 Validation Criteria

**Lint Compliance**:
- Run `npx awesome-lint updated_list.md`
- Exit code must be 0 (no errors)
- Repeat up to 10 times with fixes applied

**HTTP Validation**:
- All URLs in `new_links.json` return HTTP 200 OK
- Timeout: 10 seconds per URL
- HEAD request (not GET to save bandwidth)

**Cost Control**:
- Track real cost via `ResultMessage.total_cost_usd`
- Enforce `max_budget_usd` in ClaudeAgentOptions
- Alert if approaching ceiling (e.g., 80%)

**Wall-Time Enforcement**:
- Enforce via signal-based timeout (SIGALRM)
- Graceful shutdown: save intermediate results before exit

**Deduplication**:
- Bloom filter (fast check): O(1) lookup
- Exact match (secondary): Compare against `original.json` URLs
- Cross-category dedup: Keep highest-starred version

**Token Tracking**:
- Log `input_tokens`, `output_tokens`, `thinking_tokens`
- Per-agent summaries in `agent.log`
- Aggregate in `summary.txt`

---

## 2. ACLI v2 Feature Coverage Analysis

### 2.1 How ALR Maps to ACLI Commands

| ACLI Command | ALR Mapping | Notes |
|--------------|------------|-------|
| `acli init alr-test --spec alr-claude.md` | Project initialization | Validates project structure creation, spec file handling |
| `acli run alr-test --prompt "..."` | Orchestrator execution | Validates router classification (GREENFIELD_APP) |
| `acli status alr-test` | Progress tracking | Validates feature_list.json parsing, progress calculation |
| `acli monitor alr-test` | TUI monitoring | Validates all 7 TUI panels, keyboard navigation |
| `acli config get/set` | Config management | Validates memory persistence, config resolution |
| `acli enhance alr-claude.md` | Spec enhancement | Validates plain-English to JSON conversion |

### 2.2 ACLI Subsystems Exercised by ALR

1. **Project Initialization** (acli init)
   - Create project directory
   - Copy spec file
   - Create `.gitignore`, `feature_list.json`, `.git`

2. **Router Classification** (acli run)
   - Analyze spec → classify as GREENFIELD_APP
   - Detect tech stack (Python, Docker, Claude Agent SDK)
   - Route to correct initializer + coding agents

3. **Feature Extraction** (Initializer Agent)
   - Parse ALR spec (2,900 lines)
   - Generate feature_list.json (~200 features)
   - Track feature progress

4. **Progress Tracking** (core/session.py)
   - Read `feature_list.json`
   - Track completed vs remaining features
   - Persist progress across sessions

5. **Tech Stack Detection** (integration/skill_discovery.py)
   - Identify Python 3.12
   - Identify Docker
   - Identify Claude Agent SDK dependency
   - Suggest relevant skills

6. **Memory & Config** (integration/claude_config.py)
   - Store run metadata (timestamps, costs, tokens)
   - Persist across sessions
   - Resolve config precedence

7. **TUI Rendering** (tui/app.py + tui/widgets.py)
   - Render all 7 panels (header, agent graph, detail, logs, stats)
   - Handle real-time event streaming
   - Support keyboard navigation

---

## 3. Validation Scenario Design

### 3.1 Scenario 1: Project Initialization

**Goal**: Verify `acli init` creates correct project structure

**Command**:
```bash
acli init alr-test --spec alr-claude.md --no-interactive
```

**Validation Steps**:
```bash
# 1. Check directory exists
[ -d alr-test ] && echo "✓ Directory created"

# 2. Check spec file copied
[ -f alr-test/app_spec.txt ] && echo "✓ Spec file exists"
head -1 alr-test/app_spec.txt | grep -q "Awesome-List Researcher" && echo "✓ Spec content correct"

# 3. Check feature_list.json exists (empty initially)
[ -f alr-test/feature_list.json ] && echo "✓ feature_list.json created"
cat alr-test/feature_list.json | grep -q '^\[\]$' && echo "✓ feature_list.json is empty array"

# 4. Check .gitignore exists
[ -f alr-test/.gitignore ] && echo "✓ .gitignore created"
grep -q '__pycache__' alr-test/.gitignore && echo "✓ .gitignore has standard entries"

# 5. Check git initialized
[ -d alr-test/.git ] && echo "✓ Git repository initialized"
cd alr-test && git log --oneline | head -1 | grep -q "Initial commit" && echo "✓ Initial commit created"
```

**Evidence**: Directory listing, file content inspection

---

### 3.2 Scenario 2: Router Classification

**Goal**: Verify `acli run` classifies ALR as GREENFIELD_APP

**Command**:
```bash
acli run alr-test --headless --verbose 2>&1 | tee run-output.txt
```

**Validation Steps**:
```bash
# 1. Check router decision logged
grep -q "GREENFIELD_APP" run-output.txt && echo "✓ Router classified as GREENFIELD_APP"

# 2. Check initializer agent started
grep -q "Session 1: initializer" run-output.txt && echo "✓ Initializer session started"

# 3. Check tech stack detected
grep -q "Python 3.12" run-output.txt && echo "✓ Tech stack detected (Python)"
grep -q "Docker" run-output.txt && echo "✓ Tech stack detected (Docker)"
grep -q "claude-agent-sdk" run-output.txt && echo "✓ Tech stack detected (Agent SDK)"

# 4. Check feature_list.json was generated
[ -f alr-test/feature_list.json ] && wc -l alr-test/feature_list.json | awk '{print $1}' > lines.txt
[ $(cat lines.txt) -gt 100 ] && echo "✓ feature_list.json has 100+ lines"

# 5. Check features extracted
cat alr-test/feature_list.json | jq '.[] | .description' 2>/dev/null | head -5 | \
  grep -q "Docker\|CLI\|agent" && echo "✓ Features extracted correctly"
```

**Evidence**: Log output parsing, feature_list.json inspection

---

### 3.3 Scenario 3: Progress Tracking

**Goal**: Verify `acli status` correctly calculates progress

**Command**:
```bash
acli status alr-test --verbose > status-output.txt
```

**Validation Steps**:
```bash
# 1. Check total features count
grep "Total Features" status-output.txt | awk '{print $NF}' > total.txt
[ $(cat total.txt) -gt 100 ] && echo "✓ Total features >100"

# 2. Check passing/remaining calculation
grep "Passing" status-output.txt | awk '{print $NF}' > passing.txt
grep "Remaining" status-output.txt | awk '{print $NF}' > remaining.txt
sum_check=$(($(cat passing.txt) + $(cat remaining.txt)))
total=$(cat total.txt)
[ $sum_check -eq $total ] && echo "✓ Passing + Remaining = Total"

# 3. Check progress percentage
grep "Progress" status-output.txt | awk '{print $NF}' | grep -oE '[0-9]+\.[0-9]+' > progress.txt
prog=$(cat progress.txt)
[ $(echo "$prog > 0" | bc) -eq 1 ] && echo "✓ Progress percentage calculated"

# 4. Check recent features listed
grep -A5 "Recent Passing Features" status-output.txt | wc -l > feature_lines.txt
[ $(cat feature_lines.txt) -gt 3 ] && echo "✓ Recent features displayed"

# 5. Check next features listed
grep -A5 "Next Features" status-output.txt | wc -l > next_lines.txt
[ $(cat next_lines.txt) -gt 3 ] && echo "✓ Next features displayed"
```

**Evidence**: Status output parsing, progress calculation verification

---

### 3.4 Scenario 4: Tech Stack Detection

**Goal**: Verify `acli context alr-test` detects correct tech stack

**Command**:
```bash
acli context alr-test > context-output.txt 2>&1
```

**Expected Output**:
- Language: Python 3.12
- Framework: Claude Agent SDK
- Deployment: Docker
- Build Tool: Poetry
- Quality Tools: awesome-lint, ShellCheck

**Validation Steps**:
```bash
# 1. Check Python 3.12 detected
grep -q "Python" context-output.txt && grep -q "3.12" context-output.txt && echo "✓ Python 3.12 detected"

# 2. Check Claude Agent SDK detected
grep -q "claude-agent-sdk" context-output.txt && echo "✓ Claude Agent SDK detected"

# 3. Check Docker detected
grep -q "Docker" context-output.txt && echo "✓ Docker detected"

# 4. Check Poetry detected
grep -q "Poetry" context-output.txt && echo "✓ Poetry detected"

# 5. Check quality tools listed
grep -q "awesome-lint" context-output.txt && echo "✓ awesome-lint detected"
grep -q "ShellCheck" context-output.txt && echo "✓ ShellCheck detected"

# 6. Check suggested skills
grep -A20 "Suggested Skills" context-output.txt | grep -q "docker" && echo "✓ Docker skill suggested"
grep -A20 "Suggested Skills" context-output.txt | grep -q "agent" && echo "✓ Agent SDK skill suggested"
```

**Evidence**: Context output inspection

---

### 3.5 Scenario 5: Memory & Configuration Persistence

**Goal**: Verify memory is persisted across sessions

**Commands**:
```bash
# First session
acli run alr-test --headless --max-iterations 1

# Check memory file created
[ -f alr-test/.acli/memory.json ] && echo "✓ Memory file created"

# Second session (should resume from memory)
acli memory alr-test > memory-output.txt
```

**Validation Steps**:
```bash
# 1. Check memory file exists
[ -f alr-test/.acli/memory.json ] && echo "✓ Memory persisted"

# 2. Check previous session tracked
grep -q "Session 1" memory-output.txt && echo "✓ Previous session recorded"

# 3. Check costs accumulated
grep "Total Cost" memory-output.txt | grep -oE '\$[0-9]+\.[0-9]{2}' && echo "✓ Cost tracking persisted"

# 4. Check token counts
grep "Input Tokens" memory-output.txt && echo "✓ Token counts persisted"

# 5. Check run history
grep -q "runs/" memory-output.txt && echo "✓ Run artifacts tracked"

# 6. Check configuration loaded from memory
acli config get model | grep -q "claude" && echo "✓ Config persisted"
```

**Evidence**: Memory file inspection, config commands

---

### 3.6 Scenario 6: TUI Rendering with tmux

**Goal**: Verify TUI renders all 7 panels and responds to keyboard input

**Commands** (tmux-based):
```bash
#!/bin/bash

# Create new tmux session in background
tmux new-session -d -s acli-test -c alr-test

# Start ACLI monitor (should launch TUI)
tmux send-keys -t acli-test "acli monitor . --attach" Enter

# Wait for TUI to render
sleep 3

# Capture screen
tmux capture-pane -t acli-test -p > tui-initial.txt

# Test keyboard navigation
tmux send-keys -t acli-test "j" Enter  # Next agent
sleep 1
tmux capture-pane -t acli-test -p > tui-after-j.txt

tmux send-keys -t acli-test "k" Enter  # Prev agent
sleep 1
tmux capture-pane -t acli-test -p > tui-after-k.txt

tmux send-keys -t acli-test "F1" Enter  # All logs filter
sleep 1
tmux capture-pane -t acli-test -p > tui-after-f1.txt

tmux send-keys -t acli-test "p" Enter  # Pause
sleep 1
tmux capture-pane -t acli-test -p > tui-after-p.txt

tmux send-keys -t acli-test "q" Enter  # Quit
sleep 1

# Kill session
tmux kill-session -t acli-test
```

**Validation Steps**:
```bash
# 1. Check TUI header rendered
grep -q "ACLI Agent Monitor\|Agent Graph\|Log Stream" tui-initial.txt && echo "✓ TUI header rendered"

# 2. Check agent graph panel
grep -q "Initializer\|Coding" tui-initial.txt && echo "✓ Agent graph shows agents"

# 3. Check log stream panel
grep -q "Session\|INFO\|DEBUG" tui-initial.txt && echo "✓ Log stream panel rendered"

# 4. Check stats panel
grep -q "Cost\|Tokens\|Progress" tui-initial.txt && echo "✓ Stats panel rendered"

# 5. Check keyboard navigation (j moves selection down)
diff -q tui-initial.txt tui-after-j.txt | grep -q . && echo "✓ 'j' key navigates down"

# 6. Check keyboard navigation (k moves selection up)
diff -q tui-after-j.txt tui-after-k.txt | grep -q . && echo "✓ 'k' key navigates up"

# 7. Check filter changes (F1 changes log filter)
diff -q tui-initial.txt tui-after-f1.txt | grep -q . && echo "✓ 'F1' key filters logs"

# 8. Check pause indication
grep -q "PAUSED\|Resume" tui-after-p.txt && echo "✓ 'p' key pauses orchestrator"

# 9. Check all panel content
[ $(wc -l < tui-initial.txt) -gt 20 ] && echo "✓ TUI renders full screen"

# 10. Check no errors in logs
! grep -q "ERROR\|CRITICAL" tui-initial.txt && echo "✓ No critical errors in TUI"
```

**Evidence**: tmux capture pane output, visual comparison

---

### 3.7 Scenario 7: Full End-to-End Validation

**Goal**: Verify entire ALR workflow with ACLI (init → run → monitor → status)

**Setup**:
```bash
#!/bin/bash

# Clean slate
rm -rf alr-e2e-test

# Step 1: Init
echo "=== Step 1: Init ==="
acli init alr-e2e-test --spec alr-claude.md --no-interactive
[ -d alr-e2e-test ] && echo "✓ Init successful"

# Step 2: Start run in background
echo "=== Step 2: Run (background) ==="
cd alr-e2e-test
timeout 30 acli run . --headless --max-iterations 2 > run.log 2>&1 &
RUN_PID=$!

# Step 3: Monitor progress with status checks
echo "=== Step 3: Status checks ==="
for i in {1..5}; do
  sleep 5
  acli status . > status-$i.txt 2>&1
  passing=$(grep "Passing" status-$i.txt | awk '{print $NF}')
  echo "Check $i: $passing features passing"
done

# Step 4: Check final status
echo "=== Step 4: Final Status ==="
acli status . --verbose > final-status.txt
cat final-status.txt | head -20

# Step 5: Check artifacts
echo "=== Step 5: Artifacts ==="
[ -f feature_list.json ] && echo "✓ feature_list.json exists"
[ -f app_spec.txt ] && echo "✓ app_spec.txt exists"
[ -f .git/config ] && echo "✓ Git initialized"

# Step 6: Verify no errors
echo "=== Step 6: Error Check ==="
! grep -q "ERROR\|CRITICAL" run.log && echo "✓ No critical errors in run log"
wc -l run.log | awk '{print "✓ Run log has " $1 " lines"}'

cd ..
```

**Success Criteria**:
- [x] Init completes (project directory created)
- [x] Run starts (initializer agent executes)
- [x] Status shows increasing progress (sessions execute)
- [x] Artifacts generated (feature_list.json, git commits)
- [x] No critical errors in logs
- [x] Can run multiple iterations without failure

**Evidence**: Combined logs, artifact inspection, status progression

---

## 4. tmux Automation Framework

### 4.1 tmux Helper Functions

```bash
#!/bin/bash
# tui-automation.sh - Helper functions for TUI testing

# Create session and start ACLI
function start_acli_tui() {
  local project_dir=$1
  local session_name=${2:-acli-test}

  tmux new-session -d -s "$session_name" -c "$project_dir"
  tmux send-keys -t "$session_name" "acli monitor . --attach" Enter
  sleep 3
  return 0
}

# Send keystroke and capture output
function send_key_and_capture() {
  local session_name=$1
  local key=$2
  local delay=${3:-1}

  tmux send-keys -t "$session_name" "$key" Enter
  sleep "$delay"
  tmux capture-pane -t "$session_name" -p
}

# Check if text appears in TUI
function check_tui_text() {
  local session_name=$1
  local pattern=$2

  tmux capture-pane -t "$session_name" -p | grep -q "$pattern"
}

# Stop session
function stop_acli_tui() {
  local session_name=$1

  tmux send-keys -t "$session_name" "q" Enter
  sleep 1
  tmux kill-session -t "$session_name" 2>/dev/null
}

# Assert panel exists
function assert_panel_rendered() {
  local session_name=$1
  local panel_name=$2

  if tmux capture-pane -t "$session_name" -p | grep -q "$panel_name"; then
    echo "✓ Panel '$panel_name' rendered"
    return 0
  else
    echo "✗ Panel '$panel_name' NOT rendered"
    return 1
  fi
}

# Test keyboard sequence
function test_keyboard_sequence() {
  local session_name=$1
  shift
  local keys=("$@")
  local before=$(tmux capture-pane -t "$session_name" -p)

  for key in "${keys[@]}"; do
    tmux send-keys -t "$session_name" "$key" Enter
    sleep 1
  done

  local after=$(tmux capture-pane -t "$session_name" -p)

  if [ "$before" != "$after" ]; then
    echo "✓ Screen changed after key sequence: ${keys[*]}"
    return 0
  else
    echo "✗ Screen unchanged after key sequence: ${keys[*]}"
    return 1
  fi
}

# Export all functions
export -f start_acli_tui
export -f send_key_and_capture
export -f check_tui_text
export -f stop_acli_tui
export -f assert_panel_rendered
export -f test_keyboard_sequence
```

### 4.2 Complete TUI Test Script

```bash
#!/bin/bash
# test-alr-tui.sh - Complete TUI validation for ALR

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="alr-test"
SESSION_NAME="alr-tui-test"
PASS_COUNT=0
FAIL_COUNT=0

# Helper: assert
function assert() {
  local condition=$1
  local message=$2

  if eval "$condition"; then
    echo -e "${GREEN}✓${NC} $message"
    ((PASS_COUNT++))
    return 0
  else
    echo -e "${RED}✗${NC} $message"
    ((FAIL_COUNT++))
    return 1
  fi
}

# Helper: capture TUI
function capture_tui() {
  sleep 1
  tmux capture-pane -t "$SESSION_NAME" -p
}

echo -e "${YELLOW}=== ALR TUI Validation ===${NC}\n"

# Step 1: Initialize project
echo -e "${YELLOW}Step 1: Initialize project${NC}"
acli init "$PROJECT_DIR" --spec alr-claude.md --no-interactive > /dev/null
assert "[ -d '$PROJECT_DIR' ]" "Project directory created"

# Step 2: Start ACLI monitor
echo -e "\n${YELLOW}Step 2: Start ACLI monitor${NC}"
tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION_NAME" "acli monitor . --attach" Enter
sleep 4

# Step 3: Check initial TUI rendering
echo -e "\n${YELLOW}Step 3: Check TUI rendering${NC}"
tui_output=$(capture_tui)

assert "echo '$tui_output' | grep -q 'ACLI Agent Monitor'" "TUI title visible"
assert "echo '$tui_output' | grep -q 'Agent Graph\|Agents'" "Agent Graph panel rendered"
assert "echo '$tui_output' | grep -q 'Log Stream\|Logs'" "Log Stream panel rendered"
assert "echo '$tui_output' | grep -q 'Stats\|Cost\|Tokens'" "Stats panel rendered"

# Step 4: Test keyboard navigation (j/k)
echo -e "\n${YELLOW}Step 4: Test keyboard navigation${NC}"
before=$(capture_tui)
tmux send-keys -t "$SESSION_NAME" "j" Enter
after=$(capture_tui)
assert "[ '$before' != '$after' ]" "Screen changes after 'j' key"

before=$(capture_tui)
tmux send-keys -t "$SESSION_NAME" "k" Enter
after=$(capture_tui)
assert "[ '$before' != '$after' ]" "Screen changes after 'k' key"

# Step 5: Test filter keys (F1-F4)
echo -e "\n${YELLOW}Step 5: Test filter keys${NC}"
before=$(capture_tui)
tmux send-keys -t "$SESSION_NAME" "F1" Enter
after=$(capture_tui)
assert "[ '$before' != '$after' ]" "'F1' key changes filter"

# Step 6: Test pause (p)
echo -e "\n${YELLOW}Step 6: Test pause control${NC}"
tmux send-keys -t "$SESSION_NAME" "p" Enter
pause_output=$(capture_tui)
assert "echo '$pause_output' | grep -q 'PAUSED\|Resume\|Paused'" "Pause state visible"

# Step 7: Test resume (p again)
echo -e "\n${YELLOW}Step 7: Test resume${NC}"
tmux send-keys -t "$SESSION_NAME" "p" Enter
resume_output=$(capture_tui)
assert "! echo '$resume_output' | grep -q 'PAUSED'" "Resumed (no PAUSED text)"

# Step 8: Test quit (q)
echo -e "\n${YELLOW}Step 8: Test quit${NC}"
tmux send-keys -t "$SESSION_NAME" "q" Enter
sleep 2
if ! tmux list-sessions 2>/dev/null | grep -q "$SESSION_NAME"; then
  echo -e "${GREEN}✓${NC} 'q' key exits TUI"
  ((PASS_COUNT++))
else
  echo -e "${RED}✗${NC} 'q' key does not exit TUI"
  ((FAIL_COUNT++))
  tmux kill-session -t "$SESSION_NAME"
fi

# Summary
echo -e "\n${YELLOW}=== Summary ===${NC}"
total=$((PASS_COUNT + FAIL_COUNT))
echo -e "Passed: ${GREEN}$PASS_COUNT${NC}/$total"
echo -e "Failed: ${RED}$FAIL_COUNT${NC}/$total"

[ $FAIL_COUNT -eq 0 ] && echo -e "\n${GREEN}All tests passed!${NC}" && exit 0
echo -e "\n${RED}Some tests failed.${NC}" && exit 1
```

---

## 5. Validation Execution Plan

### 5.1 Sequential Execution (Safe for Single Session)

```bash
#!/bin/bash

echo "=== ALR Validation - Sequential Execution ==="

# Test 1: Init
echo "Test 1: Project Initialization"
bash tests/01-init-validation.sh

# Test 2: Router
echo "Test 2: Router Classification"
bash tests/02-router-validation.sh

# Test 3: Progress
echo "Test 3: Progress Tracking"
bash tests/03-progress-validation.sh

# Test 4: Tech Stack
echo "Test 4: Tech Stack Detection"
bash tests/04-techstack-validation.sh

# Test 5: Memory
echo "Test 5: Memory Persistence"
bash tests/05-memory-validation.sh

# Test 6: TUI
echo "Test 6: TUI Rendering"
bash tests/06-tui-validation.sh

# Test 7: E2E
echo "Test 7: End-to-End"
bash tests/07-e2e-validation.sh

echo "=== All Tests Complete ==="
```

### 5.2 Parallel Execution (Advanced)

```bash
#!/bin/bash

echo "=== ALR Validation - Parallel Execution ==="

# Run tests in parallel
bash tests/01-init-validation.sh &
bash tests/02-router-validation.sh &
bash tests/03-progress-validation.sh &
bash tests/04-techstack-validation.sh &
bash tests/05-memory-validation.sh &

# Wait for all background jobs
wait

# TUI test must be sequential (tmux state-sensitive)
bash tests/06-tui-validation.sh

# E2E test must be last
bash tests/07-e2e-validation.sh

echo "=== All Tests Complete ==="
```

---

## 6. Success Metrics & Acceptance Criteria

### 6.1 Init Validation
- [x] Project directory created
- [x] Spec file copied correctly
- [x] feature_list.json exists (empty array)
- [x] .gitignore created with standard entries
- [x] Git repository initialized with initial commit

**Pass Rate**: 5/5 checks must pass

### 6.2 Router Validation
- [x] Router classifies ALR as GREENFIELD_APP
- [x] Initializer agent starts
- [x] Tech stack detected (Python, Docker, Agent SDK)
- [x] feature_list.json generated with 100+ features
- [x] Features extracted correctly (descriptions contain expected keywords)

**Pass Rate**: 5/5 checks must pass

### 6.3 Progress Validation
- [x] Total features >100
- [x] Passing + Remaining = Total (math checks)
- [x] Progress percentage calculated (>0 if features executed)
- [x] Recent features displayed (≥3 shown)
- [x] Next features displayed (≥3 shown)

**Pass Rate**: 5/5 checks must pass

### 6.4 Tech Stack Validation
- [x] Python 3.12 detected
- [x] Claude Agent SDK detected
- [x] Docker detected
- [x] Poetry detected
- [x] awesome-lint, ShellCheck detected
- [x] Skills suggestions generated

**Pass Rate**: 6/6 checks must pass

### 6.5 Memory Validation
- [x] Memory file persisted
- [x] Previous sessions tracked
- [x] Costs accumulated
- [x] Token counts persisted
- [x] Run artifacts tracked
- [x] Configuration persisted

**Pass Rate**: 6/6 checks must pass

### 6.6 TUI Validation
- [x] TUI header rendered
- [x] Agent Graph panel shows agents
- [x] Log Stream panel shows logs
- [x] Stats panel shows metrics
- [x] 'j' key navigates down
- [x] 'k' key navigates up
- [x] 'F1' key filters logs
- [x] 'p' key pauses/resumes
- [x] 'q' key exits cleanly
- [x] No critical errors

**Pass Rate**: 10/10 checks must pass

### 6.7 End-to-End Validation
- [x] Init successful
- [x] Run starts without errors
- [x] Status shows progress (increasing passing features)
- [x] Artifacts created (feature_list.json, app_spec.txt)
- [x] Git commits made
- [x] No critical errors in logs

**Pass Rate**: 6/6 checks must pass

**Overall Success**: All 7 scenarios pass (42/42 checks)

---

## 7. Unresolved Questions & Open Items

1. **Initializer Agent Prompt**: How extensive should the feature extraction be? ALR spec is 2,900 lines. Should initializer create ~200 features or more granular breakdown?

2. **Coding Agent Loop**: How many iterations should ALR run for before considering it "complete"? Each feature is complex (docker setup, agent implementation, tool setup). Realistic estimate?

3. **Cost Control Validation**: How to verify cost tracking in ACLI? Should costs be logged to `feature_list.json` or separate memory file?

4. **Token Tracking**: Should token counts be per-agent or aggregated? ALR spec mentions input_tokens, output_tokens, thinking_tokens. How to expose in ACLI?

5. **TUI Panel Content**: When monitoring ALR, what should each panel show?
   - Agent Graph: Which agents? (PlannerAgent, ResearchAgent, etc.)
   - Detail Panel: What agent details matter most? (Token count, cost, status)
   - Log Stream: Filter by tool calls, agent decisions, or all activity?

6. **Memory Persistence Format**: Should ACLI use `.acli/memory.json` or `~/.claude/agent-memory/alr/` paths? How does this interact with user's personal CLAUDE.md memory?

7. **Skill Discovery Integration**: Should ACLI auto-detect ALR tools (web_search, github_info, etc.) and suggest relevant Claude Code skills? Or is this out of scope?

8. **Docker Validation**: Should ACLI validate Dockerfile during init? Or just note that Docker is required? ALR spec uses Docker—how to test without breaking host system?

---

## Appendix A: ALR Spec Summary Table

| Component | Type | Count | Details |
|-----------|------|-------|---------|
| Features | Enum | 5 | Core infra, data acq, agent orch, QA, output |
| CLI Flags | Flag | 9 | repo_url, cost_ceiling, wall_time, etc. |
| Agent Types | Agent | 5 | Planner, CategoryResearch, Aggregator, Validator, Renderer |
| Tools | Tool | 4 | web_search, browse_url, github_info, validate_url |
| Output Artifacts | File | 7 | original.json, plan.json, candidate_*.json, new_links.json, updated_list.md, agent.log, summary.txt |
| Configuration Options | Config | 9 | Same as CLI flags |
| Validation Criteria | Criterion | 6 | Lint, HTTP, Cost, Time, Dedup, Tokens |

---

## Appendix B: Test Directory Structure

```
plans/tests/
├── 01-init-validation.sh
├── 02-router-validation.sh
├── 03-progress-validation.sh
├── 04-techstack-validation.sh
├── 05-memory-validation.sh
├── 06-tui-validation.sh
├── 07-e2e-validation.sh
└── tui-automation.sh (helper functions)
```

---

**Report Generated**: 2026-03-18
**Researcher**: af8438a7f2cd36aeb
**Status**: Research complete, ready for implementation phase
