# main.py
from flask import Flask, request, jsonify
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
from datetime import datetime
import threading

app = Flask(__name__)

# 🤖 TOKENS & CONFIG
TELEGRAM_BOT_TOKEN = "8758245872:AAFFsG53k-ljzF-j9dTxaszCRKfixxU6crA"
ADMIN_CHAT_ID = 8655103281
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

MASTER_DATABASE_CACHE = {}
DB_INITIALIZED = False
API_KEYS_DB = {
    "SHIVAM_FREE_TEST": {
        "total_limit": 5000, 
        "used": 0, 
        "expiry_date": "2030-12-31"
    }
}

# Optimized Sync Mechanism
def load_all_databases_bg():
    global MASTER_DATABASE_CACHE, DB_INITIALIZED
    print("[SYSTEM] Background Database Sync Started...", flush=True)
    BASE_GITHUB_URL = "https://raw.githubusercontent.com/shivamg1110/tg-database/main/Telegram_27_part{}.json"
    
    for i in range(1, 51):
        url = BASE_GITHUB_URL.format(i)
        try:
            response = requests.get(url, timeout=15)
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
            
    DB_INITIALIZED = True
    print(f"🎉 [COMPLETE] Total records in memory: {len(MASTER_DATABASE_CACHE)}", flush=True)

@app.route('/')
def home():
    return "<h1>ICMR API Gateway is Live & Running!</h1>"

@app.route('/api', methods=['GET'])
def get_data():
    global MASTER_DATABASE_CACHE, DB_INITIALIZED
    search_query = request.args.get('id')
    user_api_key = request.args.get('key')

    if not search_query or not user_api_key:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400
    if user_api_key not in API_KEYS_DB:
        return jsonify({"status": "error", "message": "Invalid API Key"}), 401
    if not DB_INITIALIZED:
        return jsonify({"status": "error", "message": "Database is still syncing in background. Please wait 1-2 minutes."}), 503

    user_record = MASTER_DATABASE_CACHE.get(str(search_query))
    if user_record:
        return jsonify({
            "status": "success",
            "developer": "@Dark_soul_x1",
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
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "📊 *Welcome to ICMR Secure User-ID Portal*\n\n⚙️ *Status:* Active\n💻 *Dev:* @Dark_soul_x1"
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "contact_dev":
        bot.send_message(call.message.chat.id, "👨‍💻 *Official System Developer:* @Dark_soul_x1", parse_mode="Markdown")
    elif call.data == "check_status":
        bot.send_message(call.message.chat.id, "🗝️ API Key active. Limit: Unlimited for testing.")

def run_bot_loop():
    print("[SYSTEM] Bot Polling Thread Started...", flush=True)
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=20)
        except Exception as e:
            print(f"[BOT RESTART] Polling crashed, restarting... Error: {e}", flush=True)

# Main Execution Trigger
# Start DB download and Bot immediately on script load
threading.Thread(target=load_all_databases_bg, daemon=True).start()
threading.Thread(target=run_bot_loop, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)
