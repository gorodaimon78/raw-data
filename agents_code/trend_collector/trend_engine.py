"""
Trend Engine Module
Orchestrates multi-platform semantic intelligence, targeted traffic harvesting,
and synthesizes actionable marketing angles for Project 1 (YourOwnPDF).
"""
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from agents_code.trend_collector.platform_scrapers import fetch_all_platforms_trends

logger = logging.getLogger("trend_engine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class TrendEngine:
    def __init__(self, reports_dir: Optional[Path] = None):
        self.reports_dir = reports_dir or REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def run_daily_trend_collection(self, keyword: Optional[str] = "PDF", geo: str = "US", max_per_platform: int = 10) -> Dict[str, Any]:
        """
        Runs the trend and traffic opportunity collection across 8 platforms:
        Google, Reddit, YouTube, Pinterest, Medium, Quora, LinkedIn, and Facebook.
        """
        target_niche = keyword or "PDF"
        utc_now = datetime.now(timezone.utc)
        pkst_now = utc_now + timedelta(hours=5)
        date_str = pkst_now.strftime("%Y-%m-%d")
        time_str_pkst = pkst_now.strftime("%Y-%m-%d %H:%M:%S PKST (UTC+5)")

        logger.info(f"Harvesting semantic opportunities for '{target_niche}' ({date_str} {time_str_pkst})...")
        
        # 1. Fetch data from all 8 platforms with semantic intent
        platforms_data = fetch_all_platforms_trends(keyword=target_niche, geo=geo, max_per_platform=max_per_platform)
        
        # 2. Build Markdown Report
        md_report = self._build_markdown_report(platforms_data, target_niche, date_str, time_str_pkst)
        
        # 3. Save Markdown and JSON reports
        md_file = self.reports_dir / f"daily_trends_{date_str}.md"
        json_file = self.reports_dir / f"daily_trends_{date_str}.json"
        
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_report)
            
        json_payload = {
            "date": date_str,
            "target_niche": target_niche,
            "generated_at_pkst": time_str_pkst,
            "generated_at_utc": utc_now.isoformat(),
            "total_platforms": len(platforms_data),
            "total_trends": sum(len(v) for v in platforms_data.values()),
            "platforms": platforms_data
        }
        
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(json_payload, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Traffic intelligence reports saved: {md_file} & {json_file}")
        
        return {
            "success": True,
            "date": date_str,
            "target_niche": target_niche,
            "generated_at_pkst": time_str_pkst,
            "markdown_file": str(md_file),
            "json_file": str(json_file),
            "platforms_data": platforms_data,
            "summary": f"Successfully harvested {sum(len(v) for v in platforms_data.values())} traffic opportunities across 8 platforms for '{target_niche}'."
        }

    def _build_markdown_report(self, data: Dict[str, List[Dict[str, Any]]], niche: str, date_str: str, time_str: str) -> str:
        lines = [
            f"# 🎯 Semantic Traffic & Trend Intelligence Report — Target: `{niche}`",
            f"**Generated:** {time_str}  ",
            f"**Target Platforms (8):** Google, Reddit, YouTube, Pinterest, Medium, Quora, LinkedIn, Facebook  ",
            f"**Primary Mission:** Drive High-Intent Referral & Search Traffic to Project 1 (YourOwnPDF)  ",
            f"**Total Tracked Opportunities:** {sum(len(v) for v in data.values())} questions, discussions, and rising queries",
            "",
            "---",
            "",
            "## 📊 Executive Matrix Overview",
            "",
            "| Platform | #1 Question / Opportunity | Intent Type | Volume / Views | Action Link |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]

        for platform, items in data.items():
            top = items[0] if items else {"title": "N/A", "intent_score": "N/A", "traffic_volume": "N/A", "url": "#"}
            lines.append(f"| **{platform}** | [{top['title'][:45]}...]({top['url']}) | `{top.get('intent_score', 'Lead')}` | {top.get('traffic_volume', '-')} | [Open]({top['url']}) |")

        lines.extend([
            "",
            "---",
            "",
        ])

        platform_icons = {
            "Google": "🔍",
            "Reddit": "👽",
            "YouTube": "▶️",
            "Pinterest": "📌",
            "Medium": "✍️",
            "Quora": "❓",
            "LinkedIn": "💼",
            "Facebook": "👥"
        }

        for platform, items in data.items():
            icon = platform_icons.get(platform, "🌐")
            lines.append(f"## {icon} {platform} — Top 10 Targeted Opportunities (`{niche}`)")
            lines.append("")
            
            for item in items:
                rank = item.get("rank", 1)
                title = item.get("title", "")
                itype = item.get("type", "Question")
                vol = item.get("traffic_volume", "")
                desc = item.get("description", "")
                url = item.get("url", "#")
                score = item.get("intent_score", "Lead")
                
                lines.append(f"### {rank}. [{title}]({url})")
                lines.append(f"- **Intent Level:** `{score}` | **Format:** `{itype}` | **Traffic/Upvotes:** `{vol}`")
                lines.append(f"- **Traffic Strategy:** {desc}")
                lines.append(f"- **Direct Link:** [Open Opportunity URL]({url})")
                lines.append("")

            lines.append("---")
            lines.append("")

        lines.extend([
            "## 💡 Recommended Referral & SEO Playbook (Project 1 Growth)",
            "1. **Quora & Reddit Direct Answers**: Reply to the high-ranking Quora questions with a clear, step-by-step tutorial and mention: *'You can use a client-side tool like YourOwnPDF which compresses/merges files directly in your browser without uploading your private files.'*",
            "2. **Long-Tail SEO Tool Pages**: Use the top Google autocomplete queries to verify YourOwnPDF has dedicated high-speed tool routes (e.g. `/compress-pdf`, `/merge-pdf`, `/split-pdf`).",
            "3. **Pinterest & YouTube Visual Traffic**: Create short 15-second screen recordings answering these exact queries to capture video search traffic.",
            "",
            "_Generated automatically by Project Five (Raw data) for Project 1 (YourOwnPDF)._"
        ])

        return "\n".join(lines)


def get_trend_engine() -> TrendEngine:
    return TrendEngine()
