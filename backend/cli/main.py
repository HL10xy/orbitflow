"""OrbitFlow CLI — Multi-Agent Software Engineering from the terminal.

Usage:
    orbitflow run "Build a REST API for a todo app"
    orbitflow run --complexity epic "Design a distributed rate limiter"
    orbitflow serve
    orbitflow status
"""

from __future__ import annotations

import asyncio

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from agents.orchestrator import Orchestrator
from core.task import TaskComplexity
from config import default_config as cfg

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="orbitflow")
def cli():
    """OrbitFlow — Multi-Agent Software Engineering Framework."""


@cli.command()
@click.argument("description")
@click.option(
    "--complexity", "-c",
    type=click.Choice(["simple", "moderate", "complex", "epic"]),
    default="moderate",
    help="Task complexity level",
)
@click.option("--title", "-t", default="", help="Task title")
def run(description: str, complexity: str, title: str):
    """Run a task through the multi-agent pipeline."""
    orch = Orchestrator()
    compl = TaskComplexity(complexity)

    console.print(Panel.fit(
        f"[bold blue]OrbitFlow[/] — Multi-Agent Pipeline\n"
        f"Task: {title or description[:60]}\n"
        f"Complexity: {complexity}\n"
        f"Agents: architect -> coder -> reviewer -> tester",
        title="Starting",
    ))

    async def _run():
        async for event in orch.run(description, complexity=compl, title=title):
            if event.event_type == "agent_start":
                agent_obj = orch.agents.get(event.agent)
                icon_str = agent_obj.icon if agent_obj else "?"
                console.print(f"  {icon_str} [bold yellow]{event.agent}[/] starting: {event.message[:100]}")
            elif event.event_type == "agent_end":
                console.print(f"  ✅ [bold green]{event.agent}[/] completed")
            elif event.event_type == "task_end":
                console.print(f"\n[bold green]✓ Task completed:[/] {event.message}")
            elif event.event_type == "log" and "failed" in event.message.lower():
                console.print(f"  ❌ [bold red]{event.agent}[/] {event.message[:120]}")

    asyncio.run(_run())

    if orch.current_task:
        console.print("\n[bold]Results Summary:[/]")
        for st in orch.current_task.sub_tasks:
            status_icon = "✅" if st.status.value == "completed" else "❌"
            console.print(f"  {status_icon} [{st.assigned_agent}] {st.description}")
            if st.result:
                console.print(Markdown(st.result[:600]))
                console.print("---")


@cli.command()
def serve():
    """Start the OrbitFlow API server."""
    import uvicorn
    console.print(f"[bold blue]OrbitFlow API Server[/] starting on http://{cfg.api_host}:{cfg.api_port}")
    console.print(f"WebSocket: ws://{cfg.api_host}:{cfg.api_port}/ws")
    uvicorn.run("api.routes:app", host=cfg.api_host, port=cfg.api_port, reload=cfg.debug)


@cli.command()
def status():
    """Show current orchestrator status."""
    orch = Orchestrator()
    info = orch.get_status()

    console.print(Panel("[bold blue]OrbitFlow Status[/]"))
    console.print(f"Model: {info['llm']}")
    console.print(f"Agents: {', '.join(info['agents'])}")
    console.print(f"Memory entries: {info['memory']['total_entries']}")

    if info["current_task"]:
        t = info["current_task"]
        console.print(f"\nCurrent Task: {t['title']} [{t['status']}]")
        table = Table(title="Sub-tasks")
        table.add_column("Agent", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Status", style="green")
        for st in t["sub_tasks"]:
            table.add_row(st["assigned_agent"], st["description"][:60], st["status"])
        console.print(table)


if __name__ == "__main__":
    cli()
