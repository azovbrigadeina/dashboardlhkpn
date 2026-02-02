import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. FORCE LIGHT MODE & CUSTOM CSS ---
st.set_page_config(page_title="LHKPN UNJA", layout="wide")

st.markdown("""
    <style>
    /* Memaksa warna latar belakang seluruh halaman menjadi putih terang */
    .stApp {
        background-color: #FFFFFF;
    }
    
    /* Memaksa semua teks utama menjadi hitam agar terbaca */
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #101828 !important;
    }

    /* Styling Sidebar agar tetap putih/terang */
    [data-testid="stSidebar"] {
        background-color: #F9FAFB !important;
        border-right: 1px solid #EAECF0;
    }

    /* Styling Kartu Metric agar putih dengan teks hitam */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF !important;
        border: 1px solid #EAECF0 !important;
        padding: 20px;
        border-radius: 12px;
    }
    
    /* Memperbaiki warna teks di dalam dataframe agar tidak putih */
    .stDataFrame div {
        color: #101828 !important;
    }

    /* Tombol Login Biru */
    .stButton>button {
        background-color: #1570EF !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA DATA ---
def proses_data_unja(df, filter_bulan):
    df.columns = df.columns.str.strip()
    # Cleaning NIK dari tanda petik agar deduplikasi akurat
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[\'\" ]", "", regex=True)
    
    def get_zona(row):
        status = str(row['Status LHKPN']).strip()
        bulan = str(row['BULAN']).strip().upper()
        if status == "Diumumkan Lengkap" and bulan == "JANUARI": return 1, "🟢 ZONA HIJAU"
        if status == "Terverifikasi Lengkap" and bulan == "FEBRUARI": return 2, "🟡 ZONA KUNING"
        if status == "Draft" and bulan == "MARET": return 3, "🔴 ZONA MERAH"
        if status == "Belum Lapor": return 5, "⚫ ZONA HITAM"
        return 4, "⚪ LAINNYA"

    df['rank'], df['ZONA'] = zip(*df.apply(get_zona, axis=1))
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.upper() == filter_bulan]
    
    return df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')

# --- 3. LOGIN PAGE ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.write("#")
        st.markdown("<h2 style='text-align: center;'>Sistem Monitoring LHKPN</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Universitas Jambi</p>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Masuk Ke Dashboard", use_container_width=True):
            if p == "123456":
                st.session_state['auth'] = True
                st.rerun()
            else: st.error("Akses Ditolak")
    st.stop()

# --- 4. DASHBOARD UTAMA ---
with st.sidebar:
    st.markdown("<h3 style='color: #101828;'>UNJA MONITORING</h3>", unsafe_allow_html=True)
    if st.button("Keluar"):
        st.session_state['auth'] = False
        st.rerun()
    st.divider()
    file_upload = st.file_uploader("Upload File (Excel/CSV)", type=["xlsx", "csv"])

if file_upload:
    # Membaca file dengan aman
    try:
        if file_upload.name.endswith('.csv'):
            raw = pd.read_csv(file_upload)
        else:
            raw = pd.read_excel(file_upload)
            
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Pilih Periode:", list_bln)
        
        data = proses_data_unja(raw, sel_bln)

        # Header
        st.markdown(f"<h1>Dashboard Kepatuhan LHKPN</h1>", unsafe_allow_html=True)
        st.markdown(f"<b>Universitas Jambi</b> — Periode: {sel_bln}", unsafe_allow_html=True)
        st.write("---")

        # Metrik Utama
        m1, m2, m3, m4 = st.columns(4)
        total = len(data)
        hitam = len(data[data['ZONA'] == "⚫ ZONA HITAM"])
        rate = ((total - hitam) / total * 100) if total > 0 else 0

        m1.metric("Wajib Lapor", total)
        m2.metric("Zona Hijau", len(data[data['ZONA'] == "🟢 ZONA HIJAU"]))
        m3.metric("Zona Hitam", hitam)
        m4.metric("Kepatuhan", f"{rate:.1f}%")

        # Visualisasi
        st.write("#")
        c1, c2 = st.columns([1, 1.5])
        with c1:
            st.markdown("##### Komposisi Zona")
            fig = px.pie(data, names='ZONA', hole=0.5, color='ZONA',
                         color_discrete_map={"🟢 ZONA HIJAU":"#12B76A", "🟡 ZONA KUNING":"#F79009", 
                                             "🔴 ZONA MERAH":"#F04438", "⚫ ZONA HITAM":"#1D2939", "⚪ LAINNYA":"#D0D5DD"})
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.markdown("##### 10 Unit Kerja Terbanyak Belum Lapor")
            df_unit = data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            df_unit.columns = ['Unit Kerja', 'Jumlah']
            fig_bar = px.bar(df_unit, x='Jumlah', y='Unit Kerja', orientation='h', color_discrete_sequence=['#1D2939'])
            st.plotly_chart(fig_bar, use_container_width=True)

        # Detail Tabel
        with st.expander("🔍 DETAIL NAMA DAN STATUS"):
            st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], use_container_width=True)

    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
else:
    st.info("Silakan unggah database LHKPN melalui sidebar.")
