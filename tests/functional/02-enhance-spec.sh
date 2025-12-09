#!/bin/bash
# Test 02: Spec enhancement (requires ANTHROPIC_API_KEY)

set -e

echo "=== Test 02: Spec Enhancement ==="

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⊘ SKIPPED: ANTHROPIC_API_KEY not set"
    echo "  Set ANTHROPIC_API_KEY to run this test"
    echo ""
    exit 0
fi

# Setup
TEST_DIR="/tmp/acli-enhance-test-$$"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

# Test 1: Create rambling input file
echo "→ Creating test input file..."
cat > "$TEST_DIR/test-input.txt" <<'EOF'
I want to build a todo app. It should have tasks and you can mark them done.
Maybe add some categories or tags? Not sure. Also it would be cool if it had
a nice UI, probably web-based. Oh and users should be able to login somehow.
Save the data somewhere, database I guess. Make it look good!
EOF
echo "✓ Test input created"

# Test 2: Run enhance command
echo "→ Running acli enhance (this may take a moment)..."
cd "$TEST_DIR"
if ! acli enhance test-input.txt > /dev/null 2>&1; then
    echo "✗ Enhance command failed"
    rm -rf "$TEST_DIR"
    exit 1
fi
echo "✓ Enhance command executed"

# Test 3: Verify spec.json created
echo "→ Verifying spec.json created..."
if [ ! -f "spec.json" ]; then
    echo "✗ spec.json not created"
    rm -rf "$TEST_DIR"
    exit 1
fi
echo "✓ spec.json created"

# Test 4: Verify spec.json is valid JSON
echo "→ Validating spec.json structure..."
if ! python3 -c "import json; json.load(open('spec.json'))" 2>/dev/null; then
    echo "✗ spec.json is not valid JSON"
    rm -rf "$TEST_DIR"
    exit 1
fi
echo "✓ spec.json is valid JSON"

# Test 5: Verify spec.json has expected fields
echo "→ Checking spec.json contains structured data..."
SPEC_CONTENT=$(cat spec.json)
if ! echo "$SPEC_CONTENT" | grep -q "project_name\|features\|requirements"; then
    echo "✗ spec.json missing expected fields"
    rm -rf "$TEST_DIR"
    exit 1
fi
echo "✓ spec.json has structured output"

# Test 6: Verify spec.json is non-empty
echo "→ Verifying spec.json has content..."
SPEC_SIZE=$(wc -c < spec.json | tr -d ' ')
if [ "$SPEC_SIZE" -lt 100 ]; then
    echo "✗ spec.json is too small (< 100 bytes)"
    rm -rf "$TEST_DIR"
    exit 1
fi
echo "✓ spec.json has substantial content ($SPEC_SIZE bytes)"

# Cleanup
rm -rf "$TEST_DIR"

echo ""
echo "✓✓✓ Test 02 PASSED ✓✓✓"
echo ""
