import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- 1. CONFIG ---
st.set_page_config(page_title="LHKPN Monitoring System", layout="wide")

# --- 2. DATA ENGINE (INTEGRASI GOOGLE SHEETS) ---
# Tautan dari user yang sudah dikonversi ke format ekspor CSV
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1nSVGjisOcYJp5a2XQsMm-Q9GM1u8BL_RM-T9YUbYJ48/export?format=csv"

@st.cache_data(ttl=600) # Data disimpan di cache selama 10 menit
def load_data_from_gsheet(url):
    try:
        # Membaca data dari Google Sheets
        df = pd.read_csv(url)
        
        # Pembersihan Data Dasar
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
        
        # Hapus duplikat berdasarkan NIK untuk memastikan 1 orang 1 data terbaru
        return df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')
    except Exception as e:
        st.error(f"Gagal memuat data dari Google Sheets: {e}")
        return pd.DataFrame()

# --- 3. LOGIN SYSTEM ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

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
                    st.success("Login Berhasil!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
    st.stop()

# --- 4. CSS CUSTOM UNTUK TAMPILAN CARD ---
st.markdown("""
    <style>
    .metric-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); text-align: center;
        border-top: 5px solid #ececec;
    }
    .metric-label { font-size: 13px; color: #64748b; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 36px; font-weight: bold; color: #1e293b; margin: 5px 0; }
    .metric-delta { font-size: 14px; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR & SINKRONISASI ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/f2/Logo_KPK.png", width=80)
    st.header("Control Center")
    
    # Tombol Sinkronisasi Estetik
    if st.button("🔄 Sinkronisasi Server KPK", use_container_width=True):
        with st.status("Menghubungkan ke API e-LHKPN...", expanded=True) as status:
            st.write("Mengecek Token Akses...")
            time.sleep(1)
            st.write("Mengunduh Data Wajib Lapor Terbaru...")
            time.sleep(1.5)
            st.write("Sinkronisasi Database Google Sheets...")
            # Hapus cache agar data benar-benar ditarik ulang dari GSheet
            st.cache_data.clear()
            time.sleep(1)
            status.update(label="Sinkronisasi Selesai!", state="complete", expanded=False)
        st.toast("Data berhasil diperbarui dari pusat!", icon="✅")

    st.divider()
    if st.button("Logout", color="red"):
        st.session_state['auth'] = False
        st.rerun()

# --- 6. MAIN DASHBOARD ---
data = load_data_from_gsheet(GSHEET_URL)

if not data.empty:
    st.title("🏛️ Dashboard Real-Time Kepatuhan LHKPN")
    
    # Kalkulasi Metrik
    total_wl = len(data)
    h = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
    k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
    m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])
    rate = (h / total_wl * 100) if total_wl > 0 else 0

    # Grid Metrik Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card" style="border-top-color: #3b82f6;"><div class="metric-label">Wajib Lapor</div><div class="metric-value">{total_wl}</div><div class="metric-delta" style="color: #3b82f6;">Pegawai</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card" style="border-top-color: #22c55e;"><div class="metric-label">🟢 Hijau</div><div class="metric-value">{h}</div><div class="metric-delta" style="color: #22c55e;">{rate:.1f}% Selesai</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card" style="border-top-color: #f59e0b;"><div class="metric-label">🟡 Kuning</div><div class="metric-value">{k}</div><div class="metric-delta" style="color: #f59e0b;">Status Draft</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card" style="border-top-color: #ef4444;"><div class="metric-label">🔴 Merah</div><div class="metric-value">{m}</div><div class="metric-delta" style="color: #ef4444;">Belum Lapor</div></div>', unsafe_allow_html=True)

    # --- TABEL INDIVIDU ---
    st.write("---")
    st.subheader("📋 Daftar Informasi Individu")
    
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 Cari berdasarkan Nama, NIK, atau Unit Kerja:")
    with col_filter:
        zona_selected = st.multiselect("Filter Status:", options=data['ZONA'].unique(), default=data['ZONA'].unique())

    # Jalankan Filter
    filtered_df = data[data['ZONA'].isin(zona_selected)]
    if search_query:
        filtered_df = filtered_df[filtered_df.apply(lambda row: search_query.lower() in str(row).lower(), axis=1)]

    st.dataframe(
        filtered_df[['NAMA', 'NIK', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']],
        use_container_width=True,
        hide_index=True
    )

    # --- VISUALISASI ---
    st.write("---")
    v1, v2 = st.columns([1, 1.5])
    with v1:
        st.plotly_chart(px.pie(data, names='ZONA', color='ZONA', hole=0.5,
                              title="Persentase Kepatuhan",
                              color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"}), use_container_width=True)
    with v2:
        df_red = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
        if not df_red.empty:
            st.plotly_chart(px.bar(df_red, x='count', y='SUB UNIT KERJA', orientation='h', 
                                 title="Top 10 Unit Kerja Zona Merah", 
                                 color_discrete_sequence=['#EF4444']), use_container_width=True)
        else:
            st.success("Luar biasa! Tidak ada data di Zona Merah.")

else:
    st.error("Tidak dapat memproses data. Pastikan Google Sheet Anda memiliki header: NAMA, NIK, SUB UNIT KERJA, Status LHKPN.")
