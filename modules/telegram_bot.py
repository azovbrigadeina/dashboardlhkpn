import requests
import streamlit as st

def send_telegram_message(token, chat_id, message):
    """
    Sends a message via Telegram Bot API.
    """
    if not token or not chat_id:
        return False, "Token atau Chat ID tidak valid."
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        res_data = response.json()
        if response.status_code == 200 and res_data.get("ok"):
            return True, "Pesan terkirim!"
        else:
            return False, res_data.get("description", "Gagal mengirim pesan.")
    except Exception as e:
        return False, str(e)

def get_telegram_link(phone_number, message):
    """
    Generates a direct link to Telegram for manual messaging.
    """
    import urllib.parse
    clean_number = "".join(filter(str.isdigit, str(phone_number)))
    # Ensure it starts with international code if needed, but t.me works with username/phone
    encoded_msg = urllib.parse.quote(message)
    return f"https://t.me/{clean_number}?text={encoded_msg}"
