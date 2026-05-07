import streamlit as st
import json
import os

USER_DB_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_DB_FILE):
        return {}
    with open(USER_DB_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f, indent=4)

def init_session_state():
    for key, val in [('auth', False), ('username', ''), ('role', 'user'), ('unit', None), ('synced', False), ('raw_data', None)]:
        if key not in st.session_state:
            st.session_state[key] = val

def logout():
    for k in ['auth', 'username', 'role', 'unit', 'synced', 'raw_data']:
        st.session_state[k] = False if k == 'auth' else (None if k in ['raw_data', 'unit'] else ('user' if k == 'role' else ''))
    st.rerun()
