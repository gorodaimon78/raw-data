#!/usr/bin/env python
"""
Main CLI for Eleven AI Agents Supervisor.
Allows listing agents, testing graphs, adding/managing tasks, running daily cycles, and scheduling.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Fix Windows console encoding for Unicode/Emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()
console = Console(highlight=False)



def cmd_list_agents(registry: AgentRegistry, args):
    agents = registry.list_agents()
    table = Table(title="🤖 Eleven AI Agents Registry", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Agent ID", style="bold green", width=22)
    table.add_column("Name", style="bold", width=28)
    table.add_column("Category", style="magenta", width=22)
    table.add_column("Architecture Pattern", style="yellow", width=34)
    table.add_column("Description", style="white")

    for i, a in enumerate(agents, 1):
        table.add_row(str(i), a.id, a.name, a.category, a.pattern, a.description)

    console.print(table)


def cmd_test_agents(registry: AgentRegistry, args):
    console.print(Panel.fit("🧪 Testing Graph Compilation for All 11 Agents", style="bold cyan"))
    agents = registry.list_agents()
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Agent ID", width=24)
    table.add_column("Status", width=12)
    table.add_column("Mermaid Nodes / Flow", width=50)

    for a in agents:
        try:
            g = registry.get_graph(a.id)
            nodes = list(g.get_graph().nodes.keys())
            node_str = " -> ".join([n for n in nodes if not n.startswith("__")][:5])
            table.add_row(a.id, "[bold green]✅ HEALTHY[/bold green]", f"[dim]{node_str}[/dim]")
        except Exception as e:
            table.add_row(a.id, "[bold red]❌ ERROR[/bold red]", str(e)[:60])

    console.print(table)


def cmd_run_agent(registry: AgentRegistry, args):
    meta = registry.get_metadata(args.agent)
    if not meta:
        console.print(f"[bold red]Error:[/bold red] Unknown agent '{args.agent}'. Use `python supervisor.py list-agents` to view available agents.")
        return

    payload = args.input or meta.default_sample_input
    console.print(Panel.fit(f"🚀 Executing Agent: [bold green]{meta.name}[/bold green] (`{meta.id}`)\nInput: [italic]{payload}[/italic]", style="cyan"))

    res = registry.execute_agent(meta.id, payload)
    if res["success"]:
        console.print(f"\n[bold green]✅ Execution Succeeded ({res['duration_seconds']}s):[/bold green]\n")
        console.print(Panel(str(res["output_summary"]), title=f"{meta.name} Deliverable", border_style="green"))
    else:
        console.print(f"\n[bold red]❌ Execution Failed ({res['duration_seconds']}s):[/bold red] {res['error']}")


def cmd_list_tasks(tm: TaskManager, args):
    tasks = tm.list_tasks()
    table = Table(title="📋 Supervisor Task Queue", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="bold", width=4)
    table.add_column("Task Name", style="bold green", width=34)
    table.add_column("Assigned Agent", style="yellow", width=22)
    table.add_column("Schedule", style="magenta", width=16)
    table.add_column("Status", width=12)
    table.add_column("Last Run", style="dim", width=20)
    table.add_column("Input Query", style="white")

    for t in tasks:
        sched = f"{t.schedule_type} @ {t.schedule_value}" if t.schedule_type == "daily" else t.schedule_type
        stat_color = "green" if t.last_status == "SUCCESS" else ("red" if t.last_status == "FAILED" else "dim")
        stat_badge = f"[{stat_color}]{t.last_status or 'PENDING'}[/{stat_color}]"
        table.add_row(
            str(t.id),
            t.name,
            t.agent_id,
            sched,
            stat_badge,
            (t.last_run_at or "Never")[:19],
            t.input_payload[:50] + "...",
        )

    console.print(table)


def cmd_add_task(tm: TaskManager, registry: AgentRegistry, args):
    meta = registry.get_metadata(args.agent)
    if not meta:
        console.print(f"[bold red]Error:[/bold red] Unknown agent '{args.agent}'")
        return

    task_id = tm.add_task(
        name=args.name,
        agent_id=meta.id,
        input_payload=args.input,
        schedule_type=args.schedule,
        schedule_value=args.time,
        description=args.desc or "",
    )
    console.print(f"[bold green]✅ Task #{task_id} successfully created and registered into daily queue![/bold green]")


def cmd_run_task(engine: SupervisorEngine, tm: TaskManager, args):
    task = tm.get_task(args.id)
    if not task:
        console.print(f"[bold red]Error:[/bold red] Task #{args.id} not found.")
        return

    res = engine.run_single_task(task)
    console.print(Panel(str(res["summary"]), title=f"Task #{task.id} Output", border_style="cyan"))


def cmd_run_daily(engine: SupervisorEngine, args):
    console.print(Panel.fit("🌟 Triggering Daily Supervisor Execution Cycle", style="bold magenta"))
    report_file = engine.run_daily_cycle()
    console.print(f"\n[bold green]✅ Daily Cycle Complete![/bold green] Executive report saved to: [underline]{report_file}[/underline]")


def cmd_history(tm: TaskManager, args):
    records = tm.get_history(limit=args.limit)
    table = Table(title=f"📜 Execution History (Last {len(records)} runs)", show_header=True, header_style="bold cyan")
    table.add_column("Run ID", width=6)
    table.add_column("Task Name", width=30)
    table.add_column("Agent", width=18)
    table.add_column("Started At", width=19)
    table.add_column("Status", width=10)
    table.add_column("Duration", width=10)
    table.add_column("Output Preview", style="dim")

    for r in records:
        stat_color = "green" if r.status == "SUCCESS" else "red"
        table.add_row(
            str(r.id),
            r.task_name,
            r.agent_id,
            r.started_at[:19].replace("T", " "),
            f"[{stat_color}]{r.status}[/{stat_color}]",
            f"{r.duration_seconds}s",
            r.output_summary.replace("\n", " ")[:60] + "...",
        )

    console.print(table)


def cmd_start_daemon(engine: SupervisorEngine, args):
    console.print(Panel.fit("⏱️ Starting Supervisor Background Scheduler Daemon", style="bold yellow"))
    engine.start_scheduler_daemon(poll_interval_sec=args.interval)


def cmd_dashboard(registry: AgentRegistry, tm: TaskManager, args):
    console.print("\n" + "=" * 70)
    console.print("👑 [bold cyan]ELEVEN AI AGENTS - SUPERVISOR EXECUTIVE DASHBOARD[/bold cyan] 👑")
    console.print("=" * 70)

    # Agent Health
    agents = registry.list_agents()
    tasks = tm.list_tasks()
    history = tm.get_history(limit=5)

    console.print(f"\n[bold]🤖 Agents Managed:[/bold] [green]{len(agents)}[/green] | [bold]📋 Active Daily Tasks:[/bold] [yellow]{len(tasks)}[/yellow] | [bold]📜 Total Logged Runs:[/bold] [cyan]{len(history)}[/cyan]\n")

    cmd_list_tasks(tm, args)


def cmd_run_trends(args):
    console.print(Panel.fit("🌐 [bold cyan]Collecting Top 10 Searches & Trends Across 8 Platforms[/bold cyan]\nTarget: [yellow]Google, Reddit, YouTube, Pinterest, Medium, Quora, LinkedIn, Facebook[/yellow]", style="bold cyan"))
    from agents_code.trend_collector.trend_engine import TrendEngine
    engine = TrendEngine()
    res = engine.run_daily_trend_collection(geo=args.geo, max_per_platform=args.limit)
    
    console.print(f"\n[bold green]✅ Collection Successful![/bold green] Total: [yellow]{sum(len(v) for v in res['platforms_data'].values())} trends[/yellow]")
    console.print(f"📄 Markdown Report: [bold underline]{res['markdown_file']}[/bold underline]")
    console.print(f"📊 JSON Data File:  [bold underline]{res['json_file']}[/bold underline]\n")
    
    # Render overview table
    table = Table(title="Top #1 Trend Per Platform Overview", show_header=True, header_style="bold blue")
    table.add_column("Platform", style="bold green", width=14)
    table.add_column("Top #1 Search / Trend", style="bold", width=38)
    table.add_column("Type", style="magenta", width=22)
    table.add_column("Volume / Engagement", style="yellow", width=24)
    
    for platform, items in res["platforms_data"].items():
        top = items[0] if items else {"title": "N/A", "type": "N/A", "traffic_volume": "N/A"}
        table.add_row(platform, top.get("title", "")[:36], top.get("type", ""), top.get("traffic_volume", ""))
        
    console.print(table)


def cmd_pkst_scheduler(args):
    console.print(Panel.fit("⏱️ [bold yellow]Starting 06:00 AM PKST Daily Trend Scheduler Daemon[/bold yellow]\nIncludes automatic [green]Catch-up on boot[/green] if laptop was powered off!", style="bold yellow"))
    from agents_code.trend_collector.scheduler import PKSTTrendScheduler
    sched = PKSTTrendScheduler(target_hour=args.hour, target_minute=args.minute)
    sched.start_scheduler_daemon(poll_interval_sec=args.interval)


def main():
    parser = argparse.ArgumentParser(description="Eleven AI Agents Supervisor & Task Orchestrator")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list-agents
    subparsers.add_parser("list-agents", help="List all 11 managed AI agents and their capabilities")

    # test-agents
    subparsers.add_parser("test-agents", help="Test graph compilation for all 11 agents")

    # run-agent
    p_run = subparsers.add_parser("run-agent", help="Run a specific agent on demand")
    p_run.add_argument("--agent", "-a", required=True, help="Agent ID (e.g. sql_analyst, devops_triage)")
    p_run.add_argument("--input", "-i", help="Prompt, query, or file payload for the agent")

    # run-trends
    p_trends = subparsers.add_parser("run-trends", help="Extract Top 10 trends across 8 platforms right now")
    p_trends.add_argument("--geo", default="US", help="Geographic market (US, PK, GLOBAL)")
    p_trends.add_argument("--limit", type=int, default=10, help="Number of items per platform")

    # schedule-pkst
    p_pkst = subparsers.add_parser("start-pkst-scheduler", help="Start continuous 06:00 AM PKST daily scheduler with catch-up on boot")
    p_pkst.add_argument("--hour", type=int, default=6, help="Target hour in PKST (default: 6)")
    p_pkst.add_argument("--minute", type=int, default=0, help="Target minute in PKST (default: 0)")
    p_pkst.add_argument("--interval", type=int, default=30, help="Poll interval in seconds")

    # list-tasks
    subparsers.add_parser("list-tasks", help="List all configured daily and scheduled tasks")

    # add-task
    p_add = subparsers.add_parser("add-task", help="Register a new daily or scheduled task")
    p_add.add_argument("--name", "-n", required=True, help="Name of the task")
    p_add.add_argument("--agent", "-a", required=True, help="Target agent ID")
    p_add.add_argument("--input", "-i", required=True, help="Prompt or task instructions")
    p_add.add_argument("--schedule", "-s", default="daily", choices=["daily", "hourly", "manual"], help="Schedule type")
    p_add.add_argument("--time", "-t", default="09:00", help="Time of day (e.g. 09:00) for daily tasks")
    p_add.add_argument("--desc", "-d", default="", help="Description")

    # run-task
    p_rt = subparsers.add_parser("run-task", help="Execute a specific task by its ID")
    p_rt.add_argument("--id", required=True, type=int, help="Task ID")

    # run-daily
    subparsers.add_parser("run-daily", help="Execute the complete daily cycle of all registered tasks")

    # history
    p_hist = subparsers.add_parser("history", help="View past task execution history and outputs")
    p_hist.add_argument("--limit", "-l", type=int, default=15, help="Number of history rows to show")

    # start-daemon
    p_daemon = subparsers.add_parser("start-daemon", help="Start continuous supervisor scheduler daemon")
    p_daemon.add_argument("--interval", type=int, default=30, help="Check interval in seconds")

    # dashboard
    subparsers.add_parser("dashboard", help="Show supervisor overview dashboard")

    args = parser.parse_args()

    if args.command == "run-trends":
        cmd_run_trends(args)
    elif args.command == "start-pkst-scheduler":
        cmd_pkst_scheduler(args)
    else:
        # Load agent and supervisor dependencies only when agent commands are requested
        from agents_registry import AgentRegistry
        from supervisor_engine import SupervisorEngine
        from task_manager import TaskManager
        
        registry = AgentRegistry()
        tm = TaskManager()
        engine = SupervisorEngine(registry=registry, task_manager=tm)

        if args.command == "list-agents":
            cmd_list_agents(registry, args)
        elif args.command == "test-agents":
            cmd_test_agents(registry, args)
        elif args.command == "run-agent":
            cmd_run_agent(registry, args)
        elif args.command == "list-tasks":
            cmd_list_tasks(tm, args)
        elif args.command == "add-task":
            cmd_add_task(tm, registry, args)
        elif args.command == "run-task":
            cmd_run_task(engine, tm, args)
        elif args.command == "run-daily":
            cmd_run_daily(engine, args)
        elif args.command == "history":
            cmd_history(tm, args)
        elif args.command == "start-daemon":
            cmd_start_daemon(engine, args)
        elif args.command == "dashboard" or not args.command:
            cmd_dashboard(registry, tm, args)


if __name__ == "__main__":
    main()
