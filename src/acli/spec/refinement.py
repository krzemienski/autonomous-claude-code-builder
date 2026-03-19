"""
Interactive Refinement Loop
===========================

CLI interface for iterative spec enhancement with user feedback.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from .enhancer import enhance_spec, refine_spec_with_answers
from .schemas import (
    ClarificationQuestion,
    EnhancementResult,
    ProjectSpec,
)
from .validator import get_completeness_threshold, is_spec_complete

console = Console()


def display_spec_summary(spec: ProjectSpec) -> None:
    """Display spec summary in rich format."""
    table = Table(title=f"Specification: {spec.name}")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Name", spec.name)
    table.add_row("Description", spec.description[:100] + "..." if len(spec.description) > 100 else spec.description)
    table.add_row("Language", spec.tech_stack.language)
    table.add_row("Framework", spec.tech_stack.framework or "Not specified")
    table.add_row("Features", str(len(spec.features)))

    total_reqs = sum(len(f.requirements) for f in spec.features)
    table.add_row("Requirements", str(total_reqs))

    console.print(table)


def display_completeness(result: EnhancementResult) -> None:
    """Display completeness score and issues."""
    score = result.completeness_score
    threshold = get_completeness_threshold()

    if score >= threshold:
        color = "green"
        status = "COMPLETE"
    elif score >= 70:
        color = "yellow"
        status = "NEEDS WORK"
    else:
        color = "red"
        status = "INCOMPLETE"

    console.print(Panel(
        f"[{color}]Score: {score:.1f}% ({status})[/]\n"
        f"Threshold: {threshold}%",
        title="Completeness",
        border_style=color,
    ))

    if result.warnings:
        console.print("\n[yellow]Issues:[/]")
        for issue in result.warnings:
            console.print(f"  - {issue}")


def ask_clarification(question: ClarificationQuestion) -> str | None:
    """Ask user a clarification question."""
    console.print(f"\n[bold cyan]{question.question}[/]")

    if question.suggestions:
        console.print(f"[dim]Suggestions: {', '.join(question.suggestions)}[/]")

    if question.required:
        return Prompt.ask("Answer")
    else:
        answer = Prompt.ask("Answer (Enter to skip)", default="")
        return answer if answer else None


async def interactive_enhancement(
    initial_description: str,
    max_rounds: int = 3,
    model: str = "claude-sonnet-4-6",
) -> ProjectSpec:
    """
    Run interactive spec enhancement loop.

    Args:
        initial_description: Initial plain-text description
        max_rounds: Maximum clarification rounds
        model: Claude model to use

    Returns:
        Final enhanced ProjectSpec
    """
    console.print(Panel(
        "[bold]Spec Enhancement[/]\n\n"
        "I'll analyze your description and ask clarifying questions.\n"
        "This helps create a complete, actionable specification.",
        title="Welcome",
        border_style="blue",
    ))

    # Round 1: Initial enhancement
    console.print("\n[bold]Analyzing description...[/]\n")

    result = await enhance_spec(initial_description, model)

    display_spec_summary(result.spec)
    display_completeness(result)

    # Display ambiguities
    if result.ambiguities:
        console.print("\n[yellow]Detected ambiguities:[/]")
        for amb in result.ambiguities:
            console.print(f"  - {amb}")

    # Clarification rounds
    round_num = 1

    while round_num <= max_rounds:
        if is_spec_complete(result.completeness_score):
            console.print("\n[green]Specification is complete![/]")
            break

        if not result.clarifications_needed:
            console.print("\n[yellow]No more questions, but score is below threshold.[/]")
            break

        console.print(f"\n[bold]Round {round_num}/{max_rounds}: Clarifications[/]")

        # Collect answers
        answers = {}
        for question in result.clarifications_needed[:5]:  # Max 5 questions per round
            answer = ask_clarification(question)
            if answer:
                answers[question.field] = answer

        if not answers:
            if Confirm.ask("Skip remaining clarifications?"):
                break
            continue

        # Refine with answers
        console.print("\n[bold]Refining specification...[/]\n")
        result = await refine_spec_with_answers(result.spec, answers, model)

        display_spec_summary(result.spec)
        display_completeness(result)

        round_num += 1

    # Final confirmation
    console.print("\n[bold]Final Specification:[/]\n")

    # Show full JSON
    json_str = result.spec.model_dump_json(indent=2)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
    console.print(syntax)

    if Confirm.ask("\nAccept this specification?"):
        return result.spec
    else:
        console.print("[yellow]Specification rejected. You can edit manually.[/]")
        return result.spec


def save_spec_to_file(spec: ProjectSpec, path: str) -> None:
    """Save specification to JSON file."""
    from pathlib import Path

    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w") as f:
        f.write(spec.model_dump_json(indent=2))

    console.print(f"[green]Saved specification to: {filepath}[/]")


def save_feature_list(spec: ProjectSpec, path: str) -> None:
    """Save as feature_list.json format for agent consumption."""
    import json
    from pathlib import Path

    features = spec.to_feature_list()

    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w") as f:
        json.dump(features, f, indent=2)

    console.print(f"[green]Saved feature list ({len(features)} features) to: {filepath}[/]")
