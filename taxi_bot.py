import os
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton
)

# --- RENDER UCHUN SERVER ---
server = Flask(__name__)
@server.route('/')
def home(): return "Bot 24/7 ishlamoqda!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- SOZLAMALARI ---
API_ID = 37885214
API_HASH = "57ac0d55356c041d7d6210ba8d869116"
BOT_TOKEN = "8977291889:AAFwOAw_n2wQW2c7tQaYbZfZ57pv553RxA0"
HAYDOVCHILAR_GURUHI = -5115669498 # Bu yerga navbat ro'yxati chiqadi

app = Client("taxi_final_v1", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- MA'LUMOTLAR ---
navbat_list = []  # [{"id": 123, "name": "Ali"}]
active_orders = {} # {customer_id: {"text": "...", "driver_index": 0}}

def get_navbat_text():
    if not navbat_list:
        return "🚕 **NAVBAТDAGI HAYDOVCHILAR:**\n\nNavbat hozircha bo'sh."
    text = "🚕 **NAVBAТDAGI HAYDOVCHILAR:**\n\n"
    for i, driver in enumerate(navbat_list, 1):
        status = "♻️ " if i == 1 else ""
        text += f"{i}. {status}{driver['name']}\n"
    return text

# --- KLAVIATURALAR ---
main_kb = ReplyKeyboardMarkup([
    [KeyboardButton("🚕 Taxi buyurtma berish")],
    [KeyboardButton("➕ Navbatga turish"), KeyboardButton("➖ Chiqish")]
], resize_keyboard=True)

# --- 1. GURUHDA NAVBATNI KO'RSATISH ---
@app.on_message(filters.command("navbat") & filters.group)
async def show_queue_group(client, message):
    await message.reply(get_navbat_text())

# --- 2. HAYDOVCHI NAVBATGA TURISHI (BOTDA) ---
@app.on_message(filters.regex("➕ Navbatga turish") & filters.private)
async def join_queue(client, message):
    user_id = message.from_user.id
    if any(d['id'] == user_id for d in navbat_list):
        await message.reply("Siz allaqachon navbatdasiz!")
    else:
        navbat_list.append({"id": user_id, "name": message.from_user.first_name})
        await message.reply(f"Siz navbatga turdingiz. O'rningiz: {len(navbat_list)}")
        # Guruhga yangilangan navbatni yuborish
        await client.send_message(HAYDOVCHILAR_GURUHI, get_navbat_text())

@app.on_message(filters.regex("➖ Chiqish") & filters.private)
async def leave_queue(client, message):
    global navbat_list
    navbat_list = [d for d in navbat_list if d['id'] != message.from_user.id]
    await message.reply("Siz navbatdan chiqdingiz.")
    await client.send_message(HAYDOVCHILAR_GURUHI, get_navbat_text())

# --- 3. MIJOZ BUYURTMA BERISHI (BOTDA) ---
@app.on_message(filters.regex("🚕 Taxi buyurtma berish") & filters.private)
async def start_order(client, message):
    if not navbat_list:
        await message.reply("Hozircha bo'sh haydovchilar yo'q.")
        return
    await message.reply("Qayerga borasiz va telefon raqamingizni yozing:")

@app.on_message(filters.private & ~filters.command("start") & ~filters.regex("Navbatga|Chiqish|Taxi"))
async def process_order(client, message):
    customer_id = message.from_user.id
    active_orders[customer_id] = {"text": message.text, "driver_index": 0}
    await send_order_to_driver(client, customer_id)
    await message.reply("✅ Buyurtmangiz navbatdagi haydovchiga yuborildi.")

async def send_order_to_driver(client, customer_id):
    order = active_orders.get(customer_id)
    if not order or order["driver_index"] >= len(navbat_list):
        await client.send_message(customer_id, "Kechirasiz, barcha haydovchilar rad etishdi.")
        return

    driver_id = navbat_list[order["driver_index"]]["id"]
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Qabul qilish", callback_data=f"acc_{customer_id}"),
         InlineKeyboardButton("❌ Rad etish", callback_data=f"rej_{customer_id}")]
    ])
    try:
        await client.send_message(driver_id, f"🆕 **YANGI BUYURTMA!**\n\n📝: {order['text']}", reply_markup=buttons)
    except:
        order["driver_index"] += 1
        await send_order_to_driver(client, customer_id)

# --- 4. QABUL QILISH VA RAD ETISH (BOTDA) ---
@app.on_callback_query()
async def handle_callback(client, callback):
    data = callback.data
    customer_id = int(data.split("_")[1])
    
    if data.startswith("acc_"):
        # Haydovchini navbatdan o'chirish
        global navbat_list
        navbat_list = [d for d in navbat_list if d['id'] != callback.from_user.id]
        
        await callback.message.edit_text("✅ Buyurtmani qabul qildingiz!")
        await client.send_message(customer_id, f"✅ Haydovchi topildi: {callback.from_user.first_name}")
        # Guruhda navbatni yangilash
        await client.send_message(HAYDOVCHILAR_GURUHI, f"🔔 Buyurtma olindi!\nYangilangan navbat:\n\n{get_navbat_text()}")
        
    elif data.startswith("rej_"):
        await callback.message.edit_text("❌ Siz rad etdingiz.")
        active_orders[customer_id]["driver_index"] += 1
        await send_order_to_driver(client, customer_id)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app.run()
