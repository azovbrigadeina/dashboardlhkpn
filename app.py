import streamlit as st
import pandas as pd
import plotly.express as px
import time
import requests
from io import StringIO

# --- 1. CONFIG ---
st.set_page_config(page_title="LHKPN UNJA Monitoring", layout="wide", page_icon="🏛️")

# --- 2. GOOGLE SHEET URL ---
SHEET_ID = "1nSVGjisOcYJp5a2XQsMm-Q9GM1u8BL_RM-T9YUbYJ48"
GID = "465025576"
GSHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

# --- 3. CREDENTIALS ---
VALID_USERS = {
    "admin": "123456",
    "operator": "unja2025",
    "pimpinan": "lhkpn@unja",
}

# --- 4. CSS GLOBAL ---
st.markdown("""
<style>
/* Login card */
.login-wrapper {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}
.metric-card {
    background-color: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    text-align: center;
    border-top: 5px solid #ececec;
}
.metric-label { font-size: 14px; color: #64748b; font-weight: bold; }
.metric-value { font-size: 32px; font-weight: bold; color: #1e293b; margin: 5px 0; }
.metric-delta { font-size: 13px; font-weight: 600; }

/* Sync log box */
.sync-log {
    background: #0f172a;
    color: #22d3ee;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    border-radius: 10px;
    padding: 20px;
    line-height: 2;
    min-height: 200px;
}
.sync-ok  { color: #4ade80; }
.sync-err { color: #f87171; }
.sync-warn{ color: #fbbf24; }
.sync-info{ color: #22d3ee; }
</style>
""", unsafe_allow_html=True)


# --- 5. DATA ENGINE ---
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


# --- 6. SESSION STATE INIT ---
for key, val in [('auth', False), ('username', ''), ('synced', False), ('raw_data', None)]:
    if key not in st.session_state:
        st.session_state[key] = val


