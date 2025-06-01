import os

import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")

def send_message_to_user(telegram_id, message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": message,
        "parse_mode": "HTML"  # Optional: enables basic formatting
    }
    try:
        response = requests.post(url, json=payload, timeout=10)  # Using json instead of data
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        print(f"Telegram API error: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Telegram connection error: {e}")
    return False