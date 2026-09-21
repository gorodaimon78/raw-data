# 👑 Eleven AI Agents: Supervisor & Daily Task Orchestrator

This repository contains **11 production-grade LangGraph AI Agents** integrated under a **Master Supervisor & Daily Task Orchestrator System**.

---

## 🧭 Location & Quick Start

- **Project Location**: `C:\Users\gorod\.gemini\antigravity\scratch\eleven_ai_agents`
- **Virtual Environment**: `C:\Users\gorod\.gemini\antigravity\scratch\eleven_ai_agents\.venv`
- **Supervisor CLI**: `python supervisor.py`

### 1. Configure Your API Key
Edit `.env` inside the repository:
```env
ANTHROPIC_API_KEY=your_key_here
MODEL=claude-sonnet-5
```

---

## 🤖 The 11 Managed AI Agents

| # | Agent ID | Name | Category | Pattern | Core Capability |
|---|---|---|---|---|---|
| **01** | `sql_analyst` | SQL Data Analyst | Analytics | Self-correcting loop | Queries relational database, generates safe read-only SQL with auto-repair. |
| **02** | `csv_analyst` | CSV / Excel Analyst | Analytics | Structured output | Profiles tabular data, generates chart specifications, and extracts insights. |
| **03** | `bi_insights` | BI Dashboard Insights | BI & Strategy | Multi-step reasoning | Analyzes KPI movements, forms hypotheses, tests with metrics, and writes summaries. |
| **04** | `customer_support` | Customer Support | Support | Checkpointed chat | Classifies intent (Order, Return, Tech Support), tracks state across conversation turns. |
| **05** | `hr_screener` | HR Resume Screener | HR | Send fan-out + reduce | Builds grading rubric, scores candidate resumes in parallel, outputs candidate leaderboard. |
| **06** | `expense_auditor` | Finance Expense Auditor | Finance | Policy rules + interrupt | Audits expense claims, enforces compliance limits, flags anomalous receipts. |
| **07** | `marketing_creator` | Marketing Content Creator | Growth | Critique & revise loop | Drafts multi-channel content (LinkedIn, Twitter, Blogs) with quality check loops. |
| **08** | `legal_reviewer` | Legal Document Reviewer | Legal | Chunking + citation check | Chunks agreements, extracts definitions, identifies high-risk clauses with citations. |
| **09** | `healthcare_intake` | Healthcare Intake & Triage | Healthcare | Fail-closed guardrails | Collects symptoms, scrubs PII, checks medical red flags, and routes urgency level. |
| **10** | `devops_triage` | DevOps Incident Triage | DevOps | Parallel gather + severity | Correlates error logs, metrics, and git deployments, produces incident runbooks. |
| **11** | `ecommerce_recommender` | E-Commerce Recommender | Sales | Cross-session store | Recommends products matching user budget and intent with inventory validation. |

---

## 🛠️ Supervisor CLI Commands

### 1. View Agents & Health Checks
```powershell
# List all 11 agents and metadata
.\.venv\Scripts\python.exe supervisor.py list-agents

# Test graph compilation for all 11 agents (zero API tokens used)
.\.venv\Scripts\python.exe supervisor.py test-agents
```

### 2. Run Any Agent On-Demand
```powershell
# Run SQL analyst with a custom question
.\.venv\Scripts\python.exe supervisor.py run-agent --agent sql_analyst --input "What are our top 5 revenue products?"

# Run DevOps triage on an alert
.\.venv\Scripts\python.exe supervisor.py run-agent --agent devops_triage --input "Spike in HTTP 504 gateway timeouts on api-gateway"
```

### 3. Manage Daily Task Queue
```powershell
# View all registered daily tasks
.\.venv\Scripts\python.exe supervisor.py list-tasks

# Add a new daily task for an agent
.\.venv\Scripts\python.exe supervisor.py add-task --name "Morning SEO & Content Draft" --agent marketing_creator --input "Draft a 3-paragraph blog on agentic AI workflows." --schedule daily --time "08:00"

# Execute a single task by ID
.\.venv\Scripts\python.exe supervisor.py run-task --id 1
```

### 4. Execute Daily Batch Cycle & Generate Briefing
```powershell
# Executes all active daily tasks and writes reports/daily_report_YYYY-MM-DD.md
.\.venv\Scripts\python.exe supervisor.py run-daily
```

### 5. View Run History & Logs
```powershell
.\.venv\Scripts\python.exe supervisor.py history --limit 10
```

### 6. Run Continuous Scheduler Daemon
```powershell
.\.venv\Scripts\python.exe supervisor.py start-daemon
```

---

## 🎯 How Antigravity Supervises Your Daily Tasks

When you are ready to assign daily tasks:
1. Simply state the tasks or instructions in chat (e.g. *"Antigravity, supervise daily sales and devops checks every morning at 9 AM"*).
2. Antigravity can interactively register tasks, execute agents, review output quality, and deliver consolidated reports directly into your conversation or saved markdown artifacts.
