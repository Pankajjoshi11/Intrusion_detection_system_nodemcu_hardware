from flask import Flask, request, jsonify
import requests
import os
import json
import time
import threading
import logging
from datetime import datetime

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load credentials from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "7564968755:AAGMhiFJIjpJ__imIhasc0APWes5dwcSA0k")
PRIMARY_CHAT_ID = os.getenv("PRIMARY_CHAT_ID", "7878423855")
SECONDARY_CHAT_ID = os.getenv("SECONDARY_CHAT_ID", "YOUR_SECONDARY_CHAT_ID")  # Replace with actual secondary chat ID
QUEUE_FILE = "message_queue.json"

# Initialize message queue
def init_queue():
    if not os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'w') as f:
            json.dump([], f)

# Save message to queue
def save_to_queue(chat_id, message):
    try:
        with open(QUEUE_FILE, 'r+') as f:
            queue = json.load(f)
            queue.append({
                "chat_id": chat_id,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            f.seek(0)
            json.dump(queue, f, indent=2)
        logger.info(f"Queued message for chat_id {chat_id}: {message}")
    except Exception as e:
        logger.error(f"Failed to save to queue: {e}")

# Send message via Telegram API
def send_telegram_message(chat_id, message):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(telegram_url, data={
            "chat_id": chat_id,
            "text": message
        }, timeout=10)
        if response.status_code == 200:
            logger.info(f"Successfully sent message to chat_id {chat_id}")
            return True
        else:
            logger.error(f"Failed to send message to chat_id {chat_id}: {response.text}")
            return False
    except requests.RequestException as e:
        logger.error(f"Network error sending to chat_id {chat_id}: {e}")
        return False

# Background thread to retry queued messages
def retry_queued_messages():
    while True:
        try:
            with open(QUEUE_FILE, 'r+') as f:
                queue = json.load(f)
                if not queue:
                    time.sleep(60)  # Wait if queue is empty
                    continue
                updated_queue = []
                for item in queue:
                    chat_id = item["chat_id"]
                    message = item["message"]
                    if send_telegram_message(chat_id, message):
                        logger.info(f"Successfully sent queued message to chat_id {chat_id}")
                    else:
                        updated_queue.append(item)  # Keep in queue if failed
                f.seek(0)
                f.truncate()
                json.dump(updated_queue, f, indent=2)
        except Exception as e:
            logger.error(f"Error processing queue: {e}")
        time.sleep(60)  # Retry every 60 seconds

@app.route('/alert', methods=['POST'])
def alert():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"status": "error", "message": "Invalid payload"}), 400

    message = data['message']
    logger.debug(f"Received alert: {message}")

    # Try sending to primary user
    if send_telegram_message(PRIMARY_CHAT_ID, message):
        return jsonify({"status": "success", "message": "Alert sent to primary user"})
    else:
        # Queue message for primary user
        save_to_queue(PRIMARY_CHAT_ID, message)
        # Try sending to secondary user
        if send_telegram_message(SECONDARY_CHAT_ID, f"Primary user offline: {message}"):
            return jsonify({"status": "success", "message": "Primary user offline, alert sent to secondary user"})
        else:
            save_to_queue(SECONDARY_CHAT_ID, f"Primary user offline: {message}")
            return jsonify({"status": "error", "message": "Failed to send to both users, messages queued"}), 500

if __name__ == '__main__':
    # Initialize queue and start retry thread
    init_queue()
    retry_thread = threading.Thread(target=retry_queued_messages, daemon=True)
    retry_thread.start()
    app.run(host="0.0.0.0", port=5000)