"""
Autonomous CLI Application
==========================

Main CLI entry points using Typer.

Commands:
    init     - Initialize new project with spec enhancement
    run      - Run autonomous coding loop
    monitor  - Launch cyberpunk TUI for agent monitoring
    status   - Show project progress
    config   - Manage configuration
    enhance  - Enhance spec interactively
"""

import asyncio
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .utils import logger

# Create CLI app
app = typer.Typer(
    name="acli",
    help="Autonomous CLI for interactive AI-powered coding",
    add_completion=True,
    rich_markup_mode="rich",
)

console = Console()


async def _run_tui_with_orchestrator(
    orchestrator: object,
    project_dir: Path,
) -> None:
    """Run the TUI and orchestrator concurrently, cancelling the other when one completes."""
    from .tui import AgentMonitorApp

    tui = AgentMonitorApp(
        orchestrator=orchestrator,
        project_dir=project_dir,
    )

    tui_task = asyncio.create_task(tui.run_async())
    orch_task = asyncio.create_task(orchestrator.run_loop())

    try:
        done, pending = await asyncio.wait(
            [tui_task, orch_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        # Re-raise exceptions from completed tasks
        for task in done:
            if task.exception():
                raise task.exception()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error("TUI/orchestrator error: %s", e)
        sys.exit(1)


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"[bold blue]acli[/] version [green]{__version__}[/]")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version", "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
) -> None:
    """Autonomous CLI - Interactive AI-powered coding tool."""
    pass


@app.command()
def init(
    project_name: Annotated[
        str,
        typer.Argument(help="Name of the project to create"),
    ],
    template: Annotated[
        str,
        typer.Option("--template", "-t", help="Project template to use"),
    ] = "default",
    spec: Annotated[
        Optional[Path],
        typer.Option("--spec", "-s", help="Path to existing spec file"),
    ] = None,
    interactive: Annotated[
        bool,
        typer.Option("--interactive/--no-interactive", help="Run interactive spec enhancement"),
    ] = True,
) -> None:
    """
    Initialize a new autonomous coding project.

    This will:
    1. Create project directory
    2. Run spec enhancement (if interactive)
    3. Generate initial feature_list.json
    4. Set up project structure
    """
    project_path = Path.cwd() / project_name

    if project_path.exists():
        console.print(f"[red]Error:[/] Directory '{project_name}' already exists")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold]Initializing project:[/] {project_name}",
        title="acli init",
        border_style="blue",
    ))

    # Create directory
    project_path.mkdir(parents=True)
    logger.info(f"Created directory: {project_path}")

    # Create app_spec.txt
    spec_file_path = project_path / "app_spec.txt"

    if interactive and spec is None:
        # Launch spec enhancement
        console.print("\n[bold]Starting spec enhancement...[/]\n")
        # Placeholder - Phase 3 implements this
        console.print("[dim]Spec enhancement will be implemented in Phase 3[/]")
        # Create default spec file
        spec_file_path.write_text(f"# {project_name}\n\nBuild a new application.\n")
    elif spec:
        # Copy existing spec
        import shutil
        shutil.copy(spec, spec_file_path)
        logger.info(f"Copied spec from: {spec}")
    else:
        # Create default spec file
        spec_file_path.write_text(f"# {project_name}\n\nBuild a new application.\n")

    # Create .gitignore
    gitignore_path = project_path / ".gitignore"
    gitignore_content = """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
.env
.DS_Store
"""
    gitignore_path.write_text(gitignore_content)

    # Create empty feature_list.json (will be populated by first run)
    feature_list_path = project_path / "feature_list.json"
    feature_list_path.write_text("[]")

    # Initialize git
    import subprocess
    try:
        subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit: Project setup"],
            cwd=project_path,
            check=True,
            capture_output=True,
        )
        logger.info("Git repository initialized")
    except subprocess.CalledProcessError:
        console.print("[yellow]Warning: Git initialization failed (git may not be installed)[/]")

    console.print(f"\n[green]Success![/] Project initialized at: {project_path}")
    console.print("\n[bold]Next steps:[/]")
    console.print(f"  cd {project_name}")
    console.print("  acli run")


