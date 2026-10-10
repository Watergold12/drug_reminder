# 💊 Drug Remainder

> *"Your hydration prescription is ready."*

**Drug Remainder** is a Linux desktop extension that aggressively reminds you to drink water every 2 hours — disguised as a pharmaceutical drug reminder. Because if you won't drink water for your health, maybe you'll drink it if a robot pharmacist guilt-trips you into it.

## Features

- 💊 **Scheduled Doses** — Notifications fire at every even hour (06:00–22:00)
- 🎭 **Sarcastic Messages** — 5 categories: Pharmacist, Guilt Trip, Dramatic, Passive-Aggressive, and Wholesome
- 🔔 **Escalation System** — Missed doses get increasingly aggressive reminders
- 📊 **Terminal Dashboard** — View your compliance stats with `--stats`
- 🏆 **Achievement System** — Unlock sarcastic achievements (or shameful ones)
- 🎵 **Sound Effects** — Pharmacy-style chimes and hospital beeps
- 💊 **Fake Drug Names** — Water gets a new pharmaceutical name each time

## Quick Start

```bash
# 1. Install
./install.sh

# 2. Test that notifications work
./drug_remainder.py --test-notification

# 3. Get roasted immediately
./drug_remainder.py --roast-me

# 4. Check your stats
./drug_remainder.py --stats
```

## CLI Commands

```
drug_remainder.py                     # Start the daemon
drug_remainder.py --stats             # Show daily hydration report
drug_remainder.py --dose              # Manually log a dose
drug_remainder.py --snooze [min]      # Snooze current reminder
drug_remainder.py --roast-me          # Get an immediate roast
drug_remainder.py --history [days]    # Show past N days compliance
drug_remainder.py --achievements      # Show unlocked achievements
drug_remainder.py --config            # Open config in editor
drug_remainder.py --detox             # Reset all stats (with dramatic flair)
drug_remainder.py --test-notification # Send a test notification
```

## Configuration

Edit `config.json` to customize:

- **schedule_hours** — Which hours to fire reminders
- **dose_labels** — Custom names for each dose
- **escalation_enabled** — Toggle the escalation system
- **sound_enabled** — Toggle sound effects
- **message_weights** — Adjust probability of each message category
- **snooze_duration_min** — Default snooze duration

## Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| Python 3.10+ | Runtime | Pre-installed on most Linux |
| `libnotify` | Desktop notifications | `sudo apt install libnotify-bin` |
| `schedule` | Task scheduling | `pip install schedule` (in venv) |
| `pulseaudio-utils` | Sound playback | `sudo apt install pulseaudio-utils` |

## How It Works

The daemon runs as a **systemd user service** that:

1. Schedules notifications at every configured hour
2. Sends desktop notifications with random sarcastic messages
3. If you don't acknowledge within 15 minutes, it escalates
4. Tracks your compliance in daily JSON log files
5. Awards (or shames you with) achievements

## Project Structure

```
drug_remainder/
├── drug_remainder.py          # Main daemon script
├── config.json                # User configuration
├── prescriptions.json         # All the sarcastic messages
├── assets/
│   ├── icon.png               # Notification icon
│   └── sounds/
│       ├── pill_alert.wav     # Pharmacy-style chime
│       └── critical_dose.wav  # Escalation beep
├── data/
│   └── logs/                  # Daily compliance logs
├── install.sh                 # Installer
├── uninstall.sh               # Uninstaller
├── drug_remainder.service     # systemd user service file
└── README.md                  # This file
```

## Uninstall

```bash
./uninstall.sh
```

---

> *"This software is not FDA approved. But neither is your current hydration strategy."*
