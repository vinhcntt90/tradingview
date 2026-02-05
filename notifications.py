import requests
import json
import os
from .config import Config

def send_telegram_photo(image_path, caption=""):
    """Send photo to all configured Telegram channels"""
    if not Config.TELEGRAM_BOT_TOKEN:
        print("[!] Telegram Bot Token not set.")
        return

    for chat_id in Config.TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendPhoto"
        try:
            with open(image_path, 'rb') as photo:
                payload = {
                    'chat_id': chat_id,
                    'caption': caption,
                    'parse_mode': 'Markdown'
                }
                files = {'photo': photo}
                response = requests.post(url, data=payload, files=files, timeout=20)
                
                if response.status_code == 200:
                    print(f"  ✅ Telegram: Photo sent to {chat_id}!")
                else:
                    print(f"  ❌ Telegram Error ({chat_id}): {response.text}")
        except Exception as e:
            print(f"  ❌ Telegram Connection Error {chat_id}: {e}")

def send_telegram_message(message):
    """Send text message to all configured Telegram channels"""
    if not Config.TELEGRAM_BOT_TOKEN:
        return

    for chat_id in Config.TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"  ❌ Telegram Message Error {chat_id}: {e}")