@app.command()
def run(
    project_dir: Annotated[
        Path,
        typer.Argument(help="Project directory to run in"),
    ] = Path("."),
    model: Annotated[
        str,
        typer.Option("--model", "-m", help="Claude model to use"),
    ] = "claude-sonnet-4-6",
    max_iterations: Annotated[
        Optional[int],
        typer.Option("--max-iterations", help="Max sessions (None = unlimited)"),
    ] = None,
    dashboard: Annotated[
        bool,
        typer.Option("--dashboard/--no-dashboard", help="Show TUI dashboard"),
    ] = True,
    headless: Annotated[
        bool,
        typer.Option("--headless", help="Run without interactive UI"),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose logging"),
    ] = False,
    prompt: Annotated[
        Optional[str],
        typer.Option("--prompt", "-p", help="Arbitrary task prompt (v2)"),
    ] = None,
) -> None:
    """
    Run the autonomous coding loop.

    Starts the two-agent pattern:
    1. Session 1: Initializer agent creates feature_list.json
    2. Sessions 2+: Coding agent implements features one-by-one
    """
    if verbose:
        logger.setLevel("DEBUG")

    project_dir = project_dir.resolve()

    if not project_dir.exists():
        console.print(f"[red]Error:[/] Directory '{project_dir}' not found")
        raise typer.Exit(1)

    # Check for app_spec.txt or feature_list.json
    spec_file = project_dir / "app_spec.txt"
    feature_file = project_dir / "feature_list.json"

    if not spec_file.exists() and not feature_file.exists():
        console.print("[red]Error:[/] No app_spec.txt or feature_list.json found")
        console.print("Run 'acli init' first or provide a spec file")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold]Running autonomous agent[/]\n\n"
        f"Project: {project_dir}\n"
        f"Model: {model}\n"
        f"Max iterations: {max_iterations or 'unlimited'}",
        title="acli run",
        border_style="green",
    ))

    from .core.orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator(
        project_dir=project_dir,
        model=model,
        max_iterations=max_iterations,
    )

    if dashboard and not headless:
        # Launch full cyberpunk TUI
        asyncio.run(_run_tui_with_orchestrator(orchestrator, project_dir))
    else:
        # Headless mode — run orchestrator with console output
        from .ui import Dashboard

        async def run_headless():
            dash = Dashboard(console=console, theme="dark")

            async def event_listener():
                async for event in orchestrator.buffer.iter_from(0):
                    dash._handle_event(event)

            orch_task = asyncio.create_task(orchestrator.run_loop())
            listener_task = asyncio.create_task(event_listener())

            try:
                await orch_task
            finally:
                listener_task.cancel()
                try:
                    await listener_task
                except asyncio.CancelledError:
                    pass

        asyncio.run(run_headless())


@app.command()
def status(
    project_dir: Annotated[
        Path,
        typer.Argument(help="Project directory to check"),
    ] = Path("."),
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed status"),
    ] = False,
) -> None:
    """
    Show project progress status.

    Displays:
    - Tests passing vs total
    - Recent commits
    - Current feature being worked on
    """
    project_dir = project_dir.resolve()

    if not project_dir.exists():
        console.print(f"[red]Error:[/] Directory '{project_dir}' not found")
        raise typer.Exit(1)

    feature_file = project_dir / "feature_list.json"

    if not feature_file.exists():
        console.print("[yellow]Warning:[/] No feature_list.json found")
        console.print("Project may not be initialized")
        raise typer.Exit(1)

    # Read feature list (Phase 6 implements full tracking)
    import json
    try:
        with open(feature_file) as f:
            data = json.load(f)
            # Handle both list format and dict with "features" key
            if isinstance(data, list):
                features = data
            elif isinstance(data, dict) and "features" in data:
                features = data["features"]
            else:
                features = []
    except (json.JSONDecodeError, IOError) as e:
        console.print(f"[red]Error reading feature_list.json:[/] {e}")
        raise typer.Exit(1)

    # Calculate progress
    total = len(features)
    passing = sum(1 for f in features if f.get("passes", False) or f.get("status") == "completed")
    percentage = (passing / total * 100) if total > 0 else 0

    # Display status table
    table = Table(title=f"Project Status: {project_dir.name}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Features", str(total))
    table.add_row("Passing", str(passing))
    table.add_row("Remaining", str(total - passing))
    table.add_row("Progress", f"{percentage:.1f}%")

    console.print(table)

    if verbose:
        # Show recent features
        console.print("\n[bold]Recent Passing Features:[/]")
        passing_features = [f for f in features if f.get("passes", False)]
        for feat in passing_features[-5:]:
            console.print(f"  [green]✓[/] {feat.get('description', 'Unknown')[:60]}")

        console.print("\n[bold]Next Features:[/]")
        remaining = [f for f in features if not f.get("passes", False)]
        for feat in remaining[:5]:
            console.print(f"  [yellow]○[/] {feat.get('description', 'Unknown')[:60]}")


