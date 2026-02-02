import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman & Styling
st.set_page_config(page_title="Sistem Monitoring LHKPN", layout="wide")

# Custom CSS agar halaman login di tengah
st.markdown("""
    <style>
    .login-box {
        background-color: #f0f2f6;
        padding: 30px;
        border-radius: 10px;
        border: 1px solid #d1d5db;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Fungsi Logika Predikat
def tentukan_predikat(row):
    status = str(row['Status LHKPN']).strip()
    bulan = str(row['BULAN']).strip().upper()
    
    if status == "Diumumkan Lengkap" and bulan == "JANUARI":
        return "🟢 ZONA HIJAU"
    elif status == "Terverifikasi Lengkap" and bulan == "FEBRUARI":
        return "🟡 ZONA KUNING"
    elif status == "Draft" and bulan == "MARET":
        return "🔴 ZONA MERAH"
    elif status == "Belum Lapor":
        return "⚫ ZONA HITAM"
    else:
        return "⚪ LAINNYA"

# 3. Inisialisasi Session State untuk Login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- HALAMAN LOGIN ---
def login_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.write("") 
        st.write("") 
        st.markdown("<h1 style='text-align: center;'>🔐 Login Sistem LHKPN</h1>", unsafe_allow_html=True)
        with st.container():
            username = st.text_input("Username", placeholder="Masukkan username bebas...")
            password = st.text_input("Password", type="password", placeholder="Masukkan 123456")
            
            if st.button("Masuk Sekarang", use_container_width=True):
                if password == "123456":
                    st.session_state['logged_in'] = True
                    st.success("Login Berhasil! Mengalihkan...")
                    st.rerun()
                else:
                    st.error("Password salah! Coba lagi.")

# --- HALAMAN DASHBOARD ---
def main_dashboard():
    # Tombol Logout di Sidebar
    st.sidebar.title(f"👤 User: Admin")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("🏛️ Dashboard Eksekutif Kepatuhan LHKPN")
    st.sidebar.divider()
    
    # Upload File
    st.sidebar.header("📁 Manajemen Data")
    uploaded_file = st.sidebar.file_uploader("Unggah file Excel LHKPN", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        df['PREDIKAT'] = df.apply(tentukan_predikat, axis=1)

        # Filter Pencarian Nama (Fitur Tambahan)
        search_query = st.sidebar.text_input("🔍 Cari Nama Wajib Lapor")
        
        # Filter Bulan
        list_bulan = ["SEMUA"] + sorted(df['BULAN'].unique().tolist())
        sel_month = st.sidebar.selectbox("Pilih Bulan Target:", list_bulan)
        
        # Filter Logic
        dff = df
        if sel_month != "SEMUA":
            dff = dff[dff['BULAN'] == sel_month]
        if search_query:
            dff = dff[dff['NAMA'].str.contains(search_query, case=False, na=False)]

        # --- KPI METRICS ---
        total = len(dff)
        hijau = len(dff[dff['PREDIKAT'] == "🟢 ZONA HIJAU"])
        kuning = len(dff[dff['PREDIKAT'] == "🟡 ZONA KUNING"])
        merah = len(dff[dff['PREDIKAT'] == "🔴 ZONA MERAH"])
        hitam = len(dff[dff['PREDIKAT'] == "⚫ ZONA HITAM"])
        persen = ((total - hitam) / total * 100) if total > 0 else 0

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Total WL", f"{total}")
        m2.metric("🟢 Hijau", hijau)
        m3.metric("🟡 Kuning", kuning)
        m4.metric("🔴 Merah", merah)
        m5.metric("⚫ Hitam", hitam, delta_color="inverse")
        m6.metric("Kepatuhan", f"{persen:.1f}%")

        st.divider()

        # --- ZONA KRITIS ---
        st.subheader("🚨 Daftar Semua Sub-Unit Kritis (ZONA HITAM)")
        hitam_df = dff[dff['PREDIKAT'] == "⚫ ZONA HITAM"]
        if not hitam_df.empty:
            all_hitam = hitam_df['SUB UNIT KERJA'].value_counts().reset_index()
            all_hitam.columns = ['Sub Unit Kerja', 'Jumlah Personil Belum Lapor']
            st.table(all_hitam) # Menggunakan table agar terlihat lebih formal
        else:
            st.success("✅ Tidak ada personil di Zona Hitam.")

        # --- LEADERBOARD ---
        st.subheader("🏆 Leaderboard Sub-Unit (Top 10)")
        c_h, c_k, c_m = st.columns(3)

        with c_h:
            st.info("Top 10 Zona Hijau")
            top_h = dff[dff['PREDIKAT'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts().head(10)
            if not top_h.empty: st.bar_chart(top_h, color="#2E7D32")
            else: st.write("Data Kosong")

        with c_k:
            st.warning("Top 10 Zona Kuning")
            top_k = dff[dff['PREDIKAT'] == "🟡 ZONA KUNING"]['SUB UNIT KERJA'].value_counts().head(10)
            if not top_k.empty: st.bar_chart(top_k, color="#FBC02D")
            else: st.write("Data Kosong")

        with c_m:
            st.error("Top 10 Zona Merah")
            top_m = dff[dff['PREDIKAT'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().head(10)
            if not top_m.empty: st.bar_chart(top_m, color="#D32F2F")
            else: st.write("Data Kosong")

        # --- DETAIL DATA ---
        with st.expander("🔍 Lihat Detail Data Wajib Lapor"):
            st.dataframe(dff[['NAMA', 'JABATAN', 'SUB UNIT KERJA', 'PREDIKAT']], use_container_width=True)

    else:
        st.info("Silakan unggah file Excel di sidebar untuk memulai.")

# --- LOGIKA NAVIGASI ---
if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()
