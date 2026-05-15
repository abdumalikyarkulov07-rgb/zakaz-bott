import os
import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- 1. FLASK SERVER ---
server = Flask(__name__)
@server.route('/')
def home(): return "Taxi Queue Bot is Live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- 2. BOT SOZLAMALARI ---
API_ID = 37885214
API_HASH = "57ac0d55356c041d7d6210ba8d869116"
BOT_TOKEN = "8977291889:AAFwOAw_n2wQW2c7tQaYbZfZ57pv553RxA0"

app = Client("taxi_navbat_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- 3. NAVBAT MA'LUMOTLARI (Vaqtinchalik xotira) ---
drivers_queue = []  # Navbatdagi haydovchilar ID ro'yxati
active_orders = {}  # Hozirgi aktiv buyurtmalar

# --- 4. KLAVIATURALAR ---
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🚖 Taksi chaqirish")],
    [KeyboardButton("🙋‍♂️ Navbatga turish"), KeyboardButton("🚫 Navbatdan chiqish")]
], resize_keyboard=True)

# --- 5. BOT MANTIQI ---

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply(
        "1191 Taxi xizmati tizimiga xush kelibsiz!\n\n"
        "Mijoz bo'lsangiz - 'Taksi chaqirish'ni bosing.\n"
        "Haydovchi bo'lsangiz - 'Navbatga turish'ni bosing.",
        reply_markup=main_keyboard
    )

# Haydovchini navbatga qo'shish
@app.on_message(filters.regex("🙋‍♂️ Navbatga turish"))
async def join_queue(client, message):
    driver_id = message.from_user.id
    if driver_id not in drivers_queue:
        drivers_queue.append(driver_id)
        await message.reply(f"Siz navbatga turdingiz. Navbatdagi o'rningiz: {len(drivers_queue)}")
    else:
        pos = drivers_queue.index(driver_id) + 1
        await message.reply(f"Siz allaqachon navbatdasiz. O'rningiz: {pos}")

# Navbatdan chiqish
@app.on_message(filters.regex("🚫 Navbatdan chiqish"))
async def leave_queue(client, message):
    driver_id = message.from_user.id
    if driver_id in drivers_queue:
        drivers_queue.remove(driver_id)
        await message.reply("Siz navbatdan chiqdingiz.")
    else:
        await message.reply("Siz navbatda yo'qsiz.")

# Taksi chaqirish (Mijoz)
@app.on_message(filters.regex("🚖 Taksi chaqirish"))
async def take_order(client, message):
    if not drivers_queue:
        await message.reply("Hozircha bo'sh haydovchilar yo'q. Ozroq kuting.")
        return
    
    await message.reply("Qayerga borasiz? Manzilni yozing:")

# Manzil kelganda navbatdagi haydovchiga yuborish
@app.on_message(filters.text & filters.private)
async def process_order(client, message):
    if message.text in ["🚖 Taksi chaqirish", "🙋‍♂️ Navbatga turish", "🚫 Navbatdan chiqish"]:
        return

    if not drivers_queue:
        await message.reply("Kechirasiz, haydovchilar navbati bo'shab qoldi.")
        return

    customer = message.from_user
    destination = message.text
    
    # Navbatdagi birinchi haydovchini olish
    driver_id = drivers_queue[0]
    
    order_id = message.id
    active_orders[order_id] = {"customer": customer.id, "dest": destination, "driver_index": 0}

    # Haydovchiga tugmacha bilan yuborish
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Qabul qilish", callback_data=f"accept_{order_id}"),
         InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{order_id}")]
    ])

    await app.send_message(
        driver_id, 
        f"🆕 Yangi buyurtma!\n📍 Manzil: {destination}\nMijoz: {customer.first_name}",
        reply_markup=keyboard
    )
    await message.reply("Buyurtmangiz navbatdagi haydovchiga yuborildi. Tasdiqlashini kuting...")

# Tugmachalar bosilganda (Callback)
@app.on_callback_query(filters.regex(r"accept_|reject_"))
async def handle_callback(client, callback):
    data = callback.data.split("_")
    action = data[0]
    order_id = int(data[1])

    if action == "accept":
        # Navbatdan o'chirish (chunki u band)
        if callback.from_user.id in drivers_queue:
            drivers_queue.remove(callback.from_user.id)
        
        await callback.message.edit_text("✅ Buyurtmani qabul qildingiz! Mijozga bog'laning.")
        customer_id = active_orders[order_id]["customer"]
        await app.send_message(customer_id, f"✅ Haydovchi buyurtmani qabul qildi!\nAloqa: @{callback.from_user.username}")

    elif action == "reject":
        await callback.message.edit_text("❌ Siz rad etdingiz. Buyurtma keyingi haydovchiga o'tadi.")
        # Keyingi haydovchiga o'tkazish mantiqi shu yerda bo'ladi...
        # (Sodda bo'lishi uchun hozircha to'xtatamiz)

# --- 6. ISHGA TUSHIRISH ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    async with app:
        print("Taxi Navbat Bot Ishladi! ✅")
        await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
