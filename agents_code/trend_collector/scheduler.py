"""
PKST Timezone-Aware Scheduler for Daily 6:00 AM Trend Intelligence Collection
Handles:
1. Precise 06:00 AM PKST (UTC+5) scheduled daily execution.
2. Automatic "Catch-up on boot": If your laptop was off or asleep at 6:00 AM,
   it immediately detects the missed run on startup and generates today's report.
3. Windows Task Scheduler automated setup script with wake-timer support.
"""
import os
import sys
import time
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from agents_code.trend_collector.trend_engine import TrendEngine

logger = logging.getLogger("pkst_scheduler")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_pkst_now() -> datetime:
    """Returns current datetime in Pakistan Standard Time (UTC+5)."""
    return datetime.now(timezone.utc) + timedelta(hours=5)


class PKSTTrendScheduler:
    def __init__(self, target_hour: int = 6, target_minute: int = 0):
        self.target_hour = target_hour
        self.target_minute = target_minute
        self.engine = TrendEngine()
        self.last_run_date: Optional[str] = None

    def is_report_generated_for_today(self) -> bool:
        """Checks if today's PKST daily report already exists."""
        pkst_now = get_pkst_now()
        date_str = pkst_now.strftime("%Y-%m-%d")
        expected_file = self.engine.reports_dir / f"daily_trends_{date_str}.md"
        return expected_file.exists()

    def check_and_run_catchup(self):
        """
        If laptop was turned off at 6:00 AM PKST, this executes immediately upon boot
        once current time is past 6:00 AM PKST and today's report hasn't been generated yet.
        """
        pkst_now = get_pkst_now()
        date_str = pkst_now.strftime("%Y-%m-%d")
        
        # If current time is after target time (e.g. after 06:00 AM PKST) and no report exists today
        current_minute_of_day = pkst_now.hour * 60 + pkst_now.minute
        target_minute_of_day = self.target_hour * 60 + self.target_minute
        
        if current_minute_of_day >= target_minute_of_day and not self.is_report_generated_for_today():
            logger.info(f"⚡ [Catch-up on Boot] Laptop was off or asleep at 06:00 AM PKST. Generating today's ({date_str}) report now...")
            res = self.engine.run_daily_trend_collection()
            self.last_run_date = date_str
            logger.info(f"✅ Catch-up complete! Report saved to {res['markdown_file']}")
            return res
        else:
            logger.info(f"ℹ️ Report status for today ({date_str}): {'Already Generated' if self.is_report_generated_for_today() else 'Scheduled for 06:00 AM PKST'}")
            return None

    def start_scheduler_daemon(self, poll_interval_sec: int = 30):
        """
        Continuous daemon checking PKST time every 30 seconds.
        """
        logger.info(f"🚀 Starting PKST Trend Scheduler Daemon targeting {self.target_hour:02d}:{self.target_minute:02d} AM PKST daily...")
        
        # 1. Run catchup on boot if needed
        self.check_and_run_catchup()
        
        while True:
            try:
                pkst_now = get_pkst_now()
                date_str = pkst_now.strftime("%Y-%m-%d")
                
                # Check if it is currently 06:00 AM PKST and hasn't run today
                if (pkst_now.hour == self.target_hour and 
                    pkst_now.minute == self.target_minute and 
                    self.last_run_date != date_str and 
                    not self.is_report_generated_for_today()):
                    
                    logger.info(f"⏰ [06:00 AM PKST Alarm Triggered] Starting daily trend cycle...")
                    self.engine.run_daily_trend_collection()
                    self.last_run_date = date_str
                    logger.info(f"✅ Daily 6:00 AM PKST trend collection finished successfully.")
                    
                time.sleep(poll_interval_sec)
            except KeyboardInterrupt:
                logger.info("Scheduler daemon stopped by user.")
                break
            except Exception as e:
                logger.error(f"Scheduler daemon error: {e}")
                time.sleep(poll_interval_sec)


def generate_windows_task_command() -> str:
    """
    Returns PowerShell command to create a persistent Windows Task Scheduler entry
    that automatically wakes the PC or runs on startup / at 6:00 AM PKST.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    venv_python = base_dir / ".venv" / "Scripts" / "python.exe"
    script_path = base_dir / "supervisor.py"
    
    cmd = (
        f'schtasks /create /tn "ElevenAgents_DailyTrends_6AM_PKST" '
        f'/tr "\"{venv_python}\" \"{script_path}\" run-trends" '
        f'/sc daily /st 06:00 /f'
    )
    return cmd


if __name__ == "__main__":
    scheduler = PKSTTrendScheduler()
    scheduler.start_scheduler_daemon()
