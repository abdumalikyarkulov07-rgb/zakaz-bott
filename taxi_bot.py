import os
import threading
import asyncio
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton
)

# --- RENDER UCHUN VEB SERVER (PING UCHUN) ---
server = Flask(__name__)

@server.route('/')
def home():
    return "Bot 24/7 rejimida ishlamoqda!"

def run_flask():
    # Render avtomatik PORT beradi, agar bermasa 8080 ishlatiladi
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- BOT SOZLAMALARI ---
API_ID = 37885214
API_HASH = "57ac0d55356c041d7d6210ba8d869116"
BOT_TOKEN = "8977291889:AAFwOAw_n2wQW2c7tQaYbZfZ57pv553RxA0"
HAYDOVCHILAR_GURUHI = -5115669498
ADMIN_USERNAME = "N1toshkenchi"

app = Client("zakaz_bot_render", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Ma'lumotlar bazasi (vaqtinchalik xotira)
navbat_list = []
user_temp_data = {}

def get_navbat_text():
    """Navbat ro'yxatini rasmga moslab chiqarish"""
    if not navbat_list:
        return "🚕 **NAVBAТDAGI HAYDOVCHILAR:**\n\nNavbat hozircha bo'sh."
    
    text = "🚕 **NAVBAТDAGI HAYDOVCHILAR:**\n\n"
    for i, driver in enumerate(navbat_list, 1):
        status = "♻️ " if i == 1 else ""
        text += f"{i}. {status}{driver['name']}\n"
    return text

# --- MIJOZLAR UCHUN HANDLERLAR ---
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    await message.reply(
        "Assalomu alaykum! **Zakaz Bot** xizmatiga xush kelibsiz.\n\n"
        "Taxi buyurtma berish uchun pastdagi tugmani bosing:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("🚕 Taxi buyurtma berish")]],
            resize_keyboard=True
        )
    )

@app.on_message(filters.regex("🚕 Taxi buyurtma berish") & filters.private)
async def ask_order(client, message):
    user_temp_data[message.from_user.id] = True
    await message.reply("Qayerga borasiz va telefon raqamingizni yozing:")

@app.on_message(filters.private & ~filters.command("start"))
async def process_order(client, message):
    user_id = message.from_user.id
    if user_id in user_temp_data:
        order_text = message.text
        user_name = message.from_user.first_name
        next_driver = navbat_list[0]['name'] if navbat_list else "Hech kim yo'q"
        
        caption = (
            f"🛎 **YANGI BUYURTMA!**\n\n"
            f"👤 Mijoz: {user_name}\n"
            f"📝 XABAR: {order_text}\n\n"
            f"👉 **NAVBAТDAGI HAYDOVCHI:** {next_driver}"
        )
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Oldim (Navbatdan chiqish)", callback_data=f"done_{user_id}")],
            [InlineKeyboardButton("💬 Mijozga xabar", callback_data=f"ms_{user_id}")]
        ])
        
        await client.send_message(HAYDOVCHILAR_GURUHI, caption, reply_markup=buttons)
        await message.reply("✅ Buyurtmangiz haydovchilarga yuborildi.")
        del user_temp_data[user_id]

# --- GURUH VA NAVBAT HANDLERLARI ---
@app.on_message(filters.command("navbat") & filters.group)
async def show_queue(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Navbatga turish", callback_data="join"),
         InlineKeyboardButton("➖ Chiqish", callback_data="leave")]
    ])
    await message.reply(get_navbat_text(), reply_markup=buttons)

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.first_name

    if data == "join":
        if any(d['id'] == user_id for d in navbat_list):
            await callback_query.answer("Siz allaqachon navbatdasiz!", show_alert=True)
        else:
            navbat_list.append({"id": user_id, "name": user_name})
            await callback_query.edit_message_text(get_navbat_text(), reply_markup=callback_query.message.reply_markup)

    elif data == "leave":
        for i, driver in enumerate(navbat_list):
            if driver['id'] == user_id:
                navbat_list.pop(i)
                await callback_query.edit_message_text(get_navbat_text(), reply_markup=callback_query.message.reply_markup)
                return
        await callback_query.answer("Siz ro'yxatda yo'qsiz.")

    elif data.startswith("done_"):
        for i, driver in enumerate(navbat_list):
            if driver['id'] == user_id:
                navbat_list.pop(i)
                break
        await callback_query.edit_message_text(callback_query.message.text + f"\n\n🚕 **Qabul qildi:** {user_name}", reply_markup=None)

    elif data.startswith("ms_"):
        try:
            target_id = int(data.split("_")[1])
            driver_user = f"@{callback_query.from_user.username}" if callback_query.from_user.username else "Username yo'q"
            await client.send_message(target_id, f"🚖 **Sizga haydovchi topildi!**\n\nIsmi: {user_name}\nAloqa: {driver_user}")
            await callback_query.answer("Mijozga xabar yuborildi!", show_alert=True)
        except:
            await callback_query.answer("Xato: Mijoz botni bloklagan.")

# --- ISHGA TUSHIRISH (MAIN) ---
if __name__ == "__main__":
    # 1. Flask veb-serverni alohida oqimda (thread) daemon rejimida boshlaymiz
    threading.Thread(target=run_flask, daemon=True).start()
    print("Veb server port tinglashni boshladi...")

    # 2. Pyrogram uchun asinxron event loopni olib, botni ishga tushiramiz
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run())
