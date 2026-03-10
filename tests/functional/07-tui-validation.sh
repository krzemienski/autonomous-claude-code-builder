#!/bin/bash
# Test 07: TUI Agent Monitor — Functional Validation
#
# Validates the Textual-based TUI components work with real ACLI
# infrastructure. No mocks. Tests real imports, real state loading,
# real event processing, and real widget rendering.

set -e

echo "=== Test 07: TUI Agent Monitor Validation ==="

# ─── Test 1: Textual installed ───────────────────────────

echo "→ Checking Textual is installed..."
if ! python3 -c "import textual; print(f'  Textual version: {textual.__version__}')" 2>/dev/null; then
    echo "  Installing textual..."
    pip install "textual>=1.0.0" > /dev/null 2>&1
fi
echo "✓ Textual available"

# ─── Test 2: TUI module imports ─────────────────────────

echo "→ Testing TUI module imports..."
python3 -c "
from acli.tui import AgentMonitorApp, OrchestratorBridge
from acli.tui.bridge import AgentNode, OrchestratorSnapshot
from acli.tui.widgets import CyberHeader, AgentGraph, AgentDetail, LogStream, StatsPanel
from acli.tui.app import AgentMonitorApp
print('  All TUI modules imported successfully')
" || { echo "✗ TUI import failed"; exit 1; }
echo "✓ TUI modules import"

# ─── Test 3: Bridge loads real project state ─────────────

echo "→ Testing bridge with real project state..."
TMPDIR=$(mktemp -d)
python3 -c "
import json
from pathlib import Path
from acli.core.session import ProjectState
from acli.tui.bridge import OrchestratorBridge

project_dir = Path('$TMPDIR')

# Create real state
state = ProjectState(project_dir=project_dir)
session = state.start_session()
state.end_session(status='completed')
state.save()

# Create real feature_list.json
features = [
    {'id': 1, 'description': 'Button renders', 'passes': True},
    {'id': 2, 'description': 'Form submits', 'passes': False},
    {'id': 3, 'description': 'Nav links work', 'passes': True},
]
(project_dir / 'feature_list.json').write_text(json.dumps(features))

# Load through bridge
bridge = OrchestratorBridge(project_dir=project_dir)

assert bridge.snapshot.session_count == 1, f'Expected 1 session, got {bridge.snapshot.session_count}'
assert bridge.snapshot.features_total == 3, f'Expected 3 features, got {bridge.snapshot.features_total}'
assert bridge.snapshot.features_done == 2, f'Expected 2 done, got {bridge.snapshot.features_done}'
assert len(bridge.root_agent.children) == 1, f'Expected 1 child, got {len(bridge.root_agent.children)}'
assert bridge.root_agent.children[0].status == 'completed'

print('  Session count: 1 ✓')
print('  Features: 2/3 ✓')
print('  Agent hierarchy: 1 child ✓')
" || { echo "✗ Bridge state loading failed"; rm -rf "$TMPDIR"; exit 1; }
rm -rf "$TMPDIR"
echo "✓ Bridge loads real state"

# ─── Test 4: Bridge processes real stream events ─────────

echo "→ Testing bridge event processing..."
python3 -c "
from pathlib import Path
import tempfile
from acli.core.streaming import EventType, StreamEvent
from acli.tui.bridge import OrchestratorBridge

tmp = Path(tempfile.mkdtemp())
bridge = OrchestratorBridge(project_dir=tmp)

# Feed real events
events = [
    StreamEvent(type=EventType.SESSION_START, session_id=1, session_type='initializer'),
    StreamEvent(type=EventType.TOOL_START, tool_name='Bash', tool_input={'command': 'ls -la'}),
    StreamEvent(type=EventType.TOOL_END, tool_name='Bash', tool_result='file1.py', tool_duration_ms=150.0),
    StreamEvent(type=EventType.TEXT, text='Creating project structure...'),
    StreamEvent(type=EventType.TOOL_BLOCKED, tool_name='Bash', tool_error='Command rm not allowed'),
    StreamEvent(type=EventType.ERROR, text='API timeout'),
    StreamEvent(type=EventType.PROGRESS, features_done=5, features_total=200),
    StreamEvent(type=EventType.SESSION_END, session_id=1),
    StreamEvent(type=EventType.SESSION_START, session_id=2, session_type='coding'),
    StreamEvent(type=EventType.SESSION_END, session_id=2),
]

for event in events:
    bridge._handle_event(event)

