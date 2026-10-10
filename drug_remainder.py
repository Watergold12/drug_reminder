#!/usr/bin/env python3
import os, sys
venv_python = os.path.join(os.path.dirname(os.path.realpath(__file__)), "venv", "bin", "python3")
if sys.executable != venv_python and os.path.exists(venv_python):
    os.execl(venv_python, venv_python, *sys.argv)

"""
💊 Drug Remainder — Hydration Prescription Service
===================================================
A sarcastic Linux desktop extension that aggressively reminds you
to drink water, disguised as a pharmaceutical drug reminder.

"This software is not FDA approved. But neither is your current hydration strategy."
"""

import argparse
import json
import os
import random
import subprocess
import sys
import time
import threading
from datetime import datetime, date
from pathlib import Path

import schedule


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
PRESCRIPTIONS_PATH = BASE_DIR / "prescriptions.json"
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
ACHIEVEMENTS_FILE = DATA_DIR / "achievements.json"
ICON_PATH = BASE_DIR / "assets" / "icon.png"
SOUND_DIR = BASE_DIR / "assets" / "sounds"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def ensure_dirs():
    """Create data directories if they don't exist."""
    DATA_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)


def load_json(path: Path) -> dict:
    """Load a JSON file, returning an empty dict on failure."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_json(path: Path, data: dict):
    """Atomically save a JSON file."""
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, default=str)
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Daily Log
# ---------------------------------------------------------------------------
class DailyLog:
    """Tracks dose acknowledgements and stats for a single day."""

    def __init__(self):
        ensure_dirs()
        self.today = date.today().isoformat()
        self.path = LOG_DIR / f"{self.today}.json"
        self.data = self._load()

    def _load(self) -> dict:
        existing = load_json(self.path)
        if existing.get("date") == self.today:
            return existing
        return {
            "date": self.today,
            "doses_taken": {},       # {hour_str: timestamp}
            "doses_missed": [],      # [hour, ...]
            "escalation_levels": {}, # {hour_str: level}
            "total_taken": 0,
            "total_scheduled": 0,
        }

    def mark_taken(self, hour: int):
        """Record that a dose was taken."""
        key = str(hour)
        if key not in self.data["doses_taken"]:
            self.data["doses_taken"][key] = datetime.now().isoformat()
            self.data["total_taken"] = len(self.data["doses_taken"])
            self.save()

    def mark_scheduled(self, hour: int):
        """Record that a dose was scheduled (fired)."""
        self.data["total_scheduled"] = max(
            self.data["total_scheduled"],
            len(self.data.get("doses_taken", {})) + len(self.data.get("doses_missed", [])) + 1,
        )
        self.save()

    def set_escalation(self, hour: int, level: int):
        self.data["escalation_levels"][str(hour)] = level
        self.save()

    def is_taken(self, hour: int) -> bool:
        return str(hour) in self.data["doses_taken"]

    def save(self):
        save_json(self.path, self.data)

    def compliance_rate(self, schedule_hours: list[int]) -> float:
        """Return compliance percentage for the day."""
        now_hour = datetime.now().hour
        past_doses = [h for h in schedule_hours if h <= now_hour]
        if not past_doses:
            return 100.0
        taken = sum(1 for h in past_doses if self.is_taken(h))
        return (taken / len(past_doses)) * 100


# ---------------------------------------------------------------------------
# Achievement Tracker
# ---------------------------------------------------------------------------
class AchievementTracker:
    """Persistent achievement system with sarcastic unlocks."""

    def __init__(self, prescriptions: dict):
        ensure_dirs()
        self.definitions = prescriptions.get("achievements", {})
        self.data = load_json(ACHIEVEMENTS_FILE)
        if "unlocked" not in self.data:
            self.data = {"unlocked": {}, "streak": 0, "best_streak": 0}

    def check(self, log: DailyLog, config: dict) -> list[dict]:
        """Check for newly unlocked achievements. Returns list of new ones."""
        new = []
        hours = config["schedule_hours"]

        # First Sip
        if "first_sip" not in self.data["unlocked"] and log.data["total_taken"] >= 1:
            new.append(self._unlock("first_sip"))

        # Hydro Homie — all doses in a day
        now_hour = datetime.now().hour
        past_doses = [h for h in hours if h <= now_hour]
        if past_doses and all(log.is_taken(h) for h in past_doses):
            if len(past_doses) == len(hours) and "hydro_homie" not in self.data["unlocked"]:
                new.append(self._unlock("hydro_homie"))

        # Camel Mode — miss 3+
        missed = sum(1 for h in past_doses if not log.is_taken(h))
        if missed >= 3 and "camel_mode" not in self.data["unlocked"]:
            new.append(self._unlock("camel_mode"))

        # Desert Survivor — all missed (only at end of day)
        if now_hour >= 22 and len(past_doses) == len(hours):
            if all(not log.is_taken(h) for h in hours) and "desert_survivor" not in self.data["unlocked"]:
                new.append(self._unlock("desert_survivor"))

        # Streaks are checked at end of day by the streak updater
        return new

    def update_streak(self, log: DailyLog, config: dict):
        """Update the streak counter. Call at end of day."""
        hours = config["schedule_hours"]
        if all(log.is_taken(h) for h in hours):
            self.data["streak"] += 1
            self.data["best_streak"] = max(self.data["streak"], self.data["best_streak"])

            if self.data["streak"] >= 7 and "streak_master" not in self.data["unlocked"]:
                self._unlock("streak_master")
            if self.data["streak"] >= 30 and "pharmacists_favorite" not in self.data["unlocked"]:
                self._unlock("pharmacists_favorite")
        else:
            if self.data["streak"] >= 3 and "relapse" not in self.data["unlocked"]:
                self._unlock("relapse")
            self.data["streak"] = 0

        self.save()

    def _unlock(self, key: str) -> dict:
        defn = self.definitions.get(key, {})
        self.data["unlocked"][key] = {
            "date": datetime.now().isoformat(),
            "name": defn.get("name", key),
            "badge": defn.get("badge", "🏅"),
        }
        self.save()
        return {**defn, "key": key}

    def save(self):
        save_json(ACHIEVEMENTS_FILE, self.data)

    def get_all(self) -> list[dict]:
        """Return all achievements with their unlock status."""
        result = []
        for key, defn in self.definitions.items():
            entry = {**defn, "key": key}
            if key in self.data["unlocked"]:
                entry["unlocked"] = True
                entry["unlock_date"] = self.data["unlocked"][key]["date"]
            else:
                entry["unlocked"] = False
            result.append(entry)
        return result


# ---------------------------------------------------------------------------
# Notification System
# ---------------------------------------------------------------------------
class Notifier:
    """Send desktop notifications via notify-send."""

    @staticmethod
    def send(title: str, body: str, urgency: str = "normal",
             icon: str | None = None, actions: list[tuple[str, str]] | None = None,
             timeout_ms: int = 0) -> str | None:
        """
        Send a notification via notify-send.
        Returns the action key if the user interacts, or None.
        """
        cmd = ["notify-send"]

        # Urgency
        cmd.extend(["--urgency", urgency])

        # Icon
        if icon and Path(icon).exists():
            cmd.extend(["--icon", str(icon)])

        # App name
        cmd.extend(["--app-name", "Drug Remainder"])

        # Actions (notify-send >= 0.7.9)
        if actions:
            for key, label in actions:
                cmd.extend(["--action", f"{key}={label}"])

        # Wait for action response
        if actions:
            cmd.append("--wait")

        # Timeout
        if timeout_ms > 0:
            cmd.extend(["--expire-time", str(timeout_ms)])

        # Title and body
        cmd.extend([title, body])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # Don't hang forever
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    @staticmethod
    def send_fire_and_forget(title: str, body: str, urgency: str = "normal",
                             icon: str | None = None):
        """Send a notification without waiting for interaction."""
        cmd = ["notify-send", "--urgency", urgency, "--app-name", "Drug Remainder"]
        if icon and Path(icon).exists():
            cmd.extend(["--icon", str(icon)])
        cmd.extend([title, body])
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            print(f"[ERROR] notify-send not found. Install libnotify-bin.", file=sys.stderr)


class SoundPlayer:
    """Play alert sounds via paplay (PulseAudio/PipeWire)."""

    @staticmethod
    def play(sound_file: str):
        """Play a .wav file if it exists."""
        path = Path(sound_file)
        if not path.exists():
            return
        try:
            subprocess.Popen(
                ["paplay", str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass  # No paplay available, skip silently


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
class DrugRemainder:
    """The core hydration prescription daemon."""

    def __init__(self):
        self.config = load_json(CONFIG_PATH)
        self.prescriptions = load_json(PRESCRIPTIONS_PATH)
        self.log = DailyLog()
        self.achievements = AchievementTracker(self.prescriptions)
        self.notifier = Notifier()
        self.sound = SoundPlayer()
        self._escalation_timers: dict[int, threading.Timer] = {}

    def _pick_message(self, category: str | None = None) -> str:
        """Pick a random message using weighted category selection."""
        if category is None:
            weights = self.config.get("message_weights", {})
            categories = list(weights.keys())
            probs = list(weights.values())
            if not categories:
                categories = ["pharmacist"]
                probs = [1]
            category = random.choices(categories, weights=probs, k=1)[0]

        messages = self.prescriptions.get(category, [])
        if not messages:
            return "Drink water. Now. (Message pool empty — this is a bug AND a hydration crisis.)"
        return random.choice(messages)

    def _get_drug_name(self) -> str:
        """Get a random fake pharmaceutical name for water."""
        names = self.prescriptions.get("drug_names", ["Water"])
        return random.choice(names)

    def _maybe_side_effect(self) -> str:
        """15% chance to append a fake side effects warning."""
        if random.random() < 0.15:
            effects = self.prescriptions.get("side_effects", [])
            if effects:
                return "\n\n" + random.choice(effects)
        return ""

    def dispense_dose(self, hour: int):
        """Send a notification with a random sarcastic message."""
        # Refresh the log if the day rolled over
        if self.log.today != date.today().isoformat():
            # End-of-day streak update for yesterday
            self.achievements.update_streak(self.log, self.config)
            self.log = DailyLog()

        if self.log.is_taken(hour):
            return  # Already taken

        dose_label = self.config.get("dose_labels", {}).get(str(hour), "Scheduled Dose")
        drug_name = self._get_drug_name()
        message = self._pick_message()
        message += self._maybe_side_effect()

        title = f"💊 Dose #{hour // 2} — {dose_label}"
        body = f"[{drug_name}]\n\n{message}"

        icon = str(ICON_PATH) if ICON_PATH.exists() else None

        # Play sound if enabled
        if self.config.get("sound_enabled"):
            self.sound.play(str(SOUND_DIR / "pill_alert.wav"))

        alert_data = {
            "active": True,
            "hour": hour,
            "title": title,
            "body": body,
            "level": 1
        }
        save_json(DATA_DIR / "current_alert.json", alert_data)

        self.log.mark_scheduled(hour)

        # Schedule escalation if enabled
        if self.config.get("escalation_enabled"):
            self._schedule_escalation(hour, level=1)

    def _schedule_escalation(self, hour: int, level: int):
        """Schedule an escalation check after the configured interval."""
        intervals = self.config.get("escalation_intervals_min", [15, 30, 45])
        if level > len(intervals):
            return  # Max escalation reached

        delay_min = intervals[level - 1]
        delay_sec = delay_min * 60

        def _escalate():
            if self.log.is_taken(hour):
                return  # Acknowledged in the meantime
            self.log.set_escalation(hour, level + 1)
            self._fire_escalation(hour, level + 1, delay_min)
            self._schedule_escalation(hour, level + 1)

        # Cancel any existing timer for this hour
        if hour in self._escalation_timers:
            self._escalation_timers[hour].cancel()

        timer = threading.Timer(delay_sec, _escalate)
        timer.daemon = True
        timer.start()
        self._escalation_timers[hour] = timer

    def _fire_escalation(self, hour: int, level: int, minutes_late: int):
        """Fire an escalation notification."""
        dose_label = self.config.get("dose_labels", {}).get(str(hour), "Scheduled Dose")

        # Pick an escalation message
        esc_messages = self.prescriptions.get("escalation", [])
        if esc_messages:
            msg = random.choice(esc_messages)
            msg = msg.replace("{minutes}", str(minutes_late))
            msg = msg.replace("{level}", str(level))
        else:
            msg = self._pick_message("dramatic")

        urgency = "critical" if level >= 3 else "normal"
        title = f"🚨 MISSED DOSE — {dose_label} (Level {level})"

        icon = str(ICON_PATH) if ICON_PATH.exists() else None

        if self.config.get("sound_enabled") and level >= 2:
            self.sound.play(str(SOUND_DIR / "critical_dose.wav"))

        alert_data = {
            "active": True,
            "hour": hour,
            "title": title,
            "body": msg,
            "level": level
        }
        save_json(DATA_DIR / "current_alert.json", alert_data)

    def _snooze_dose(self, hour: int):
        """Snooze a dose reminder."""
        alert_file = DATA_DIR / "current_alert.json"
        if alert_file.exists():
            alert_file.unlink()

        snooze_min = self.config.get("snooze_duration_min", 15)
        print(f"[SNOOZE] Dose for {hour:02d}:00 snoozed for {snooze_min} minutes.")

        def _re_dispense():
            if not self.log.is_taken(hour):
                self.dispense_dose(hour)

        timer = threading.Timer(snooze_min * 60, _re_dispense)
        timer.daemon = True
        timer.start()

    def acknowledge_dose(self, hour: int):
        """Mark a dose as taken, log it, check achievements."""
        alert_file = DATA_DIR / "current_alert.json"
        if alert_file.exists():
            alert_file.unlink()

        self.log.mark_taken(hour)
        print(f"[DOSE TAKEN] {hour:02d}:00 acknowledged at {datetime.now().strftime('%H:%M:%S')}")

        # Cancel pending escalation
        if hour in self._escalation_timers:
            self._escalation_timers[hour].cancel()
            del self._escalation_timers[hour]

        # Check for new achievements
        new_achievements = self.achievements.check(self.log, self.config)
        for ach in new_achievements:
            self.notifier.send_fire_and_forget(
                title=f"🏆 Achievement Unlocked!",
                body=f"{ach.get('badge', '🏅')} {ach.get('name', 'Unknown')}\n{ach.get('description', '')}",
                urgency="low",
                icon=str(ICON_PATH) if ICON_PATH.exists() else None,
            )
            print(f"[ACHIEVEMENT] {ach.get('badge')} {ach.get('name')} unlocked!")

    # -------------------------------------------------------------------
    # CLI Commands
    # -------------------------------------------------------------------
    def show_stats(self):
        """Display the terminal hydration dashboard."""
        hours = self.config.get("schedule_hours", [])
        patient = self.config.get("patient_name", "Patient")
        today = date.today().isoformat()
        taken = self.log.data.get("total_taken", 0)
        now_hour = datetime.now().hour
        past_doses = [h for h in hours if h <= now_hour]
        total = len(past_doses) if past_doses else len(hours)
        compliance = self.log.compliance_rate(hours)
        streak = self.achievements.data.get("streak", 0)

        if compliance >= 90:
            status = "✅ EXCELLENT"
            doctor_note = '"Keep it up. I almost don\'t hate you."'
        elif compliance >= 70:
            status = "👍 GOOD"
            doctor_note = '"Acceptable. Barely."'
        elif compliance >= 50:
            status = "⚠️  MODERATE RISK"
            doctor_note = '"Disappointing but expected."'
        elif compliance >= 25:
            status = "🚨 HIGH RISK"
            doctor_note = '"I\'m not mad. Just dehydrated on your behalf."'
        else:
            status = "💀 CRITICAL"
            doctor_note = '"Are you even alive? Drink water immediately."'

        w = 50
        print()
        print(f"╔{'═' * w}╗")
        print(f"║{'💊 DRUG REMAINDER — DAILY REPORT':^{w}}║")
        print(f"╠{'═' * w}╣")
        print(f"║  Patient: {patient:<{w - 12}}║")
        print(f"║  Date: {today:<{w - 9}}║")
        print(f"║  Doses Taken: {taken}/{total:<{w - 17}}║")
        print(f"║  Compliance Rate: {compliance:>5.1f}%{' ' * (w - 25)}║")
        print(f"║  Streak: {streak} day{'s' if streak != 1 else '':<{w - 13}}║")
        print(f"║  Status: {status:<{w - 11}}║")
        print(f"║{' ' * w}║")

        # Dose timeline
        print(f"║  Timeline:{' ' * (w - 12)}║")
        timeline = "  "
        for h in hours:
            if h <= now_hour:
                if self.log.is_taken(h):
                    timeline += f"✅{h:02d} "
                else:
                    timeline += f"❌{h:02d} "
            else:
                timeline += f"⬜{h:02d} "
        print(f"║  {timeline:<{w - 4}}║")
        print(f"║{' ' * w}║")

        print(f"║  Doctor's Note: {doctor_note:<{w - 18}}║")
        print(f"╚{'═' * w}╝")
        print()

    def show_achievements(self):
        """Display all achievements and their unlock status."""
        all_ach = self.achievements.get_all()
        w = 50
        print()
        print(f"╔{'═' * w}╗")
        print(f"║{'🏆 ACHIEVEMENTS':^{w}}║")
        print(f"╠{'═' * w}╣")
        for ach in all_ach:
            badge = ach.get("badge", "🏅")
            name = ach.get("name", "Unknown")
            desc = ach.get("description", "")
            if ach.get("unlocked"):
                status = "✅"
                unlock_date = ach.get("unlock_date", "")[:10]
                line = f"  {status} {badge} {name} — {unlock_date}"
            else:
                status = "🔒"
                line = f"  {status} {badge} {name}"
            print(f"║{line:<{w}}║")
            # Description (truncated to fit)
            desc_line = f"      {desc}"
            if len(desc_line) > w:
                desc_line = desc_line[: w - 3] + "..."
            print(f"║{desc_line:<{w}}║")
        print(f"╚{'═' * w}╝")
        print()

    def show_history(self, days: int = 7):
        """Show compliance history for the past N days."""
        from datetime import timedelta

        hours = self.config.get("schedule_hours", [])
        w = 50
        print()
        print(f"╔{'═' * w}╗")
        print(f"║{'📊 HYDRATION HISTORY':^{w}}║")
        print(f"╠{'═' * w}╣")
        for i in range(days):
            d = date.today() - timedelta(days=i)
            log_path = LOG_DIR / f"{d.isoformat()}.json"
            data = load_json(log_path)
            if data:
                taken = len(data.get("doses_taken", {}))
                total = len(hours)
                pct = (taken / total * 100) if total else 0
                bar_len = 20
                filled = int(bar_len * pct / 100)
                bar = "█" * filled + "░" * (bar_len - filled)
                line = f"  {d.isoformat()}  [{bar}] {taken}/{total} ({pct:.0f}%)"
            else:
                line = f"  {d.isoformat()}  [{'░' * 20}] No data"
            print(f"║{line:<{w}}║")
        print(f"╚{'═' * w}╝")
        print()

    def roast_me(self):
        """Deliver an immediate savage roast."""
        msg = self._pick_message("dramatic")
        drug = self._get_drug_name()
        print(f"\n🔥 [{drug}] ROAST INCOMING:\n")
        print(f"   \"{msg}\"")
        self._maybe_print_side_effect()
        print()

        # Also send as notification
        alert_data = {
            "active": True,
            "hour": 99,
            "title": "🔥 ROAST — You Asked For This",
            "body": msg,
            "level": 3
        }
        save_json(DATA_DIR / "current_alert.json", alert_data)

    def _maybe_print_side_effect(self):
        effect = self._maybe_side_effect()
        if effect:
            print(f"   {effect.strip()}")

    def manual_dose(self):
        """Manually log a dose for the current hour."""
        now_hour = datetime.now().hour
        # Find the closest scheduled hour
        hours = self.config.get("schedule_hours", [])
        closest = min(hours, key=lambda h: abs(h - now_hour), default=now_hour)
        self.acknowledge_dose(closest)
        print(f"💊 Dose for {closest:02d}:00 manually logged at {datetime.now().strftime('%H:%M:%S')}.")

    def detox(self):
        """Reset all stats with dramatic flair."""
        print("\n🧹 DETOX PROTOCOL INITIATED...")
        print("   Purging all records...")
        time.sleep(0.5)
        print("   Erasing your shameful history...")
        time.sleep(0.5)
        print("   Resetting achievements...")

        # Actually reset
        self.achievements.data = {"unlocked": {}, "streak": 0, "best_streak": 0}
        self.achievements.save()

        # Clear logs
        for f in LOG_DIR.glob("*.json"):
            f.unlink()
        self.log = DailyLog()

        time.sleep(0.5)
        print("   ✅ Detox complete.")
        print()
        print('   "Every saint has a past, and every sinner has a future."')
        print("   — Oscar Wilde, probably talking about your hydration habits.")
        print()
        print("   Your prescription has been renewed. Don't waste this fresh start.")
        print()

    # -------------------------------------------------------------------
    # Daemon
    # -------------------------------------------------------------------
    def run(self):
        """Main daemon loop — schedule all doses and run forever."""
        print("💊 Drug Remainder — Hydration Prescription Service")
        print("=" * 50)
        print(f"Patient: {self.config.get('patient_name', 'Unknown')}")
        print(f"Schedule: {self.config.get('schedule_hours', [])}")
        print(f"Escalation: {'ON' if self.config.get('escalation_enabled') else 'OFF'}")
        print(f"Sound: {'ON' if self.config.get('sound_enabled') else 'OFF'}")
        print("=" * 50)
        print("Service started. Press Ctrl+C to stop.\n")

        hours = self.config.get("schedule_hours", [])
        for hour in hours:
            schedule.every().day.at(f"{hour:02d}:00").do(self.dispense_dose, hour=hour)
            print(f"  📅 Dose scheduled at {hour:02d}:00")

        print()

        # Check if we missed any doses that should have already fired today
        now_hour = datetime.now().hour
        now_min = datetime.now().minute
        for hour in hours:
            if hour < now_hour or (hour == now_hour and now_min > 0):
                if not self.log.is_taken(hour):
                    print(f"  ⚠️  Missed dose at {hour:02d}:00 — firing now")
                    self.dispense_dose(hour)

        try:
            while True:
                schedule.run_pending()

                # Refresh log at midnight
                if self.log.today != date.today().isoformat():
                    self.achievements.update_streak(self.log, self.config)
                    self.log = DailyLog()

                time.sleep(30)
        except KeyboardInterrupt:
            print("\n\n💊 Drug Remainder shutting down.")
            print('"Your prescription has been paused. But your dehydration hasn\'t."')
            print()


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        prog="drug_remainder",
        description="💊 Drug Remainder — Your sarcastic hydration prescription service.",
        epilog='"This software is not FDA approved. But neither is your current hydration strategy."',
    )

    parser.add_argument("--stats", action="store_true", help="Show daily hydration report")
    parser.add_argument("--dose", action="store_true", help="Manually log a dose")
    parser.add_argument("--snooze", type=int, nargs="?", const=15, metavar="MIN",
                        help="Snooze current reminder (default: 15 min)")
    parser.add_argument("--roast-me", action="store_true", help="Get an immediate roast")
    parser.add_argument("--history", type=int, nargs="?", const=7, metavar="DAYS",
                        help="Show past N days compliance (default: 7)")
    parser.add_argument("--achievements", action="store_true", help="Show unlocked achievements")
    parser.add_argument("--detox", action="store_true", help="Reset all stats (with dramatic flair)")
    parser.add_argument("--config", action="store_true", help="Open config in editor")
    parser.add_argument("--test-notification", action="store_true",
                        help="Send a test notification to verify setup")

    args = parser.parse_args()

    app = DrugRemainder()

    if args.stats:
        app.show_stats()
    elif args.dose:
        app.manual_dose()
    elif args.roast_me:
        app.roast_me()
    elif args.history is not None:
        app.show_history(args.history)
    elif args.achievements:
        app.show_achievements()
    elif args.detox:
        app.detox()
    elif args.config:
        editor = os.environ.get("EDITOR", "nano")
        os.execvp(editor, [editor, str(CONFIG_PATH)])
    elif args.test_notification:
        print("Sending test notification...")
        msg = app._pick_message()
        drug = app._get_drug_name()
        alert_data = {
            "active": True,
            "hour": 99,
            "title": f"💊 Drug Remainder — Test ({drug})",
            "body": msg,
            "level": 1
        }
        save_json(DATA_DIR / "current_alert.json", alert_data)
        print(f"✅ Sent! Message: \"{msg}\"")
    elif args.snooze is not None:
        print(f"⏰ Snoozing for {args.snooze} minutes...")
        alert_file = DATA_DIR / "current_alert.json"
        if alert_file.exists():
            alert_file.unlink()
        print("Alert cleared. Daemon will re-escalate automatically.")
    else:
        # No flags — start the daemon
        app.run()


if __name__ == "__main__":
    main()
