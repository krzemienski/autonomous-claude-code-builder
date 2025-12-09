"""
Autonomous CLI Application
==========================

Main CLI entry points using Typer.

Commands:
    init     - Initialize new project with spec enhancement
    run      - Run autonomous coding loop
    status   - Show project progress
    config   - Manage configuration
    enhance  - Enhance spec interactively
"""

import asyncio
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
    ] = "claude-sonnet-4-20250514",
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

    if dashboard and not headless:
        # Launch TUI dashboard (Phase 5)
        console.print("[dim]Dashboard will be implemented in Phase 5[/]")
        console.print("[dim]Running in headless mode for now...[/]\n")

    # Run agent loop (Phase 4)
    console.print("[dim]Agent orchestration will be implemented in Phase 4[/]")

    # Placeholder for async run
    # asyncio.run(run_autonomous_loop(project_dir, model, max_iterations))


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
        "model": "claude-sonnet-4-20250514",
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


if __name__ == "__main__":
    app()
