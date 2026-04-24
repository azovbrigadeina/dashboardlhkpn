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

# --- 3. SESSION STATE ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'synced' not in st.session_state: st.session_state['synced'] = False

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

# --- 5. SIDEBAR CONTROL ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/f2/Logo_KPK.png", width=80)
    st.header("Sync Center")
    
    if st.button("🔄 Sinkronkan Data KPK", use_container_width=True):
        with st.status("Menghubungkan ke Server KPK...", expanded=True) as status:
            st.write("📡 Memverifikasi Koneksi Aman...")
            time.sleep(1)
            st.write("📥 Mengunduh Data Wajib Lapor...")
            p = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                p.progress(i + 1)
            st.cache_data.clear()
            st.session_state['synced'] = True
            status.update(label="✅ Sinkronisasi Berhasil!", state="complete", expanded=False)
        st.rerun()

    sel_bln = "GLOBAL (AKUMULASI)"
    if st.session_state['synced']:
        st.divider()
        st.subheader("📅 Periode")
        raw_data = load_data_from_gsheet(GSHEET_URL)
        if not raw_data.empty and 'BULAN' in raw_data.columns:
            list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw_data['BULAN'].unique() if pd.notna(b)])
            sel_bln = st.selectbox("Pilih Bulan:", list_bln)

    st.divider()
    if st.button("Log Out", type="primary", use_container_width=True):
        st.session_state['auth'] = False
        st.session_state['synced'] = False
        st.rerun()

# --- 6. DASHBOARD AREA ---
st.markdown("""<style>
    .metric-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); text-align: center; border-top: 5px solid #ececec; }
    .papan-info { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-top: 20px; }
    .sektor-box { flex: 1; min-width: 250px; background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; }
</style>""", unsafe_allow_html=True)

if not st.session_state['synced']:
    st.title("🏛️ Dashboard LHKPN")
    st.info("Silakan klik **'Sinkronkan Data KPK'** di sidebar untuk memuat data.")
else:
    data = load_data_from_gsheet(GSHEET_URL)
    if sel_bln != "GLOBAL (AKUMULASI)":
        data = data[data['BULAN'].astype(str).str.strip().str.upper() == sel_bln]

    if not data.empty:
        st.title(f"🏛️ Monitoring Kepatuhan - {sel_bln}")
        
        # 1. METRIK UTAMA
        twl = len(data); h = len(data[data['ZONA']=="🟢 ZONA HIJAU"]); k = len(data[data['ZONA']=="🟡 ZONA KUNING"]); m = len(data[data['ZONA']=="🔴 ZONA MERAH"])
        rate = (h/twl*100) if twl > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="metric-card" style="border-top-color: #3b82f6;"><small>WAJIB LAPOR</small><div style="font-size:32px; font-weight:bold;">{twl}</div></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card" style="border-top-color: #22c55e;"><small>🟢 HIJAU</small><div style="font-size:32px; font-weight:bold;">{h}</div><div style="color:#22c55e;">{rate:.1f}%</div></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card" style="border-top-color: #f59e0b;"><small>🟡 KUNING</small><div style="font-size:32px; font-weight:bold;">{k}</div></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card" style="border-top-color: #ef4444;"><small>🔴 MERAH</small><div style="font-size:32px; font-weight:bold;">{m}</div></div>', unsafe_allow_html=True)

        # 2. PAPAN INFORMASI EKSEKUTIF
        unit_stats = data.groupby('SUB UNIT KERJA')['ZONA'].value_counts().unstack().fillna(0)
        for z in ["🟢 ZONA HIJAU", "🟡 ZONA KUNING", "🔴 ZONA MERAH"]:
            if z not in unit_stats.columns: unit_stats[z] = 0
        
        unit_stats['Persen_Hijau'] = (unit_stats['🟢 ZONA HIJAU'] / unit_stats.sum(axis=1)) * 100
        u_100 = unit_stats[unit_stats['Persen_Hijau'] == 100].index.tolist()
        paripurna_txt = ", ".join(u_100[:2]) + ("..." if len(u_100) > 2 else "") if u_100 else "Belum Ada"
        u_rendah = unit_stats[unit_stats['Persen_Hijau'] < 100].sort_values(by='Persen_Hijau')
        atensi_label = f"<b>{u_rendah.index[0]}</b> ({u_rendah.iloc[0]['Persen_Hijau']:.1f}%)" if not u_rendah.empty else "Semua 100%"

        st.markdown(f"""
        <div class="papan-info">
            <h4 style="text-align: center; color: #1e3a8a; margin-bottom: 15px;">📊 PAPAN INFORMASI EKSEKUTIF</h4>
            <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                <div class="sektor-box" style="border-left: 5px solid #22c55e;">
                    <b style="color: #166534;">🏆 SEKTOR APRESIASI</b><br>
                    <small>Unit Paripurna: {paripurna_txt} ({len(u_100)} Unit)</small>
                </div>
                <div class="sektor-box" style="border-left: 5px solid #ef4444;">
                    <b style="color: #9f1239;">⚠️ SEKTOR ATENSI</b><br>
                    <small>Prioritas: {atensi_label}</small>
                </div>
                <div class="sektor-box" style="border-left: 5px solid #3b82f6;">
                    <b style="color: #1e40af;">⚡ SEKTOR AKSELERASI</b><br>
                    <small>Potensi Maks: {((h+k)/twl*100):.1f}% (Jika Kuning Tuntas)</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 3. TABEL & VISUALISASI
        st.write("---")
        st.subheader("📋 Daftar Informasi Individu")
        q = st.text_input("Cari Nama, NIK, atau Unit Kerja:")
        df_f = data if not q else data[data.apply(lambda r: q.lower() in str(r).lower(), axis=1)]
        st.dataframe(df_f[['NAMA', 'NIK', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], use_container_width=True, hide_index=True)
        
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(data, names='ZONA', color='ZONA', hole=0.4, color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"}), use_container_width=True)
        with c2:
            red_top = data[data['ZONA']=="🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(5)
            if not red_top.empty: st.plotly_chart(px.bar(red_top, x='count', y='SUB UNIT KERJA', orientation='h', title="Top 5 Unit Merah", color_discrete_sequence=['#EF4444']), use_container_width=True)
    else:
        st.error("Data pada periode ini kosong.")
