"""
Unified Agent Registry for Eleven AI Agents.
Provides standard discovery, metadata, and programmatic execution for all 11 agents.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from langgraph.checkpoint.memory import MemorySaver

BASE_DIR = Path(__file__).parent.resolve()
AGENTS_CODE_DIR = BASE_DIR / "agents_code"


@dataclass
class AgentMetadata:
    id: str
    folder_name: str
    name: str
    category: str
    description: str
    pattern: str
    default_sample_input: Any


AGENT_DEFINITIONS: List[AgentMetadata] = [
    AgentMetadata(
        id="sql_analyst",
        folder_name="01_sql_data_analyst",
        name="SQL Data Analyst",
        category="Data & Analytics",
        description="Executes read-only SQL queries with self-correction loop on sales & business database.",
        pattern="Tool loop + SQL self-correction",
        default_sample_input="What are the top 5 products by total revenue?",
    ),
    AgentMetadata(
        id="csv_analyst",
        folder_name="02_csv_excel_data_analyst",
        name="CSV / Excel Data Analyst",
        category="Data & Analytics",
        description="Analyzes tabular data files (CSV/Excel) with structured Pydantic schema output and charts.",
        pattern="File tools + structured output",
        default_sample_input="Which region had the highest total revenue in Q4?",
    ),
    AgentMetadata(
        id="bi_insights",
        folder_name="03_bi_dashboard_insights",
        name="BI Dashboard Insights",
        category="Business Intelligence",
        description="Performs multi-step reasoning, hypothesis generation, and executive summaries from KPI metrics.",
        pattern="Multi-step reasoning + summariser",
        default_sample_input="Analyze our recent conversion and retention drop across subscription tiers.",
    ),
    AgentMetadata(
        id="customer_support",
        folder_name="04_customer_support",
        name="Customer Support Agent",
        category="Customer Operations",
        description="Classifies customer inquiries, checks orders & policies, and conducts multi-turn checkpointed conversations.",
        pattern="Intent router + checkpointed chat",
        default_sample_input="I need to know the status of order ORD-1002 and how to return it.",
    ),
    AgentMetadata(
        id="hr_screener",
        folder_name="05_hr_resume_screener",
        name="HR Resume Screener",
        category="Human Resources",
        description="Builds an evaluation rubric, fans out across candidate resumes, and generates ranked candidate scorecards.",
        pattern="Send fan-out + reduce",
        default_sample_input="Screen candidate resumes for Senior Backend Python Engineer role.",
    ),
    AgentMetadata(
        id="expense_auditor",
        folder_name="06_finance_expense_auditor",
        name="Finance Expense Auditor",
        category="Finance & Accounting",
        description="Audits expense claims against compliance policies with approval workflows and SQLite persistence.",
        pattern="Rules + interrupt approval + SQLite checkpointing",
        default_sample_input="Audit batch of corporate expense claims for travel and team dinners.",
    ),
    AgentMetadata(
        id="marketing_creator",
        folder_name="07_marketing_content",
        name="Marketing Content Specialist",
        category="Marketing & Growth",
        description="Generates multi-channel marketing campaigns with iterative critique, revision, and quality checks.",
        pattern="Generate -> critique -> revise loop",
        default_sample_input="Create a product launch campaign for our new AI Automation Toolkit targeting tech leads.",
    ),
    AgentMetadata(
        id="legal_reviewer",
        folder_name="08_legal_document_reviewer",
        name="Legal Document Reviewer",
        category="Legal & Compliance",
        description="Reviews contracts and agreements, checks clauses, flags risk levels, and verifies citations.",
        pattern="Chunking + fan-out + citation verification",
        default_sample_input="Review Master Services Agreement for indemnity and liability exposure.",
    ),
    AgentMetadata(
        id="healthcare_intake",
        folder_name="09_healthcare_intake",
        name="Healthcare Intake & Triage",
        category="Healthcare",
        description="Performs patient intake with fail-closed medical safety guardrails, PII scrubbing, and urgency escalation.",
        pattern="Fail-closed guardrails + PII scrub + escalation",
        default_sample_input="Patient reporting mild headache and seasonal allergies for 2 days.",
    ),
    AgentMetadata(
        id="devops_triage",
        folder_name="10_devops_incident_triage",
        name="DevOps Incident Triage",
        category="DevOps & Infrastructure",
        description="Gathers logs, traces, and metrics in parallel, runs severity triage, and generates remediation runbooks.",
        pattern="Parallel gather + severity matrix + approval gate",
        default_sample_input="Investigate latency spike and 502 Bad Gateway alerts on payments service.",
    ),
    AgentMetadata(
        id="ecommerce_recommender",
        folder_name="11_ecommerce_recommender",
        name="E-Commerce Recommender",
        category="Sales & E-Commerce",
        description="Recommends personalized products from catalog based on customer history, session intent, and preferences.",
        pattern="Thread checkpointer + cross-session Store",
        default_sample_input="Recommend noise-cancelling headphones and accessories under $250.",
    ),
]


class AgentRegistry:
    def __init__(self, agents_dir: Optional[Path] = None):
        self.agents_dir = agents_dir or AGENTS_CODE_DIR
        self._meta_by_id = {m.id: m for m in AGENT_DEFINITIONS}
        self._meta_by_folder = {m.folder_name: m for m in AGENT_DEFINITIONS}

    def list_agents(self) -> List[AgentMetadata]:
        return AGENT_DEFINITIONS

    def get_metadata(self, agent_id_or_folder: str) -> Optional[AgentMetadata]:
        return self._meta_by_id.get(agent_id_or_folder) or self._meta_by_folder.get(agent_id_or_folder)

    def load_agent_module(self, agent_id_or_folder: str):
        meta = self.get_metadata(agent_id_or_folder)
        if not meta:
            raise ValueError(f"Unknown agent: {agent_id_or_folder}")

        folder = self.agents_dir / meta.folder_name
        agent_file = folder / "agent.py"
        if not agent_file.exists():
            raise FileNotFoundError(f"Agent file not found: {agent_file}")

        module_name = f"agents_code_{meta.folder_name}"
        if module_name in sys.modules:
            return sys.modules[module_name]

        orig_sys_path = list(sys.path)
        sys.path.insert(0, str(folder))
        try:
            spec = importlib.util.spec_from_file_location(module_name, str(agent_file))
            mod = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = mod
            spec.loader.exec_module(mod)
            return mod
        finally:
            sys.path = orig_sys_path

    def get_graph(self, agent_id_or_folder: str):
        mod = self.load_agent_module(agent_id_or_folder)
        if not hasattr(mod, "build_graph"):
            raise AttributeError(f"Module {mod} does not have build_graph()")

        varnames = mod.build_graph.__code__.co_varnames
        if "checkpointer" in varnames:
            return mod.build_graph(checkpointer=MemorySaver())
        return mod.build_graph()

    def execute_agent(self, agent_id_or_folder: str, payload: Any) -> Dict[str, Any]:
        """
        Executes an agent with a given payload and returns execution details.
        """
        meta = self.get_metadata(agent_id_or_folder)
        if not meta:
            raise ValueError(f"Unknown agent: {agent_id_or_folder}")

        start_time = time.time()
        mod = self.load_agent_module(agent_id_or_folder)
        graph = self.get_graph(agent_id_or_folder)

        input_state = self._prepare_state(meta.id, payload, mod)
        config = {"configurable": {"thread_id": f"sup-{int(time.time()*1000)}"}}

        try:
            result = graph.invoke(input_state, config=config)
            duration = round(time.time() - start_time, 2)
            summary = self._extract_summary(meta.id, result)
            return {
                "success": True,
                "agent_id": meta.id,
                "agent_name": meta.name,
                "duration_seconds": duration,
                "output_summary": summary,
                "raw_output": result,
                "error": None,
            }
        except Exception as exc:
            duration = round(time.time() - start_time, 2)
            return {
                "success": False,
                "agent_id": meta.id,
                "agent_name": meta.name,
                "duration_seconds": duration,
                "output_summary": f"Execution failed: {str(exc)}",
                "raw_output": None,
                "error": str(exc),
            }

    def _prepare_state(self, agent_id: str, payload: Any, mod: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return payload

        text = str(payload) if payload else ""

        if agent_id == "sql_analyst":
            db_path = getattr(mod, "DB_PATH", str(self.agents_dir / "01_sql_data_analyst" / "sales.db"))
            return {"question": text, "attempts": 0}

        elif agent_id == "csv_analyst":
            csv_path = str(self.agents_dir / "02_csv_excel_data_analyst" / "sales_data.csv")
            return {
                "file_path": csv_path,
                "question": text or "What is total sales by region?",
                "exec_retries": 0,
                "format_attempts": 0,
            }

        elif agent_id == "bi_insights":
            # Load sample json if available
            fixture_path = self.agents_dir / "03_bi_dashboard_insights" / "metrics.json"
            metrics_data = {}
            if fixture_path.exists():
                with open(fixture_path, "r", encoding="utf-8") as f:
                    metrics_data = json.load(f)
            return {"query": text, "metrics_data": metrics_data}

        elif agent_id == "customer_support":
            from langchain_core.messages import HumanMessage
            return {"messages": [HumanMessage(content=text)], "customer_id": "CUST-1001"}

        elif agent_id == "hr_screener":
            return {"job_description": text or "Senior Full Stack Python Developer"}

        elif agent_id == "expense_auditor":
            return {"claims_file": "sample_expenses.json", "prompt": text}

        elif agent_id == "marketing_creator":
            return {"brief": text or "Product launch announcement for our new AI assistant toolkit."}

        elif agent_id == "legal_reviewer":
            return {"contract_text": text or "Standard Non-Disclosure Agreement and Master Services Agreement clauses."}

        elif agent_id == "healthcare_intake":
            from langchain_core.messages import HumanMessage
            return {"messages": [HumanMessage(content=text or "Patient reporting mild seasonal allergy symptoms.")]}

        elif agent_id == "devops_triage":
            return {"alert_text": text or "P1 Alert: Elevated 500 error rate on checkout service."}

        elif agent_id == "ecommerce_recommender":
            from langchain_core.messages import HumanMessage
            return {"messages": [HumanMessage(content=text or "Looking for wireless headphones under $200.")], "user_id": "user_42"}

        return {"input": text}

    def _extract_summary(self, agent_id: str, result: Any) -> str:
        if not isinstance(result, dict):
            return str(result)[:300]

        for key in ["answer", "summary", "report", "response", "triage_report", "briefing", "critique", "recommendations"]:
            if key in result and result[key]:
                val = result[key]
                if isinstance(val, str):
                    return val
                elif isinstance(val, dict) and "summary" in val:
                    return str(val["summary"])
                return str(val)[:500]

        if "messages" in result and result["messages"]:
            last = result["messages"][-1]
            if hasattr(last, "content"):
                return str(last.content)
            elif isinstance(last, dict) and "content" in last:
                return str(last["content"])

        return json.dumps({k: v for k, v in result.items() if not k.startswith("_")}, default=str)[:400]
