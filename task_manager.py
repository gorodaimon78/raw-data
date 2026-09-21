"""
Task Manager & Database Persistence for Supervisor.
Manages daily, recurring, and manual tasks, schedules, and run history.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_FILE = Path(__file__).parent / "supervisor_tasks.db"


@dataclass
class Task:
    id: Optional[int]
    name: str
    agent_id: str
    schedule_type: str  # 'daily', 'hourly', 'interval', 'manual'
    schedule_value: str  # e.g. '09:00', '60', 'manual'
    input_payload: str
    description: str
    enabled: bool = True
    created_at: str = ""
    last_run_at: Optional[str] = None
    last_status: Optional[str] = None


@dataclass
class TaskRunRecord:
    id: Optional[int]
    task_id: int
    task_name: str
    agent_id: str
    started_at: str
    finished_at: str
    duration_seconds: float
    status: str  # 'SUCCESS', 'FAILED', 'PENDING'
    output_summary: str
    full_output: str
    error_message: Optional[str] = None


class TaskManager:
    def __init__(self, db_path: Path = DB_FILE):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    schedule_type TEXT NOT NULL DEFAULT 'daily',
                    schedule_value TEXT NOT NULL DEFAULT '09:00',
                    input_payload TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_run_at TEXT,
                    last_status TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    task_name TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    status TEXT NOT NULL,
                    output_summary TEXT NOT NULL,
                    full_output TEXT NOT NULL,
                    error_message TEXT
                )
                """
            )
            conn.commit()

        # Seed default tasks if empty
        if self.count_tasks() == 0:
            self._seed_default_tasks()

    def _seed_default_tasks(self) -> None:
        defaults = [
            (
                "Daily Revenue & Sales Triage",
                "sql_analyst",
                "daily",
                "08:30",
                "What are total sales by product category and top 5 items for the last 24 hours?",
                "Queries the core SQL database to compute daily sales volume and top revenue drivers.",
            ),
            (
                "Daily Cloud & Service Incident Triage",
                "devops_triage",
                "daily",
                "09:00",
                "Perform daily scan on service latency, error spikes, and active alerts across microservices.",
                "Gathers DevOps signals, checks severity matrix, and prepares preventive runbooks.",
            ),
            (
                "Daily Expense & Invoice Compliance Audit",
                "expense_auditor",
                "daily",
                "10:00",
                "Audit all pending corporate expense claims and flag policy violations or suspicious receipts.",
                "Runs rule-based and compliance checks on submitted expense claims.",
            ),
            (
                "Daily Growth & Marketing Content Brief",
                "marketing_creator",
                "daily",
                "11:00",
                "Draft daily tech innovation highlight, LinkedIn leadership post, and product tip.",
                "Generates, critiques, and refines marketing and thought-leadership copy.",
            ),
            (
                "Daily BI Executive KPI Insights",
                "bi_insights",
                "daily",
                "17:00",
                "Generate executive briefing on user retention, acquisition channels, and conversion health.",
                "Performs multi-step reasoning over daily business metric fixtures.",
            ),
        ]
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            for name, agent_id, sched_type, sched_val, payload, desc in defaults:
                conn.execute(
                    """
                    INSERT INTO tasks (name, agent_id, schedule_type, schedule_value, input_payload, description, enabled, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (name, agent_id, sched_type, sched_val, payload, desc, now),
                )
            conn.commit()

    def count_tasks(self) -> int:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM tasks")
            return cur.fetchone()[0]

    def add_task(
        self,
        name: str,
        agent_id: str,
        input_payload: str,
        schedule_type: str = "daily",
        schedule_value: str = "09:00",
        description: str = "",
        enabled: bool = True,
    ) -> int:
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO tasks (name, agent_id, schedule_type, schedule_value, input_payload, description, enabled, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    agent_id,
                    schedule_type,
                    schedule_value,
                    input_payload,
                    description,
                    1 if enabled else 0,
                    now,
                ),
            )
            conn.commit()
            return cur.lastrowid

    def list_tasks(self, only_enabled: bool = False) -> List[Task]:
        query = "SELECT * FROM tasks"
        if only_enabled:
            query += " WHERE enabled = 1"
        query += " ORDER BY id ASC"

        with self._get_conn() as conn:
            rows = conn.execute(query).fetchall()
            return [
                Task(
                    id=r["id"],
                    name=r["name"],
                    agent_id=r["agent_id"],
                    schedule_type=r["schedule_type"],
                    schedule_value=r["schedule_value"],
                    input_payload=r["input_payload"],
                    description=r["description"] or "",
                    enabled=bool(r["enabled"]),
                    created_at=r["created_at"],
                    last_run_at=r["last_run_at"],
                    last_status=r["last_status"],
                )
                for r in rows
            ]

    def get_task(self, task_id: int) -> Optional[Task]:
        with self._get_conn() as conn:
            r = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not r:
                return None
            return Task(
                id=r["id"],
                name=r["name"],
                agent_id=r["agent_id"],
                schedule_type=r["schedule_type"],
                schedule_value=r["schedule_value"],
                input_payload=r["input_payload"],
                description=r["description"] or "",
                enabled=bool(r["enabled"]),
                created_at=r["created_at"],
                last_run_at=r["last_run_at"],
                last_status=r["last_status"],
            )

    def update_task_status(self, task_id: int, status: str) -> None:
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE tasks SET last_run_at = ?, last_status = ? WHERE id = ?",
                (now, status, task_id),
            )
            conn.commit()

    def record_run(
        self,
        task_id: int,
        task_name: str,
        agent_id: str,
        started_at: str,
        finished_at: str,
        duration_seconds: float,
        status: str,
        output_summary: str,
        full_output: Any,
        error_message: Optional[str] = None,
    ) -> int:
        full_out_str = (
            full_output if isinstance(full_output, str) else json.dumps(full_output, default=str)
        )
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO task_history (task_id, task_name, agent_id, started_at, finished_at, duration_seconds, status, output_summary, full_output, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    task_name,
                    agent_id,
                    started_at,
                    finished_at,
                    duration_seconds,
                    status,
                    output_summary,
                    full_out_str,
                    error_message,
                ),
            )
            conn.commit()
            return cur.lastrowid

    def get_history(self, limit: int = 20) -> List[TaskRunRecord]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM task_history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                TaskRunRecord(
                    id=r["id"],
                    task_id=r["task_id"],
                    task_name=r["task_name"],
                    agent_id=r["agent_id"],
                    started_at=r["started_at"],
                    finished_at=r["finished_at"],
                    duration_seconds=r["duration_seconds"],
                    status=r["status"],
                    output_summary=r["output_summary"],
                    full_output=r["full_output"],
                    error_message=r["error_message"],
                )
                for r in rows
            ]
