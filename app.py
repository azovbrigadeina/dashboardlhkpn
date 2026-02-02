import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & APP IDENTITY ---
st.set_page_config(page_title="LHKPN Universitas Jambi", layout="wide", initial_sidebar_state="expanded")

# --- 2. PREMIUM CSS STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    /* Background Dashboard */
    .main { background-color: #fcfcfd; }
    
    /* Card Metrics */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #f2f4f7;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
    }
    
    /* Sidebar Dark Mode */
    section[data-testid="stSidebar"] {
        background-color: #101828;
    }
    
    /* Hide Header Streamlit */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom Alert Success/Error */
    .stAlert { border-radius: 12px; border: none; }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE (BACKEND LOGIC) ---
def clean_and_process(df, filter_bulan):
    df.columns = df.columns.str.strip()
    # Identifikasi NIK tanpa menampilkan teks teknis
    df['NIK_HIDDEN'] = df['NIK'].astype(str).str.replace("'", "")
    
    def get_zone(row):
        status = str(row['Status LHKPN']).strip()
        bulan = str(row['BULAN']).strip().upper()
        if status == "Diumumkan Lengkap" and bulan == "JANUARI": return 1, "🟢 ZONA HIJAU"
        if status == "Terverifikasi Lengkap" and bulan == "FEBRUARI": return 2, "🟡 ZONA KUNING"
        if status == "Draft" and bulan == "MARET": return 3, "🔴 ZONA MERAH"
        if status == "Belum Lapor": return 5, "⚫ ZONA HITAM"
        return 4, "⚪ LAINNYA"

    df['rank'], df['ZONA'] = zip(*df.apply(get_zone, axis=1))
    
    if filter_bulan != "SELURUH PERIODE (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.upper() == filter_bulan]
    
    # Ambil status terbaik per individu
    return df.sort_values('rank').drop_duplicates(subset=['NIK_HIDDEN'], keep='first')

# --- 4. AUTHENTICATION ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.write("#")
        st.markdown("<h1 style='text-align: center; color: #101828;'>Sistem Monitoring LHKPN</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #667085;'>Universitas Jambi</p>", unsafe_allow_html=True)
        with st.form("Login"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk Ke Dashboard", use_container_width=True):
                if pw == "123456":
                    st.session_state['authenticated'] = True
                    st.rerun()
                else: st.error("Password Salah")
    st.stop()

# --- 5. DASHBOARD INTERFACE ---
with st.sidebar:
    st.markdown("<h2 style='color: white;'>UNJA LHKPN</h2>", unsafe_allow_html=True)
    if st.button("🚪 Keluar"):
        st.session_state['authenticated'] = False
        st.rerun()
    st.divider()
    file_excel = st.file_uploader("Upload Database (.xlsx)", type=["xlsx"])
    st.divider()

if file_excel:
    raw_data = pd.read_excel(file_excel)
    list_bulan = ["SELURUH PERIODE (AKUMULASI)"] + sorted([str(b).upper() for b in raw_data['BULAN'].unique() if pd.notna(b)])
    pilih_bulan = st.sidebar.selectbox("Pilih Periode Laporan:", list_bulan)
    
    data = clean_and_process(raw_data, pilih_bulan)

    # --- TOP SECTION ---
    st.markdown(f"<h1 style='color: #101828; margin-bottom: 0;'>Dashboard Kepatuhan Pelaporan LHKPN</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #667085; font-size: 18px;'>Universitas Jambi • Periode: {pilih_bulan}</p>", unsafe_allow_html=True)
    st.write("#")

    # --- KPI METRICS ---
    k1, k2, k3, k4, k5 = st.columns(5)
    total_wl = len(data)
    hitam = len(data[data['ZONA'] == "⚫ ZONA HITAM"])
    patuh_per = ((total_wl - hitam) / total_wl * 100) if total_wl > 0 else 0

    k1.metric("Wajib Lapor", f"{total_wl}")
    k2.metric("Zona Hijau", len(data[data['ZONA'] == "🟢 ZONA HIJAU"]))
    k3.metric("Zona Merah", len(data[data['ZONA'] == "🔴 ZONA MERAH"]))
    k4.metric("Zona Hitam", hitam)
    k5.metric("Kepatuhan", f"{patuh_per:.1f}%")

    st.write("#")

    # --- VISUALIZATION ---
    col_pie, col_bar = st.columns([1, 1.5])
    
    with col_pie:
        st.markdown("### 📊 Status Kepatuhan")
        fig_pie = px.pie(data, names='ZONA', hole=0.6,
                         color='ZONA', color_discrete_map={
                             "🟢 ZONA HIJAU":"#12B76A", "🟡 ZONA KUNING":"#F79009", 
                             "🔴 ZONA MERAH":"#F04438", "⚫ ZONA HITAM":"#1D2939", "⚪ LAINNYA":"#98A2B3"})
        fig_pie.update_layout(margin=dict(l=0,r=0,b=0,t=0), showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        st.markdown("### 🚨 Unit Kerja Belum Lapor (Zona Hitam)")
        df_hitam = data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts().reset_index()
        df_hitam.columns = ['Unit Kerja', 'Jumlah']
        fig_bar = px.bar(df_hitam.head(10), x='Jumlah', y='Unit Kerja', orientation='h', 
                         color_discrete_sequence=['#1D2939'])
        fig_bar.update_layout(margin=dict(l=0,r=0,b=0,t=0), height=300, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- RANKING TABLE ---
    st.divider()
    st.markdown("### 🏆 Peringkat Kepatuhan Unit Kerja")
    t1, t2 = st.columns(2)
    
    with t1:
        st.success("Unit Kerja Teladan (Zona Hijau)")
        unit_h = data[data['ZONA'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts().reset_index()
        unit_h.columns = ['Unit Kerja', 'Personil']
        st.dataframe(unit_h, use_container_width=True, hide_index=True)

    with t2:
        st.error("Unit Kerja Perhatian (Zona Merah)")
        unit_m = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index()
        unit_m.columns = ['Unit Kerja', 'Personil']
        st.dataframe(unit_m, use_container_width=True, hide_index=True)

    # --- DETAIL DATA ---
    st.write("#")
    with st.expander("🔍 DATA LENGKAP WAJIB LAPOR (KLIK UNTUK MELIHAT)"):
        # Tampilkan kolom yang relevan saja bagi pimpinan
        st.dataframe(data[['NAMA', 'JABATAN', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], 
                     use_container_width=True, hide_index=True)

else:
    st.markdown("<div style='text-align: center; padding: 100px;'><h3>Silakan Unggah Database LHKPN UNJA untuk Memulai Analysis</h3></div>", unsafe_allow_html=True)
