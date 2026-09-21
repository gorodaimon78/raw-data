"""
Project Five ("Raw data") - Web Application Server
Serves the modern Semantic Trends & Traffic Intelligence Dashboard and API,
including Agent 07 Live Human-Outreach Engine with randomized jitter delays and direct jump-links.
"""
import os
import sys

# Fix Windows console encoding for Unicode/Emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
import logging
import mimetypes
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone, timedelta

import importlib

from agents_code.trend_collector.trend_engine import TrendEngine

_outreach_mod = importlib.import_module("agents_code.07_marketing_content.outreach_engine")
Agent07OutreachManager = _outreach_mod.Agent07OutreachManager
draft_human_reply = _outreach_mod.draft_human_reply
draft_polite_defensive_reply = _outreach_mod.draft_polite_defensive_reply

_yt_mod = importlib.import_module("agents_code.07_marketing_content.youtube_comment_harvester")
YouTubeCommentHarvester = _yt_mod.YouTubeCommentHarvester
draft_youtube_human_reply = _yt_mod.draft_youtube_human_reply

_fleet_mod = importlib.import_module("agents_code.07_marketing_content.multi_persona_dispatcher")
SupervisorPersonaDispatcher = _fleet_mod.SupervisorPersonaDispatcher
WORKER_ROSTER = _fleet_mod.WORKER_ROSTER

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
REPORTS_DIR = BASE_DIR / "reports"
WEB_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = "Goro Daimon"
APP_VERSION = "v1"

