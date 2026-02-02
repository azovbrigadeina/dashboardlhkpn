import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi & Session State
st.set_page_config(page_title="Dashboard LHKPN Unifikasi", layout="wide")
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- LOGIKA PENENTUAN PREDIKAT (Ditingkatkan) ---
def proses_data_unik(df):
    # Bersihkan nama kolom
    df.columns = df.columns.str.strip()
    
    # Pastikan NIK diperlakukan sebagai string agar tidak berantakan
    df['NIK'] = df['NIK'].astype(str)

    # Logika Penentuan Predikat per Baris
    def get_row_predikat(row):
        status = str(row['Status LHKPN']).strip()
        bulan = str(row['BULAN']).strip().upper()
        
        if status == "Diumumkan Lengkap" and bulan == "JANUARI":
            return 1, "🟢 ZONA HIJAU"
        elif status == "Terverifikasi Lengkap" and bulan == "FEBRUARI":
            return 2, "🟡 ZONA KUNING"
        elif status == "Draft" and bulan == "MARET":
            return 3, "🔴 ZONA MERAH"
        elif status == "Belum Lapor":
            return 5, "⚫ ZONA HITAM"
        else:
            return 4, "⚪ LAINNYA"

    # Tambahkan kolom sementara untuk ranking predikat (makin kecil makin baik)
    df['rank'], df['PREDIKAT'] = zip(*df.apply(get_row_predikat, axis=1))

    # PROSES UNIFIKASI: Ambil 1 NIK 1 Status terbaik
    # Kita urutkan berdasarkan NIK dan Rank terkecil (terbaik)
    df_sorted = df.sort_values(by=['NIK', 'rank'])
    
    # Drop duplikat, simpan baris dengan predikat terbaik untuk tiap NIK
    df_unik = df_sorted.drop_duplicates(subset=['NIK'], keep='first')
    
    return df_unik

# --- HALAMAN LOGIN ---
def login_page():
    # ... (sama seperti sebelumnya) ...
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🔐 Login Sistem</h1>", unsafe_allow_html=True)
        password = st.text_input("Password", type="password")
        if st.button("Masuk", use_container_width=True):
            if password == "123456":
                st.session_state['logged_in'] = True
                st.rerun()

# --- HALAMAN UTAMA ---
def main_dashboard():
    st.sidebar.title("👤 Admin Panel")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("🏛️ Dashboard Unifikasi Wajib Lapor LHKPN")
    uploaded_file = st.sidebar.file_uploader("Unggah Gabungan File Excel", type=["xlsx"])

    if uploaded_file:
        raw_df = pd.read_excel(uploaded_file)
        
        # Eksekusi logika pembersihan data ganda
        df = proses_data_unik(raw_df)

        # --- Dashboard Metrics ---
        total_individu = len(df) # Sekarang menghitung NIK unik
        hijau = len(df[df['PREDIKAT'] == "🟢 ZONA HIJAU"])
        kuning = len(df[df['PREDIKAT'] == "🟡 ZONA KUNING"])
        merah = len(df[df['PREDIKAT'] == "🔴 ZONA MERAH"])
        hitam = len(df[df['PREDIKAT'] == "⚫ ZONA HITAM"])
        persen = ((total_individu - hitam) / total_individu * 100) if total_individu > 0 else 0

        st.subheader("📊 Statistik Individu Wajib Lapor (Data Unik)")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Total Individu", f"{total_individu}")
        m2.metric("🟢 Hijau", hijau)
        m3.metric("🟡 Kuning", kuning)
        m4.metric("🔴 Merah", merah)
        m5.metric("⚫ Hitam", hitam, delta_color="inverse")
        m6.metric("Kepatuhan", f"{persen:.1f}%")

        # --- Visualisasi ---
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(df, names='PREDIKAT', title="Proporsi Predikat Kepatuhan (Individu)",
                             color='PREDIKAT', color_discrete_map={
                                 "🟢 ZONA HIJAU": "#2E7D32", "🟡 ZONA KUNING": "#FBC02D",
                                 "🔴 ZONA MERAH": "#D32F2F", "⚫ ZONA HITAM": "#212121", "⚪ LAINNYA": "#9E9E9E"
                             })
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with c2:
            # Tabel Sub-Unit Kritis berdasarkan JUMLAH ORANG, bukan jumlah baris
            st.write("### 🚨 Sub-Unit Paling Kritis (Hitam)")
            hitam_df = df[df['PREDIKAT'] == "⚫ ZONA HITAM"]
            unit_kritis = hitam_df['SUB UNIT KERJA'].value_counts().reset_index()
            unit_kritis.columns = ['Sub Unit Kerja', 'Jumlah Orang']
            st.dataframe(unit_kritis, use_container_width=True, height=300)

        # --- Leaderboard ---
        st.divider()
        st.subheader("🏆 Leaderboard Performa Sub-Unit (Top 10 Orang)")
        l1, l2, l3 = st.columns(3)
        with l1:
            st.success("Top 10 Hijau")
            st.bar_chart(df[df['PREDIKAT'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts().head(10))
        with l2:
            st.warning("Top 10 Kuning")
            st.bar_chart(df[df['PREDIKAT'] == "🟡 ZONA KUNING"]['SUB UNIT KERJA'].value_counts().head(10))
        with l3:
            st.error("Top 10 Merah")
            st.bar_chart(df[df['PREDIKAT'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().head(10))

    else:
        st.info("Silakan unggah file Excel gabungan Januari-Maret Anda.")

# Navigasi
if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()
