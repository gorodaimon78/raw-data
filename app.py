"""
Project Five ("Raw data") - Web Application Server
Serves the modern live Trends Intelligence Web Dashboard and API.
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

from agents_code.trend_collector.trend_engine import TrendEngine

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
REPORTS_DIR = BASE_DIR / "reports"
WEB_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("web_app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_latest_trends_data():
    """Finds and loads the latest daily_trends_*.json file."""
    json_files = sorted(REPORTS_DIR.glob("daily_trends_*.json"), key=os.path.getmtime, reverse=True)
    if json_files:
        try:
            with open(json_files[0], "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading {json_files[0]}: {e}")
            
    # Fallback to generating on the fly
    engine = TrendEngine()
    res = engine.run_daily_trend_collection()
    with open(res["json_file"], "r", encoding="utf-8") as f:
        return json.load(f)


class TrendsAPIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/api/trends":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = get_latest_trends_data()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
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
                "project_name": "Project Five (Raw data)"
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
        
        if parsed.path == "/api/refresh":
            try:
                engine = TrendEngine()
                res = engine.run_daily_trend_collection()
                with open(res["json_file"], "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Trends refreshed successfully!", "data": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


def run_server(port: int = 8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, TrendsAPIHandler)
    print(f"===============================================================")
    print(f"  🌐 Project Five (Raw data) Web Dashboard is Running!")
    print(f"  👉 Open URL: http://localhost:{port}")
    print(f"  ⏰ Daily Schedule: 06:00 AM PKST (01:00 UTC)")
    print(f"===============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web server...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
