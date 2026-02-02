import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="LHKPN Universitas Jambi", layout="wide")

# CSS Adaptif agar teks otomatis menyesuaikan (Hitam di terang, Putih di gelap)
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

# --- 2. LOGIKA PENENTUAN 4 ZONA ---
def proses_data_lhkpn(df, filter_bulan):
    df.columns = df.columns.str.strip()
    
    # Membersihkan NIK dari tanda petik agar deduplikasi akurat
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[\'\" ]", "", regex=True)
    
    def tentukan_zona(row):
        status = str(row['Status LHKPN']).strip()
        bulan = str(row['BULAN']).strip().upper()
        
        # 1. ZONA HIJAU (Lengkap di Januari)
        if status == "Diumumkan Lengkap" and bulan == "JANUARI":
            return 1, "🟢 ZONA HIJAU"
        # 2. ZONA KUNING (Verifikasi di Februari)
        elif status == "Terverifikasi Lengkap" and bulan == "FEBRUARI":
            return 2, "🟡 ZONA KUNING"
        # 3. ZONA MERAH (Masih Draft di Maret)
        elif status == "Draft" and bulan == "MARET":
            return 3, "🔴 ZONA MERAH"
        # 4. ZONA HITAM (Belum Lapor sama sekali)
        elif status == "Belum Lapor":
            return 5, "⚫ ZONA HITAM"
        # Lainnya (Status di luar kriteria spesifik)
        else:
            return 4, "⚪ LAINNYA"

    # Terapkan ranking untuk mengambil status terbaik saat digabung
    df['rank'], df['ZONA'] = zip(*df.apply(tentukan_zona, axis=1))
    
    # Jika filter bulan dipilih
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.upper() == filter_bulan]
    
    # DEDUPLIKASI: 1 NIK hanya diambil 1 baris dengan ZONA terbaik
    df_final = df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')
    return df_final

# --- 3. LOGIN SISTEM ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.write("#")
        st.title("Sistem LHKPN UNJA")
        st.write("Silakan masuk untuk akses dashboard")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Masuk Sekarang", use_container_width=True):
            if password == "123456":
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Password salah. Gunakan 123456")
    st.stop()

# --- 4. DASHBOARD UTAMA ---
with st.sidebar:
    st.title("UNJA MONITORING")
    if st.button("Logout"):
        st.session_state['authenticated'] = False
        st.rerun()
    st.divider()
    uploaded_file = st.file_uploader("Upload File Gabungan (Jan-Mar)", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # Load Data
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
            
        list_bulan = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in df_raw['BULAN'].unique() if pd.notna(b)])
        pilihan_bulan = st.sidebar.selectbox("Pilih Periode View:", list_bulan)
        
        # Proses Unifikasi
        data = proses_data_lhkpn(df_raw, pilihan_bulan)

        # UI Header
        st.title("📊 Dashboard Kepatuhan LHKPN")
        st.markdown(f"**Universitas Jambi** | Periode: {pilihan_bulan}")
        st.write("---")

        # Row 1: KPI Metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        total_orang = len(data)
        z_hijau = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
        z_kuning = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
        z_merah = len(data[data['ZONA'] == "🔴 ZONA MERAH"])
        z_hitam = len(data[data['ZONA'] == "⚫ ZONA HITAM"])
        persen_patuh = ((total_orang - z_hitam) / total_orang * 100) if total_orang > 0 else 0

        m1.metric("Wajib Lapor", total_orang)
        m2.metric("Hijau", z_hijau)
        m3.metric("Kuning", z_kuning)
        m4.metric("Merah", z_merah)
        m5.metric("Hitam", z_hitam)

        st.write("#")

        # Row 2: Charts
        col_pie, col_bar = st.columns([1, 1.5])
        
        with col_pie:
            st.subheader("Distribusi Zona")
            fig_pie = px.pie(data, names='ZONA', hole=0.5,
                             color='ZONA', color_discrete_map={
                                 "🟢 ZONA HIJAU": "#22C55E", 
                                 "🟡 ZONA KUNING": "#F59E0B", 
                                 "🔴 ZONA MERAH": "#EF4444", 
                                 "⚫ ZONA HITAM": "#475569", 
                                 "⚪ LAINNYA": "#94A3B8"})
            fig_pie.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_bar:
            st.subheader("Unit Kerja Paling Kritis (Zona Hitam)")
            df_hitam = data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            df_hitam.columns = ['Unit', 'Jumlah']
            fig_bar = px.bar(df_hitam, x='Jumlah', y='Unit', orientation='h', color_discrete_sequence=['#475569'])
            st.plotly_chart(fig_bar, use_container_width=True)

        # Row 3: Detail Data
        st.divider()
        with st.expander("🔍 Klik untuk melihat Detail Nama dan Predikat"):
            st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'BULAN', 'ZONA']], 
                         use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error: Pastikan kolom file sesuai. Detail: {e}")
else:
    st.info("👋 Selamat Datang. Silakan unggah file database di sidebar.")