assert bridge.snapshot.events_processed == 10, f'Events: {bridge.snapshot.events_processed}'
assert bridge.snapshot.total_tool_calls == 1, f'Tools: {bridge.snapshot.total_tool_calls}'
assert bridge.snapshot.total_errors == 2, f'Errors: {bridge.snapshot.total_errors}'
assert bridge.snapshot.features_done == 5
assert bridge.snapshot.features_total == 200
assert bridge.snapshot.session_count == 2
assert len(bridge.root_agent.children) == 2

# Verify agent details
init_agent = bridge.root_agent.children[0]
assert init_agent.agent_type == 'initializer'
assert init_agent.tool_calls == 1
assert len(init_agent.errors) == 2  # blocked + error

coding_agent = bridge.root_agent.children[1]
assert coding_agent.agent_type == 'coding'
assert coding_agent.status == 'completed'

# Lookup by ID
assert bridge.get_agent_by_id('session-1') is not None
assert bridge.get_agent_by_id('session-2') is not None
assert bridge.get_agent_by_id('nonexistent') is None
assert bridge.get_agent_by_id('orchestrator') is not None

print('  Events processed: 10 ✓')
print('  Tool calls tracked: 1 ✓')
print('  Errors tracked: 2 ✓')
print('  Features: 5/200 ✓')
print('  Sessions: 2 ✓')
print('  Agent lookup: ✓')
" || { echo "✗ Event processing failed"; exit 1; }
echo "✓ Bridge processes events"

# ─── Test 5: Agent graph renders real hierarchy ──────────

echo "→ Testing agent graph rendering..."
python3 -c "
from pathlib import Path
import tempfile
from acli.core.streaming import EventType, StreamEvent
from acli.tui.bridge import OrchestratorBridge
from acli.tui.widgets import AgentGraph

tmp = Path(tempfile.mkdtemp())
bridge = OrchestratorBridge(project_dir=tmp)

# Build real hierarchy
bridge._handle_event(StreamEvent(type=EventType.SESSION_START, session_id=1, session_type='initializer'))
bridge._handle_event(StreamEvent(type=EventType.SESSION_END, session_id=1))
bridge._handle_event(StreamEvent(type=EventType.SESSION_START, session_id=2, session_type='coding'))
bridge._handle_event(StreamEvent(type=EventType.TOOL_START, tool_name='Write'))
bridge._handle_event(StreamEvent(type=EventType.PROGRESS, features_done=10, features_total=100))

graph = AgentGraph(bridge)
rendered = graph.render_graph()

assert 'ORCHESTRATOR' in rendered, 'Missing ORCHESTRATOR'
assert 'S#1' in rendered, 'Missing session 1'
assert 'initializer' in rendered, 'Missing initializer'
assert 'S#2' in rendered, 'Missing session 2'
assert 'coding' in rendered, 'Missing coding'
assert 'HIERARCHY' in rendered, 'Missing hierarchy header'

print('  Orchestrator node: ✓')
print('  Session 1 (initializer): ✓')
print('  Session 2 (coding): ✓')
print('  Graph structure valid: ✓')
print()
print('  Sample output:')
# Print without Rich markup for shell
clean = rendered.replace('[', '').replace(']', '')
for line in clean.split(chr(10))[:8]:
    cleaned = line
    for tag in ['#0abdc6', '#00ff41', '#4a6670', '#133e7c', '#ea00d9', '#ff003c', '#f5a623', '/']:
        cleaned = cleaned.replace(tag, '')
    print(f'    {cleaned}')
" || { echo "✗ Graph rendering failed"; exit 1; }
echo "✓ Agent graph renders"

# ─── Test 6: Event callbacks fire ────────────────────────

echo "→ Testing event callback system..."
python3 -c "
from pathlib import Path
import tempfile
from acli.core.streaming import EventType, StreamEvent
from acli.tui.bridge import OrchestratorBridge

tmp = Path(tempfile.mkdtemp())
bridge = OrchestratorBridge(project_dir=tmp)

received = []
bridge.on_event(lambda e: received.append(e))

bridge._handle_event(StreamEvent(type=EventType.TEXT, text='hello'))
bridge._handle_event(StreamEvent(type=EventType.TOOL_START, tool_name='Bash'))
bridge._handle_event(StreamEvent(type=EventType.SESSION_START, session_id=1, session_type='coding'))

assert len(received) == 3, f'Expected 3 callbacks, got {len(received)}'
assert received[0].text == 'hello'
assert received[1].tool_name == 'Bash'
assert received[2].session_type == 'coding'

print('  3 events received via callback ✓')
" || { echo "✗ Callback system failed"; exit 1; }
echo "✓ Event callbacks work"

# ─── Test 7: Async StreamBuffer integration ──────────────

echo "→ Testing async StreamBuffer integration..."
python3 -c "
import asyncio
from pathlib import Path
import tempfile
from acli.core.streaming import StreamBuffer, StreamingHandler, EventType
from acli.tui.bridge import OrchestratorBridge

