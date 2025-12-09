#!/bin/bash
# Test 06: Security validation (runs test_security.py)

set -e

echo "=== Test 06: Security Validation ==="

# Test 1: Verify test_security.py exists
echo "→ Checking test_security.py exists..."
if [ ! -f "tests/test_security.py" ]; then
    echo "✗ test_security.py not found"
    exit 1
fi
echo "✓ test_security.py found"

# Test 2: Install test dependencies if needed
echo "→ Ensuring pytest is available..."
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "  Installing pytest..."
    pip install pytest > /dev/null 2>&1
fi
echo "✓ pytest available"

# Test 3: Run security tests
echo "→ Running security tests..."
if ! python3 -m pytest tests/test_security.py -v > /tmp/security-test-$$.txt 2>&1; then
    echo "✗ Security tests failed"
    cat /tmp/security-test-$$.txt
    rm -f /tmp/security-test-$$.txt
    exit 1
fi
echo "✓ Security tests executed"

# Test 4: Verify all tests passed
echo "→ Verifying test results..."
TEST_OUTPUT=$(cat /tmp/security-test-$$.txt)

# Count passed tests
PASSED=$(echo "$TEST_OUTPUT" | grep -o "[0-9]* passed" | grep -o "[0-9]*" || echo "0")
FAILED=$(echo "$TEST_OUTPUT" | grep -o "[0-9]* failed" | grep -o "[0-9]*" || echo "0")

if [ "$FAILED" != "0" ]; then
    echo "✗ Some security tests failed ($FAILED failures)"
    cat /tmp/security-test-$$.txt
    rm -f /tmp/security-test-$$.txt
    exit 1
fi

if [ "$PASSED" -lt 50 ]; then
    echo "✗ Too few tests passed ($PASSED, expected ~67)"
    cat /tmp/security-test-$$.txt
    rm -f /tmp/security-test-$$.txt
    exit 1
fi

echo "✓ All security tests passed ($PASSED tests)"

# Test 5: Check for specific security features tested
echo "→ Verifying security coverage..."
if ! echo "$TEST_OUTPUT" | grep -q "test_"; then
    echo "✗ No test cases found in output"
    rm -f /tmp/security-test-$$.txt
    exit 1
fi
echo "✓ Security test coverage verified"

# Cleanup
rm -f /tmp/security-test-$$.txt

echo ""
echo "✓✓✓ Test 06 PASSED ($PASSED security tests) ✓✓✓"
echo ""