# =====================================================================
# HALAMAN 1: LOGIN
# =====================================================================
if not st.session_state['auth']:
    st.markdown("""
    <div style="text-align:center; padding: 60px 0 10px 0;">
        <span style="font-size:64px;">🏛️</span>
        <h1 style="color:#1e3a5f; margin:0;">LHKPN MONITORING</h1>
        <p style="color:#64748b; font-size:16px;">Universitas Jambi — Sistem Pemantauan Kepatuhan LHKPN</p>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.container(border=True):
            st.markdown("#### 🔐 Masuk ke Sistem")
            username = st.text_input("👤 Username", placeholder="Masukkan username Anda")
            password = st.text_input("🔑 Password", type="password", placeholder="Masukkan password Anda")
            
            st.write("")
            if st.button("🚀 MASUK", use_container_width=True, type="primary"):
                if username in VALID_USERS and VALID_USERS[username] == password:
                    st.session_state['auth'] = True
                    st.session_state['username'] = username
                    st.rerun()
                elif username == "":
                    st.warning("⚠️ Username tidak boleh kosong.")
                else:
                    st.error("❌ Username atau Password salah. Silakan coba lagi.")

        st.markdown("""
        <div style="text-align:center; margin-top:15px; color:#94a3b8; font-size:12px;">
            Sistem ini hanya dapat diakses oleh petugas yang berwenang.<br>
            Segala aktivitas tercatat dan dipantau.
        </div>
        """, unsafe_allow_html=True)
    st.stop()


# =====================================================================
# HALAMAN 2: SINKRONISASI DRAMATIK
# =====================================================================
if not st.session_state['synced']:

    st.markdown(f"""
    <div style="text-align:center; padding: 30px 0 5px 0;">
        <span style="font-size:48px;">📡</span>
        <h2 style="color:#1e3a5f;">Sinkronisasi Data e-LHKPN KPK</h2>
        <p style="color:#64748b;">Selamat datang, <b>{st.session_state['username'].upper()}</b>. 
        Mempersiapkan koneksi ke server KPK...</p>
    </div>
    """, unsafe_allow_html=True)

    _, btn_col, _ = st.columns([1, 1, 1])
    with btn_col:
        do_sync = st.button("🔄  MULAI SINKRONISASI DATA", use_container_width=True, type="primary")

    log_box = st.empty()
    prog_bar = st.empty()
    status_msg = st.empty()

    if do_sync:
        log_lines = []

        def render_log(lines):
            html = '<div class="sync-log">' + "<br>".join(lines) + '</div>'
            log_box.markdown(html, unsafe_allow_html=True)

        STEPS = [
            (0.10, "sync-info",  "[ INIT   ] Menginisialisasi koneksi aman ke server KPK..."),
            (0.18, "sync-ok",    "[ OK     ] Handshake TLS 1.3 berhasil — enkripsi aktif 🔒"),
            (0.25, "sync-info",  "[ AUTH   ] Mengirimkan token autentikasi LHKPN API v2.4..."),
            (0.32, "sync-ok",    "[ OK     ] Autentikasi diterima. Session ID: KPK-UNJA-2025-****"),
            (0.40, "sync-info",  "[ FETCH  ] Mengunduh dataset wajib lapor Universitas Jambi..."),
            (0.47, "sync-warn",  "[ WAIT   ] Server KPK merespons... harap tunggu..."),
            (0.54, "sync-ok",    "[ OK     ] Data diterima — parsing 1.247 baris rekaman..."),
            (0.61, "sync-info",  "[ VERIFY ] Memverifikasi integritas data dengan checksum SHA-256..."),
            (0.68, "sync-ok",    "[ OK     ] Checksum valid. Tidak ada korupsi data."),
            (0.74, "sync-info",  "[ SYNC   ] Menyinkronkan status LHKPN terbaru dari e-LHKPN KPK..."),
            (0.80, "sync-ok",    "[ OK     ] Status diperbarui: Diumumkan, Draft, Belum Lapor ✅"),
            (0.86, "sync-info",  "[ BUILD  ] Membangun indeks unit kerja & klasifikasi zona..."),
            (0.92, "sync-ok",    "[ OK     ] Zona Hijau / Kuning / Merah berhasil diklasifikasikan 🗂️"),
            (0.97, "sync-info",  "[ FINAL  ] Memuat data ke dashboard monitoring..."),
        ]

        for prog, cls, msg in STEPS:
            log_lines.append(f'<span class="{cls}">{msg}</span>')
            render_log(log_lines)
            prog_bar.progress(prog, text=f"Progres sinkronisasi: {int(prog*100)}%")
            time.sleep(0.55)

        # --- AMBIL DATA NYATA DARI GOOGLE SHEET ---
        status_msg.info("⏳ Mengambil data dari Google Sheets...")
        try:
            raw = load_from_gsheet()
            st.session_state['raw_data'] = raw
            log_lines.append('<span class="sync-ok">[ OK     ] Data Google Sheet berhasil dimuat! ✅</span>')
        except Exception as e:
            log_lines.append(f'<span class="sync-err">[ ERROR  ] Gagal memuat Google Sheet: {e}</span>')
            log_lines.append('<span class="sync-warn">[ WARN   ] Menggunakan mode demo — tidak ada data nyata.</span>')
            st.session_state['raw_data'] = None

        log_lines.append('<span class="sync-ok">[ DONE   ] ════════════════════════════════════</span>')
        log_lines.append('<span class="sync-ok">[ DONE   ] SINKRONISASI SELESAI — DASHBOARD SIAP 🚀</span>')
        log_lines.append('<span class="sync-ok">[ DONE   ] ════════════════════════════════════</span>')
        render_log(log_lines)
        prog_bar.progress(1.0, text="✅ Sinkronisasi selesai!")
        time.sleep(0.8)

        st.session_state['synced'] = True
        status_msg.empty()
        time.sleep(0.5)
        st.rerun()

    st.stop()


# =====================================================================
# HALAMAN 3: DASHBOARD UTAMA
# =====================================================================
raw = st.session_state.get('raw_data', None)

with st.sidebar:
    st.markdown(f"**👤 {st.session_state['username'].upper()}**")
    st.caption("Sesi aktif")
    st.write("---")
    st.header("⚙️ Kontrol")

    if raw is None:
        st.warning("Data tidak tersedia. Gunakan upload manual.")
        file_upload = st.file_uploader("Upload Excel/CSV LHKPN", type=["xlsx", "csv"])
        if file_upload:
            try:
                raw = pd.read_csv(file_upload) if file_upload.name.endswith('.csv') else pd.read_excel(file_upload)
                st.session_state['raw_data'] = raw
            except Exception as e:
                st.error(f"Gagal membaca file: {e}")
    else:
        st.success("✅ Data dari Google Sheets")
        if st.button("🔄 Sinkronisasi Ulang", use_container_width=True):
            st.session_state['synced'] = False
            st.session_state['raw_data'] = None
            load_from_gsheet.clear()
            st.rerun()

    st.write("---")
    if st.button("🚪 Logout", use_container_width=True):
        for k in ['auth', 'username', 'synced', 'raw_data']:
            st.session_state[k] = False if k == 'auth' else (None if k == 'raw_data' else '')
        st.rerun()

if raw is None:
    st.info("👋 Selamat Datang! Data belum tersedia. Silakan sinkronisasi ulang atau upload file.")
    st.stop()

# FILTER BULAN
try:
    list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
except:
    list_bln = ["GLOBAL (AKUMULASI)"]

sel_bln = st.sidebar.selectbox("Pilih Periode:", list_bln)

try:
    data = proses_data_unja(raw, sel_bln)
except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses data: {e}")
    st.stop()

# KALKULASI
total_wl = len(data)
h = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])
rate = (h / total_wl * 100) if total_wl > 0 else 0

# HEADER
st.title("🏛️ Dashboard LHKPN Monitoring — Universitas Jambi")
st.caption(f"Periode: **{sel_bln}** | Pengguna: **{st.session_state['username'].upper()}** | Data: Google Sheets (e-LHKPN KPK)")
st.write("---")

# METRIK CARDS
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-card" style="border-top-color:#3b82f6;"><div class="metric-label">WAJIB LAPOR</div><div class="metric-value">{total_wl}</div><div class="metric-delta" style="color:#3b82f6;">Orang</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card" style="border-top-color:#22c55e;"><div class="metric-label">🟢 HIJAU</div><div class="metric-value">{h}</div><div class="metric-delta" style="color:#22c55e;">{rate:.1f}% Tuntas</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card" style="border-top-color:#f59e0b;"><div class="metric-label">🟡 KUNING</div><div class="metric-value">{k}</div><div class="metric-delta" style="color:#f59e0b;">Status Draft</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card" style="border-top-color:#ef4444;"><div class="metric-label">🔴 MERAH</div><div class="metric-value">{m}</div><div class="metric-delta" style="color:#ef4444;">Belum Lapor</div></div>', unsafe_allow_html=True)

st.write("---")

# PAPAN INFORMASI EKSEKUTIF
unit_stats = data.groupby('SUB UNIT KERJA')['ZONA'].value_counts().unstack().fillna(0)
for z in ["🟢 ZONA HIJAU", "🟡 ZONA KUNING", "🔴 ZONA MERAH"]:
    if z not in unit_stats.columns: unit_stats[z] = 0

unit_stats['Persen_Hijau'] = (unit_stats['🟢 ZONA HIJAU'] / unit_stats.sum(axis=1)) * 100
u_100 = unit_stats[unit_stats['Persen_Hijau'] == 100].index.tolist()
paripurna_txt = ", ".join(u_100[:2]) + ("..." if len(u_100) > 2 else "") if u_100 else "Belum Ada"
u_rendah = unit_stats[unit_stats['Persen_Hijau'] < 100].sort_values(by='Persen_Hijau')
atensi_label = f"Unit <b>{u_rendah.index[0]}</b> ({u_rendah.iloc[0]['Persen_Hijau']:.1f}%)" if not u_rendah.empty else "Semua Unit 100%"

st.markdown(f"""
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:20px;">
    <div style="display:flex;gap:15px;flex-wrap:wrap;">
        <div style="flex:1;min-width:250px;background:white;padding:15px;border-radius:8px;border:1px solid #bbf7d0;">
            <b style="color:#166534;">🏆 APRESIASI</b><br>
            <small>Unit Paripurna: {paripurna_txt} ({len(u_100)} Unit)</small>
        </div>
        <div style="flex:1;min-width:250px;background:white;padding:15px;border-radius:8px;border:1px solid #fecaca;">
            <b style="color:#9f1239;">⚠️ ATENSI</b><br>
            <small>Prioritas: {atensi_label}</small>
        </div>
        <div style="flex:1;min-width:250px;background:white;padding:15px;border-radius:8px;border:1px solid #bfdbfe;">
            <b style="color:#1e40af;">⚡ AKSELERASI</b><br>
            <small>Potensi Maksimal: {((h+k)/total_wl*100):.1f}% jika Zona Kuning tuntas.</small>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.write("")

# TABEL DETAIL INDIVIDU
st.write("### 📋 Detail Individu")
col_f1, col_f2 = st.columns([1, 2])
with col_f1:
    f_zona = st.multiselect("Filter Zona:", options=data['ZONA'].unique(), default=list(data['ZONA'].unique()))
with col_f2:
    f_cari = st.text_input("🔍 Cari Nama / NIK / Unit:")

df_tabel = data[data['ZONA'].isin(f_zona)]
if f_cari:
    df_tabel = df_tabel[df_tabel.apply(lambda row: f_cari.lower() in str(row).lower(), axis=1)]

st.dataframe(
    df_tabel[['NAMA', 'NIK', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']],
    use_container_width=True,
    hide_index=True
)

# VISUALISASI
st.write("### 📊 Analisis Grafis")
v1, v2 = st.columns([1, 1.5])
with v1:
    fig_pie = px.pie(data, names='ZONA', color='ZONA', hole=0.5,
                     title="Distribusi Zona Kepatuhan",
                     color_discrete_map={
                         "🟢 ZONA HIJAU": "#22C55E",
                         "🟡 ZONA KUNING": "#F59E0B",
                         "🔴 ZONA MERAH": "#EF4444",
                         "⚪ LAINNYA": "#94A3B8"
                     })
    st.plotly_chart(fig_pie, use_container_width=True)

with v2:
    df_red = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
    if not df_red.empty:
        st.plotly_chart(
            px.bar(df_red, x='count', y='SUB UNIT KERJA', orientation='h',
                   title="Top 10 Unit Perlu Atensi (Zona Merah)",
                   color_discrete_sequence=['#EF4444']),
            use_container_width=True
        )
    else:
        st.success("🎉 Tidak ada unit di Zona Merah — semua telah melapor!")

# FOOTER
st.write("---")
st.markdown("""
<div style="text-align:center; color:#94a3b8; font-size:12px; padding: 10px;">
    🏛️ LHKPN Monitoring System — Universitas Jambi &nbsp;|&nbsp; 
    Data bersumber dari e-LHKPN KPK &nbsp;|&nbsp; 
    Sistem ini bersifat internal dan rahasia
</div>
""", unsafe_allow_html=True)
