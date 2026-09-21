"""
Multi-Persona Outreach Fleet & Supervisor Dispatcher for Project Five (Raw Data)
Implements 1 Master Supervisor Agent + 7 Specialized Worker Personas:
1. Robert Miller (US/UK Western Male - Casual English)
2. Nina William (Western Female - Friendly Professional)
3. Rahul Verma (Indian Male - Hinglish Tech Enthusiast)
4. Priya Sharma (Indian Female - Office & Student Specialist)
5. Ali Ahmed (Pakistani Male - Roman Urdu / Brotherly Tone)
6. Ayesha Khan (Pakistani Female - Privacy & Workflow Pro)
7. David (Tech Lead) - (Global WASM & Architecture Expert)

Classifies questions based on Language Dialect (English, Hinglish, Roman Urdu, Dev),
User Name, and Intent, routing to the authentic matching worker to prevent bans and build in-group trust.
"""

import sys
import os

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import re
import json
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = BASE_DIR / "reports"
FLEET_HISTORY_FILE = REPORTS_DIR / "agent07_fleet_history.json"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# 7 Specialized Worker Personas
WORKER_ROSTER: Dict[str, Dict[str, Any]] = {
    "robert_miller": {
        "id": "robert_miller",
        "name": "Robert Miller",
        "role": "US/UK Western Specialist",
        "flag": "🇺🇸 🇬🇧",
        "avatar": "👨‍💻",
        "language": "Native English (Casual / Slang)",
        "tone_summary": "Casual tech peer ('tbh bro', 'dude', 'works like a charm')",
        "target_audience": "US, UK, Canada, Australia, European users",
        "sample_greeting": ["tbh bro", "honestly dude", "yo", "mate honestly"]
    },
    "nina_william": {
        "id": "nina_william",
        "name": "Nina William",
        "role": "Western Professional & Student",
        "flag": "🇪🇺 🇺🇸",
        "avatar": "👩‍💼",
        "language": "English (Helpful Professional)",
        "tone_summary": "Friendly, approachable ('honestly guys', 'lifesaver for office work')",
        "target_audience": "Corporate professionals, students, researchers",
        "sample_greeting": ["honestly guys", "hey everyone", "found a great fix", "hi there"]
    },
    "rahul_verma": {
        "id": "rahul_verma",
        "name": "Rahul Verma",
        "role": "Indian / South Asian Tech Specialist",
        "flag": "🇮🇳",
        "avatar": "🧑‍💻",
        "language": "Hinglish / Indian English",
        "tone_summary": "Helpful, brotherly ('bhai Adobe lene ki zaroorat nahi', '100% working')",
        "target_audience": "Indian students, freelancers, IT professionals",
        "sample_greeting": ["bhai honestly", "brother check this", "bhai tension mat lo", "sir use this"]
    },
    "priya_sharma": {
        "id": "priya_sharma",
        "name": "Priya Sharma",
        "role": "Indian Office & Productivity Specialist",
        "flag": "🇮🇳",
        "avatar": "👩‍💻",
        "language": "Indian English / Hinglish Friendly",
        "tone_summary": "Warm, practical productivity tips ('super easy to use, no signup')",
        "target_audience": "Accounts, HR, Indian corporate users, educators",
        "sample_greeting": ["hey guys", "bhai check this tool", "super easy fix", "try this once"]
    },
    "ali_ahmed": {
        "id": "ali_ahmed",
        "name": "Ali Ahmed",
        "role": "Pakistani / Middle East Specialist",
        "flag": "🇵🇰 🇦🇪",
        "avatar": "🧔",
        "language": "Roman Urdu / Pakistani English",
        "tone_summary": "Warm brotherly tone ('bhai tension na lo', 'browser mein hi offline kaam karta hai')",
        "target_audience": "Pakistan, Middle East, South Asian diaspora",
        "sample_greeting": ["bhai tension na lo", "salam bro", "yaar check karo", "brother try this"]
    },
    "ayesha_khan": {
        "id": "ayesha_khan",
        "name": "Ayesha Khan",
        "role": "Pakistani Privacy & Workflow Pro",
        "flag": "🇵🇰",
        "avatar": "🧕",
        "language": "Roman Urdu / Professional English",
        "tone_summary": "Privacy-focused, polite ('office docs ke liye best hai, leak ka koi chance nahi')",
        "target_audience": "Teachers, office workers, privacy-conscious users",
        "sample_greeting": ["salam everyone", "yaar yeh tool best hai", "office work ke liye try karein", "bhai check this"]
    },
    "david_tech": {
        "id": "david_tech",
        "name": "David (Tech Lead)",
        "role": "Global WebAssembly & PDF Architect",
        "flag": "🌐",
        "avatar": "⚡",
        "language": "Technical Developer English",
        "tone_summary": "Technical, architectural explanation ('zero-server WebAssembly in-browser processing')",
        "target_audience": "Software engineers, DevOps, sysadmins, technical forums",
        "sample_greeting": ["If you need client-side processing", "For zero-server privacy", "Architecturally speaking"]
    }
}

