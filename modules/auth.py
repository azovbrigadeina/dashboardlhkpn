import streamlit as st
import json
import os
import requests

USER_DB_FILE = "users.json"

def get_api_credentials():
    try:
        # Check Streamlit secrets
        api_url = st.secrets.get("GSHEET_API_URL")
        api_key = st.secrets.get("GSHEET_API_KEY")
        if api_url and api_key:
            return api_url, api_key
    except:
        pass
    return None, None

def load_users():
    api_url, api_key = get_api_credentials()
    if api_url and api_key:
        try:
            payload = {
                "apiKey": api_key,
                "action": "load_users"
            }
            res = requests.post(api_url, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get("success"):
                    # Simpan data user lokal sebagai backup
                    users = data.get("users", {})
                    try:
                        with open(USER_DB_FILE, "w") as f:
                            json.dump(users, f, indent=4)
                    except:
                        pass
                    return users
        except Exception as e:
            st.sidebar.warning(f"⚠️ Gagal sinkronisasi user Cloud: {e}. Menggunakan data lokal.")
            
    # Fallback ke users.json lokal jika offline/belum di-set secrets-nya
    if not os.path.exists(USER_DB_FILE):
        default_users = {
            "admin": {
                "password": "123456",
                "role": "admin",
                "unit": None
            },
            "operator": {
                "password": "unja2025",
                "role": "admin",
                "unit": None
            },
            "pimpinan": {
                "password": "lhkpn@unja",
                "role": "pimpinan",
                "unit": None
            }
        }
        try:
            with open(USER_DB_FILE, "w") as f:
                json.dump(default_users, f, indent=4)
        except:
            pass
        return default_users
        
    try:
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    api_url, api_key = get_api_credentials()
    cloud_success = False
    
    if api_url and api_key:
        try:
            payload = {
                "apiKey": api_key,
                "action": "save_users",
                "users": users
            }
            res = requests.post(api_url, json=payload, timeout=10)
            if res.status_code == 200 and res.json().get("success"):
                cloud_success = True
        except Exception as e:
            st.sidebar.error(f"❌ Gagal menyimpan user ke Cloud: {e}")
            
    # Selalu simpan lokal juga sebagai backup
    try:
        with open(USER_DB_FILE, "w") as f:
            json.dump(users, f, indent=4)
        return True
    except:
        return False

def load_settings():
    api_url, api_key = get_api_credentials()
    default_settings = {
        "email_subject": "PENGINGAT: Pengisian LHKPN Universitas Jambi",
        "email_body": "Yth. Bapak/Ibu {NAMA},\n\nBerdasarkan data pemantauan e-LHKPN KPK, status LHKPN Anda saat ini: {STATUS_LHKPN}.\n\nMohon segera melakukan pengisian atau pembaharuan laporan LHKPN Anda untuk periode {BULAN}.\n\nTerima kasih atas kepatuhan Anda.\n\nSalam,\nAdmin LHKPN Universitas Jambi"
    }
    
    if api_url and api_key:
        try:
            payload = {
                "apiKey": api_key,
                "action": "load_settings"
            }
            res = requests.post(api_url, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get("success"):
                    return data.get("settings", default_settings)
        except Exception as e:
            st.sidebar.warning(f"⚠️ Gagal memuat setting dari Cloud: {e}. Menggunakan default.")
            
    return default_settings

def save_settings(settings):
    api_url, api_key = get_api_credentials()
    if api_url and api_key:
        try:
            payload = {
                "apiKey": api_key,
                "action": "save_settings",
                "settings": settings
            }
            res = requests.post(api_url, json=payload, timeout=10)
            if res.status_code == 200 and res.json().get("success"):
                return True
        except Exception as e:
            st.sidebar.error(f"❌ Gagal menyimpan setting ke Cloud: {e}")
    return False

def send_email_via_gas(to, subject, body):
    api_url, api_key = get_api_credentials()
    if not (api_url and api_key):
        return False, "Kredensial API (Secrets) belum diatur di Streamlit."
        
    try:
        payload = {
            "apiKey": api_key,
            "action": "send_email",
            "to": to,
            "subject": subject,
            "body": body
        }
        res = requests.post(api_url, json=payload, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if data.get("success"):
                return True, "Email terkirim"
            else:
                return False, data.get("error", "Gagal mengirim email")
        else:
            return False, f"Server Error {res.status_code}"
    except Exception as e:
        return False, str(e)

def init_session_state():
    for key, val in [('auth', False), ('username', ''), ('role', 'user'), ('unit', None), ('synced', False), ('raw_data', None)]:
        if key not in st.session_state:
            st.session_state[key] = val

def logout():
    for k in ['auth', 'username', 'role', 'unit', 'synced', 'raw_data']:
        st.session_state[k] = False if k == 'auth' else (None if k in ['raw_data', 'unit'] else ('user' if k == 'role' else ''))
    st.rerun()