async def test():
    buffer = StreamBuffer()
    handler = StreamingHandler(buffer)

    # Push real events through the real streaming infrastructure
    await handler.handle_session_start(1, 'initializer')
    await handler.handle_tool_start('Bash', {'command': 'npm init -y'})
    await handler.handle_tool_end('Bash', result='package.json created')
    await handler.handle_text('Setting up project...')
    await handler.handle_progress(0, 200)
    await handler.handle_session_end(1)

    events = buffer.get_recent(10)
    assert len(events) == 6, f'Expected 6 events, got {len(events)}'

    # Feed into bridge
    tmp = Path(tempfile.mkdtemp())
    bridge = OrchestratorBridge(project_dir=tmp)
    for event in events:
        bridge._handle_event(event)

    assert bridge.snapshot.events_processed == 6
    assert bridge.snapshot.total_tool_calls == 1
    assert bridge.snapshot.session_count == 1
    assert bridge.snapshot.features_total == 200

    print('  6 events through real StreamBuffer ✓')
    print('  Bridge state consistent ✓')

asyncio.run(test())
" || { echo "✗ Async integration failed"; exit 1; }
echo "✓ Async StreamBuffer integration works"

# ─── Test 8: CSS theme file exists and is valid ──────────

echo "→ Validating cyberpunk theme..."
python3 -c "
from pathlib import Path

css_path = Path('src/acli/tui/cyberpunk.tcss')
assert css_path.exists(), 'cyberpunk.tcss not found'

content = css_path.read_text()

# Check cyberpunk color palette is present
colors = ['#000b1e', '#0abdc6', '#ea00d9', '#00ff41', '#ff003c', '#133e7c']
for color in colors:
    assert color in content, f'Missing cyberpunk color: {color}'

# Check key selectors
selectors = ['Screen', '#header', '#log-stream', '#agent-graph', 'DataTable', 'Footer']
for sel in selectors:
    assert sel in content, f'Missing selector: {sel}'

lines = len(content.strip().split(chr(10)))
print(f'  CSS file: {lines} lines ✓')
print(f'  Color palette: 6/6 cyberpunk colors ✓')
print(f'  Key selectors: {len(selectors)}/{len(selectors)} ✓')
" || { echo "✗ Theme validation failed"; exit 1; }
echo "✓ Cyberpunk theme valid"

# ─── Test 9: CLI monitor command registered ──────────────

echo "→ Checking monitor CLI command..."
python3 -c "
from acli.cli import app
from typer.testing import CliRunner

runner = CliRunner()
result = runner.invoke(app, ['--help'])
assert 'monitor' in result.output, 'monitor command not found in CLI help'
print('  acli monitor command registered ✓')
" || { echo "✗ CLI command check failed"; exit 1; }
echo "✓ Monitor CLI command present"

# ─── Test 10: Resilience — malformed data ────────────────

echo "→ Testing resilience with malformed data..."
TMPDIR2=$(mktemp -d)
python3 -c "
from pathlib import Path
from acli.core.streaming import EventType, StreamEvent
from acli.tui.bridge import OrchestratorBridge

tmp = Path('$TMPDIR2')

# Corrupt state file
(tmp / '.acli_state.json').write_text('{broken json!!!')
bridge = OrchestratorBridge(project_dir=tmp)
assert bridge.snapshot.session_count == 0
print('  Corrupt .acli_state.json: survived ✓')

# Corrupt feature file
(tmp / 'feature_list.json').write_text('not json{{{')
bridge2 = OrchestratorBridge(project_dir=tmp)
assert bridge2.snapshot.features_total == 0
print('  Corrupt feature_list.json: survived ✓')

# Empty events
bridge3 = OrchestratorBridge(project_dir=tmp)
bridge3._handle_event(StreamEvent(type=EventType.TEXT, text=''))
bridge3._handle_event(StreamEvent(type=EventType.TOOL_START, tool_name=''))
bridge3._handle_event(StreamEvent(type=EventType.TOOL_END, tool_name=''))
assert bridge3.snapshot.events_processed == 3
print('  Empty events: survived ✓')
" || { echo "✗ Resilience test failed"; rm -rf "$TMPDIR2"; exit 1; }
rm -rf "$TMPDIR2"
echo "✓ Resilience validated"

# ─── Summary ─────────────────────────────────────────────

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║   ALL TUI FUNCTIONAL VALIDATIONS PASSED              ║"
echo "║   10/10 checks completed successfully                ║"
echo "║   No mocks used — all real infrastructure            ║"
echo "╚═══════════════════════════════════════════════════════╝"
