# Gate Validation Protocol

Every validation gate in this plan follows this exact protocol. No exceptions.

## Pre-Gate (mandatory)

1. Invoke `/functional-validation` skill — load Iron Rule context
2. Invoke `/gate-validation-discipline` skill — load evidence verification rules
3. Define PASS criteria BEFORE capturing evidence (never after)

## Execution (mandatory)

1. `pip install -e ".[dev]"` in project root — must exit 0
2. Run REAL `acli` CLI commands as an end user would
3. Capture ALL stdout/stderr to `evidence/{gate-id}/` directory using `tee`
4. For TUI gates: use tmux (see tmux protocol below)
5. Allow gates to take real time — minutes, not seconds
6. Never use `python -c "assert..."` as the PRIMARY validation — only as supplementary

## Evidence Capture

```bash
mkdir -p evidence/{gate-id}
# Every command saves output:
acli <command> 2>&1 | tee evidence/{gate-id}/command-name.txt
echo "EXIT_CODE: $?" >> evidence/{gate-id}/command-name.txt
```

## Post-Gate Verification (mandatory)

### Verifier 1 (independent agent)
- READ every evidence file (not just check existence)
- CITE specific lines/content that prove PASS
- Quote actual output, not paraphrase
- Determine PASS or FAIL with reasoning

### Verifier 2 (independent agent)
- Independently READ the same evidence files
- Independently determine PASS or FAIL
- Must NOT see Verifier 1's determination first

### Consensus
- Both must agree PASS for gate to pass
- If disagreement: escalate to user
- If both FAIL: fix real system, re-run from Execution step

## Evidence Quality Standards

| Good Evidence | Bad Evidence |
|--------------|-------------|
| "acli config list output shows `model: claude-sonnet-4-6-20250514` on line 3" | "config command works" |
| "acli init created 4 files: app_spec.txt, .gitignore, feature_list.json, .git/" | "project initialized" |
| "tmux capture-pane shows 'ACLI Agent Monitor' on line 1 and 'AGENT HIERARCHY' on line 5" | "TUI renders" |
| "grep returned 0 matches for old model string" | "no stale strings" |
| "JSONL file has 4 lines, first line type='session_start', last line type='session_end'" | "logging works" |

## tmux Protocol (for TUI gates)

```bash
# Start
tmux new-session -d -s {session-name} -x 120 -y 40
tmux send-keys -t {session-name} "acli monitor {project-dir} --detached" Enter
sleep 4  # Let TUI render

# Capture
tmux capture-pane -t {session-name} -p > evidence/{gate-id}/tui-capture.txt

# Interact
tmux send-keys -t {session-name} "j"   # Navigate down
sleep 1
tmux capture-pane -t {session-name} -p > evidence/{gate-id}/tui-after-j.txt

tmux send-keys -t {session-name} "/"   # Focus prompt
sleep 1
tmux capture-pane -t {session-name} -p > evidence/{gate-id}/tui-prompt-focus.txt

# Cleanup
tmux send-keys -t {session-name} "q"
sleep 1
tmux kill-session -t {session-name} 2>/dev/null
```

## Mock Detection Guard

Before executing ANY gate, check intent:
- Creating test files → STOP
- Importing mock libraries → STOP
- Using in-memory databases → STOP
- Adding TEST_MODE flags → STOP

If the urge to mock arises, that's a signal the real system has a bug. Fix it.

## ALR Test Payload

The Awesome-List-Researcher spec (`alr-claude.md` in project root) is used as the REAL project payload:
- **Greenfield test**: `acli init alr-test --spec alr-claude.md` → builds from scratch
- **Brownfield test**: After greenfield, `acli onboard alr-test` → re-analyzes as existing project
- **Router test**: Router should classify ALR + app_spec.txt as GREENFIELD_APP
- **Context test**: After onboard, context should show Python, Docker, Claude Agent SDK
