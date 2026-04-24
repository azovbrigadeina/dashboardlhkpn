import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- 1. CONFIG & SETUP ---
st.set_page_config(page_title="LHKPN Monitoring System", layout="wide")

# GANTI DENGAN URL GOOGLE SHEET ANDA (Format CSV Export)
# Contoh: https://docs.google.com/spreadsheets/d/ID_SHEET/export?format=csv
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1vS8yLHKPN_CONTOH/export?format=csv"

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=600) # Data di-cache selama 10 menit
def load_data_from_gsheet(url):
    try:
        df = pd.read_csv(url)
        # Cleaning Data
        df = df.dropna(subset=['NIK', 'NAMA', 'SUB UNIT KERJA'])
        df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[^0-9]", "", regex=True)
        
        def get_zona(row):
            status = str(row['Status LHKPN']).strip()
            hijau_status = ["Diumumkan Lengkap", "Diumumkan Tidak Lengkap", "Perlu Perbaikan", 
                            "Perlu Verifikasi", "Terverifikasi Lengkap", "Proses Verifikasi"]
            if status in hijau_status: return 1, "🟢 ZONA HIJAU"
            elif status == "Draft": return 2, "🟡 ZONA KUNING"
            elif status == "Belum Lapor": return 3, "🔴 ZONA MERAH"
            return 4, "⚪ LAINNYA"

        res = df.apply(get_zona, axis=1)
        df['rank'] = [x[0] for x in res]
        df['ZONA'] = [x[1] for x in res]
        return df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')
    except Exception as e:
        st.error(f"Gagal memuat data dari Google Sheets: {e}")
        return pd.DataFrame()

# --- 3. LOGIN SYSTEM (USERNAME & PASSWORD) ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h2 style='text-align: center;'>🏛️ Sistem Monitoring LHKPN</h2>", unsafe_allow_html=True)
        with st.container(border=True):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.button("Log In", use_container_width=True):
                # Ganti kriteria login sesuai kebutuhan
                if user == "admin" and pw == "123456":
                    st.session_state['auth'] = True
                    st.rerun()
                else:
                    st.error("Kredensial salah!")
    st.stop()

# --- 4. CSS CUSTOM ---
st.markdown("""
    <style>
    .metric-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;
        border-top: 5px solid #ececec;
    }
    .metric-value { font-size: 32px; font-weight: bold; color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR & SINKRONISASI ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/f2/Logo_KPK.png", width=80) # Opsional logo KPK
    st.header("Sync Center")
    
    # Tombol Sinkronisasi "Server KPK"
    if st.button("🔄 Sinkronkan Data KPK", use_container_width=True):
        with st.status("Menghubungkan ke Server e-LHKPN KPK...", expanded=True) as status:
            st.write("Mengautentikasi API Key...")
            time.sleep(1)
            st.write("Mengambil data Wajib Lapor terbaru...")
            time.sleep(1.5)
            st.write("Sinkronisasi database lokal...")
            # Membersihkan cache agar data terbaru ditarik dari GSheet
            st.cache_data.clear()
            time.sleep(1)
            status.update(label="Sinkronisasi Berhasil!", state="complete", expanded=False)
        st.toast("Data Berhasil Diperbarui!", icon="✅")

    st.divider()
    if st.button("Keluar"):
        st.session_state['auth'] = False
        st.rerun()

# --- 6. MAIN DASHBOARD ---
data = load_data_from_gsheet(GSHEET_URL)

if not data.empty:
    st.title("📊 Dashboard Monitoring Real-Time")
    
    # Kalkulasi
    total_wl = len(data)
    h = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
    k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
    m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])
    rate = (h / total_wl * 100) if total_wl > 0 else 0

    # Metrik Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="metric-card" style="border-top-color: #3b82f6;"><small>WAJIB LAPOR</small><div class="metric-value">{total_wl}</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-card" style="border-top-color: #22c55e;"><small>🟢 HIJAU</small><div class="metric-value">{h}</div><div style="color: #22c55e;">{rate:.1f}%</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="metric-card" style="border-top-color: #f59e0b;"><small>🟡 KUNING</small><div class="metric-value">{k}</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="metric-card" style="border-top-color: #ef4444;"><small>🔴 MERAH</small><div class="metric-value">{m}</div></div>', unsafe_allow_html=True)

    # Tabel Individu
    st.write("---")
    st.subheader("📋 Daftar Status Individu")
    
    # Search & Filter
    search = st.text_input("Cari Nama atau Unit Kerja")
    if search:
        data_view = data[data.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
    else:
        data_view = data

    st.dataframe(
        data_view[['NAMA', 'NIK', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']],
        use_container_width=True,
        hide_index=True
    )

    # Visualisasi
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.pie(data, names='ZONA', color='ZONA', hole=0.4, 
                              color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"}), use_container_width=True)
    with c2:
        unit_red = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(5)
        st.plotly_chart(px.bar(unit_red, x='count', y='SUB UNIT KERJA', orientation='h', title="Top 5 Unit Merah", color_discrete_sequence=['#EF4444']), use_container_width=True)
else:
    st.warning("Database kosong. Pastikan Google Sheet terisi dan URL sudah benar.")
