# main.py
from flask import Flask, request, jsonify
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import time
import secrets
from datetime import datetime, timedelta
import threading

app = Flask(__name__)

# 🤖 TOKENS & CONFIG (Shivams Ultimate System)
TELEGRAM_BOT_TOKEN = "8758245872:AAFFsG53k-ljzF-j9dTxaszCRKfixxU6crA"
ADMIN_CHAT_ID = 8655103281
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

KEYS_FILE = "keys_db.json"
MASTER_DATABASE_CACHE = {}
DB_INITIALIZED = False

def load_keys_from_storage():
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, 'r') as f: return json.load(f)
        except Exception: pass
    return {
        "SHIVAM_FREE_TEST": {
            "total_limit": 5000, "used": 0, "expiry_date": "2030-12-31"
        }
    }

API_KEYS_DB = load_keys_from_storage()

def save_keys_to_storage():
    try:
        with open(KEYS_FILE, 'w') as f: json.dump(API_KEYS_DB, f, indent=4)
    except Exception: pass

# 🔄 Anti-Crash Smart Database Loader
def load_all_databases_bg():
    global MASTER_DATABASE_CACHE, DB_INITIALIZED
    
    # Render ko boot up hone ke liye pehle 15 seconds ka time do (Taaki health check pass ho jaye)
    print("[SYSTEM] Holding DB Sync for 15s to bypass Render Health Check...", flush=True)
    time.sleep(15)
    
    print("[SYSTEM] Smart Background Database Sync Started...", flush=True)
    BASE_GITHUB_URL = "https://raw.githubusercontent.com/shivamg1110/tg-database/main/Telegram_27_part{}.json"
    
    for i in range(1, 51):
        url = BASE_GITHUB_URL.format(i)
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                part_data = response.json()
                for row in part_data:
                    u_id = str(row.get('user_id'))
                    if u_id:
                        MASTER_DATABASE_CACHE[u_id] = row
                print(f"[SUCCESS] Part {i} integrated into memory.", flush=True)
            elif response.status_code == 404:
                continue
        except Exception as e:
            print(f"[EXCEPTION] Part {i} error: {str(e)}", flush=True)
        
        # 💤 CPU aur Network ko thoda aaram do taaki Flask live rahe
        time.sleep(1)
            
    DB_INITIALIZED = True
    print(f"🎉 [COMPLETE] Total records in memory: {len(MASTER_DATABASE_CACHE)}", flush=True)

# ==================== 🌐 FLASK API GATEWAY ====================

@app.route('/')
def home():
    return "<h1>ICMR API Gateway V7 (Key Gen System Active) is Live!</h1>"

@app.route('/api', methods=['GET'])
def get_data():
    global MASTER_DATABASE_CACHE, DB_INITIALIZED
    search_query = request.args.get('id')
    user_api_key = request.args.get('key')

    if not search_query or not user_api_key:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400
    if user_api_key not in API_KEYS_DB:
        return jsonify({"status": "error", "message": "Invalid API Key"}), 401

    key_info = API_KEYS_DB[user_api_key]
    current_date = datetime.now().strftime('%Y-%m-%d')

    if current_date > key_info["expiry_date"]:
        return jsonify({"status": "error", "message": "API Key has expired!"}), 403
    if key_info["used"] >= key_info["total_limit"]:
        return jsonify({"status": "error", "message": "API Key plan limit reached!"}), 403
    if not DB_INITIALIZED and len(MASTER_DATABASE_CACHE) == 0:
        return jsonify({"status": "error", "message": "Database is initializing. Please retry in a moment."}), 503

    user_record = MASTER_DATABASE_CACHE.get(str(search_query))
    if user_record:
        key_info["used"] += 1
        save_keys_to_storage()
        return jsonify({
            "status": "success",
            "developer": "@Dark_soul_x1",
            "remaining_limits": key_info["total_limit"] - key_info["used"],
            "expiry_date": key_info["expiry_date"],
            "data": user_record
        }), 200
                
    return jsonify({"status": "error", "message": "Requested User ID not found."}), 404

# ==================== 🤖 TELEGRAM BOT LOGIC ====================

def main_menu_keyboard(is_admin=False):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("📋 Check Key Status", callback_data="check_status"),
        InlineKeyboardButton("👨‍💻 Contact Developer", callback_data="contact_dev")
    )
    if is_admin:
        markup.add(InlineKeyboardButton("🛠️ Admin Panel (Generate Key)", callback_data="admin_panel"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    is_admin = (message.chat.id == ADMIN_CHAT_ID)
    welcome_text = "📊 *Welcome to ICMR Secure User-ID Portal*\n\n⚙️ *Status:* Active\n💻 *Dev:* @Dark_soul_x1"
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=main_menu_keyboard(is_admin))

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    is_admin = (call.message.chat.id == ADMIN_CHAT_ID)
    
    if call.data == "contact_dev":
        bot.send_message(call.message.chat.id, "👨‍💻 *Official System Developer:* @Dark_soul_x1", parse_mode="Markdown")
    elif call.data == "check_status":
        msg = bot.send_message(call.message.chat.id, "🗝️ Please send your API Key to check validation:")
        bot.register_next_step_handler(msg, process_key_status_check)
    elif call.data == "admin_panel":
        if not is_admin: return
        admin_markup = InlineKeyboardMarkup()
        admin_markup.add(
            InlineKeyboardButton("✨ Plan A (100 Req)", callback_data="gen_plan_a"),
            InlineKeyboardButton("🔥 Plan B (1000 Req)", callback_data="gen_plan_b"),
            InlineKeyboardButton("⬅️ Back Menu", callback_data="back_main")
        )
        bot.edit_message_text("🛠️ *Admin Key Generator Panel*:", call.message.chat.id, call.message.message_id, reply_markup=admin_markup)
    elif call.data == "back_main":
        bot.edit_message_text("Select an option from below:", call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard(is_admin))
    elif call.data.startswith("gen_plan_"):
        if not is_admin: return
        limit = 100 if call.data == "gen_plan_a" else 1000
        new_key = f"sk_{secrets.token_hex(6)}"
        expiry_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        API_KEYS_DB[new_key] = {"total_limit": limit, "used": 0, "expiry_date": expiry_date}
        save_keys_to_storage()
        bot.send_message(call.message.chat.id, f"✅ *Key Generated!*\n\n🗝️ *Key:* `{new_key}`\n📊 *Limit:* {limit}\n📅 *Expiry:* {expiry_date}", parse_mode="Markdown")

def process_key_status_check(message):
    key = message.text.strip()
    if key not in API_KEYS_DB:
        bot.reply_to(message, "❌ Invalid Key!")
        return
    info = API_KEYS_DB[key]
    bot.reply_to(message, f"🗝️ *Token:* `{key}`\n📈 *Usage:* {info['used']} / {info['total_limit']}\n⏳ *Expires:* {info['expiry_date']}", parse_mode="Markdown")

def run_bot_loop():
    # Bot ko thoda ruk ke chalayenge taaki startup clear ho sake
    time.sleep(5)
    print("[SYSTEM] Bot Polling Thread Started...", flush=True)
    while True:
        try:
            bot.polling(none_stop=True, interval=3, timeout=30)
        except Exception as e:
            print(f"[BOT RESTART] Restarting loop... Error: {e}", flush=True)
            time.sleep(5)

# Threads Gateway
threading.Thread(target=load_all_databases_bg, daemon=True).start()
threading.Thread(target=run_bot_loop, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)
