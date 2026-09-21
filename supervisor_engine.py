"""
Supervisor Engine & Orchestrator.
Supervises agent execution, daily task scheduling, and report synthesis.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import schedule


from agents_registry import AgentRegistry
from task_manager import Task, TaskManager

BASE_DIR = Path(__file__).parent.resolve()
REPORTS_DIR = BASE_DIR / "reports"


class SupervisorEngine:
    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        task_manager: Optional[TaskManager] = None,
    ):
        self.registry = registry or AgentRegistry()
        self.task_manager = task_manager or TaskManager()
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def run_single_task(self, task: Task) -> Dict[str, Any]:
        """
        Executes a specific task via its designated agent and logs the outcome.
        """
        started_at = datetime.now().isoformat()
        print(f"\n[Supervisor] 🚀 Starting Task #{task.id}: '{task.name}' using agent [{task.agent_id}]...")

        exec_res = self.registry.execute_agent(task.agent_id, task.input_payload)
        finished_at = datetime.now().isoformat()

        status = "SUCCESS" if exec_res["success"] else "FAILED"
        summary = exec_res["output_summary"]
        duration = exec_res["duration_seconds"]
        error = exec_res.get("error")

        # Update database
        self.task_manager.update_task_status(task.id, status)
        self.task_manager.record_run(
            task_id=task.id,
            task_name=task.name,
            agent_id=task.agent_id,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration,
            status=status,
            output_summary=summary,
            full_output=exec_res["raw_output"] or {},
            error_message=error,
        )

        icon = "✅" if status == "SUCCESS" else "❌"
        print(f"[Supervisor] {icon} Completed Task #{task.id} in {duration}s -> Status: {status}")
        return {
            "task_id": task.id,
            "task_name": task.name,
            "agent_id": task.agent_id,
            "status": status,
            "duration": duration,
            "summary": summary,
            "error": error,
        }

    def run_daily_cycle(self) -> str:
        """
        Executes all active daily tasks and produces a Daily Supervisor Briefing Report.
        """
        tasks = self.task_manager.list_tasks(only_enabled=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n{'='*60}")
        print(f"🌟 SUPERVISOR: Executing Daily Task Cycle for {date_str}")
        print(f"📋 Found {len(tasks)} active daily tasks.")
        print(f"{'='*60}\n")

        results = []
        for task in tasks:
            res = self.run_single_task(task)
            results.append(res)

        # Generate Report
        report_md = self._generate_daily_report(results, timestamp_str)
        report_file = REPORTS_DIR / f"daily_report_{date_str}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_md)

        print(f"\n{'='*60}")
        print(f"📄 Daily Briefing Report written to: {report_file}")
        print(f"{'='*60}\n")
        return str(report_file)

    def _generate_daily_report(self, results: List[Dict[str, Any]], timestamp: str) -> str:
        success_count = sum(1 for r in results if r["status"] == "SUCCESS")
        fail_count = sum(1 for r in results if r["status"] == "FAILED")
        total_duration = round(sum(r["duration"] for r in results), 2)

        lines = [
            f"# 🤖 Daily AI Agent Supervisor Briefing",
            f"**Generated at**: `{timestamp}`  ",
            f"**Total Tasks**: `{len(results)}` | **Success**: `{success_count}` | **Failed**: `{fail_count}` | **Duration**: `{total_duration}s`\n",
            "## 📊 Executive Summary Table\n",
            "| Task ID | Task Name | Agent | Status | Duration | Output Preview |",
            "| :--- | :--- | :--- | :---: | :---: | :--- |",
        ]

        for r in results:
            badge = "🟢 SUCCESS" if r["status"] == "SUCCESS" else "🔴 FAILED"
            short_prev = (r["summary"] or "").replace("\n", " ")[:80] + "..."
            lines.append(
                f"| #{r['task_id']} | **{r['task_name']}** | `{r['agent_id']}` | {badge} | {r['duration']}s | {short_prev} |"
            )

        lines.append("\n---\n")
        lines.append("## 📝 Detailed Agent Deliverables\n")

        for r in results:
            status_icon = "✅" if r["status"] == "SUCCESS" else "❌"
            lines.append(f"### {status_icon} Task #{r['task_id']}: {r['task_name']}")
            lines.append(f"- **Agent**: `{r['agent_id']}`")
            lines.append(f"- **Status**: `{r['status']}` ({r['duration']}s)")
            if r.get("error"):
                lines.append(f"- **Error Encountered**: `{r['error']}`")
            lines.append(f"\n**Deliverable / Result**:\n")
            lines.append(f"```text\n{r['summary']}\n```\n")

        return "\n".join(lines)

    def start_scheduler_daemon(self, poll_interval_sec: int = 30) -> None:
        """
        Runs the background schedule loop.
        """
        print(f"\n[Supervisor Daemon] ⏱️ Initializing task schedules...")
        tasks = self.task_manager.list_tasks(only_enabled=True)

        schedule.clear()
        for task in tasks:
            if task.schedule_type == "daily":
                t_val = task.schedule_value if ":" in task.schedule_value else "09:00"
                schedule.every().day.at(t_val).do(self.run_single_task, task)
                print(f"  - Registered daily task #{task.id} '{task.name}' at {t_val}")
            elif task.schedule_type == "hourly":
                schedule.every().hour.do(self.run_single_task, task)
                print(f"  - Registered hourly task #{task.id} '{task.name}'")

        print(f"[Supervisor Daemon] Running. Press Ctrl+C to stop.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(poll_interval_sec)
        except KeyboardInterrupt:
            print("\n[Supervisor Daemon] Stopped by user.")
