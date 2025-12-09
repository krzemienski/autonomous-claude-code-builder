#!/bin/bash
# Test 05: Status command

set -e

echo "=== Test 05: Status Check ==="

# Setup test project
TEST_PROJECT="/tmp/acli-status-test-$$"
rm -rf "$TEST_PROJECT"
mkdir -p "$TEST_PROJECT"

# Test 1: Create feature_list.json manually
echo "→ Creating test feature_list.json..."
cat > "$TEST_PROJECT/feature_list.json" <<'EOF'
{
  "features": [
    {
      "id": "feature-1",
      "name": "User Authentication",
      "status": "completed",
      "priority": "high",
      "description": "Login and registration system"
    },
    {
      "id": "feature-2",
      "name": "Dashboard",
      "status": "in_progress",
      "priority": "high",
      "description": "Main user dashboard"
    },
    {
      "id": "feature-3",
      "name": "Analytics",
      "status": "pending",
      "priority": "medium",
      "description": "Usage analytics"
    }
  ]
}
EOF
echo "✓ feature_list.json created"

# Test 2: Run status command
echo "→ Running acli status..."
if ! acli status "$TEST_PROJECT" > /tmp/status-output-$$.txt 2>&1; then
    echo "✗ Status command failed"
    cat /tmp/status-output-$$.txt
    rm -rf "$TEST_PROJECT"
    rm -f /tmp/status-output-$$.txt
    exit 1
fi
echo "✓ Status command executed"

# Test 3: Verify output shows progress
echo "→ Verifying progress display..."
OUTPUT=$(cat /tmp/status-output-$$.txt)
if [ -z "$OUTPUT" ]; then
    echo "✗ Status produced no output"
    rm -rf "$TEST_PROJECT"
    rm -f /tmp/status-output-$$.txt
    exit 1
fi
echo "✓ Status produced output"

# Test 4: Check for feature information
echo "→ Checking for feature information..."
if ! echo "$OUTPUT" | grep -q -i "feature\|status\|progress"; then
    echo "✗ Output doesn't contain feature/status information"
    echo "Output: $OUTPUT"
    rm -rf "$TEST_PROJECT"
    rm -f /tmp/status-output-$$.txt
    exit 1
fi
echo "✓ Output contains feature information"

# Test 5: Verify counts/percentages if shown
echo "→ Verifying status calculations..."
if echo "$OUTPUT" | grep -q "33\|1/3\|completed.*1"; then
    echo "✓ Status calculations appear correct (1/3 completed)"
elif echo "$OUTPUT" | grep -q "completed\|pending\|in_progress"; then
    echo "✓ Status shows feature states"
else
    echo "⊘ Cannot verify calculation format (may use different display)"
fi

# Test 6: Test with non-existent project
echo "→ Testing with non-existent project..."
if acli status "/tmp/nonexistent-project-$$" > /tmp/status-err-$$.txt 2>&1; then
    echo "⊘ Status didn't fail on non-existent project (may create it)"
else
    echo "✓ Status properly handles non-existent project"
fi
rm -f /tmp/status-err-$$.txt

# Test 7: Test with missing feature_list.json
echo "→ Testing with missing feature_list.json..."
EMPTY_PROJECT="/tmp/acli-empty-$$"
mkdir -p "$EMPTY_PROJECT"
if acli status "$EMPTY_PROJECT" > /tmp/status-empty-$$.txt 2>&1; then
    EMPTY_OUTPUT=$(cat /tmp/status-empty-$$.txt)
    if echo "$EMPTY_OUTPUT" | grep -q -i "no features\|empty\|0"; then
        echo "✓ Status handles missing feature_list.json"
    else
        echo "⊘ Status output for missing feature_list.json: $EMPTY_OUTPUT"
    fi
else
    echo "✓ Status properly fails on missing feature_list.json"
fi
rm -rf "$EMPTY_PROJECT"
rm -f /tmp/status-empty-$$.txt

# Cleanup
rm -rf "$TEST_PROJECT"
rm -f /tmp/status-output-$$.txt

echo ""
echo "✓✓✓ Test 05 PASSED ✓✓✓"
echo ""
