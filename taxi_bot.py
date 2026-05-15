import os
import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton

# --- 1. FLASK SERVER (Render uchun) ---
server = Flask(__name__)
@server.route('/')
def home(): return "Taxi Bot is Live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- 2. BOT SOZLAMALARI ---
API_ID = 37885214
API_HASH = "57ac0d55356c041d7d6210ba8d869116"
BOT_TOKEN = "8977291889:AAFwOAw_n2wQW2c7tQaYbZfZ57pv553RxA0"

# Haydovchilar guruhi ID-si (Shu yerga haydovchilar qo'shilgan guruh ID-sini yozing)
# Masalan: -100123456789
DRIVER_GROUP_ID = -5115669498 # O'zingizni guruh ID-ngizga almashtiring

app = Client("taxi_bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- 3. KLAVIATURALAR ---
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🚖 Taksi chaqirish")],
    [KeyboardButton("📋 Mening buyurtmalarim"), KeyboardButton("✍️ Bog'lanish")]
], resize_keyboard=True)

# --- 4. BOT MANTIQI ---

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply(
        f"Assalomu alaykum, {message.from_user.first_name}!\n"
        "1191 Taxi xizmatiga xush kelibsiz. Taksi kerak bo'lsa tugmani bosing.",
        reply_markup=main_keyboard
    )

@app.on_message(filters.regex("🚖 Taksi chaqirish") & filters.private)
async def ask_location(client, message):
    await message.reply("Iltimos, qayerga borishingizni yozing (Masalan: Chorsu bozori):")

@app.on_message(filters.text & filters.private)
async def handle_order(client, message):
    # Agar bu start yoki boshqa komanda bo'lmasa, buyurtma deb qabul qilamiz
    if message.text in ["🚖 Taksi chaqirish", "📋 Mening buyurtmalarim", "✍️ Bog'lanish"]:
        return

    user = message.from_user
    destination = message.text
    
    # Haydovchilar guruhiga yuboriladigan xabar
    order_text = (
        "🆕 **Yangi buyurtma!**\n\n"
        f"👤 **Mijoz:** {user.first_name}\n"
        f"📍 **Manzil:** {destination}\n"
        f"📞 **Aloqa:** [{user.id}](tg://user?id={user.id})\n\n"
        "Haydovchilar, buyurtmani qabul qilish uchun mijozga yozing!"
    )

    # Guruhga yuborish
    try:
        await app.send_message(DRIVER_GROUP_ID, order_text)
        await message.reply("✅ Buyurtmangiz haydovchilarga yuborildi! Tez orada siz bilan bog'lanishadi.")
    except Exception as e:
        await message.reply("⚠️ Xatolik: Haydovchilar guruhi topilmadi. Botni guruhga qo'shing va ID-ni to'g'rilang.")
        print(f"Guruhga yuborishda xato: {e}")

# --- 5. ISHGA TUSHIRISH ---
async def start_services():
    threading.Thread(target=run_flask, daemon=True).start()
    async with app:
        print("Bot LIVE holatga o'tdi! ✅")
        await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_services())
