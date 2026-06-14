# main.py
from flask import Flask, request, jsonify
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import secrets
import json
import os
from datetime import datetime, timedelta
import threading

app = Flask(__name__)

# 🤖 TOKENS & CONFIG
TELEGRAM_BOT_TOKEN = "8758245872:AAFFsG53k-ljzF-j9dTxaszCRKfixxU6crA"
ADMIN_CHAT_ID = 8655103281
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

MASTER_DATABASE_CACHE = {} # Memory optimization ke liye Dict use kar rahe hain (Speed 100x ho jayegi)
API_KEYS_DB = {
    "SHIVAM_FREE_TEST": {
        "total_limit": 5000, 
        "used": 0, 
        "expiry_date": "2030-12-31"
    }
}

# Fast Sync Mechanism (Dict Key-Value Pair)
def load_all_databases():
    global MASTER_DATABASE_CACHE
    print("[SYSTEM] Booting Multi-Database Fast Merger...")
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
                        MASTER_DATABASE_CACHE[u_id] = row # Instant O(1) lookup speed
                print(f"[SUCCESS] Part {i} integrated.")
            elif response.status_code == 404:
                continue
        except Exception as e:
            print(f"[EXCEPTION] Part {i} error: {str(e)}")
    print(f"🎉 Pool Ready! Total unique records in memory: {len(MASTER_DATABASE_CACHE)}")

@app.route('/')
def home():
    return "<h1>ICMR Secure Telegram User-ID API Gateway Live on Render!</h1>"

@app.route('/api', methods=['GET'])
def get_data():
    search_query = request.args.get('id')
    user_api_key = request.args.get('key')

    if not search_query or not user_api_key:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400
    if user_api_key not in API_KEYS_DB:
        return jsonify({"status": "error", "message": "Invalid API Key"}), 401

    # Instant dictionary search
    user_record = MASTER_DATABASE_CACHE.get(str(search_query))

    if user_record:
        return jsonify({
            "status": "success",
            "developer": "@Dark_soul_x1",
            "data": user_record
        }), 200
                
    return jsonify({"status": "error", "message": "Requested User ID not found."}), 404

def run_bot():
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Bot error: {e}")

if __name__ == '__main__':
    load_all_databases()
    
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Render automatically passes the port number in environment variables
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)
