#!/bin/bash
# Test 01: Project initialization

set -e

echo "=== Test 01: Project Initialization ==="

# Cleanup from previous runs
TEST_PROJECT="/tmp/acli-test-project-$$"
rm -rf "$TEST_PROJECT"

# Test 1: Create new project
echo "→ Running acli init..."
acli init "$TEST_PROJECT" > /dev/null 2>&1
echo "✓ Init command executed"

# Test 2: Verify directory created
echo "→ Verifying directory created..."
if [ ! -d "$TEST_PROJECT" ]; then
    echo "✗ Project directory not created"
    exit 1
fi
echo "✓ Project directory exists"

# Test 3: Verify app_spec.txt created
echo "→ Verifying app_spec.txt..."
if [ ! -f "$TEST_PROJECT/app_spec.txt" ]; then
    echo "✗ app_spec.txt not created"
    exit 1
fi
echo "✓ app_spec.txt created"

# Test 4: Verify git initialized
echo "→ Verifying git initialization..."
if [ ! -d "$TEST_PROJECT/.git" ]; then
    echo "✗ Git repository not initialized"
    exit 1
fi
echo "✓ Git repository initialized"

# Test 5: Verify feature_list.json created
echo "→ Verifying feature_list.json..."
if [ ! -f "$TEST_PROJECT/feature_list.json" ]; then
    echo "✗ feature_list.json not created"
    exit 1
fi
echo "✓ feature_list.json created"

# Test 6: Verify feature_list.json is valid JSON
echo "→ Validating feature_list.json structure..."
if ! python3 -c "import json; json.load(open('$TEST_PROJECT/feature_list.json'))" 2>/dev/null; then
    echo "✗ feature_list.json is not valid JSON"
    exit 1
fi
echo "✓ feature_list.json is valid JSON"

# Test 7: Verify gitignore
echo "→ Verifying .gitignore..."
if [ ! -f "$TEST_PROJECT/.gitignore" ]; then
    echo "✗ .gitignore not created"
    exit 1
fi
echo "✓ .gitignore created"

# Cleanup
rm -rf "$TEST_PROJECT"

echo ""
echo "✓✓✓ Test 01 PASSED ✓✓✓"
echo ""
