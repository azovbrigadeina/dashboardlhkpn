import streamlit as st
import pandas as pd
import requests
from io import StringIO

SHEET_ID = "1nSVGjisOcYJp5a2XQsMm-Q9GM1u8BL_RM-T9YUbYJ48"
GID = "465025576"
GSHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=300)
def load_from_gsheet():
    response = requests.get(GSHEET_CSV_URL, timeout=15)
    response.raise_for_status()
    df = pd.read_csv(StringIO(response.text))
    return df

def proses_data_unja(df, filter_bulan):
    df = df.dropna(subset=['NIK', 'NAMA', 'SUB UNIT KERJA'])
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[^0-9]", "", regex=True)

    def get_zona(row):
        status = str(row['Status LHKPN']).strip()
        hijau_status = ["Diumumkan Lengkap", "Diumumkan Tidak Lengkap", "Perlu Perbaikan",
                        "Perlu Verifikasi", "Terverifikasi Lengkap", "Proses Verifikasi"]
        if status in hijau_status: return 1, "🟢 ZONA HIJAU"
        elif status == "Draft":    return 2, "🟡 ZONA KUNING"
        elif status == "Belum Lapor": return 3, "🔴 ZONA MERAH"
        return 4, "⚪ LAINNYA"

    res = df.apply(get_zona, axis=1)
    df['rank'] = [x[0] for x in res]
    df['ZONA'] = [x[1] for x in res]

    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.strip().str.upper() == filter_bulan]

    return df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')
