import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. SET PAGE CONFIG ---
st.set_page_config(page_title="Executive LHKPN Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- 2. CUSTOM CSS FOR BEAUTIFICATION ---
st.markdown("""
    <style>
    /* Mengubah font dan background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main { background-color: #f4f7f9; }
    
    /* Styling Kartu Metric */
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; color: #1e293b; }
    div[data-testid="stMetricLabel"] { font-size: 14px; color: #64748b; font-weight: 600; }
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
        border: 1px solid #f1f5f9;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] { background-color: #0f172a; color: white; }
    section[data-testid="stSidebar"] .stMarkdown { color: white; }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        border: none;
        background-color: #3b82f6;
        color: white;
        font-weight: 600;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #2563eb; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
def process_data(df, filter_bulan):
    df.columns = df.columns.str.strip()
    df['NIK'] = df['NIK'].astype(str).str.replace("'", "")
    
    def get_rank(row):
        status = str(row['Status LHKPN']).strip()
        bulan = str(row['BULAN']).strip().upper()
        if status == "Diumumkan Lengkap" and bulan == "JANUARI": return 1, "🟢 ZONA HIJAU"
        if status == "Terverifikasi Lengkap" and bulan == "FEBRUARI": return 2, "🟡 ZONA KUNING"
        if status == "Draft" and bulan == "MARET": return 3, "🔴 ZONA MERAH"
        if status == "Belum Lapor": return 5, "⚫ ZONA HITAM"
        return 4, "⚪ LAINNYA"

    df['rank'], df['PREDIKAT'] = zip(*df.apply(get_rank, axis=1))
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.upper() == filter_bulan]
    
    return df.sort_values('rank').drop_duplicates(subset=['NIK'], keep='first')

# --- 4. AUTHENTICATION ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("#")
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100) # Logo placeholder
        st.title("Executive Login")
        st.markdown("---")
        user = st.text_input("Username", value="Pimpinan")
        pw = st.text_input("Password", type="password")
        if st.button("Masuk Ke Dashboard"):
            if pw == "123456":
                st.session_state['auth'] = True
                st.rerun()
            else:
                st.error("Akses Ditolak: Password Salah")
    st.stop()

# --- 5. MAIN CONTENT ---
# Sidebar controls
with st.sidebar:
    st.markdown("### 🎛️ NAVIGATION")
    if st.button("🚪 Logout"):
        st.session_state['auth'] = False
        st.rerun()
    st.divider()
    up_file = st.file_uploader("📂 Upload File Data", type=["xlsx"])
    st.divider()
    st.info("💡 **Tips:** Pilih mode GLOBAL untuk melihat status kepatuhan final setiap personil.")

if up_file:
    raw_df = pd.read_excel(up_file)
    list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw_df['BULAN'].unique() if pd.notna(b)])
    sel_bln = st.sidebar.selectbox("📅 Pilih Periode View:", list_bln)
    
    df = process_data(raw_df, sel_bln)

    # --- TOP HEADER ---
    st.markdown(f"## 🏛️ Monitoring Kepatuhan LHKPN - {sel_bln}")
    st.markdown(f"**Data Unik:** {len(df)} Personil Terdeteksi")
    st.write("#")

    # --- KPI CARDS ---
    c1, c2, c3, c4, c5 = st.columns(5)
    hitam = len(df[df['PREDIKAT'] == "⚫ ZONA HITAM"])
    rate = ((len(df) - hitam) / len(df) * 100) if len(df) > 0 else 0
    
    c1.metric("TOTAL PERSONIL", len(df))
    c2.metric("🟢 ZONA HIJAU", len(df[df['PREDIKAT'] == "🟢 ZONA HIJAU"]))
    c3.metric("🔴 ZONA MERAH", len(df[df['PREDIKAT'] == "🔴 ZONA MERAH"]))
    c4.metric("⚫ ZONA HITAM", hitam)
    c5.metric("KEPATUHAN (%)", f"{rate:.1f}%")

    st.write("#")

    # --- CHARTS SECTION ---
    row1_1, row1_2 = st.columns([1, 1.5])
    
    with row1_1:
        st.markdown("#### 🍩 Distribusi Predikat")
        fig_donut = px.pie(df, names='PREDIKAT', hole=0.5,
                           color='PREDIKAT', color_discrete_map={
                               "🟢 ZONA HIJAU":"#10b981", "🟡 ZONA KUNING":"#f59e0b", 
                               "🔴 ZONA MERAH":"#ef4444", "⚫ ZONA HITAM":"#1e293b", "⚪ LAINNYA":"#94a3b8"})
        fig_donut.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_donut, use_container_width=True)

    with row1_2:
        st.markdown("#### 🚨 Sub-Unit Paling Kritis (Zona Hitam)")
        hitam_data = df[df['PREDIKAT'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts().reset_index()
        hitam_data.columns = ['Unit', 'Jumlah']
        fig_bar = px.bar(hitam_data.head(10), x='Jumlah', y='Unit', orientation='h', 
                         color_discrete_sequence=['#1e293b'])
        fig_bar.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- LEADERBOARD & TABLE ---
    st.divider()
    st.markdown("### 🏆 Leaderboard Kepatuhan Sub-Unit")
    col_l1, col_l2 = st.columns(2)
    
    with col_l1:
        st.markdown("<h5 style='color: #10b981;'>Paling Patuh (Hijau)</h5>", unsafe_allow_html=True)
        top_h = df[df['PREDIKAT'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts().head(5)
        st.dataframe(top_h, use_container_width=True)

    with col_l2:
        st.markdown("<h5 style='color: #ef4444;'>Paling Merah (Draft Maret)</h5>", unsafe_allow_html=True)
        top_m = df[df['PREDIKAT'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().head(5)
        st.dataframe(top_m, use_container_width=True)

    st.write("#")
    with st.expander("📄 KLIK UNTUK MELIHAT TABEL DETAIL LENGKAP"):
        st.dataframe(df[['NAMA', 'JABATAN', 'SUB UNIT KERJA', 'Status LHKPN', 'PREDIKAT']], use_container_width=True)

else:
    st.markdown("""
        <div style='text-align: center; padding: 100px;'>
            <h2 style='color: #64748b;'>👋 Selamat Datang, Pimpinan</h2>
            <p style='color: #94a3b8;'>Silakan unggah file data LHKPN gabungan melalui sidebar untuk memuat analisis kepatuhan.</p>
        </div>
    """, unsafe_allow_html=True)
