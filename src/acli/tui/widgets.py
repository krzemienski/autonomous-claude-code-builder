"""
TUI Widgets
============

Custom Textual widgets for the agent monitoring TUI.
All widgets read from the real OrchestratorBridge — no mocks.
"""

import logging
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import RichLog, Static

from ..core.streaming import EventType, StreamEvent
from .bridge import OrchestratorBridge, OrchestratorSnapshot

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────
# Header Bar
# ──────────────────────────────────────────────────────────

class CyberHeader(Widget):
    """Cyberpunk header showing system status."""

    status_text: reactive[str] = reactive("IDLE")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._session_start: datetime | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Static("⟁ ACLI AGENT MONITOR", id="header-title")
            yield Static(self.status_text, id="header-status")
            yield Static("", id="header-elapsed")

    def _compute_elapsed(self) -> str:
        if not self._session_start:
            return "00:00:00"
        delta = datetime.now() - self._session_start
        total = int(delta.total_seconds())
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def update_from_snapshot(self, snap: OrchestratorSnapshot) -> None:
        if snap.running:
            if not self._session_start:
                self._session_start = datetime.now()
            self.status_text = "● RUNNING"
            self.query_one("#header-status", Static).update("● RUNNING")
            self.query_one("#header-status", Static).styles.color = "#00ff41"
        elif snap.paused:
            self.status_text = "◉ PAUSED"
            self.query_one("#header-status", Static).update("◉ PAUSED")
            self.query_one("#header-status", Static).styles.color = "#f5a623"
        else:
            self._session_start = None
            self.status_text = "○ IDLE"
            self.query_one("#header-status", Static).update("○ IDLE")
            self.query_one("#header-status", Static).styles.color = "#4a6670"

        elapsed = self._compute_elapsed()
        if snap.current_session_id:
            session_info = (
                f"S#{snap.current_session_id} [{snap.current_session_type}] "
                f"│ {elapsed}"
            )
            self.query_one("#header-elapsed", Static).update(session_info)
        else:
            self.query_one("#header-elapsed", Static).update(elapsed)


# ──────────────────────────────────────────────────────────
# Agent Graph Visualization
# ──────────────────────────────────────────────────────────