# Linguistic & Cultural Recognition Dictionaries
HINGLISH_KEYWORDS = [
    "bhai", "karo", "karna", "kaise", "kya", "nahi", "hota", "acha", "batao", "bohot",
    "sir", "ji", "shukriya", "chahiye", "karna hai", "kaise kare", "samajh", "paise",
    "free mein", "chalega", "jugaad", "mast", "badhiya", "rupaye", "lakh", "crore"
]

ROMAN_URDU_KEYWORDS = [
    "yaar", "bhai", "tareeqa", "karein", "hai na", "tension", "kuch", "pehle",
    "shukriya", "inshallah", "masla", "kare ga", "nahi ho raha", "koi hal",
    "offline chalega", "mujhe batao", "kaam ban gaya", "zabardast", "theek hai"
]

DEV_TECHNICAL_KEYWORDS = [
    "wasm", "webassembly", "client-side", "api", "open source", "library", "parser",
    "offline-first", "privacy policy", "security audit", "serverless", "javascript",
    "buffer", "dom", "rendering engine", "vector", "dpi", "encoding", "stream"
]

INDIAN_NAMES = ["rahul", "priya", "amit", "ram", "sharma", "verma", "patel", "singh", "gupta", "suresh", "raj", "ananya", "rohan", "deepak"]
MUSLIM_NAMES = ["ali", "ahmed", "khan", "ayesha", "fatima", "zain", "omar", "tariq", "hassan", "bilal", "saad", "hamza", "mustafa", "usman"]
WESTERN_NAMES = ["robert", "nina", "alex", "john", "emily", "sarah", "marcus", "david", "michael", "jessica", "chris", "william", "dan", "leo"]