@app.command()
def enhance(
    spec_file: Annotated[
        Optional[Path],
        typer.Argument(help="Path to spec file (or read from stdin)"),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output path for enhanced spec"),
    ] = None,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: json, markdown, xml"),
    ] = "json",
) -> None:
    """
    Enhance a plain-English spec into structured format.

    Can read from file or interactively from stdin.
    Outputs JSON/Markdown/XML spec with clarifications.
    """
    console.print(Panel(
        "[bold]Spec Enhancement[/]\n\n"
        "Transform plain English into structured project spec",
        title="acli enhance",
        border_style="magenta",
    ))

    if spec_file:
        if not spec_file.exists():
            console.print(f"[red]Error:[/] File '{spec_file}' not found")
            raise typer.Exit(1)
        content = spec_file.read_text()
    else:
        # Interactive input
        console.print("[bold]Enter your project description[/] (Ctrl+D when done):\n")
        import sys
        content = sys.stdin.read()

    if not content.strip():
        console.print("[red]Error:[/] Empty spec provided")
        raise typer.Exit(1)

    # Run enhancement (Phase 3)
    console.print(f"\n[dim]Spec enhancement (format={format}) will be implemented in Phase 3[/]")

    # Placeholder output
    if output:
        console.print(f"[dim]Would write to: {output}[/]")


@app.command()
def config(
    key: Annotated[
        Optional[str],
        typer.Argument(help="Config key to get/set"),
    ] = None,
    value: Annotated[
        Optional[str],
        typer.Argument(help="Value to set"),
    ] = None,
    list_all: Annotated[
        bool,
        typer.Option("--list", "-l", help="List all config"),
    ] = False,
) -> None:
    """
    Manage acli configuration.

    Reads/writes to ~/.config/acli/config.json
    """
    config_dir = Path.home() / ".config" / "acli"
    config_file = config_dir / "config.json"

    # Default config
    default_config = {
        "model": "claude-sonnet-4-6",
        "max_iterations": None,
        "dashboard": True,
        "auto_commit": True,
        "feature_count": 200,
    }

    # Load existing config
    import json
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
    else:
        config = default_config.copy()

    if list_all or (key is None and value is None):
        # List all config
        table = Table(title="Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")

        for k, v in config.items():
            table.add_row(k, str(v))

        console.print(table)
        console.print(f"\n[dim]Config file: {config_file}[/]")
        return

    if key and value is None:
        # Get specific key
        if key in config:
            console.print(f"{key} = {config[key]}")
        else:
            console.print(f"[yellow]Key '{key}' not found[/]")
        return

    if key and value:
        # Set key
        # Try to parse value as JSON for types
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            parsed_value = value

        config[key] = parsed_value

        # Save config
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        console.print(f"[green]Set[/] {key} = {parsed_value}")


@app.command()
def list_skills(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed skill info"),
    ] = False,
) -> None:
    """
    List available skills in ~/.claude/skills/

    Shows all Claude Code skills available for use.
    """
    skills_dir = Path.home() / ".claude" / "skills"

    if not skills_dir.exists():
        console.print("[yellow]No skills directory found[/]")
        console.print(f"Expected: {skills_dir}")
        return

    skills = [d for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]

    if not skills:
        console.print("[yellow]No skills found in:[/] {skills_dir}")
        return

    table = Table(title=f"Available Skills ({len(skills)})")
    table.add_column("Name", style="cyan")
    if verbose:
        table.add_column("Description", style="dim")

    for skill_dir in sorted(skills):
        skill_name = skill_dir.name
        if verbose:
            # Read first line of SKILL.md for description
            skill_md = skill_dir / "SKILL.md"
            try:
                with open(skill_md) as f:
                    first_line = f.readline().strip("# \n")
                table.add_row(skill_name, first_line[:50])
            except Exception:
                table.add_row(skill_name, "[dim]No description[/]")
        else:
            table.add_row(skill_name)

    console.print(table)
    console.print(f"\n[dim]Skills directory: {skills_dir}[/]")


