# 💊 Drug Remainder — Implementation Plan

> *"Your hydration prescription is ready."*

**Drug Remainder** is a Linux desktop extension that aggressively reminds you to drink water every 2 hours — disguised as a pharmaceutical drug reminder. Because if you won't drink water for your health, maybe you'll drink it if a robot pharmacist guilt-trips you into it.

---

## 🧠 Concept

You're chronically dehydrated. Normal "drink water" reminders don't work on you — you ignore them like terms & conditions. So we're escalating. This extension treats water like a **life-saving prescription drug** you must take on schedule. Miss a dose? Get roasted.

### The Tone
- **Sarcastic** — it judges you
- **Clinical** — talks like a pharmacist dispensing medication
- **Dramatic** — treats skipping water like a felony
- **Wholesome underneath** — actually cares about your hydration

---

## 🏗️ Architecture

```
drug_remainder/
├── implementation.md          # This file
├── drug_remainder.py          # Main daemon script
├── config.json                # User configuration (schedule, dosage, persona)
├── assets/
│   ├── icon.png               # Pill/water hybrid icon for notifications
│   └── sounds/
│       ├── pill_alert.wav     # Pharmacy-style alert chime
│       └── critical_dose.wav  # Escalation sound for missed doses
├── prescriptions.json         # All the sarcastic reminder messages
├── install.sh                 # Installer script (systemd service + autostart)
├── uninstall.sh               # Uninstaller
├── drug_remainder.service     # systemd user service file
└── README.md                  # Project README
```

---

## 📋 Features

### 1. 💊 Scheduled "Doses" (Core Reminder System)

Reminders fire at **every even hour** on the clock:

| Dose # | Time  | Label              |
|--------|-------|--------------------|
| 1      | 06:00 | Morning Primer     |
| 2      | 08:00 | Breakfast Dose     |
| 3      | 10:00 | Mid-Morning Hit    |
| 4      | 12:00 | Noon Prescription  |
| 5      | 14:00 | Afternoon Fix      |
| 6      | 16:00 | Evening Supplement |
| 7      | 18:00 | Sunset Therapy     |
| 8      | 20:00 | Night Cap Dose     |
| 9      | 22:00 | Final Dose         |

> **Configurable**: Users can adjust which hours are active in `config.json`.

### 2. 🎭 Sarcastic Prescription Messages

Each notification is randomly selected from a pool of themed messages. Categories:

#### Pharmacist Mode (Clinical)
- *"⏰ PRESCRIPTION ALERT: Your H₂O has been dispensed. Take 250ml orally. No excuses."*
- *"Dr. Hydration here. Your bloodstream called — it's running on fumes. Take your meds."*
- *"Refill notice: Your body's water reserves are critically low. Insurance doesn't cover camel mode."*
- *"This is your pharmacist speaking. Take your water. Side effects of skipping: headache, crankiness, and looking like a raisin."*

#### Guilt Trip Mode
- *"Your kidneys filed a complaint. They said, and I quote: 'We're drowning in toxins, not water.' Drink up."*
- *"Fun fact: You're 60% water. At this rate, you're down to 40%. You're becoming beef jerky."*
- *"Your houseplants get watered more consistently than you water yourself. Let that sink in."*
- *"The Sahara Desert called. It wants its hydration strategy back."*

#### Dramatic Mode
- *"🚨 CODE BLUE: Hydration levels critical. This is not a drill. DRINK. WATER. NOW."*
- *"BREAKING NEWS: Local developer found fossilized at desk. Cause of death: stubbornness and zero glasses of water."*
- *"If this were a video game, your health bar just turned red. Drink water or game over."*
- *"You are 1 skipped glass away from your blood type changing to 'dust'."*

#### Passive-Aggressive Mode
- *"Oh, you're busy? Cool. Your organs are busy too — busy shutting down. But sure, finish that one more line of code."*
- *"No pressure, but the last time you drank water, dinosaurs roamed the earth."*
- *"I'm not saying you're dehydrated, but your lips just filed for refugee status."*
- *"Remember when you said 'I'll drink water later'? That was 4 hours ago. Later is NOW."*

#### Wholesome Mode (Rare — 10% chance)
- *"Hey, you're doing great. Just a gentle reminder to drink some water. You deserve to feel good. 💙"*
- *"Proud of you for showing up today. Now show up for your body too — grab some water. 🥤"*

### 3. 🔔 Escalation System (Missed Doses)

If the user doesn't acknowledge a reminder within **15 minutes**, the system escalates:

| Level | Delay After Reminder | Action |
|-------|---------------------|--------|
| 1     | 0 min               | Normal notification with sarcastic message |
| 2     | 15 min              | Repeat notification + more aggressive message |
| 3     | 30 min              | Full-screen notification + sound alert |
| 4     | 45 min              | Desktop wallpaper changes to "DRINK WATER" meme (optional, off by default) |

### 4. 📊 Hydration Dashboard (Terminal UI)

