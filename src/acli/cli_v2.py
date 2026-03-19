"""
v2 CLI Commands
===============

New commands added for brownfield onboarding, prompt execution,
validation, session management, memory, and context inspection.

Registered as individual commands on the main Typer app.
"""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def register_v2_commands(app: typer.Typer) -> None:
    """Register all v2 commands on the main CLI app."""

    @app.command()
    def onboard(
        project_dir: Annotated[
            Path, typer.Argument(help="Project directory to onboard")
        ] = Path("."),
    ) -> None:
        """Onboard an existing codebase for autonomous development."""
        project_dir = project_dir.resolve()
        if not project_dir.exists():
            console.print(f"[red]Error:[/] Directory '{project_dir}' not found")
            raise typer.Exit(1)

        from .context.onboarder import BrownfieldOnboarder
        from .core.streaming import StreamBuffer, StreamingHandler

        async def run_onboard() -> None:
            """Run the brownfield onboarding pipeline."""
            buffer = StreamBuffer()
            streaming = StreamingHandler(buffer)
            onboarder = BrownfieldOnboarder()
            result = await onboarder.onboard(project_dir, streaming)
            console.print(
                f"[green]Onboarding complete![/] "
                f"{len(result.get('files', []))} files analyzed"
            )

        asyncio.run(run_onboard())

    @app.command()
    def prompt(
        task: Annotated[str, typer.Argument(help="Task prompt to execute")],
        project_dir: Annotated[
            Path, typer.Option("--dir", "-d", help="Project directory")
        ] = Path("."),
        model: Annotated[
            str, typer.Option("--model", "-m", help="Model to use")
        ] = "claude-sonnet-4-6",
    ) -> None:
        """Execute a single task prompt without TUI."""
        project_dir = project_dir.resolve()
        if not project_dir.exists():
            console.print(f"[red]Error:[/] Directory '{project_dir}' not found")
            raise typer.Exit(1)

        from .core.orchestrator_v2 import EnhancedOrchestrator

        orch = EnhancedOrchestrator(project_dir=project_dir, model=model)
        console.print(f"[bold]Executing:[/] {task}")
        asyncio.run(orch.run(task))

    @app.command()
    def validate(
        project_dir: Annotated[
            Path, typer.Argument(help="Project directory")
        ] = Path("."),
        gate_id: Annotated[
            str | None,
            typer.Option("--gate", "-g", help="Specific gate to run"),
        ] = None,
    ) -> None:
        """Run validation gates."""
        project_dir = project_dir.resolve()
        from .validation.engine import ValidationEngine

        engine = ValidationEngine(project_dir)
        console.print("[bold]Running validation gates...[/]")
        summary = engine.get_phase_summary()
        console.print(
            f"Total: {summary['total_gates']}, "
            f"Passed: {summary['passed']}, "
            f"Failed: {summary['failed']}"
        )
        if gate_id:
            console.print(f"[dim]Gate filter: {gate_id}[/]")

    @app.command()
    def session(
        action: Annotated[
            str, typer.Argument(help="Action: list, resume, or replay")
        ],
        session_id: Annotated[
            str | None,
            typer.Argument(help="Session ID (for resume/replay)"),
        ] = None,
        project_dir: Annotated[
            Path, typer.Option("--dir", "-d", help="Project directory")
        ] = Path("."),
    ) -> None:
        """Manage agent sessions."""
        project_dir = project_dir.resolve()
        from .core.session import SessionLogger

        if action == "list":
            sessions = SessionLogger.list_sessions(project_dir)
            if not sessions:
                console.print("[yellow]No sessions found[/]")
                return
            table = Table(title="Sessions")
            table.add_column("ID", style="cyan")
            table.add_column("Modified", style="green")
            table.add_column("Size", style="dim")
            for s in sessions:
                table.add_row(
                    s["session_id"], s["modified"][:19], f"{s['size_bytes']}B"
                )
            console.print(table)
        elif action in ("resume", "replay"):
            if not session_id:
                console.print(
                    "[red]Error:[/] Session ID required for resume/replay"
                )
                raise typer.Exit(1)
            events = SessionLogger.load_session(project_dir, session_id)
            console.print(
                f"Loaded {len(events)} events from session {session_id}"
            )
        else:
            console.print(
                f"[red]Error:[/] Unknown action '{action}'. "
                "Use: list, resume, replay"
            )
            raise typer.Exit(1)

    @app.command()
    def memory(
        action: Annotated[
            str, typer.Argument(help="Action: list, add, or clear")
        ],
        fact: Annotated[
            str | None,
            typer.Argument(help="Fact to add (for add action)"),
        ] = None,
        category: Annotated[
            str, typer.Option("--category", "-c", help="Fact category")
        ] = "general",
        project_dir: Annotated[
            Path, typer.Option("--dir", "-d", help="Project directory")
        ] = Path("."),
    ) -> None:
        """Manage project memory."""
        project_dir = project_dir.resolve()
        from .context.memory import MemoryManager

        mem = MemoryManager(project_dir)

        if action == "list":
            facts = mem.get_facts()
            if not facts:
                console.print("[yellow]No facts stored[/]")
                return
            for f in facts:
                console.print(
                    f"  [{f.get('category', '?')}] {f.get('fact', '')}"
                )
        elif action == "add":
            if not fact:
                console.print("[red]Error:[/] Fact text required for add")
                raise typer.Exit(1)
            mem.add_fact(category, fact)
            console.print(f"[green]Added fact[/] ({category}): {fact}")
        elif action == "clear":
            mem.clear()
            console.print("[green]Memory cleared[/]")
        else:
            console.print(
                f"[red]Error:[/] Unknown action '{action}'. "
                "Use: list, add, clear"
            )
            raise typer.Exit(1)

    @app.command()
    def context(
        project_dir: Annotated[
            Path, typer.Argument(help="Project directory")
        ] = Path("."),
        verbose: Annotated[
            bool,
            typer.Option("--verbose", "-v", help="Show detailed context"),
        ] = False,
    ) -> None:
        """Show project context store."""
        project_dir = project_dir.resolve()
        from .context.store import ContextStore

        store = ContextStore(project_dir)

        if store.is_onboarded():
            console.print("[green]Project is onboarded[/]")
            if verbose:
                summary = store.get_context_summary()
                console.print(summary)
            tech = store.get_tech_stack()
            if tech:
                console.print(f"Tech stack: {tech}")
        else:
            console.print("[yellow]Project not yet onboarded[/]")
            console.print("Run 'acli onboard' first")
