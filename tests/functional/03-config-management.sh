#!/bin/bash
# Test 03: Config management

set -e

echo "=== Test 03: Config Management ==="

# Backup existing config if present
CONFIG_DIR="$HOME/.config/acli"
CONFIG_FILE="$CONFIG_DIR/config.json"
BACKUP_FILE="$CONFIG_DIR/config.json.bak.$$"

if [ -f "$CONFIG_FILE" ]; then
    echo "→ Backing up existing config..."
    cp "$CONFIG_FILE" "$BACKUP_FILE"
    echo "✓ Config backed up"
fi

# Test 1: List config (should work even if empty)
echo "→ Testing config list..."
LIST_OUTPUT=$(acli config --list 2>&1)
if [ $? -ne 0 ]; then
    echo "✗ Config list failed"
    exit 1
fi
echo "✓ Config list executed"

# Test 2: Set a config value
echo "→ Setting model config..."
acli config model claude-sonnet-4-5 > /dev/null 2>&1
echo "✓ Config set executed"

# Test 3: Get the config value back
echo "→ Getting model config..."
MODEL=$(acli config model 2>&1)
if ! echo "$MODEL" | grep -q "claude-sonnet-4-5"; then
    echo "✗ Config get doesn't contain expected value: $MODEL"
    exit 1
fi
echo "✓ Config get returned correct value"

# Test 4: Verify config file exists
echo "→ Verifying config file created..."
if [ ! -f "$CONFIG_FILE" ]; then
    echo "✗ Config file not created at $CONFIG_FILE"
    exit 1
fi
echo "✓ Config file exists"

# Test 5: Verify config file is valid JSON
echo "→ Validating config file structure..."
if ! python3 -c "import json; json.load(open('$CONFIG_FILE'))" 2>/dev/null; then
    echo "✗ Config file is not valid JSON"
    exit 1
fi
echo "✓ Config file is valid JSON"

# Test 6: Set another value
echo "→ Testing multiple config values..."
acli config max_tokens 4096 > /dev/null 2>&1
TOKENS=$(acli config max_tokens 2>&1)
if ! echo "$TOKENS" | grep -q "4096"; then
    echo "✗ Second config value not persisted: $TOKENS"
    exit 1
fi
echo "✓ Multiple config values work"

# Test 7: List should show both values
echo "→ Verifying list shows all values..."
LIST_OUTPUT=$(acli config --list 2>&1)
if ! echo "$LIST_OUTPUT" | grep -q "model"; then
    echo "✗ List doesn't show model config"
    exit 1
fi
if ! echo "$LIST_OUTPUT" | grep -q "max_tokens"; then
    echo "✗ List doesn't show max_tokens config"
    exit 1
fi
echo "✓ List shows all config values"

# Restore original config or cleanup
if [ -f "$BACKUP_FILE" ]; then
    echo "→ Restoring original config..."
    mv "$BACKUP_FILE" "$CONFIG_FILE"
    echo "✓ Config restored"
else
    echo "→ Removing test config..."
    rm -f "$CONFIG_FILE"
    echo "✓ Test config removed"
fi

echo ""
echo "✓✓✓ Test 03 PASSED ✓✓✓"
echo ""