logger = logging.getLogger("web_app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_latest_trends_data(keyword: Optional[str] = None):
    """Finds or generates trend data for the target niche."""
    engine = TrendEngine()
    if keyword and keyword.strip() and keyword.lower() != "pdf":
        res = engine.run_daily_trend_collection(keyword=keyword)
        with open(res["json_file"], "r", encoding="utf-8") as f:
            return json.load(f)
            
    json_files = sorted(REPORTS_DIR.glob("daily_trends_*.json"), key=os.path.getmtime, reverse=True)
    if json_files:
        try:
            with open(json_files[0], "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading {json_files[0]}: {e}")
            
    res = engine.run_daily_trend_collection(keyword="PDF")
    with open(res["json_file"], "r", encoding="utf-8") as f:
        return json.load(f)


class TrendsAPIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        
        if parsed.path == "/api/trends":
            keyword = qs.get("keyword", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = get_latest_trends_data(keyword=keyword)
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif parsed.path == "/api/agent07/history":
            manager = Agent07OutreachManager()
            data = manager.get_latest_outreach_log()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return
            
        elif parsed.path == "/api/youtube/harvest":
            qs = parse_qs(parsed.query)
            topic = qs.get("topic", ["all"])[0]
            harvester = YouTubeCommentHarvester()
            items = harvester.harvest_by_topic(topic)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "count": len(items), "items": items}, ensure_ascii=False).encode("utf-8"))
            return

        elif parsed.path == "/api/fleet/workers":
            dispatcher = SupervisorPersonaDispatcher()
            stats = dispatcher.get_fleet_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "data": stats}, ensure_ascii=False).encode("utf-8"))
            return

        elif parsed.path == "/api/fleet/history":
            dispatcher = SupervisorPersonaDispatcher()
            stats = dispatcher.get_fleet_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "history": stats.get("history", [])}, ensure_ascii=False).encode("utf-8"))
            return

        elif parsed.path == "/api/status":
            utc_now = datetime.now(timezone.utc)
            pkst_now = utc_now + timedelta(hours=5)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            status_data = {
                "server_time_utc": utc_now.isoformat(),
                "time_pkst": pkst_now.strftime("%Y-%m-%d %H:%M:%S PKST"),
                "daily_schedule": "06:00 AM PKST (01:00 UTC)",
                "platforms_count": 8,
                "project_name": "Project Five (Goro Daimon) -> Project 1 (YourOwnPDF Traffic Engine)",
                "version": APP_VERSION,
                "app_name": APP_NAME
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
            return
            
        elif parsed.path == "/" or parsed.path == "/index.html":
            index_file = WEB_DIR / "index.html"
            if index_file.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(index_file, "rb") as f:
                    self.wfile.write(f.read())
                return

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body_str = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body_str) if body_str else {}
        except Exception:
            payload = {}
        
        if parsed.path == "/api/refresh":
            keyword = payload.get("keyword", "PDF")
            try:
                engine = TrendEngine()
                res = engine.run_daily_trend_collection(keyword=keyword)
                with open(res["json_file"], "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": f"Harvested opportunities for '{keyword}'", "data": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif parsed.path == "/api/draft-reply":
            q = payload.get("question", "")
            p = payload.get("platform", "Reddit")
            reply = draft_human_reply(q, platform=p)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "reply": reply}).encode("utf-8"))
            return

        elif parsed.path == "/api/agent07/counter-reply":
            user_complaint = payload.get("complaint", "")
            orig_q = payload.get("question", "")
            counter_reply = draft_polite_defensive_reply(user_complaint, orig_q)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "counter_reply": counter_reply}).encode("utf-8"))
            return

        elif parsed.path == "/api/agent07/dispatch-campaign":
            questions = payload.get("questions", [])
            manager = Agent07OutreachManager()
            scheduled = manager.queue_outreach_campaign(questions)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "scheduled_count": len(scheduled), "items": scheduled}).encode("utf-8"))
            return

        elif parsed.path == "/api/youtube/harvest":
            topic = payload.get("topic", "all")
            harvester = YouTubeCommentHarvester()
            items = harvester.harvest_by_topic(topic)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "count": len(items), "items": items}, ensure_ascii=False).encode("utf-8"))
            return

        elif parsed.path == "/api/youtube/custom":
            video_url = payload.get("video_url", "")
            harvester = YouTubeCommentHarvester()
            res = harvester.harvest_custom_video(video_url)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            return

        elif parsed.path == "/api/youtube/draft-reply":
            comm_text = payload.get("comment_text", "")
            intent = payload.get("intent", "PDF Workflow")
            author = payload.get("author", "User")
            reply = draft_youtube_human_reply(comm_text, intent, author)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "reply": reply}, ensure_ascii=False).encode("utf-8"))
            return

        elif parsed.path == "/api/fleet/classify-and-draft":
            q = payload.get("question", "")
            author = payload.get("author", "User")
            platform = payload.get("platform", "Reddit")
            dispatcher = SupervisorPersonaDispatcher()
            result = dispatcher.classify_and_assign(q, author_name=author, platform=platform)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "data": result}, ensure_ascii=False).encode("utf-8"))
            return

        elif parsed.path == "/api/fleet/dispatch":
            items = payload.get("items", [])
            if not items:
                # Pull top leads from latest trends automatically
                trends_data = get_latest_trends_data()
                if trends_data and "platforms" in trends_data:
                    for p, list_items in trends_data["platforms"].items():
                        if p in ["Reddit", "Quora", "Facebook", "Medium", "YouTube"]:
                            for itm in list_items[:2]:
                                items.append({
                                    "title": itm.get("title", ""),
                                    "author": itm.get("type", "User"),
                                    "platform": p,
                                    "url": itm.get("url", "#")
                                })
            dispatcher = SupervisorPersonaDispatcher()
            scheduled = dispatcher.queue_fleet_campaign(items)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "scheduled_count": len(scheduled), "items": scheduled}, ensure_ascii=False).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


def run_server(port: int = 8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, TrendsAPIHandler)
    print(f"===============================================================")
    print(f"  🎯 Raw Data (Project Five) Semantic Traffic Engine Active!")
    print(f"  👉 Open URL: http://localhost:{port}")
    print(f"  🤖 Agent 07 Human Outreach & Traffic Engine Active!")
    print(f"===============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web server...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
