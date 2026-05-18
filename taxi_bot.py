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

# --- SERVER ---
server = Flask(__name__)
@server.route('/')
def home(): return "Taxi Bot 24/7 Live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- BOT SOZLAMALARI ---
API_ID = 37885214
API_HASH = "57ac0d55356c041d7d6210ba8d869116"
BOT_TOKEN = "8977291889:AAFwOAw_n2wQW2c7tQaYbZfZ57pv553RxA0"
HAYDOVCHILAR_GURUHI = -5115669498 

app = Client("taxi_professional", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- MA'LUMOTLAR ---
navbat_list = []  # [{"id": 123, "name": "Ali"}]
active_orders = {} # {customer_id: {"text": "...", "driver_index": 0}}
waiting_for_address = set() # Faqat manzil kutayotgan mijozlar ID-si

# --- KLAVIATURALAR ---
main_kb = ReplyKeyboardMarkup([
    [KeyboardButton("🚕 Taxi buyurtma berish")],
    [KeyboardButton("➕ Navbatga turish"), KeyboardButton("➖ Chiqish")]
], resize_keyboard=True)

# --- FUNKSIYALAR ---
async def send_to_next_driver(client, customer_id):
    order = active_orders.get(customer_id)
    if not order or order["driver_index"] >= len(navbat_list):
        await client.send_message(customer_id, "😔 Kechirasiz, barcha haydovchilar band yoki rad etishdi.")
        active_orders.pop(customer_id, None)
        return

    driver = navbat_list[order["driver_index"]]
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Qabul qilish", callback_data=f"acc_{customer_id}"),
         InlineKeyboardButton("❌ Rad etish", callback_data=f"rej_{customer_id}")]
    ])
    
    try:
        await client.send_message(
            driver["id"], 
            f"🆕 **YANGI BUYURTMA!**\n\n📍 Manzil: {order['text']}\n\nQabul qilasizmi?",
            reply_markup=buttons
        )
    except:
        order["driver_index"] += 1
        await send_to_next_driver(client, customer_id)

# --- HANDLERLAR ---

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    waiting_for_address.discard(message.from_user.id) # Start bosilganda barcha kutishni bekor qilish
    await message.reply("Xush kelibsiz! Taxi xizmati botiga o'z xizmatingizni boshlang.", reply_markup=main_kb)

@app.on_message(filters.regex("➕ Navbatga turish") & filters.private)
async def join(client, message):
    user_id = message.from_user.id
    if not any(d['id'] == user_id for d in navbat_list):
        navbat_list.append({"id": user_id, "name": message.from_user.first_name})
        await message.reply(f"Siz navbatga turdingiz. O'rningiz: {len(navbat_list)}")
    else:
        await message.reply("Siz allaqachon navbatdasiz.")

@app.on_message(filters.regex("➖ Chiqish") & filters.private)
async def leave(client, message):
    global navbat_list
    navbat_list = [d for d in navbat_list if d['id'] != message.from_user.id]
    await message.reply("Siz navbatdan chiqdingiz.")

@app.on_message(filters.regex("🚕 Taxi buyurtma berish") & filters.private)
async def order_start(client, message):
    if not navbat_list:
        return await message.reply("Hozircha bo'sh haydovchilar yo'q.")
    
    waiting_for_address.add(message.from_user.id) # Mijozni kutish ro'yxatiga qo'shish
    await message.reply("📍 Qayerga borishingizni va telefon raqamingizni bitta xabarda yozing:")

# FAQAT MANZIL KUTILAYOTGAN MIJOZLAR UCHUN FILTR
@app.on_message(filters.private & ~filters.command("start"))
async def handle_text(client, message):
    user_id = message.from_user.id
    
    # Agar mijoz oldin "Taxi buyurtma berish" tugmasini bosgan bo'lsa
    if user_id in waiting_for_address:
        if message.text in ["➕ Navbatga turish", "➖ Chiqish", "🚕 Taxi buyurtma berish"]:
            return # Tugmalarni manzil deb qabul qilmaymiz

        active_orders[user_id] = {"text": message.text, "driver_index": 0}
        waiting_for_address.remove(user_id) # Kutish ro'yxatidan o'chirish
        
        await message.reply("✅ Buyurtmangiz qabul qilindi. Haydovchi javobini kuting...")
        await send_to_next_driver(client, user_id)

@app.on_callback_query()
async def callbacks(client, callback):
    data = callback.data
    driver_id = callback.from_user.id
    try:
        customer_id = int(data.split("_")[1])
    except: return

    if data.startswith("acc_"):
        if customer_id not in active_orders:
            return await callback.answer("Bu buyurtma allaqachon olingan.", show_alert=True)
            
        order_text = active_orders[customer_id]['text']
        await callback.message.edit_text(f"✅ Qabul qildingiz!\n📍 Manzil: {order_text}")
        await client.send_message(customer_id, f"✅ Haydovchi buyurtmani qabul qildi!\nAloqa: @{callback.from_user.username}")
        
        global navbat_list
        navbat_list = [d for d in navbat_list if d['id'] != driver_id]
        active_orders.pop(customer_id, None)
    
    elif data.startswith("rej_"):
        await callback.message.edit_text("❌ Rad etildi.")
        if customer_id in active_orders:
            active_orders[customer_id]["driver_index"] += 1
            await send_to_next_driver(client, customer_id)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app.run()
