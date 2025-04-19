from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Your Telegram bot credentials
BOT_TOKEN = "7564968755:AAGMhiFJIjpJ__imIhasc0APWes5dwcSA0k"
CHAT_ID = "7878423855"

@app.route('/alert', methods=['POST'])
def alert():
    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({"status": "error", "message": "Invalid payload"}), 400

    message = data['message']
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(telegram_url, data={
        "chat_id": CHAT_ID,
        "text": message
    })

    if response.status_code == 200:
        return jsonify({"status": "success", "message": "Alert sent to Telegram"})
    else:
        return jsonify({"status": "error", "message": "Failed to send to Telegram"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