Run `drug_remainder --stats` to see your compliance report:

```
╔══════════════════════════════════════════════╗
║        💊 DRUG REMAINDER — DAILY REPORT      ║
╠══════════════════════════════════════════════╣
║  Patient: mcrae                              ║
║  Date: 2026-10-09                            ║
║  Doses Taken: 5/9                            ║
║  Compliance Rate: 55.5%                      ║
║  Streak: 3 days                              ║
║  Status: ⚠️  MODERATE RISK                   ║
║                                              ║
║  Prescription: Increase intake immediately.  ║
║  Doctor's Note: "Disappointing but expected." ║
╚══════════════════════════════════════════════╝
```

### 5. 🏆 Achievement System

Unlock sarcastic achievements for consistency (or lack thereof):

| Achievement | Condition | Badge |
|-------------|-----------|-------|
| First Sip | Take your first dose | 🍼 |
| Hydro Homie | Complete all doses in a day | 🏆 |
| Camel Mode | Miss 3+ doses in a day | 🐪 |
| Desert Survivor | Go an entire day without acknowledging | 🏜️ |
| Streak Master | 7-day perfect compliance | 💎 |
| Relapse | Break a 3+ day streak | 💔 |
| Pharmacist's Favorite | 30-day perfect compliance | 👨‍⚕️ |

### 6. 🎵 Sound Effects (Optional)

- **Default alert**: Pharmacy counter "ding" sound
- **Escalation alert**: Hospital heart monitor beep
- **Achievement unlocked**: Pill bottle shaking sound
- **All configurable / can be disabled**

---

## 🔧 Technical Implementation

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Notifications | `notify-send` (libnotify) via `subprocess` |
| Scheduling | `schedule` library + daemon loop |
| Sound | `playsound` or `paplay` (PulseAudio) |
| Persistence | JSON file for logs & config |
| Service | systemd user service (auto-start on login) |
| CLI | `argparse` for `--stats`, `--snooze`, `--config` |

### Core Logic — `drug_remainder.py`

```python
# Pseudocode outline

class DrugRemainder:
    def __init__(self):
        self.config = load_config()
        self.prescriptions = load_prescriptions()
        self.log = load_daily_log()
    
    def dispense_dose(self, dose_number):
        """Send a notification with a random sarcastic message."""
        category = random_weighted_category()
        message = random.choice(self.prescriptions[category])
        send_notification(
            title=f"💊 Dose #{dose_number} — {self.config['dose_labels'][dose_number]}",
            body=message,
            icon="assets/icon.png",
            actions=["Take Dose", "Snooze 15min"]
        )
        self.schedule_escalation(dose_number)
    
    def schedule_escalation(self, dose_number):
        """If not acknowledged, escalate after 15 min."""
        # ... escalation logic
    
    def acknowledge_dose(self, dose_number):
        """Mark dose as taken, log it, check achievements."""
        self.log.mark_taken(dose_number)
        self.check_achievements()
    
    def run(self):
        """Main daemon loop with schedule."""
        for hour in self.config['schedule_hours']:
            schedule.every().day.at(f"{hour:02d}:00").do(
                self.dispense_dose, dose_number=hour
            )
        while True:
            schedule.run_pending()
            time.sleep(30)
```

### Notification Delivery

Uses `notify-send` for maximum Linux compatibility:

```bash
notify-send \
  --urgency=critical \
  --icon=/path/to/icon.png \
  --app-name="Drug Remainder" \
  --action="take=Take Dose" \
  --action="snooze=Snooze" \
  "💊 Dose #3 — Mid-Morning Hit" \
  "Your kidneys filed a complaint. Drink water NOW."
```

### systemd User Service — `drug_remainder.service`

```ini
[Unit]
Description=Drug Remainder — Hydration Prescription Service
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/drug_remainder/drug_remainder.py
Restart=on-failure
RestartSec=10
Environment=DISPLAY=:0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%U/bus

[Install]
WantedBy=default.target
```

### Configuration — `config.json`

```json
{
  "patient_name": "mcrae",
  "schedule_hours": [6, 8, 10, 12, 14, 16, 18, 20, 22],
  "dose_labels": {
    "6": "Morning Primer",
    "8": "Breakfast Dose",
    "10": "Mid-Morning Hit",
    "12": "Noon Prescription",
    "14": "Afternoon Fix",
    "16": "Evening Supplement",
    "18": "Sunset Therapy",
    "20": "Night Cap Dose",
    "22": "Final Dose"
  },
  "escalation_enabled": true,
  "escalation_intervals_min": [15, 30, 45],
  "sound_enabled": true,
  "wallpaper_escalation": false,
  "snooze_duration_min": 15,
  "message_weights": {
    "pharmacist": 30,
    "guilt_trip": 25,
    "dramatic": 20,
    "passive_aggressive": 15,
    "wholesome": 10
  }
}
```

---

