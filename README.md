# 🌐 Raw Data (Project Five) — 8-Platform Daily Trends Intelligence

[![Daily 6 AM PKST Trends Intelligence](https://github.com/actions/workflows/daily_trends_6am_pkst.yml/badge.svg)](../../actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-indigo.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)

**Raw Data (Project Five)** is an autonomous multi-platform trend intelligence web application and AI supervisor that aggregates, synthesizes, and visualizes the **Top 10 most searched topics, questions, discussions, and hashtags (last 24 hours)** across **8 major platforms**:

1. 🔍 **Google** (Daily Search Trends & Rising Queries)
2. 👽 **Reddit** (Top viral discussions & questions across `r/popular`, `r/all`, `r/AskReddit`, `r/technology`)
3. ▶️ **YouTube** (Trending searches & high-velocity videos)
4. 📌 **Pinterest** (Pinterest Trends, aesthetic inspiration keywords & rising ideas)
5. ✍️ **Medium** (Top editorial stories, tech/AI discussions & trending tags)
6. ❓ **Quora** (Top asked community questions & debates)
7. 💼 **LinkedIn** (Workforce news, Daily Rundown headlines & trending professional hashtags)
8. 👥 **Facebook** (Viral public discussions, community topics & trending hashtags)

---

## ⏰ Automated Daily 6:00 AM PKST Execution

- **Pakistan Standard Time (PKST)** is **UTC+5**.
- **Automated Cloud Schedule**: Configured via GitHub Actions (`.github/workflows/daily_trends_6am_pkst.yml`) running daily at **01:00 UTC (06:00 AM PKST)**.
- **Runs Even If Laptop Is Off**: Because GitHub Actions runs on cloud servers, daily reports are generated and committed automatically every morning even if your laptop is shut down!
- **On-Demand Trigger (Anytime)**: Trigger the workflow anytime directly on GitHub with 1-click via the **"Run workflow"** button.

---

## 🚀 Quick Start (Local Web Application)

### 1. Start the Live Web Dashboard
```bash
python app.py 8080
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser to access:
- Live 8-Platform Top 10 Cards with source links and volume metrics.
- **⚡ "Execute Trends Now"** instant trigger button.
- Real-time search and platform category filters.
- Export to Markdown, JSON, and CSV.
- Actionable content angles synthesized by Marketing Specialist (Agent 07).

---

## 💻 CLI & Supervisor Commands

```bash
# Run trends on-demand right now from terminal
python supervisor.py run-trends

# Start continuous 06:00 AM PKST local scheduler daemon (with boot catch-up)
python supervisor.py start-pkst-scheduler

# View executive supervisor dashboard
python supervisor.py dashboard

# List all 11 managed AI agents
python supervisor.py list-agents
```

---

## 📁 Output Reports & Data Structure

- **Executive Markdown Reports**: `reports/daily_trends_YYYY-MM-DD.md`
- **Structured JSON Datasets**: `reports/daily_trends_YYYY-MM-DD.json`
- **GitHub Pages Dashboard**: `docs/index.html` + `docs/data.json`

---

## 🔒 Privacy & Zero Password Policy

All 8 platform extractors operate via open RSS feeds, public JSON endpoints, and search trend aggregators. **No user accounts, passwords, or personal credentials are required.**
