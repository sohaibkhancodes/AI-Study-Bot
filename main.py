import json
import asyncio
from datetime import datetime
import pytz  # Naya Timezone Import
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import google.generativeai as genai

# ==========================================
# 1. API KEYS
# ==========================================
TELEGRAM_TOKEN = "YOUR_TELEGRAM_TOKEN_HERE"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

DB_FILE = "attendance.json"
CHAT_ID_FILE = "chat_id.txt"

# ==========================================
# 2. IQRA UNIVERSITY TIMETABLE (FALL 2026)
# ==========================================
TIMETABLE = {
    "mon": [
        {"subject": "Advance Database Systems Lab", "venue": "Comp Lab4", "remind_time": "08:21", "end_time": "10:05"},
        {"subject": "Compiler Construction Lab", "venue": "Comp Lab2", "remind_time": "11:00", "end_time": "14:15"},
        {"subject": "Web Engineering", "venue": "LR27", "remind_time": "15:41", "end_time": "17:55"}
    ],
    "tue": [
        {"subject": "Advance Database Management Systems", "venue": "LR28", "remind_time": "07:50", "end_time": "10:05"},
        {"subject": "Internet of Things", "venue": "LR26", "remind_time": "09:56", "end_time": "11:40"}
    ],
    "wed": [
        {"subject": "Artificial Intelligence", "venue": "LR33", "remind_time": "09:25", "end_time": "11:05"},
        {"subject": "Compiler Construction", "venue": "LR31", "remind_time": "12:31", "end_time": "14:45"}
    ],
    "thu": [
        {"subject": "Web Engineering Lab", "venue": "Comp Lab8", "remind_time": "07:50", "end_time": "11:05"},
        {"subject": "Artificial Intelligence Lab", "venue": "Comp Lab13", "remind_time": "14:40", "end_time": "17:55"}
    ],
    "fri": [
        {"subject": "HCI & Computer Graphics", "venue": "LR42", "remind_time": "09:56", "end_time": "12:10"},
        {"subject": "Internet of Things", "venue": "LR32", "remind_time": "14:40", "end_time": "16:20"},
        {"subject": "Artificial Intelligence", "venue": "LR29", "remind_time": "16:15", "end_time": "17:55"}
    ]
}

# ==========================================
# 3. DATABASE FUNCTIONS (Pakistan Time ke sath)
# ==========================================
def save_chat_id(chat_id):
    with open(CHAT_ID_FILE, "w") as f:
        f.write(str(chat_id))

def get_chat_id():
    try:
        with open(CHAT_ID_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return None

def save_attendance(subject, status):
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
    except:
        data = []
        
    pak_tz = pytz.timezone('Asia/Karachi')
    now = datetime.now(pak_tz)
    
    data.append({
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "subject": subject,
        "status": status
    })
    
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ==========================================
# 4. BOT COMMANDS & HANDLERS
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text("👋 Welcome Sohaib! I am your AI Study Agent.\nYour Fall 2026 Timetable is active and Pakistan Time is set!")

async def send_reminder(app, subject, venue):
    chat_id = get_chat_id()
    if chat_id:
        await app.bot.send_message(chat_id, f"🔔 *Class Reminder*\n\n*{subject}* in 10 mins!\n📍 Venue: *{venue}*", parse_mode='Markdown')

async def ask_attendance(app, subject):
    chat_id = get_chat_id()
    if chat_id:
        keyboard = [
            [InlineKeyboardButton("✅ Yes, Attended", callback_data=f"yes_{subject}")],
            [InlineKeyboardButton("❌ No, Missed It", callback_data=f"no_{subject}")]
        ]
        await app.bot.send_message(chat_id, f"⏰ The time for *{subject}* is over. Did you attend?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, subject = query.data.split('_', 1)
    
    status = "Present" if action == "yes" else "Absent"
    save_attendance(subject, status)
    
    icon = "✅" if action == "yes" else "❌"
    await query.edit_message_text(text=f"{icon} Attendance saved: *{subject}* -> {status}", parse_mode='Markdown')

async def test_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    keyboard = [
        [InlineKeyboardButton("✅ Yes, Attended", callback_data="yes_Test Class")],
        [InlineKeyboardButton("❌ No, Missed It", callback_data="no_Test Class")]
    ]
    await update.message.reply_text("⏰ Class is over! Did you attend?", reply_markup=InlineKeyboardMarkup(keyboard))

async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 AI is analyzing your attendance...")
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
    except:
        await update.message.reply_text("No records found yet.")
        return
        
    prompt = f"You are an AI Academic Coach for a CS student named Sohaib. Data: {data}. Give a short weekly attendance report out of 100 with feedback."
    try:
        response = model.generate_content(prompt)
        await update.message.reply_text(f"📊 *Weekly Report*\n\n{response.text}", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error in AI: {str(e)}")

# ==========================================
# 5. SCHEDULER & MAIN RUNNER
# ==========================================
async def check_schedule(app):
    pak_tz = pytz.timezone('Asia/Karachi')
    now = datetime.now(pak_tz)
    day = now.strftime("%a").lower()
    current_hm = now.strftime("%H:%M")
    
    if day in TIMETABLE:
        for item in TIMETABLE[day]:
            if item["remind_time"] == current_hm:
                await send_reminder(app, item["subject"], item["venue"])
            elif item["end_time"] == current_hm:
                await ask_attendance(app, item["subject"])

async def start_scheduler(app):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_schedule, 'cron', second=0, args=[app])
    scheduler.start()

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(start_scheduler).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_flow))
    app.add_handler(CommandHandler("report", generate_report))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is online on PythonAnywhere! Polling Telegram...")
    app.run_polling()

if __name__ == '__main__':
    main()
