#!/usr/bin/env python3
"""
Orchestrator Verification Script
=================================

Demonstrates core orchestrator functionality without API calls.
"""

import asyncio
import tempfile
from pathlib import Path

from acli.core import (
    AgentOrchestrator,
    EventType,
    StreamBuffer,
    StreamEvent,
    StreamingHandler,
    get_project_state,
)


async def test_stream_buffer():
    """Test StreamBuffer event handling."""
    print("Testing StreamBuffer...")

    buffer = StreamBuffer()
    handler = StreamingHandler(buffer)

    # Simulate events
    await handler.handle_text("Building feature...")
    await handler.handle_tool_start("Bash", {"command": "npm install"})
    await handler.handle_tool_end("Bash", result="Success")
    await handler.handle_progress(5, 200)

    # Verify events
    events = buffer.get_recent(10)
    assert len(events) == 4
    assert events[0].type == EventType.TEXT
    assert events[1].type == EventType.TOOL_START
    assert events[2].type == EventType.TOOL_END
    assert events[3].type == EventType.PROGRESS

    print("✓ StreamBuffer test passed")


async def test_orchestrator():
    """Test AgentOrchestrator initialization and state."""
    print("\nTesting AgentOrchestrator...")

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"
        project_dir.mkdir()
        (project_dir / "app_spec.txt").write_text("Build a todo app")

        # Initialize orchestrator
        orch = AgentOrchestrator(project_dir, max_iterations=1)

        # Verify initial state
        assert orch.is_first_run
        assert not orch.is_running
        assert orch.max_iterations == 1

        # Test status
        status = orch.get_status()
        assert status["is_first_run"] is True
        assert status["running"] is False
        assert status["session_count"] == 0
        assert status["progress"]["done"] == 0
        assert status["progress"]["total"] == 0

        print("✓ Initial state correct")

        # Test state management
        state = get_project_state(project_dir)
        session = state.start_session()

        assert session.session_type == "initializer"
        assert session.session_id == 1

        state.end_session(status="completed")
        state.save()

        # Load state from file
        state2 = get_project_state(project_dir)
        assert len(state2.sessions) == 1
        assert state2.sessions[0].status == "completed"

        print("✓ State persistence works")

        # Test pause/resume
        orch.request_pause()
        assert orch._pause_requested
        orch.resume()
        assert not orch._pause_requested

        print("✓ Pause/resume works")

        # Test event handlers
        events_received = []

        def on_text(event: StreamEvent):
            events_received.append(event)

        orch.on_event("text", on_text)

        await orch.streaming.handle_text("Test message")
        await asyncio.sleep(0.1)  # Allow event to propagate

        assert len(events_received) == 1
        assert events_received[0].text == "Test message"

        print("✓ Event handlers work")

    print("✓ AgentOrchestrator test passed")


async def test_progress_tracking():
    """Test progress tracking from feature_list.json."""
    print("\nTesting progress tracking...")

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"
        project_dir.mkdir()

        orch = AgentOrchestrator(project_dir)

        # No feature list yet
        progress = orch._get_progress()
        assert progress is None

        # Create feature list
        import json

        features = [
            {"id": 1, "description": "Feature 1", "passes": True},
            {"id": 2, "description": "Feature 2", "passes": False},
            {"id": 3, "description": "Feature 3", "passes": True},
        ]

        feature_file = project_dir / "feature_list.json"
        with open(feature_file, "w") as f:
            json.dump(features, f)

        # Check progress
        progress = orch._get_progress()
        assert progress == (2, 3)  # 2 passing, 3 total

        print("✓ Progress tracking works")


async def main():
    """Run all tests."""
    print("=" * 70)
    print("  ORCHESTRATOR VERIFICATION")
    print("=" * 70)

    await test_stream_buffer()
    await test_orchestrator()
    await test_progress_tracking()

    print("\n" + "=" * 70)
    print("  ALL TESTS PASSED ✓")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