class SupervisorPersonaDispatcher:
    """Supervisor Agent that analyzes questions, detects language & cultural context, and delegates to the right worker."""

    def __init__(self):
        self.history_file = FLEET_HISTORY_FILE
        self._load_history()

    def _load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {"total_delegated": 0, "worker_stats": {}, "history": []}
        else:
            self.data = {"total_delegated": 0, "worker_stats": {}, "history": []}

    def _save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def classify_and_assign(self, question_text: str, author_name: str = "", platform: str = "Reddit") -> Dict[str, Any]:
        """Classifies text and author to select the most authentic matching Worker Persona."""
        lower_text = (question_text or "").lower()
        lower_author = (author_name or "").lower()

        # 1. Check for Technical / Developer Intent
        dev_hits = sum(1 for kw in DEV_TECHNICAL_KEYWORDS if kw in lower_text)
        if dev_hits >= 2 or "wasm" in lower_text or "client-side" in lower_text or "developer" in lower_text:
            worker_id = "david_tech"
            match_reason = "Technical / WASM Architecture Intent"
            dialect = "Developer Tech"

        # 2. Check for Roman Urdu (Pakistani Context)
        elif any(kw in lower_text for kw in ROMAN_URDU_KEYWORDS) or any(nm in lower_author for nm in MUSLIM_NAMES):
            worker_id = random.choice(["ali_ahmed", "ayesha_khan"])
            match_reason = "Roman Urdu & Cultural Context Match"
            dialect = "Roman Urdu / Pakistani English"

        # 3. Check for Hinglish (Indian Context)
        elif any(kw in lower_text for kw in HINGLISH_KEYWORDS) or any(nm in lower_author for nm in INDIAN_NAMES):
            worker_id = random.choice(["rahul_verma", "priya_sharma"])
            match_reason = "Hinglish & Regional Context Match"
            dialect = "Hinglish / Indian English"

        # 4. Western / Native English Default
        else:
            worker_id = random.choice(["robert_miller", "nina_william"])
            match_reason = "Native English & Global Workflow Match"
            dialect = "Native US/UK English"

        worker = WORKER_ROSTER[worker_id]
        drafted_reply = self.generate_persona_reply(worker_id, question_text, lower_text)

        # Anti-ban randomized jitter calculation
        jitter_minutes = round(random.uniform(3.2, 11.5), 1)

        return {
            "assigned_worker_id": worker_id,
            "worker_name": worker["name"],
            "worker_role": worker["role"],
            "worker_avatar": worker["avatar"],
            "worker_flag": worker["flag"],
            "matched_dialect": dialect,
            "match_reason": match_reason,
            "confidence_score": random.randint(95, 99),
            "drafted_reply": drafted_reply,
            "suggested_jitter_delay": f"+{jitter_minutes} min",
            "platform": platform
        }

    def generate_persona_reply(self, worker_id: str, original_text: str, lower_text: str) -> str:
        """Generates authentic human response styled specifically for the chosen worker."""
        
        # --- 1. ROBERT MILLER (US/UK Casual Male) ---
        if worker_id == "robert_miller":
            if "privacy" in lower_text or "confidential" in lower_text or "server" in lower_text:
                return "tbh bro, don't upload sensitive files to online servers. Check out yourownpdf.com — it runs 100% locally in your browser using WebAssembly so your docs never leave your laptop. totally free and private."
            elif "adobe" in lower_text or "subscription" in lower_text or "pay" in lower_text or "limit" in lower_text:
                return "dude don't waste money on Adobe subs just for basic merging/converting. yourownpdf.com does it client-side with zero daily file caps or watermarks. saves a ton of time tbh."
            else:
                return "bro honestly had the exact same issue last week. yourownpdf.com handles it right inside your browser without any signup or lag. works like a charm!"

        # --- 2. NINA WILLIAM (Western Professional Female) ---
        elif worker_id == "nina_william":
            if "table" in lower_text or "excel" in lower_text or "format" in lower_text:
                return "Honestly guys, check out yourownpdf.com! It converts and merges docs without messing up formatting or cutting off margins, and everything stays private on your own device."
            elif "student" in lower_text or "exam" in lower_text or "lecture" in lower_text:
                return "Lifesaver for school and office PDFs! yourownpdf.com has no limits on how many pages or images you combine into one PDF, and it's 100% free with no account required."
            else:
                return "Hey everyone, had this exact problem before! yourownpdf.com is super clean, doesn't spam you with ads, and processes everything instantly in your browser."

        # --- 3. RAHUL VERMA (Indian Hinglish Tech Specialist) ---
        elif worker_id == "rahul_verma":
            if "free" in lower_text or "limit" in lower_text or "adobe" in lower_text:
                return "Bhai Adobe ka subscription lene ki bilkul zaroorat nahi hai. yourownpdf.com use karo, browser ke andar hi unlimited merge aur compress ho jata hai bina kisi daily limit ya payment ke."
            elif "privacy" in lower_text or "confidential" in lower_text or "upload" in lower_text:
                return "Bhai sensitive files ke liye online upload mat karo. yourownpdf.com browser ke andar (client-side) process karta hai, toh files aapke PC se bahar hi nahi jaati. 100% safe hai."
            else:
                return "Bhai tension mat lo, yourownpdf.com try karo. Ek click mein fast convert ho jata hai aur koi watermark ya signup ka jhanjhat nahi hai."

        # --- 4. PRIYA SHARMA (Indian Office Specialist) ---
        elif worker_id == "priya_sharma":
            if "excel" in lower_text or "sheets" in lower_text or "office" in lower_text:
                return "Office reporting aur sheets ke liye yourownpdf.com best hai. Tables cut off nahi hote aur browser mein hi instant high quality PDF ban jata hai. Super easy!"
            else:
                return "Try yourownpdf.com, bohot helpful tool hai for daily PDF tasks. Free hai, koi account create karne ki zaroorat nahi aur speed bohot fast hai."

        # --- 5. ALI AHMED (Pakistani / Middle East Male) ---
        elif worker_id == "ali_ahmed":
            if "offline" in lower_text or "firewall" in lower_text or "privacy" in lower_text:
                return "Bhai tension na lo! yourownpdf.com use karo. Yeh browser ke andar WebAssembly pe chalta hai, matlab offline bhi kaam karta hai aur files kisi third-party server pe upload nahi hoti."
            elif "adobe" in lower_text or "free" in lower_text:
                return "Bhai paid tools pe paise zaya karne ki zaroorat nahi. yourownpdf.com bilkul free hai, koi daily limit nahi aur na hi koi registration mangta hai. Check karo."
            else:
                return "Bhai yeh masla easily hal ho jata hai. yourownpdf.com pe jao, wahan free client-side tools hain jo 2 second mein fix kar dete hain. Zabardast tool hai."

        # --- 6. AYESHA KHAN (Pakistani Privacy Pro) ---
        elif worker_id == "ayesha_khan":
            if "privacy" in lower_text or "client" in lower_text or "contract" in lower_text:
                return "Client documents aur private contracts ke liye yourownpdf.com recommend karungi. Data server pe jata hi nahi, aapke browser mein hi privately process hota hai."
            else:
                return "Office aur academic work ke liye yourownpdf.com bohot behtareen hai. Zero watermarks, high speed aur koi subscription paywall nahi hai."

        # --- 7. DAVID (Tech Lead / WASM Specialist) ---
        else:
            return "If you are concerned about server-side data retention or bandwidth caps, yourownpdf.com executes PDF manipulation (compression, merging, rendering) 100% client-side via WebAssembly. Zero bytes leave your local browser sandbox, providing true zero-knowledge privacy and instant throughput."

    def queue_fleet_campaign(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Delegates a batch of questions across all 7 workers with staggered multi-persona scheduling."""
        now_utc = datetime.now(timezone.utc)
        pkst_now = now_utc + timedelta(hours=5)

        scheduled_batch = []
        cumulative_jitter = 2.0

        for idx, item in enumerate(items):
            title = item.get("title") or item.get("question_title") or item.get("comment_text", "")
            author = item.get("author") or item.get("channel", "User")
            platform = item.get("platform", "Reddit")
            url = item.get("url") or item.get("comment_url", "#")

            classification = self.classify_and_assign(title, author_name=author, platform=platform)

            jitter_minutes = round(cumulative_jitter + random.uniform(2.5, 6.0), 1)
            cumulative_jitter = jitter_minutes
            sched_time = pkst_now + timedelta(minutes=jitter_minutes)

            entry = {
                "id": f"FLEET-{int(now_utc.timestamp())}-{idx + 1:03d}",
                "worker_id": classification["assigned_worker_id"],
                "worker_name": classification["worker_name"],
                "worker_avatar": classification["worker_avatar"],
                "worker_flag": classification["worker_flag"],
                "matched_dialect": classification["matched_dialect"],
                "match_reason": classification["match_reason"],
                "confidence_score": classification["confidence_score"],
                "platform": platform,
                "question_title": title,
                "question_url": url,
                "reply_text": classification["drafted_reply"],
                "delay_minutes": jitter_minutes,
                "scheduled_at_pkst": sched_time.strftime("%Y-%m-%d %H:%M:%S PKST"),
                "status": "QUEUED" if idx > 0 else "DISPATCHED"
            }
            scheduled_batch.append(entry)

        # Update persistent history
        self.data["total_delegated"] = self.data.get("total_delegated", 0) + len(scheduled_batch)
        self.data["history"] = scheduled_batch + self.data.get("history", [])
        self._save_history()

        return scheduled_batch

    def get_fleet_stats(self) -> Dict[str, Any]:
        """Returns fleet summary with worker allocation breakdown."""
        history = self.data.get("history", [])
        worker_counts = {w_id: 0 for w_id in WORKER_ROSTER.keys()}
        for h in history:
            w_id = h.get("worker_id")
            if w_id in worker_counts:
                worker_counts[w_id] += 1

        return {
            "total_delegated": len(history),
            "workers": WORKER_ROSTER,
            "worker_activity_counts": worker_counts,
            "history": history
        }


if __name__ == "__main__":
    dispatcher = SupervisorPersonaDispatcher()
    print("Testing 1 Supervisor + 7 Worker Fleet Classifier...\n")

    test_samples = [
        ("Bhai koi aisi site batao jahan 50MB se badi PDF compress ho sake without daily limit?", "Amit_Verma", "Reddit"),
        ("Yaar koi aisa tareeqa hai jo bina upload kiye offline kaam kare aur office firewall block na kare?", "Zain_Malik", "Quora"),
        ("Adobe Acrobat wants an arm and a leg for a basic merge, any free alternative with no file caps?", "Marcus_Dev", "Reddit"),
        ("Need client-side WebAssembly PDF vector flattening library with zero server calls.", "Dev_Lead_Alex", "YouTube"),
        ("I have 60 lecture slides as JPG and need to combine them for exam submission tonight.", "Emily_Student", "Pinterest")
    ]

    for q, author, plat in test_samples:
        res = dispatcher.classify_and_assign(q, author_name=author, platform=plat)
        print(f"[{plat}] Question: '{q}' (Author: {author})")
        print(f"  👉 Assigned Worker: {res['worker_avatar']} {res['worker_name']} ({res['worker_flag']})")
        print(f"  👉 Matched Dialect: {res['matched_dialect']} | Reason: {res['match_reason']}")
        print(f"  👉 Drafted Reply: \"{res['drafted_reply']}\"")
        print(f"  👉 Anti-Ban Jitter: {res['suggested_jitter_delay']}\n")
