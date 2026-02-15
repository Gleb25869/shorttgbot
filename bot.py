import sqlite3
import string
import random
import asyncio
import re
from datetime import datetime
from io import BytesIO
import qrcode

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    BufferedInputFile
)
from aiogram.filters import Command


TOKEN = "8430903715:AAEEH7iBocErg43XDGLhM0BdbpG163h9NXQ"
DOMAIN = "http://short.tumblersapp.ru/"

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ================= DATABASE =================

def get_connection():
    return sqlite3.connect("database.db")


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            code TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            created_at TEXT,
            clicks INTEGER DEFAULT 0
        )
        """)
        conn.commit()


def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def save_link(code, url):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO links (code, url, created_at, clicks) VALUES (?, ?, ?, 0)",
            (code, url, datetime.utcnow().isoformat())
        )
        conn.commit()


def get_clicks(code):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT clicks FROM links WHERE code=?", (code,))
        row = cursor.fetchone()
        return row[0] if row else 0


# ================= HELPERS =================

def normalize_url(url: str) -> str:
    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


def is_valid_url(url: str) -> bool:
    pattern = re.compile(
        r'^(https?:\/\/)'
        r'([\da-z\.-]+)\.'
        r'([a-z\.]{2,6})'
        r'([\/\w\.-]*)*\/?$'
    )
    return bool(pattern.match(url))


def generate_qr(url: str) -> BufferedInputFile:
    qr_img = qrcode.make(url)
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    return BufferedInputFile(buffer.getvalue(), filename="qr.png")


def build_keyboard(short_url: str, code: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Открыть", url=short_url)],
            [InlineKeyboardButton(text="📊 Статистика", callback_data=f"stats:{code}")],
            [InlineKeyboardButton(text="➕ Новая ссылка", callback_data="new")]
        ]
    )


# ================= HANDLERS =================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Отправь ссылку — я сокращу её 🚀")


@dp.message(F.text)
async def shorten(message: Message):
    raw_url = message.text.strip()
    url = normalize_url(raw_url)

    if not is_valid_url(url):
        await message.answer("❌ Пришли корректную ссылку.")
        return

    code = generate_code()
    short_url = DOMAIN + code

    try:
        save_link(code, url)
    except sqlite3.IntegrityError:
        await message.answer("Ошибка при сохранении ссылки.")
        return

    keyboard = build_keyboard(short_url, code)
    qr_photo = generate_qr(short_url)

    await message.answer_photo(
        photo=qr_photo,
        caption=f"🔗 Ваша ссылка:\n{short_url}",
        reply_markup=keyboard
    )


@dp.callback_query(F.data.startswith("stats:"))
async def stats_callback(callback: CallbackQuery):
    code = callback.data.split(":")[1]
    clicks = get_clicks(code)

    await callback.message.answer(f"📊 Кликов: {clicks}")
    await callback.answer()


@dp.callback_query(F.data == "new")
async def new_callback(callback: CallbackQuery):
    await callback.message.answer("Отправь новую ссылку 🚀")
    await callback.answer()


# ================= MAIN =================

async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())