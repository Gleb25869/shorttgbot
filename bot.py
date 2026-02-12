import sqlite3
import string
import random
import asyncio
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


# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS links (
        code TEXT PRIMARY KEY,
        url TEXT,
        created_at TEXT,
        clicks INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def save_link(code, url):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO links VALUES (?, ?, ?, 0)",
        (code, url, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_clicks(code):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT clicks FROM links WHERE code=?", (code,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


# ---------- START ----------
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Отправь ссылку — я сокращу её 🚀")


# ---------- SHORTEN ----------
@dp.message(F.text)
async def shorten(message: Message):
    url = message.text.strip()

    if not url.startswith("http"):
        await message.answer("Пришли корректную ссылку.")
        return

    code = generate_code()
    save_link(code, url)

    short_url = DOMAIN + code

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Открыть", url=short_url)],
            [InlineKeyboardButton(text="📊 Статистика", callback_data=f"stats:{code}")],
            [InlineKeyboardButton(text="➕ Новая ссылка", callback_data="new")]
        ]
    )

    # --- QR ---
    qr_img = qrcode.make(short_url)
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")

    photo = BufferedInputFile(
        buffer.getvalue(),
        filename="qr.png"
    )

    await message.answer_photo(
        photo=photo,
        caption=f"🔗 Ваша ссылка:\n{short_url}",
        reply_markup=keyboard
    )


# ---------- CALLBACKS ----------
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


# ---------- MAIN ----------
async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())