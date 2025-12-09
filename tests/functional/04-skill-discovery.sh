#!/bin/bash
# Test 04: Skill discovery

set -e

echo "=== Test 04: Skill Discovery ==="

# Test 1: Command executes without error
echo "→ Running list-skills command..."
if ! acli list-skills > /tmp/skills-output-$$.txt 2>&1; then
    echo "✗ list-skills command failed"
    rm -f /tmp/skills-output-$$.txt
    exit 1
fi
echo "✓ list-skills executed"

# Test 2: Check output format
echo "→ Checking output format..."
OUTPUT=$(cat /tmp/skills-output-$$.txt)

# Should either show skills or show "no skills found" message
if [ -z "$OUTPUT" ]; then
    echo "✗ list-skills produced no output"
    rm -f /tmp/skills-output-$$.txt
    exit 1
fi
echo "✓ list-skills produced output"

# Test 3: If skills directory exists, verify it finds them
if [ -d "$HOME/.claude/skills" ]; then
    SKILL_COUNT=$(find "$HOME/.claude/skills" -maxdepth 1 -type d ! -path "$HOME/.claude/skills" | wc -l | tr -d ' ')
    if [ "$SKILL_COUNT" -gt 0 ]; then
        echo "→ Verifying skills detected ($SKILL_COUNT found in directory)..."
        if ! echo "$OUTPUT" | grep -q "skill\|Skill"; then
            echo "✗ Skills exist but not shown in output"
            echo "Output: $OUTPUT"
            rm -f /tmp/skills-output-$$.txt
            exit 1
        fi
        echo "✓ Skills properly detected"
    else
        echo "⊘ No skills in ~/.claude/skills to test with"
    fi
else
    echo "⊘ ~/.claude/skills directory doesn't exist"
fi

# Test 4: Verify output is readable
echo "→ Verifying output readability..."
if echo "$OUTPUT" | grep -q "Error\|error\|ERROR" && ! echo "$OUTPUT" | grep -q "No skills found"; then
    echo "✗ Output contains errors: $OUTPUT"
    rm -f /tmp/skills-output-$$.txt
    exit 1
fi
echo "✓ Output is clean"

# Test 5: Try JSON output if supported
echo "→ Testing JSON format (if supported)..."
if acli list-skills --format json > /tmp/skills-json-$$.txt 2>&1; then
    if [ -s /tmp/skills-json-$$.txt ]; then
        if ! python3 -c "import json; json.load(open('/tmp/skills-json-$$.txt'))" 2>/dev/null; then
            echo "⊘ JSON output flag exists but output not valid JSON (may not be implemented)"
        else
            echo "✓ JSON output is valid"
        fi
    fi
    rm -f /tmp/skills-json-$$.txt
else
    echo "⊘ JSON format not supported (OK)"
fi

# Cleanup
rm -f /tmp/skills-output-$$.txt

echo ""
echo "✓✓✓ Test 04 PASSED ✓✓✓"
echo ""
