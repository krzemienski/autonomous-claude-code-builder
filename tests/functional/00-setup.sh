#!/bin/bash
# Test 00: Installation and CLI availability

set -e

echo "=== Test 00: Installation and CLI Availability ==="

# Test 1: Install package
echo "→ Installing acli package..."
pip install -e . > /dev/null 2>&1
echo "✓ Package installed"

# Test 2: CLI available in PATH
echo "→ Testing CLI availability..."
if ! command -v acli &> /dev/null; then
    echo "✗ acli command not found in PATH"
    exit 1
fi
echo "✓ acli command available"

# Test 3: Version command
echo "→ Testing --version..."
VERSION=$(acli --version 2>&1)
if [ -z "$VERSION" ]; then
    echo "✗ Version command failed"
    exit 1
fi
echo "✓ Version: $VERSION"

# Test 4: Help command
echo "→ Testing --help..."
HELP=$(acli --help 2>&1)
if ! echo "$HELP" | grep -qi "usage:"; then
    echo "✗ Help command failed"
    exit 1
fi
echo "✓ Help output contains usage information"

# Test 5: Python import
echo "→ Testing Python import..."
python3 -c "import sys; sys.path.insert(0, 'src'); import acli; print('Import successful')" > /dev/null 2>&1
echo "✓ Python package importable"

# Test 6: Check main commands exist
echo "→ Verifying commands exist..."
for cmd in init enhance config status list-skills; do
    if ! acli --help 2>&1 | grep -q "$cmd"; then
        echo "✗ Command '$cmd' not found in help"
        exit 1
    fi
done
echo "✓ All expected commands present"

echo ""
echo "✓✓✓ Test 00 PASSED ✓✓✓"
echo ""
