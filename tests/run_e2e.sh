#!/bin/bash
# Master script to run all functional end-to-end tests
# NO mocks, NO pytest - pure shell script functional tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Autonomous CLI Builder - Functional Test Suite           ║"
echo "║  Pure shell scripts testing REAL CLI commands              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Test counters
TOTAL=0
PASSED=0
FAILED=0
SKIPPED=0

# Array to store results
declare -a RESULTS

# Function to run a test
run_test() {
    local test_file=$1
    local test_name=$(basename "$test_file" .sh)

    TOTAL=$((TOTAL + 1))

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Running: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Run test and capture output
    if bash "$test_file" 2>&1; then
        PASSED=$((PASSED + 1))
        RESULTS+=("${GREEN}✓${NC} $test_name")
        echo ""
        return 0
    else
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 0 ]; then
            # Test was skipped
            SKIPPED=$((SKIPPED + 1))
            RESULTS+=("${YELLOW}⊘${NC} $test_name (skipped)")
            echo ""
            return 0
        else
            FAILED=$((FAILED + 1))
            RESULTS+=("${RED}✗${NC} $test_name")
            echo ""
            return 1
        fi
    fi
}

# Find and run all test scripts in order
if [ -d "tests/functional" ]; then
    for test in tests/functional/*.sh; do
        if [ -f "$test" ]; then
            # Make executable if not already
            chmod +x "$test"
            run_test "$test"
        fi
    done
else
    echo "${RED}Error: tests/functional directory not found${NC}"
    exit 1
fi

# Print summary
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  TEST SUMMARY                                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Print individual results
for result in "${RESULTS[@]}"; do
    echo -e "$result"
done

echo ""
echo "────────────────────────────────────────────────────────────"
echo -e "Total Tests:    $TOTAL"
echo -e "${GREEN}Passed:${NC}        $PASSED"
if [ $SKIPPED -gt 0 ]; then
    echo -e "${YELLOW}Skipped:${NC}       $SKIPPED"
fi
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed:${NC}        $FAILED"
fi
echo "────────────────────────────────────────────────────────────"

# Exit with appropriate code
if [ $FAILED -gt 0 ]; then
    echo ""
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
fi
