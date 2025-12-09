# Functional Test Suite

End-to-end functional tests for Autonomous CLI Builder. These are **pure shell scripts** that test REAL CLI commands with NO mocking.

## Test Philosophy

- **NO unit tests** - Only functional/integration tests
- **NO mocks** - Tests run against real CLI commands
- **NO pytest** - Pure bash scripts (except test_security.py)
- **Real workflows** - Tests actual user scenarios
- **Real files** - Creates and manipulates real test projects

## Running Tests

### Run All Tests

```bash
# From project root
./tests/run_e2e.sh
```

### Run Individual Test

```bash
# From project root
bash tests/functional/01-init-project.sh
```

## Test Suite

| Test | Description | Requirements |
|------|-------------|--------------|
| **00-setup.sh** | Installation and CLI availability | None |
| **01-init-project.sh** | Project initialization workflow | None |
| **02-enhance-spec.sh** | Spec enhancement via Claude API | `ANTHROPIC_API_KEY` |
| **03-config-management.sh** | Config get/set/list commands | None |
| **04-skill-discovery.sh** | Skill discovery and listing | None |
| **05-status-check.sh** | Project status reporting | None |
| **06-security-validation.sh** | Security hooks validation | pytest |
| **99-cleanup.sh** | Cleanup test artifacts | None |

## Test Details

### 00-setup.sh

Tests that package installation works and CLI is accessible:
- pip install -e .
- acli --version works
- acli --help works
- Python import works
- All expected commands present

### 01-init-project.sh

Tests project initialization workflow:
- Creates new project directory
- Generates app_spec.txt
- Initializes git repository
- Creates feature_list.json
- Creates .gitignore

### 02-enhance-spec.sh

Tests spec enhancement via Claude API (skipped if no API key):
- Takes rambling input text
- Calls acli enhance
- Generates structured spec.json
- Validates JSON output
- Checks for expected fields

**Note**: Requires `ANTHROPIC_API_KEY` environment variable.

### 03-config-management.sh

Tests configuration management:
- acli config list
- acli config set model claude-sonnet-4-5
- acli config get model
- Verifies ~/.config/acli/config.json
- Tests multiple config values
- Backups and restores config

### 04-skill-discovery.sh

Tests skill discovery functionality:
- acli list-skills works
- Output format is readable
- Detects skills if ~/.claude/skills exists
- Tests JSON output if supported

### 05-status-check.sh

Tests project status reporting:
- Creates test feature_list.json
- acli status shows progress
- Displays feature information
- Handles missing files gracefully
- Calculates completion percentages

### 06-security-validation.sh

Runs the comprehensive security test suite:
- Executes tests/test_security.py
- Verifies all 67 security tests pass
- Tests command injection prevention
- Tests path traversal prevention
- Tests file operation safety

### 99-cleanup.sh

Cleanup test artifacts:
- Removes test projects
- Removes temp files
- Preserves config backups

## Output Format

Each test outputs:
- Test name and description
- Step-by-step progress with → indicators
- Success with ✓ checkmarks
- Failures with ✗ marks
- Skipped tests with ⊘ symbol

Example:
```
=== Test 01: Project Initialization ===
→ Running acli init...
✓ Init command executed
→ Verifying directory created...
✓ Project directory exists
...
✓✓✓ Test 01 PASSED ✓✓✓
```

## Master Script Output

The `run_e2e.sh` master script provides:
- Running header with box drawing
- Per-test execution with separator lines
- Summary with color-coded results
- Pass/fail/skip counts
- Exit code 0 for success, 1 for failures

## Test Isolation

Tests use unique temp directories to avoid conflicts:
- Pattern: `/tmp/acli-*-$$` (uses process ID)
- Each test cleans up its own artifacts
- Test 99 does final cleanup sweep
- Config backups preserved

## Dependencies

**Required**:
- bash
- python3
- pip

**Optional**:
- ANTHROPIC_API_KEY (for test 02)
- pytest (for test 06, auto-installed)
- ~/.claude/skills/ (for test 04 to verify detection)

## Exit Codes

- **0**: All tests passed or skipped
- **1**: One or more tests failed
- **Test skipped**: Exits 0 with skip message (e.g., no API key)

## Adding New Tests

1. Create `NN-test-name.sh` in `tests/functional/`
2. Follow naming convention: `NN-descriptive-name.sh`
3. Use consistent output format (→, ✓, ✗, ⊘)
4. Make executable: `chmod +x tests/functional/NN-test-name.sh`
5. Test will auto-run in `run_e2e.sh`

### Test Script Template

```bash
#!/bin/bash
# Test NN: Description

set -e

echo "=== Test NN: Description ==="

# Test 1: Description
echo "→ Testing something..."
# ... test code ...
echo "✓ Test passed"

# Cleanup
# ... cleanup code ...

echo ""
echo "✓✓✓ Test NN PASSED ✓✓✓"
echo ""
```

## CI/CD Integration

To run in CI:

```yaml
- name: Run functional tests
  run: |
    pip install -e .
    ./tests/run_e2e.sh
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Security Note

`test_security.py` is the ONLY Python test file kept. It tests real security hooks and cannot be easily converted to shell scripts. All other functionality tests are pure shell.

## Troubleshooting

**Test fails immediately**: Check that you've installed the package first
```bash
pip install -e .
```

**API test skipped**: Set ANTHROPIC_API_KEY if you want to test enhancement
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

**Permission denied**: Make scripts executable
```bash
chmod +x tests/functional/*.sh tests/run_e2e.sh
```

**Old artifacts interfere**: Run cleanup manually
```bash
bash tests/functional/99-cleanup.sh
```
