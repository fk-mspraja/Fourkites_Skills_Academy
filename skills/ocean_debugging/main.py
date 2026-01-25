#!/usr/bin/env python3
"""
Ocean Debugging Agent CLI

Usage:
    python main.py --case 00123456 --verbose
    python main.py --case 00123456 --update-sf
    python main.py --validate-config
"""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.markdown import Markdown

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from modes.ocean.agent import OceanDebuggingAgent
from core.utils.config import Config
from core.utils.logging import setup_logging

console = Console()


@click.group()
def cli():
    """Ocean Debugging Agent - Investigate ocean shipment tracking issues"""
    pass


@cli.command()
@click.option("--case", "-c", required=True, help="Salesforce case number")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--update-sf", is_flag=True, help="Update Salesforce with results")
@click.option("--json-output", is_flag=True, help="Output results as JSON")
def investigate(case: str, verbose: bool, update_sf: bool, json_output: bool):
    """Investigate a Salesforce case"""
    # Setup logging
    setup_logging(level="DEBUG" if verbose else "INFO", json_output=json_output)

    console.print(f"\n[bold blue]Ocean Debugging Agent[/]")
    console.print(f"Investigating case: [cyan]{case}[/]\n")

    # Run investigation
    asyncio.run(_run_investigation(case, verbose, update_sf, json_output))


async def _run_investigation(
    case: str,
    verbose: bool,
    update_sf: bool,
    json_output: bool
):
    """Run the investigation asynchronously"""
    agent = OceanDebuggingAgent()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Investigating...", total=100)

            def update_progress(pct: int):
                progress.update(task, completed=pct)

            result = await agent.investigate(
                case_number=case,
                progress_callback=update_progress
            )

        # Display results
        if json_output:
            import json
            console.print(json.dumps(result.model_dump(), indent=2, default=str))
        else:
            _display_result(result, verbose)

        # Update Salesforce if requested
        if update_sf and result.root_cause:
            console.print("\n[dim]Updating Salesforce...[/]")
            await agent.update_salesforce(case, result)
            console.print("[green]Salesforce updated successfully[/]")

    finally:
        agent.close()


def _display_result(result, verbose: bool):
    """Display investigation result in rich format"""
    console.print()

    # Status panel
    if result.is_resolved:
        status_color = "green"
        status_text = "Root Cause Identified"
    elif result.needs_human:
        status_color = "yellow"
        status_text = "Human Review Required"
    else:
        status_color = "red"
        status_text = "Investigation Incomplete"

    console.print(Panel(
        f"[bold {status_color}]{status_text}[/]",
        title="Investigation Status"
    ))

    # Main results table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim")
    table.add_column("Value")

    table.add_row("Case", result.case_number)
    table.add_row("Load ID", result.load_id or "N/A")
    table.add_row("Investigation Time", f"{result.investigation_time:.1f}s")
    table.add_row("Steps Executed", str(result.steps_executed))

    if result.root_cause:
        table.add_row("", "")
        table.add_row("[bold]Root Cause[/]", f"[bold]{result.root_cause}[/]")
        table.add_row("Category", result.root_cause_category.value if result.root_cause_category else "N/A")
        table.add_row("Confidence", f"{result.confidence:.0%}")

    if result.needs_human:
        table.add_row("", "")
        table.add_row("[yellow]Question[/]", result.human_question or "N/A")

    console.print(table)

    # Explanation
    if result.explanation:
        console.print(f"\n[bold]Explanation:[/]")
        console.print(Panel(result.explanation, border_style="dim"))

    # Evidence (if verbose)
    if verbose and result.evidence:
        console.print(f"\n[bold]Evidence ({len(result.evidence)} items):[/]")
        evidence_table = Table(show_header=True, box=None)
        evidence_table.add_column("Source", style="cyan")
        evidence_table.add_column("Finding")

        for ev in result.evidence:
            evidence_table.add_row(ev.source.value, ev.finding)

        console.print(evidence_table)

    # Similar loads impact
    if result.similar_loads_affected > 0:
        console.print(f"\n[bold yellow]Impact:[/] {result.similar_loads_affected} similar loads affected")
        if result.pattern_detected:
            console.print("[yellow]Pattern detected - may affect many loads[/]")

    # Recommended action
    if result.recommended_action:
        console.print(f"\n[bold]Recommended Action:[/]")
        action = result.recommended_action
        console.print(f"  Action: {action.action}")
        console.print(f"  Priority: {action.priority.value}")
        if action.assignee:
            console.print(f"  Assignee: {action.assignee}")
        if action.human_approval_required:
            console.print("  [yellow]Human approval required[/]")


@cli.command()
def validate_config():
    """Validate configuration and show status"""
    console.print("\n[bold]Configuration Status[/]\n")

    config = Config()
    validation = config.validate()

    table = Table(show_header=True)
    table.add_column("Service")
    table.add_column("Status")
    table.add_column("Required")

    required_services = ["salesforce", "redshift", "clickhouse", "llm"]

    for service, configured in validation.items():
        is_required = service in required_services
        status = "[green]Configured[/]" if configured else "[red]Missing[/]"
        required = "[yellow]Yes[/]" if is_required else "No"
        table.add_row(service, status, required)

    console.print(table)

    missing = config.get_missing_configs()
    if missing:
        console.print(f"\n[yellow]Missing configurations: {', '.join(missing)}[/]")
        console.print("See .env.example for required environment variables")
    else:
        console.print("\n[green]All services configured![/]")


@cli.command()
@click.option("--case", "-c", required=True, help="Salesforce case number")
def test_extraction(case: str):
    """Test identifier extraction from a case (dry run)"""
    setup_logging(level="INFO")

    console.print(f"\n[bold]Testing Identifier Extraction[/]")
    console.print(f"Case: {case}\n")

    asyncio.run(_test_extraction(case))


async def _test_extraction(case: str):
    """Test extraction asynchronously"""
    agent = OceanDebuggingAgent()

    try:
        # Get ticket
        console.print("[dim]Fetching ticket from Salesforce...[/]")
        ticket = await agent._get_ticket(case)

        console.print(f"\n[bold]Ticket:[/]")
        console.print(f"  Subject: {ticket.subject}")
        console.print(f"  Description: {ticket.description[:200] if ticket.description else 'N/A'}...")

        # Extract identifiers
        console.print("\n[dim]Extracting identifiers with LLM...[/]")
        identifiers = await agent._extract_identifiers(ticket)

        console.print(f"\n[bold]Extracted Identifiers:[/]")
        for key, value in identifiers.items():
            if value:
                console.print(f"  {key}: {value}")

    finally:
        agent.close()


@cli.command()
def version():
    """Show version information"""
    from src import __version__
    console.print(f"Ocean Debugging Agent v{__version__}")


if __name__ == "__main__":
    cli()
