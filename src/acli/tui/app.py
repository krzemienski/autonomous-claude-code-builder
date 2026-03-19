"""
Agent Monitor TUI Application
===============================

The main Textual application for monitoring autonomous ACLI agents.
Cyberpunk-themed, real-time, full-verbosity monitoring dashboard.

Connects directly to the real ACLI orchestrator — no mocks.
"""

import asyncio
import logging
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.widgets import Footer

from ..core.orchestrator_v1 import AgentOrchestrator
from ..core.streaming import StreamEvent
from .bridge import OrchestratorBridge
from .prompt_input import PromptInput
from .widgets import (
    AgentDetail,
    AgentGraph,
    ContextExplorer,
    CyberHeader,
    LogStream,
    StatsPanel,
    ValidationGatePanel,
)

logger = logging.getLogger(__name__)


class AgentMonitorApp(App):
    """
    Cyberpunk Agent Monitoring TUI.

    A full-screen terminal dashboard that connects to the real
    ACLI orchestrator, visualizing agents, streaming logs, and
    showing the complete hierarchy of agent operations.

    Keyboard Navigation:
        q       - Quit
        p       - Pause/Resume orchestrator
        s       - Stop orchestrator
        j/k     - Navigate agents (down/up)
        F1-F4   - Switch log filter (All/Tools/Errors/Text)
        Tab     - Cycle focus between panels
        Enter   - Drill into selected agent
    """

    CSS_PATH = "cyberpunk.tcss"
    TITLE = "ACLI Agent Monitor"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("p", "toggle_pause", "Pause/Resume"),
        Binding("s", "stop_orchestrator", "Stop"),
        Binding("j", "select_next_agent", "Next Agent", show=False),
        Binding("k", "select_prev_agent", "Prev Agent", show=False),
        Binding("down", "select_next_agent", "Next Agent", show=False),
        Binding("up", "select_prev_agent", "Prev Agent", show=False),
        Binding("enter", "drill_into_agent", "Detail"),
        Binding("f1", "filter_all", "All Logs"),
        Binding("f2", "filter_tools", "Tool Logs"),
        Binding("f3", "filter_errors", "Error Logs"),
        Binding("f4", "filter_text", "Text Logs"),
        Binding("r", "refresh_all", "Refresh", show=False),
        Binding("slash", "focus_prompt", "Prompt", show=True),
        Binding("v", "toggle_validation", "Validation", show=True),
        Binding("c", "toggle_context", "Context", show=True),
    ]

    def __init__(
        self,
        orchestrator: AgentOrchestrator | None = None,
        project_dir: Path | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.bridge = OrchestratorBridge(
            orchestrator=orchestrator,
            project_dir=project_dir,
        )
        self._stop_event = asyncio.Event()
        self._selected_index = 0

    def compose(self) -> ComposeResult:
        yield CyberHeader()

        with Horizontal(id="main-container"):
            # Left panel: Agent graph + detail
            with Vertical(id="left-panel"):
                yield AgentGraph(self.bridge, id="agent-graph-widget")
                yield AgentDetail(self.bridge, id="agent-detail-widget")

            # Right panel: Logs + Stats
            with Vertical(id="right-panel"):
                yield LogStream(self.bridge, id="log-stream-widget")
                yield StatsPanel(self.bridge, id="stats-panel-widget")
                yield ContextExplorer(id="context-explorer-widget")
                yield ValidationGatePanel(id="validation-gate-widget")

        yield PromptInput()
        yield Footer()

    def on_mount(self) -> None:
        """Start consuming real events when the app mounts."""
        # Register bridge event callback to feed widgets
        self.bridge.on_event(self._on_bridge_event)

        # Start background tasks that consume real orchestrator data
        if self.bridge.buffer:
            self.run_worker(self._consume_events(), exclusive=True, name="events")

        self.run_worker(self._poll_state(), exclusive=True, name="poller")
        self.run_worker(self._refresh_loop(), exclusive=True, name="refresh")

        # Initial render
        self._refresh_all_widgets()

    async def _consume_events(self) -> None:
        """Consume events from the real orchestrator StreamBuffer."""
        await self.bridge.consume_events(self._stop_event)

    async def _poll_state(self) -> None:
        """Periodically poll orchestrator state."""
        await self.bridge.poll_state(
            interval=1.0,
            stop_event=self._stop_event,
        )

    async def _refresh_loop(self) -> None:
        """Refresh all widgets at a fixed rate."""
        while not self._stop_event.is_set():
            self._refresh_all_widgets()
            await asyncio.sleep(0.25)  # 4 FPS

    def _on_bridge_event(self, event: StreamEvent) -> None:
        """Handle a real event from the orchestrator bridge."""
        try:
            log_widget = self.query_one("#log-stream-widget", LogStream)
            log_widget.write_event(event)
        except NoMatches:
            pass
        except Exception:
            logger.debug("Error handling bridge event", exc_info=True)

    def _refresh_all_widgets(self) -> None:
        """Refresh all widgets from live data."""
        snap = self.bridge.snapshot

        try:
            header = self.query_one(CyberHeader)
            header.update_from_snapshot(snap)
        except NoMatches:
            pass

        try:
            graph = self.query_one("#agent-graph-widget", AgentGraph)
            graph.refresh_graph()
        except NoMatches:
            pass

        try:
            detail = self.query_one("#agent-detail-widget", AgentDetail)
            detail.refresh_detail()
        except NoMatches:
            pass

        try:
            stats = self.query_one("#stats-panel-widget", StatsPanel)
            stats.refresh_stats()
        except NoMatches:
            pass

        try:
            ctx_explorer = self.query_one(ContextExplorer)
            ctx_explorer.refresh_context(snap.context_summary)
        except (NoMatches, Exception):
            pass

        try:
            gate_panel = self.query_one(ValidationGatePanel)
            gate_panel.refresh_gates(snap.gate_results)
        except (NoMatches, Exception):
            pass

    # ── Keybinding Actions ──────────────────────────────────

    def action_toggle_pause(self) -> None:
        """Pause or resume the real orchestrator."""
        snap = self.bridge.snapshot
        if snap.paused:
            self.bridge.send_command("resume")
            self.notify("Orchestrator RESUMED", severity="information")
        elif snap.running:
            self.bridge.send_command("pause")
            self.notify("Orchestrator PAUSED", severity="warning")
        else:
            self.notify("Orchestrator is not running", severity="warning")

    def action_stop_orchestrator(self) -> None:
        """Stop the real orchestrator."""
        self.bridge.send_command("stop")
        self.notify("Orchestrator STOP requested", severity="error")

    def action_select_next_agent(self) -> None:
        """Select next agent in the hierarchy."""
        agents = self.bridge.get_all_agents_flat()
        if agents:
            self._selected_index = min(
                self._selected_index + 1, len(agents) - 1
            )
            agent = agents[self._selected_index]

            try:
                graph = self.query_one("#agent-graph-widget", AgentGraph)
                graph.selected_agent_id = agent.agent_id
                graph.refresh_graph()
            except NoMatches:
                pass

            try:
                detail = self.query_one("#agent-detail-widget", AgentDetail)
                detail.show_agent(agent.agent_id)
            except NoMatches:
                pass

    def action_select_prev_agent(self) -> None:
        """Select previous agent in the hierarchy."""
        agents = self.bridge.get_all_agents_flat()
        if agents:
            self._selected_index = max(self._selected_index - 1, 0)
            agent = agents[self._selected_index]

            try:
                graph = self.query_one("#agent-graph-widget", AgentGraph)
                graph.selected_agent_id = agent.agent_id
                graph.refresh_graph()
            except NoMatches:
                pass

            try:
                detail = self.query_one("#agent-detail-widget", AgentDetail)
                detail.show_agent(agent.agent_id)
            except NoMatches:
                pass

    def action_drill_into_agent(self) -> None:
        """Drill into the selected agent for full detail."""
        agents = self.bridge.get_all_agents_flat()
        if agents and 0 <= self._selected_index < len(agents):
            agent = agents[self._selected_index]
            try:
                detail = self.query_one("#agent-detail-widget", AgentDetail)
                detail.show_agent(agent.agent_id)
            except NoMatches:
                pass

    def action_filter_all(self) -> None:
        try:
            log = self.query_one("#log-stream-widget", LogStream)
            log.set_filter("all")
            self.notify("Log filter: ALL", severity="information")
        except NoMatches:
            pass

    def action_filter_tools(self) -> None:
        try:
            log = self.query_one("#log-stream-widget", LogStream)
            log.set_filter("tools")
            self.notify("Log filter: TOOLS", severity="information")
        except NoMatches:
            pass

    def action_filter_errors(self) -> None:
        try:
            log = self.query_one("#log-stream-widget", LogStream)
            log.set_filter("errors")
            self.notify("Log filter: ERRORS", severity="information")
        except NoMatches:
            pass

    def action_filter_text(self) -> None:
        try:
            log = self.query_one("#log-stream-widget", LogStream)
            log.set_filter("text")
            self.notify("Log filter: TEXT", severity="information")
        except NoMatches:
            pass

    def action_refresh_all(self) -> None:
        self._refresh_all_widgets()

    def action_focus_prompt(self) -> None:
        """Focus the prompt input field."""
        try:
            self.query_one("#prompt-field").focus()
        except Exception:
            pass

    def action_toggle_validation(self) -> None:
        """Toggle validation gate panel visibility."""
        try:
            panel = self.query_one(ValidationGatePanel)
            panel.display = not panel.display
        except Exception:
            pass

    def action_toggle_context(self) -> None:
        """Toggle context explorer visibility."""
        try:
            explorer = self.query_one(ContextExplorer)
            explorer.display = not explorer.display
        except Exception:
            pass

    def on_unmount(self) -> None:
        """Clean up when the app exits."""
        self._stop_event.set()
