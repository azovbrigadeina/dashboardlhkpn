import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & IDENTITY ---
st.set_page_config(page_title="LHKPN Universitas Jambi", layout="wide")

# --- 2. CLEAN LIGHT UI CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .main { background-color: #f9fafb; }
    section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #f2f4f7; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #eaecf0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.1);
    }
    div[data-testid="stMetricLabel"] { color: #667085; font-size: 14px; font-weight: 600; }
    div[data-testid="stMetricValue"] { color: #101828; font-weight: 700; }
    .stButton>button { background-color: #1570ef; color: white; border-radius: 8px; border: none; font-weight: 600; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA LOGIC ---
def clean_data(df, filter_bulan):
    df.columns = df.columns.str.strip()
    # NIK digunakan sebagai kunci unik internal saja
    df['NIK_INTERNAL'] = df['NIK'].astype(str).str.replace("'", "")
    
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
    
    # Ambil status terbaik per individu unik
    return df.sort_values('rank').drop_duplicates(subset=['NIK_INTERNAL'], keep='first')

# --- 4. AUTHENTICATION ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.write("#")
        st.write("#")
        st.markdown("<h2 style='text-align: center; color: #101828;'>Sistem Monitoring LHKPN</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #667085;'>Universitas Jambi</p>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Masuk", use_container_width=True):
            if p == "123456":
                st.session_state['auth'] = True
                st.rerun()
            else: st.error("Password Salah")
    st.stop()

# --- 5. MAIN DASHBOARD ---
with st.sidebar:
    st.markdown("<h3 style='color: #101828;'>UNJA LHKPN</h3>", unsafe_allow_html=True)
    if st.button("🚪 Keluar"):
        st.session_state['auth'] = False
        st.rerun()
    st.divider()
    file_in = st.file_uploader("Upload Database LHKPN", type=["xlsx"])

if file_in:
    raw = pd.read_excel(file_in)
    bln_list = ["SELURUH PERIODE (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
    sel_bln = st.sidebar.selectbox("Pilih Periode Laporan:", bln_list)
    
    data = clean_data(raw, sel_bln)

    # Header
    st.markdown(f"<h1 style='color: #101828;'>Dashboard Kepatuhan Pelaporan LHKPN</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #667085; font-size: 16px; margin-top: -15px;'>Universitas Jambi — {sel_bln}</p>", unsafe_allow_html=True)
    st.write("#")

    # Metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    total = len(data)
    hitam = len(data[data['ZONA'] == "⚫ ZONA HITAM"])
    rate = ((total - hitam) / total * 100) if total > 0 else 0

    m1.metric("Wajib Lapor", total)
    m2.metric("Zona Hijau", len(data[data['ZONA'] == "🟢 ZONA HIJAU"]))
    m3.metric("Zona Merah", len(data[data['ZONA'] == "🔴 ZONA MERAH"]))
    m4.metric("Zona Hitam", hitam)
    m5.metric("Kepatuhan", f"{rate:.1f}%")

    st.write("#")

    # Charts Row
    c_pie, c_bar = st.columns([1, 1.3])
    with c_pie:
        st.markdown("##### Ringkasan Status")
        fig_p = px.pie(data, names='ZONA', hole=0.6,
                       color='ZONA', color_discrete_map={
                           "🟢 ZONA HIJAU":"#12B76A", "🟡 ZONA KUNING":"#F79009", 
                           "🔴 ZONA MERAH":"#F04438", "⚫ ZONA HITAM":"#344054", "⚪ LAINNYA":"#D0D5DD"})
        fig_p.update_layout(margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig_p, use_container_width=True)

    with c_bar:
        st.markdown("##### Unit Kerja Belum Lapor (Terbanyak)")
        df_h = data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
        df_h.columns = ['Unit', 'Jumlah']
        fig_b = px.bar(df_h, x='Jumlah', y='Unit', orientation='h', color_discrete_sequence=['#344054'])
        fig_b.update_layout(margin=dict(t=0,b=0,l=0,r=0), height=350, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_b, use_container_width=True)

    # Tables Row
    st.divider()
    st.markdown("### 📋 Evaluasi Unit Kerja")
    t1, t2 = st.columns(2)
    with t1:
        st.success("Unit Kerja Teladan (Zona Hijau)")
        st.dataframe(data[data['ZONA'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts(), use_container_width=True)
    with t2:
        st.error("Unit Kerja Perlu Atensi (Zona Hitam)")
        st.dataframe(data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts(), use_container_width=True)

    st.write("#")
    with st.expander("🔍 LIHAT DETAIL DAFTAR WAJIB LAPOR"):
        # Tampilkan data bersih tanpa kolom teknis
        st.dataframe(data[['NAMA', 'JABATAN', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], 
                     use_container_width=True, hide_index=True)

else:
    st.info("Silakan unggah database LHKPN di panel samping untuk memulai.")
