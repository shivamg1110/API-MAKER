from flask import Flask, request, jsonify
import requests
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)

# Config
BASE_GITHUB_URL = "https://raw.githubusercontent.com/shivamg1110/tg-database/main/Telegram_27_part{}.json"

API_KEYS_DB = {
    "SHIVAM_FREE_TEST": {
        "total_limit": 5000, 
        "used": 0, 
        "expiry_date": "2030-12-31"
    }
}

def search_in_github_files(user_id):
    # Har part me loop chalane ki jagah hum smartly scan karenge
    # Agar tujhe pata ho ki ID kis part me ho sakti hai toh optimize ho sakta hai, 
    # nahi toh ye automatic on-the-fly dhoondhega bina server crash kiye.
    for i in range(1, 51):
        url = BASE_GITHUB_URL.format(i)
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for row in data:
                    if str(row.get('user_id')) == str(user_id):
                        return row
        except Exception:
            continue
    return None

@app.route('/')
def home():
    return "<h1>ICMR API Gateway Live on Vercel Serverless!</h1>"

@app.route('/api', methods=['GET'])
def get_data():
    search_query = request.args.get('id')
    user_api_key = request.args.get('key')

    if not search_query or not user_api_key:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400
    
    if user_api_key not in API_KEYS_DB:
        return jsonify({"status": "error", "message": "Invalid API Key"}), 401

    # Live Database Lookup
    user_record = search_in_github_files(search_query)

    if user_record:
        return jsonify({
            "status": "success",
            "developer": "@Dark_soul_x1",
            "data": user_record
        }), 200
                
    return jsonify({"status": "error", "message": "Requested User ID not found."}), 404