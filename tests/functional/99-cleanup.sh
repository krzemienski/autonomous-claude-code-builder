#!/bin/bash
# Test 99: Cleanup test artifacts

set -e

echo "=== Test 99: Cleanup ==="

# Cleanup any leftover test directories
echo "→ Cleaning up test projects..."
rm -rf /tmp/acli-test-project-*
rm -rf /tmp/acli-enhance-test-*
rm -rf /tmp/acli-status-test-*
rm -rf /tmp/acli-empty-*
echo "✓ Test projects cleaned"

# Cleanup temp files
echo "→ Cleaning up temp files..."
rm -f /tmp/skills-output-*.txt
rm -f /tmp/skills-json-*.txt
rm -f /tmp/status-output-*.txt
rm -f /tmp/status-err-*.txt
rm -f /tmp/status-empty-*.txt
rm -f /tmp/security-test-*.txt
echo "✓ Temp files cleaned"

# Note: We don't remove config backups as they might be needed

echo "→ Verifying cleanup..."
LEFTOVER=$(find /tmp -name "acli-*-$$" 2>/dev/null | wc -l | tr -d ' ')
if [ "$LEFTOVER" -gt 0 ]; then
    echo "⊘ Some test artifacts remain in /tmp (may be from other runs)"
else
    echo "✓ All test artifacts cleaned"
fi

echo ""
echo "✓✓✓ Test 99 PASSED ✓✓✓"
echo ""
