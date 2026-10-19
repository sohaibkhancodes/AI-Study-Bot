# 🤖 AI Study Agent

A 24/7 cloud-hosted Telegram bot that automates university schedules, tracks attendance, and generates AI-powered performance reports.

## 🚀 Features
- **Auto Reminders:** Alerts 10 mins before class (Asia/Karachi timezone).
- **Attendance Tracking:** Inline buttons (✅/❌) to log attendance right after class.
- **AI Reports:** Uses Gemini 1.5 Flash for personalized weekly progress.
- **Cloud Hosted:** Runs persistently on PythonAnywhere.

## 🛠️ Tech Stack
Python 3 | `python-telegram-bot` | `APScheduler` | `google-generativeai` | `pytz` | JSON Database

## ⚙️ How It Works
The bot monitors the schedule in real-time to send automated alerts, logs user responses in a local JSON file, and generates AI-driven academic evaluations via the `/report` command.
