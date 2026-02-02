import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & STYLE ---
st.set_page_config(page_title="LHKPN Universitas Jambi", layout="wide")

st.markdown("""
    <style>
    .stMetric {
        background-color: rgba(151, 166, 195, 0.1);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(151, 166, 195, 0.2);
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA DATA (NIK CLEANING & 4 ZONA) ---
def proses_data_unja(df, filter_bulan):
    df.columns = df.columns.str.strip()
    # Hapus tanda petik satu pada NIK agar deduplikasi akurat
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[\'\" ]", "", regex=True)
    
    def get_zona(row):
        status = str(row['Status LHKPN']).strip()
        bulan = str(row['BULAN']).strip().upper()
        # Logika Predikat
        if status == "Diumumkan Lengkap" and bulan == "JANUARI": return 1, "🟢 ZONA HIJAU"
        if status == "Terverifikasi Lengkap" and bulan == "FEBRUARI": return 2, "🟡 ZONA KUNING"
        if status == "Draft" and bulan == "MARET": return 3, "🔴 ZONA MERAH"
        if status == "Belum Lapor": return 5, "⚫ ZONA HITAM"
        return 4, "⚪ LAINNYA"

    df['rank'], df['ZONA'] = zip(*df.apply(get_zona, axis=1))
    
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.upper() == filter_bulan]
    
    # AMBIL 1 NIK 1 STATUS TERBAIK
    return df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')

# --- 3. LOGIN ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.write("#")
        st.title("Sistem LHKPN UNJA")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Masuk", use_container_width=True):
            if p == "123456":
                st.session_state['auth'] = True
                st.rerun()
            else: st.error("Salah!")
    st.stop()

# --- 4. DASHBOARD UTAMA ---
with st.sidebar:
    st.title("UNJA DASHBOARD")
    if st.button("Log Out"):
        st.session_state['auth'] = False
        st.rerun()
    st.divider()
    file_upload = st.file_uploader("Upload Database", type=["xlsx", "csv"])

if file_upload:
    try:
        if file_upload.name.endswith('.csv'):
            raw = pd.read_csv(file_upload)
        else:
            raw = pd.read_excel(file_upload)
            
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Filter Periode:", list_bln)
        
        data = proses_data_unja(raw, sel_bln)

        # Header
        st.title("🏛️ Monitoring Kepatuhan LHKPN")
        st.subheader(f"Universitas Jambi — {sel_bln}")
        st.write("---")

        # KPI Metrics (4 Zona + Total)
        m1, m2, m3, m4, m5 = st.columns(5)
        total = len(data)
        h = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
        k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
        m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])
        hitam = len(data[data['ZONA'] == "⚫ ZONA HITAM"])

        m1.metric("Wajib Lapor", total)
        m2.metric("🟢 Hijau", h)
        m3.metric("🟡 Kuning", k)
        m4.metric("🔴 Merah", m)
        m5.metric("⚫ Hitam", hitam)

        st.write("#")

        # Visualisasi Utama
        col_pie, col_bar = st.columns([1, 1.5])
        with col_pie:
            st.markdown("### Komposisi Kepatuhan")
            fig = px.pie(data, names='ZONA', hole=0.5, color='ZONA',
                         color_discrete_map={
                             "🟢 ZONA HIJAU":"#22C55E", "🟡 ZONA KUNING":"#F59E0B", 
                             "🔴 ZONA MERAH":"#EF4444", "⚫ ZONA HITAM":"#64748B", "⚪ LAINNYA":"#94A3B8"})
            st.plotly_chart(fig, use_container_width=True)
        
        with col_bar:
            st.markdown("### 🚨 Unit Kerja Kritis (Zona Hitam)")
            df_hitam = data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            df_hitam.columns = ['Unit Kerja', 'Jumlah']
            fig_bar = px.bar(df_hitam, x='Jumlah', y='Unit Kerja', orientation='h', color_discrete_sequence=['#64748B'])
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- PERINGKAT LEADERSHIP (UNIT KERJA) ---
        st.divider()
        st.markdown("### 🏆 Peringkat Kepemimpinan Unit Kerja")
        l1, l2 = st.columns(2)
        
        with l1:
            st.markdown("<h5 style='color: #22C55E;'>Top 5 Unit Kerja Patuh (Zona Hijau)</h5>", unsafe_allow_html=True)
            leader_h = data[data['ZONA'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts().reset_index()
            leader_h.columns = ['Unit Kerja', 'Jumlah Personil']
            st.dataframe(leader_h.head(5), use_container_width=True, hide_index=True)

        with l2:
            st.markdown("<h5 style='color: #EF4444;'>5 Unit Kerja Terbanyak Belum Lapor (Hitam)</h5>", unsafe_allow_html=True)
            leader_hitam = data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts().reset_index()
            leader_hitam.columns = ['Unit Kerja', 'Jumlah Personil']
            st.dataframe(leader_hitam.head(5), use_container_width=True, hide_index=True)

        # Detail Data
        st.write("#")
        with st.expander("🔍 Detail Seluruh Nama Wajib Lapor"):
            st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], 
                         use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Silakan unggah file database untuk melihat peringkat kepemimpinan.")
