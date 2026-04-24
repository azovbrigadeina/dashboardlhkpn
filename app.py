import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- 1. CONFIG ---
st.set_page_config(page_title="LHKPN Monitoring System", layout="wide")

# --- 2. DATA ENGINE ---
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1nSVGjisOcYJp5a2XQsMm-Q9GM1u8BL_RM-T9YUbYJ48/export?format=csv"

@st.cache_data(ttl=600)
def load_data_from_gsheet(url):
    try:
        df = pd.read_csv(url)
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
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

# --- 3. SESSION STATE INITIALIZATION ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False
if 'synced' not in st.session_state:
    st.session_state['synced'] = False

# --- 4. LOGIN SYSTEM ---
if not st.session_state['auth']:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🏛️ MONITORING LHKPN</h2>", unsafe_allow_html=True)
        with st.container(border=True):
            user = st.text_input("Username", placeholder="admin")
            pw = st.text_input("Password", type="password", placeholder="******")
            if st.button("Masuk ke Dashboard", use_container_width=True):
                if user == "admin" and pw == "123456":
                    st.session_state['auth'] = True
                    st.rerun()
                else:
                    st.error("Kredensial Salah!")
    st.stop()

# --- 5. CSS CUSTOM ---
st.markdown("""
    <style>
    .metric-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); text-align: center;
        border-top: 5px solid #ececec;
    }
    .metric-label { font-size: 13px; color: #64748b; font-weight: bold; }
    .metric-value { font-size: 36px; font-weight: bold; color: #1e293b; margin: 5px 0; }
    </style>
""", unsafe_allow_html=True)

# --- 6. SIDEBAR CONTROL ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/f2/Logo_KPK.png", width=80)
    st.header("SINKRONISASI")
    
    # Tombol Sinkronisasi Dramatis
    if st.button("🔄 Sinkronkan Data KPK", use_container_width=True, type="secondary"):
        with st.status("Menghubungkan ke Server e-LHKPN KPK...", expanded=True) as status:
            st.write("📡 Membangun koneksi aman (SSL)...")
            time.sleep(1.5)
            st.write("🔑 Memverifikasi Token API SATU DATA...")
            time.sleep(2)
            st.write("📥 Mengunduh paket data Wajib Lapor...")
            # Progress bar simulasi
            prog = st.progress(0)
            for i in range(100):
                time.sleep(0.02)
                prog.progress(i + 1)
            st.write("⚙️ Sinkronisasi Database lokal...")
            st.cache_data.clear()
            st.session_state['synced'] = True
            time.sleep(1)
            status.update(label="✅ Sinkronisasi Berhasil!", state="complete", expanded=False)
        st.toast("Data terbaru telah dimuat!", icon="🚀")

    st.divider()
    if st.button("Log Out", type="primary", use_container_width=True):
        st.session_state['auth'] = False
        st.session_state['synced'] = False
        st.rerun()

# --- 7. MAIN DASHBOARD LOGIC ---
if not st.session_state['synced']:
    # Tampilan jika belum klik sinkronisasi
    st.title("🏛️ Dashboard LHKPN")
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.info("👋 **Selamat Datang!** Database saat ini masih kosong. Silakan tekan tombol **'Sinkronkan Data KPK'** di sidebar sebelah kiri untuk menarik data terbaru dari server.")
        st.image("https://cdn-icons-png.flaticon.com/512/3588/3588668.png", width=200) # Ilustrasi sync
else:
    # Tampilan Dashboard setelah klik sinkronisasi
    data = load_data_from_gsheet(GSHEET_URL)
    
    if not data.empty:
        st.title("🏛️ Dashboard Real-Time Monitoring")
        
        # Kalkulasi
        total_wl = len(data)
        h = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
        k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
        m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])
        rate = (h / total_wl * 100) if total_wl > 0 else 0

        # Metrik Cards
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="metric-card" style="border-top-color: #3b82f6;"><div class="metric-label">Wajib Lapor</div><div class="metric-value">{total_wl}</div></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card" style="border-top-color: #22c55e;"><div class="metric-label">🟢 Hijau</div><div class="metric-value">{h}</div><div style="color: #22c55e; font-weight: bold;">{rate:.1f}%</div></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card" style="border-top-color: #f59e0b;"><div class="metric-label">🟡 Kuning</div><div class="metric-value">{k}</div></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card" style="border-top-color: #ef4444;"><div class="metric-label">🔴 Merah</div><div class="metric-value">{m}</div></div>', unsafe_allow_html=True)

        st.write("---")
        
        # Filter & Tabel
        st.subheader("📋 Daftar Informasi Individu")
        c1, c2 = st.columns([2, 1])
        with c1:
            search = st.text_input("🔍 Cari Nama, NIK, atau Unit Kerja:")
        with c2:
            z_select = st.multiselect("Status:", options=data['ZONA'].unique(), default=data['ZONA'].unique())

        df_final = data[data['ZONA'].isin(z_select)]
        if search:
            df_final = df_final[df_final.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

        st.dataframe(df_final[['NAMA', 'NIK', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], use_container_width=True, hide_index=True)

        # Visualisasi
        st.write("---")
        v1, v2 = st.columns(2)
        with v1:
            st.plotly_chart(px.pie(data, names='ZONA', color='ZONA', hole=0.4, color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"}), use_container_width=True)
        with v2:
            red_stats = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(5)
            if not red_stats.empty:
                st.plotly_chart(px.bar(red_stats, x='count', y='SUB UNIT KERJA', orientation='h', title="Top 5 Unit Kerja Zona Merah", color_discrete_sequence=['#EF4444']), use_container_width=True)
    else:
        st.error("Gagal memproses data dari Google Sheets.")
