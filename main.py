import requests
import random
import concurrent.futures
from bs4 import BeautifulSoup
import time
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import asyncio

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F)"
]

running = False

def load_usernames():
    try:
        with open("usernames.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def save_usernames(usernames):
    with open("usernames.txt", "w") as f:
        f.write("\n".join(usernames))

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS)
    }

def send_discord_notification(username):
    data = {
        "username": "Insta Notifier",
        "embeds": [{
            "title": "UNBAND NOTICE",
            "description": "unband by sr.4",
            "color": 3066993,
            "fields": [{
                "name": "Username",
                "value": f"@{username}",
                "inline": True
            }],
            "footer": {"text": "Insta Monitor Bot"}
        }]
    }
    try:
        res = requests.post(WEBHOOK_URL, json=data)
    except Exception as e:
        print("Webhook error:", e)

def check_account(username):
    time.sleep(random.uniform(0.3, 0.8))
    url = f"https://www.instagram.com/{username}/"
    headers = get_headers()
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            meta = soup.find("meta", property="og:description")
            if meta and "Instagram" in meta.get("content", ""):
                send_discord_notification(username)
        return True
    except:
        return False

async def monitor_loop():
    global running
    while running:
        usernames = load_usernames()
        if usernames:
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                executor.map(check_account, usernames)
        await asyncio.sleep(45)

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("تشغيل", callback_data="start"),
        InlineKeyboardButton("ايقاف", callback_data="stop"),
        InlineKeyboardButton("عرض اليوزرات", callback_data="view"),
        InlineKeyboardButton("حذف الكل", callback_data="clear")
    )
    await message.reply("تحكم البوت:", reply_markup=kb)

@dp.callback_query_handler(lambda c: True)
async def callback_handler(callback_query: types.CallbackQuery):
    global running
    if callback_query.from_user.id != OWNER_ID:
        return
    data = callback_query.data
    if data == "start":
        if not running:
            running = True
            asyncio.create_task(monitor_loop())
            await callback_query.message.answer("تم التشغيل.")
        else:
            await callback_query.message.answer("يعمل بالفعل.")
    elif data == "stop":
        running = False
        await callback_query.message.answer("تم الإيقاف.")
    elif data == "view":
        usernames = load_usernames()
        if usernames:
            await callback_query.message.answer("\n".join(usernames))
        else:
            await callback_query.message.answer("لا توجد يوزرات.")
    elif data == "clear":
        save_usernames([])
        await callback_query.message.answer("تم حذف جميع اليوزرات.")

@dp.message_handler(lambda m: m.from_user.id == OWNER_ID)
async def handle_usernames(message: types.Message):
    text = message.text.strip()
    if text:
        usernames = load_usernames()
        if text in usernames:
            await message.reply("اليوزر موجود بالفعل.")
        else:
            usernames.append(text)
            save_usernames(usernames)
            await message.reply("تمت الإضافة.")

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp)