@app.command()
def monitor(
    project_dir: Annotated[
        Path,
        typer.Argument(help="Project directory to monitor"),
    ] = Path("."),
    model: Annotated[
        str,
        typer.Option("--model", "-m", help="Claude model to use"),
    ] = "claude-sonnet-4-6",
    max_iterations: Annotated[
        Optional[int],
        typer.Option("--max-iterations", help="Max sessions (None = unlimited)"),
    ] = None,
    attach: Annotated[
        bool,
        typer.Option("--attach/--detached", help="Attach to running orchestrator or view-only"),
    ] = True,
) -> None:
    """
    Launch the cyberpunk TUI for real-time agent monitoring.

    Opens a full-screen terminal dashboard that connects directly
    to the ACLI orchestrator. Shows:

    - Agent hierarchy visualization
    - Real-time log streaming with full verbosity
    - Agent drill-down details
    - Progress tracking and tool execution board

    Use --attach (default) to launch a live orchestrator alongside
    the TUI. Use --detached to view an existing project's state.
    """
    project_dir = project_dir.resolve()

    if not project_dir.exists():
        console.print(f"[red]Error:[/] Directory '{project_dir}' not found")
        raise typer.Exit(1)

    orchestrator = None

    if attach:
        # Check for spec or feature list
        spec_file = project_dir / "app_spec.txt"
        feature_file = project_dir / "feature_list.json"

        if spec_file.exists() or feature_file.exists():
            from .core.orchestrator import AgentOrchestrator

            orchestrator = AgentOrchestrator(
                project_dir=project_dir,
                model=model,
                max_iterations=max_iterations,
            )

    if orchestrator and attach:
        asyncio.run(_run_tui_with_orchestrator(orchestrator, project_dir))
    else:
        # View-only mode — just show project state
        from .tui import AgentMonitorApp

        tui = AgentMonitorApp(
            orchestrator=None,
            project_dir=project_dir,
        )
        tui.run()


# ── v2 Commands ──────────────────────────────────────────


@app.command()
def onboard(
    project_dir: Annotated[
        Path,
        typer.Argument(help="Project directory to onboard"),
    ] = Path("."),
) -> None:
    """
    Onboard an existing codebase for autonomous development.

    Runs brownfield analysis: tech stack detection, architecture mapping,
    convention detection, and context store population.
    """
    project_dir = project_dir.resolve()
    if not project_dir.exists():
        console.print(f"[red]Error:[/] Directory '{project_dir}' not found")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold]Onboarding project:[/] {project_dir.name}",
        title="acli onboard",
        border_style="cyan",
    ))

    from .context.onboarder import BrownfieldOnboarder
    from .core.streaming import StreamBuffer, StreamingHandler

    async def _onboard() -> None:
        buffer = StreamBuffer()
        streaming = StreamingHandler(buffer)
        onboarder = BrownfieldOnboarder()
        result = await onboarder.onboard(project_dir, streaming)
        console.print("\n[green]Onboarding complete![/]")
        console.print(f"  Tech stack: {result.get('tech_stack', {})}")
        console.print(f"  Files analyzed: {result.get('architecture', {}).get('files', 0)}")
        console.print(f"  Knowledge chunks: {result.get('chunk_count', 0)}")

    asyncio.run(_onboard())


@app.command()
def prompt(
    task: Annotated[
        str,
        typer.Argument(help="Task prompt to execute"),
    ],
    project_dir: Annotated[
        Path,
        typer.Option("--project", "-p", help="Project directory"),
    ] = Path("."),
    model: Annotated[
        str,
        typer.Option("--model", "-m", help="Claude model to use"),
    ] = "claude-sonnet-4-6",
) -> None:
    """
    Send a single task prompt without TUI.

    Executes the task using the v2 orchestrator in headless mode.
    """
    project_dir = project_dir.resolve()
    if not project_dir.exists():
        console.print(f"[red]Error:[/] Directory '{project_dir}' not found")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold]Task:[/] {task[:100]}",
        title="acli prompt",
        border_style="green",
    ))

    from .core.orchestrator_v2 import EnhancedOrchestrator

    async def _run() -> None:
        orch = EnhancedOrchestrator(project_dir=project_dir, model=model)
        await orch.run(task)

    asyncio.run(_run())