## 📦 Installation Flow — `install.sh`

```bash
#!/bin/bash
# 1. Check dependencies (python3, notify-send, paplay)
# 2. Copy files to /opt/drug_remainder/ (or ~/.local/share/drug_remainder/)
# 3. Install Python dependencies: pip install schedule playsound
# 4. Install systemd user service
# 5. Enable and start the service
# 6. Print sarcastic welcome message:
#    "Your prescription has been filled. 
#     Drug Remainder is now monitoring your hydration.
#     Remember: water isn't optional. Neither is this service."
```

---

## 🗓️ Implementation Phases

### Phase 1 — MVP (Core Reminders)
- [ ] Set up project structure
- [ ] Create `prescriptions.json` with all message categories
- [ ] Implement `drug_remainder.py` with scheduled notifications via `notify-send`
- [ ] Create `config.json` with customizable schedule
- [ ] Test notifications on even-hour schedule
- [ ] Create `install.sh` and `drug_remainder.service`

### Phase 2 — Escalation & Acknowledgment
- [ ] Add action buttons to notifications (Take Dose / Snooze)
- [ ] Implement D-Bus listener for notification actions
- [ ] Build escalation system (Level 1–4)
- [ ] Add daily log persistence (JSON)

### Phase 3 — Stats & Achievements
- [ ] Build `--stats` terminal dashboard
- [ ] Implement achievement system
- [ ] Add streak tracking
- [ ] Create compliance reporting

### Phase 4 — Polish & Fun
- [ ] Add sound effects
- [ ] Optional wallpaper-change escalation
- [ ] Add `--roast-me` mode (continuous savage messages)
- [ ] Add `--detox` command to reset stats with a sarcastic intervention message
- [ ] Create a `--relapse` report for when you fall off the wagon

---

## 🎯 CLI Commands

```
drug_remainder                    # Start the daemon
drug_remainder --stats            # Show daily hydration report
drug_remainder --dose             # Manually log a dose
drug_remainder --snooze [min]     # Snooze current reminder
drug_remainder --roast-me         # Get an immediate roast
drug_remainder --history [days]   # Show past N days compliance
drug_remainder --achievements     # Show unlocked achievements
drug_remainder --config           # Open config in editor
drug_remainder --detox            # Reset all stats (with dramatic flair)
drug_remainder --install          # Run installation
drug_remainder --uninstall        # Remove service
```

---

## 💬 Sample Notification Flow

**10:00 AM — Dose #3 fires:**
```
┌─────────────────────────────────────────────┐
│ 💊 Drug Remainder                       ╳   │
│─────────────────────────────────────────────│
│ Dose #3 — Mid-Morning Hit                  │
│                                             │
│ "The Sahara Desert called. It wants its     │
│  hydration strategy back."                  │
│                                             │
│  [ 💊 Take Dose ]    [ ⏰ Snooze 15min ]    │
└─────────────────────────────────────────────┘
```

**10:15 AM — Escalation Level 2 (not acknowledged):**
```
┌─────────────────────────────────────────────┐
│ 🚨 Drug Remainder — MISSED DOSE        ╳   │
│─────────────────────────────────────────────│
│ ⚠️ DOSE #3 OVERDUE                         │
│                                             │
│ "Oh, you're busy? Cool. Your organs are     │
│  busy too — busy shutting down."            │
│                                             │
│  [ 💊 Take Dose NOW ]  [ 😤 Fine, 15 more ] │
└─────────────────────────────────────────────┘
```

---

## 🧪 Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| Python 3.10+ | Runtime | Pre-installed on most Linux |
| `libnotify` | Desktop notifications | `sudo apt install libnotify-bin` |
| `schedule` | Task scheduling | `pip install schedule` |
| `pulseaudio-utils` | Sound playback | `sudo apt install pulseaudio-utils` |

---

## 🤡 Easter Eggs (Bonus Ideas)

1. **"Intervention" Mode**: If you miss all doses for 3 days straight, it sends a notification titled *"We need to talk."* with a long heartfelt (but still sarcastic) message about your life choices.

2. **Random Drug Names**: Each reminder gives water a different fake pharmaceutical name:
   - *Hydrocure™*, *AquaRX*, *Waterin 500mg*, *DiHydrogen Monoxide Capsules*, *H₂O Extended Release*

3. **Fake Side Effects Warning**: Occasional messages like:
   - *"Warning: Not taking this medication may cause symptoms including: being a dried mango, keyboard face imprints, and existential crisis."*

4. **Pharmacist Voice Lines** (TTS — optional): Use `espeak` or `festival` to actually *speak* the reminder out loud:
   - *"Attention patient. Your prescription is ready for pickup at the kitchen tap."*

5. **Progress Bar in Notification**: Shows how much of your daily "prescription" you've completed:
   - `[████████░░░░░░░░] 5/9 doses — 55% compliance`

---

> *"This software is not FDA approved. But neither is your current hydration strategy."*