class AgentGraph(Widget):
    """
    Visualizes the agent hierarchy as an ASCII graph.

    Reads directly from the OrchestratorBridge's live agent tree.
    """

    selected_agent_id: reactive[str] = reactive("")

    def __init__(self, bridge: OrchestratorBridge, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bridge = bridge

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Static("", id="graph-content"), id="agent-graph")

    def render_graph(self) -> str:
        """Render the live agent hierarchy as ASCII art."""
        root = self.bridge.root_agent
        lines: list[str] = []

        # Title
        lines.append("╔═══════════════════════════════════╗")
        lines.append("║     AGENT HIERARCHY               ║")
        lines.append("╚═══════════════════════════════════╝")
        lines.append("")

        # Root orchestrator node
        root_icon = self._status_icon(root.status)
        root_color = self._status_color(root.status)
        progress = ""
        if root.features_total > 0:
            pct = (root.features_done / root.features_total) * 100
            bar = self._mini_progress_bar(pct)
            progress = f" {bar} {root.features_done}/{root.features_total}"

        lines.append(
            f"[{root_color}]{root_icon} ORCHESTRATOR[/]"
            f"[#4a6670]{progress}[/]"
        )

        # Child session agents
        children = root.children
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            connector = "╰─" if is_last else "├─"
            branch = "  " if is_last else "│ "

            child_icon = self._status_icon(child.status)
            child_color = self._status_color(child.status)

            # Selection indicator
            sel = "»" if child.agent_id == self.selected_agent_id else " "

            # Current tool indicator
            tool_info = ""
            if child.current_tool:
                tool_info = f" [#ea00d9]⚡ {child.current_tool}[/]"

            # Duration
            dur = self._format_duration(child.duration_seconds)

            # Error count
            err_info = ""
            if child.errors:
                err_info = f" [#ff003c]✗{len(child.errors)}[/]"

            lines.append(
                f"[#133e7c]{connector}[/]"
                f"[{child_color}]{sel}{child_icon} "
                f"S#{child.session_id} [{child.agent_type}][/]"
                f"[#4a6670] {dur} "
                f"⚙{child.tool_calls}[/]"
                f"{tool_info}{err_info}"
            )

            # Show last activity for running agents
            if child.status == "running" and child.last_text:
                snippet = child.last_text[:60].replace("\n", " ")
                lines.append(
                    f"[#133e7c]{branch}[/]"
                    f"[#4a6670]  └ {snippet}…[/]"
                )

        if not children:
            lines.append("[#4a6670]  (no sessions yet)[/]")

        return "\n".join(lines)

    def refresh_graph(self) -> None:
        """Re-render graph from live data."""
        try:
            content = self.query_one("#graph-content", Static)
            content.update(self.render_graph())
        except NoMatches:
            pass
        except Exception:
            logger.debug("Error refreshing agent graph", exc_info=True)

    @staticmethod
    def _status_icon(status: str) -> str:
        return {
            "idle": "◇",
            "running": "◆",
            "completed": "✓",
            "error": "✗",
            "paused": "◈",
        }.get(status, "?")

    @staticmethod
    def _status_color(status: str) -> str:
        return {
            "idle": "#4a6670",
            "running": "#00ff41",
            "completed": "#0abdc6",
            "error": "#ff003c",
            "paused": "#f5a623",
        }.get(status, "#d7fffe")

    @staticmethod
    def _mini_progress_bar(pct: float, width: int = 12) -> str:
        filled = int(pct / 100 * width)
        empty = width - filled
        return f"[#0abdc6]{'█' * filled}[/][#133e7c]{'░' * empty}[/]"

    @staticmethod
    def _format_duration(seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            m, s = divmod(int(seconds), 60)
            return f"{m}m{s:02d}s"
        else:
            h, rem = divmod(int(seconds), 3600)
            m, s = divmod(rem, 60)
            return f"{h}h{m:02d}m"


# ──────────────────────────────────────────────────────────
# Agent Detail View
# ──────────────────────────────────────────────────────────

class AgentDetail(Widget):
    """
    Detailed view of a single selected agent.

    Drill-down from the graph — shows all properties
    of the real agent session.
    """

    def __init__(self, bridge: OrchestratorBridge, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bridge = bridge
        self._selected_id: str = ""

    def compose(self) -> ComposeResult:
        with Vertical(id="agent-detail"):
            yield Static("SELECT AN AGENT", id="agent-detail-title")
            yield VerticalScroll(
                Static("", id="agent-detail-body"),
                id="agent-detail-content",
            )

    def show_agent(self, agent_id: str) -> None:
        """Show details for a specific agent."""
        self._selected_id = agent_id
        self.refresh_detail()

    def refresh_detail(self) -> None:
        """Refresh detail view from live data."""
        if not self._selected_id:
            return

        agent = self.bridge.get_agent_by_id(self._selected_id)
        if not agent:
            return

        lines: list[str] = []

        # Title
        title_widget = self.query_one("#agent-detail-title", Static)
        title_widget.update(
            f"[#ea00d9]◆ {agent.agent_type.upper()}[/] "
            f"[#4a6670]({agent.agent_id})[/]"
        )

        # Properties
        lines.append(f"[#0abdc6]Status:[/]     [{self._color(agent.status)}]{agent.status}[/]")
        lines.append(f"[#0abdc6]Session:[/]    #{agent.session_id}")
        lines.append(f"[#0abdc6]Type:[/]       {agent.agent_type}")

        if agent.start_time:
            lines.append(f"[#0abdc6]Started:[/]    {agent.start_time.strftime('%H:%M:%S')}")
        if agent.end_time:
            lines.append(f"[#0abdc6]Ended:[/]      {agent.end_time.strftime('%H:%M:%S')}")

        dur = AgentGraph._format_duration(agent.duration_seconds)
        lines.append(f"[#0abdc6]Duration:[/]   {dur}")
        lines.append(f"[#0abdc6]Tool Calls:[/] {agent.tool_calls}")

        if agent.current_tool:
            lines.append(f"[#0abdc6]Active Tool:[/] [#ea00d9]{agent.current_tool}[/]")

        if agent.features_total > 0:
            pct = (agent.features_done / agent.features_total) * 100
            lines.append(
                f"[#0abdc6]Progress:[/]   "
                f"{agent.features_done}/{agent.features_total} ({pct:.1f}%)"
            )

        # Errors
        if agent.errors:
            lines.append("")
            lines.append(f"[#ff003c]── ERRORS ({len(agent.errors)}) ──[/]")
            for err in agent.errors[-5:]:
                lines.append(f"  [#ff003c]✗[/] {err[:80]}")

        # Last output
        if agent.last_text:
            lines.append("")
            lines.append("[#f5a623]── LAST OUTPUT ──[/]")
            for line in agent.last_text[:300].split("\n")[:5]:
                lines.append(f"  [#d7fffe]{line}[/]")

        try:
            body = self.query_one("#agent-detail-body", Static)
            body.update("\n".join(lines))
        except NoMatches:
            pass

    @staticmethod
    def _color(status: str) -> str:
        return AgentGraph._status_color(status)


# ──────────────────────────────────────────────────────────
# Log Streaming Panel
# ──────────────────────────────────────────────────────────

class LogStream(Widget):
    """
    Full-verbosity log streaming panel.

    Reads events directly from the orchestrator's StreamBuffer.
    Shows every event type with complete detail.
    """

    DEFAULT_CSS = """
    LogStream {
        height: 1fr;
    }
    """

    def __init__(self, bridge: OrchestratorBridge, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bridge = bridge
        self._log_level_filter: str = "all"

    def compose(self) -> ComposeResult:
        with Vertical(id="log-panel"):
            yield Horizontal(
                Static(
                    "[#0abdc6]LOGS[/] │ "
                    "[#4a6670]F1[/][#d7fffe]:All [/]"
                    "[#4a6670]F2[/][#d7fffe]:Tools [/]"
                    "[#4a6670]F3[/][#d7fffe]:Errors [/]"
                    "[#4a6670]F4[/][#d7fffe]:Text[/]",
                    id="log-filter-bar",
                ),
                id="log-header",
            )
            yield RichLog(
                highlight=True,
                markup=True,
                wrap=True,
                auto_scroll=True,
                id="log-stream",
            )

    def write_event(self, event: StreamEvent) -> None:
        """Write a real event to the log stream."""
        if not self._should_show(event):
            return

        try:
            log = self.query_one("#log-stream", RichLog)
        except NoMatches:
            return

        ts = event.timestamp.strftime("%H:%M:%S.%f")[:-3]
        ts_str = f"[#4a6670]{ts}[/]"

        if event.type == EventType.TEXT:
            text = event.text[:200].replace("\n", "↵ ")
            log.write(f"{ts_str} [#0abdc6]TXT[/] {text}")

        elif event.type == EventType.TOOL_START:
            input_preview = str(event.tool_input)[:80] if event.tool_input else ""
            log.write(
                f"{ts_str} [#ea00d9]TOL[/] "
                f"[#ea00d9]▶ {event.tool_name}[/] "
                f"[#4a6670]{input_preview}[/]"
            )

        elif event.type == EventType.TOOL_END:
            if event.tool_error:
                log.write(
                    f"{ts_str} [#ff003c]ERR[/] "
                    f"[#ff003c]✗ {event.tool_name}: {event.tool_error[:100]}[/]"
                )
            else:
                dur = f"{event.tool_duration_ms:.0f}ms" if event.tool_duration_ms else ""
                result = event.tool_result[:80] if event.tool_result else "OK"
                log.write(
                    f"{ts_str} [#00ff41]TOL[/] "
                    f"[#00ff41]✓ {event.tool_name}[/] "
                    f"[#4a6670]{dur} {result}[/]"
                )

        elif event.type == EventType.TOOL_BLOCKED:
            log.write(
                f"{ts_str} [#ff003c]BLK[/] "
                f"[#ff003c]⊘ {event.tool_name}: {event.tool_error[:100]}[/]"
            )

        elif event.type == EventType.ERROR:
            log.write(
                f"{ts_str} [#ff003c]ERR[/] "
                f"[#ff003c]{event.text[:150]}[/]"
            )

        elif event.type == EventType.SESSION_START:
            log.write(
                f"{ts_str} [#00ff41]SES[/] "
                f"[#00ff41]═══ Session #{event.session_id} STARTED "
                f"[{event.session_type}] ═══[/]"
            )

        elif event.type == EventType.SESSION_END:
            log.write(
                f"{ts_str} [#0abdc6]SES[/] "
                f"[#0abdc6]═══ Session #{event.session_id} ENDED ═══[/]"
            )

        elif event.type == EventType.PROGRESS:
            pct = (
                (event.features_done / event.features_total * 100)
                if event.features_total > 0
                else 0
            )
            log.write(
                f"{ts_str} [#f5a623]PRG[/] "
                f"[#f5a623]Features: {event.features_done}/{event.features_total} "
                f"({pct:.1f}%)[/]"
            )

    def _should_show(self, event: StreamEvent) -> bool:
        if self._log_level_filter == "all":
            return True
        elif self._log_level_filter == "tools":
            return event.type in (
                EventType.TOOL_START,
                EventType.TOOL_END,
                EventType.TOOL_BLOCKED,
            )
        elif self._log_level_filter == "errors":
            return event.type in (
                EventType.ERROR,
                EventType.TOOL_BLOCKED,
            ) or (event.type == EventType.TOOL_END and bool(event.tool_error))
        elif self._log_level_filter == "text":
            return event.type == EventType.TEXT
        return True

    def set_filter(self, level: str) -> None:
        self._log_level_filter = level


# ──────────────────────────────────────────────────────────
# Stats / Progress Panel
# ──────────────────────────────────────────────────────────

class StatsPanel(Widget):
    """
    Live statistics and progress panel.

    Shows real metrics from the orchestrator — feature progress,
    session count, tool call stats, error rates.
    """

    def __init__(self, bridge: OrchestratorBridge, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bridge = bridge

    def compose(self) -> ComposeResult:
        with Vertical(id="stats-panel"):
            yield Static("", id="stats-content")
            yield Static("", id="tool-board")

    def refresh_stats(self) -> None:
        """Refresh stats from real data."""
        snap = self.bridge.snapshot

        lines: list[str] = []

        # Progress bar
        if snap.features_total > 0:
            pct = (snap.features_done / snap.features_total) * 100
            bar_width = 30
            filled = int(pct / 100 * bar_width)
            empty = bar_width - filled
            bar = f"[#0abdc6]{'█' * filled}[/][#133e7c]{'░' * empty}[/]"
            lines.append(
                f"[#0abdc6]PROGRESS[/] {bar} "
                f"[#d7fffe]{snap.features_done}[/]"
                f"[#4a6670]/{snap.features_total}[/] "
                f"[#ea00d9]{pct:.1f}%[/]"
            )
        else:
            lines.append("[#4a6670]PROGRESS  (waiting for feature_list.json)[/]")

        lines.append("")

        # Stats grid
        lines.append(
            f"[#0abdc6]Sessions:[/]  [#d7fffe]{snap.session_count}[/]  "
            f"[#0abdc6]│[/]  "
            f"[#0abdc6]Tools:[/]  [#d7fffe]{snap.total_tool_calls}[/]  "
            f"[#0abdc6]│[/]  "
            f"[#0abdc6]Errors:[/]  [#ff003c]{snap.total_errors}[/]  "
            f"[#0abdc6]│[/]  "
            f"[#0abdc6]Events:[/]  [#d7fffe]{snap.events_processed}[/]"
        )

        lines.append(
            f"[#0abdc6]Model:[/]    [#d7fffe]{snap.model or 'N/A'}[/]  "
            f"[#0abdc6]│[/]  "
            f"[#0abdc6]Project:[/]  [#d7fffe]{snap.project_dir}[/]"
        )

        try:
            content = self.query_one("#stats-content", Static)
            content.update("\n".join(lines))
        except NoMatches:
            pass

        # Tool board - last 8 tool events
        self._refresh_tool_board()

    def _refresh_tool_board(self) -> None:
        """Render recent tool executions from the real buffer."""
        if not self.bridge.buffer:
            return

        recent = self.bridge.buffer.get_recent(100)
        tool_events: list[StreamEvent] = [
            e for e in recent
            if e.type in (EventType.TOOL_START, EventType.TOOL_END, EventType.TOOL_BLOCKED)
        ]

        # Pair starts and ends
        tool_lines: list[str] = []
        active_tools: dict[str, StreamEvent] = {}

        for event in tool_events:
            if event.type == EventType.TOOL_START:
                active_tools[event.tool_name] = event
            elif event.type == EventType.TOOL_END:
                icon = "[#00ff41]✓[/]" if not event.tool_error else "[#ff003c]✗[/]"
                dur = f"{event.tool_duration_ms:.0f}ms" if event.tool_duration_ms else ""
                name = event.tool_name or "?"
                tool_lines.append(
                    f"  {icon} [#ea00d9]{name:<12}[/] "
                    f"[#4a6670]{dur:>6}[/]"
                )
                active_tools.pop(event.tool_name, None)
            elif event.type == EventType.TOOL_BLOCKED:
                tool_lines.append(
                    f"  [#ff003c]⊘[/] [#ea00d9]{event.tool_name:<12}[/] "
                    f"[#ff003c]BLOCKED[/]"
                )
                active_tools.pop(event.tool_name, None)

        # Show running tools
        for name, event in active_tools.items():
            elapsed = (datetime.now() - event.timestamp).total_seconds() * 1000
            tool_lines.append(
                f"  [#0abdc6]→[/] [#ea00d9]{name:<12}[/] "
                f"[#0abdc6]{elapsed:.0f}ms...[/]"
            )

        # Only keep last 8
        tool_lines = tool_lines[-8:]

        if tool_lines:
            header = "[#0abdc6]RECENT TOOLS[/]"
            output = header + "\n" + "\n".join(tool_lines)
        else:
            output = "[#4a6670]RECENT TOOLS  (none yet)[/]"

        try:
            board = self.query_one("#tool-board", Static)
            board.update(output)
        except NoMatches:
            pass