@app.command()
def validate(
    project_dir: Annotated[
        Path,
        typer.Argument(help="Project directory to validate"),
    ] = Path("."),
) -> None:
    """
    Run validation gates on the current project.

    Executes all configured validation gates and reports results.
    """
    project_dir = project_dir.resolve()
    if not project_dir.exists():
        console.print(f"[red]Error:[/] Directory '{project_dir}' not found")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold]Validating:[/] {project_dir.name}",
        title="acli validate",
        border_style="yellow",
    ))

    from .validation.engine import ValidationEngine

    async def _validate() -> None:
        engine = ValidationEngine(project_dir)
        summary = engine.get_phase_summary()
        console.print(f"  Total gates: {summary['total_gates']}")
        console.print(f"  Passed: {summary['passed']}")
        console.print(f"  Failed: {summary['failed']}")

    asyncio.run(_validate())


@app.command()
def session(
    action: Annotated[
        str,
        typer.Argument(help="Action: list, resume, replay"),
    ] = "list",
    session_id: Annotated[
        Optional[str],
        typer.Argument(help="Session ID for resume/replay"),
    ] = None,
    project_dir: Annotated[
        Path,
        typer.Option("--project", "-p", help="Project directory"),
    ] = Path("."),
) -> None:
    """
    Manage agent sessions (list, resume, replay).

    View session history and replay past sessions.
    """
    project_dir = project_dir.resolve()

    from .core.session import SessionLogger

    if action == "list":
        sessions = SessionLogger.list_sessions(project_dir)
        if not sessions:
            console.print("[yellow]No sessions found[/]")
            return
        table = Table(title="Sessions")
        table.add_column("ID", style="cyan")
        table.add_column("Events", style="green")
        table.add_column("First", style="dim")
        table.add_column("Last", style="dim")
        for s in sessions:
            table.add_row(
                s.get("session_id", "?"),
                str(s.get("event_count", 0)),
                s.get("first_event", ""),
                s.get("last_event", ""),
            )
        console.print(table)
    elif action == "replay" and session_id:
        events = SessionLogger.load_session(project_dir, session_id)
        console.print(f"[bold]Replaying session {session_id} ({len(events)} events)[/]")
        for event in events:
            console.print(f"  [{event.get('type', '?')}] {event.get('timestamp', '')}")
    else:
        console.print(f"[yellow]Unknown action: {action}[/]")
        console.print("Usage: acli session list | acli session replay <id>")


@app.command()
def memory(
    action: Annotated[
        str,
        typer.Argument(help="Action: list, add, clear"),
    ] = "list",
    fact: Annotated[
        Optional[str],
        typer.Argument(help="Fact to add (for 'add' action)"),
    ] = None,
    category: Annotated[
        str,
        typer.Option("--category", "-c", help="Fact category"),
    ] = "general",
    project_dir: Annotated[
        Path,
        typer.Option("--project", "-p", help="Project directory"),
    ] = Path("."),
) -> None:
    """
    Manage project memory (list, add, clear).

    Cross-session facts that persist across agent sessions.
    """
    project_dir = project_dir.resolve()

    from .context.memory import MemoryManager

    mem = MemoryManager(project_dir)

    if action == "list":
        facts = mem.get_facts()
        if not facts:
            console.print("[yellow]No memory facts stored[/]")
            return
        table = Table(title=f"Project Memory ({mem.fact_count} facts)")
        table.add_column("Category", style="cyan")
        table.add_column("Fact", style="green")
        for f in facts:
            table.add_row(f.get("category", ""), f.get("fact", "")[:80])
        console.print(table)
    elif action == "add" and fact:
        mem.add_fact(category, fact)
        console.print(f"[green]Added fact[/] [{category}]: {fact}")
    elif action == "clear":
        mem.clear()
        console.print("[green]Memory cleared[/]")
    else:
        console.print("[yellow]Usage: acli memory list | add <fact> | clear[/]")


@app.command()
def context(
    project_dir: Annotated[
        Path,
        typer.Argument(help="Project directory"),
    ] = Path("."),
) -> None:
    """
    Show project context store contents.

    Displays detected tech stack, architecture, conventions,
    and onboarding status.
    """
    project_dir = project_dir.resolve()
    if not project_dir.exists():
        console.print(f"[red]Error:[/] Directory '{project_dir}' not found")
        raise typer.Exit(1)

    from .context.store import ContextStore

    store = ContextStore(project_dir)

    if not store.is_onboarded():
        console.print("[yellow]Project not onboarded yet[/]")
        console.print("Run: acli onboard")
        return

    summary = store.get_context_summary()
    console.print(Panel(summary, title="Project Context", border_style="cyan"))


if __name__ == "__main__":
    app()
