import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="LHKPN Monitoring System", layout="wide")

# Styling agar tampilan lebih profesional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA DATA PROCESSING ---
def proses_data_lhkpn(df, filter_bulan):
    df.columns = df.columns.str.strip()
    df['NIK'] = df['NIK'].astype(str).str.replace("'", "") # Bersihkan tanda petik pada NIK

    # Fungsi penentuan ranking (Angka rendah = Prioritas status terbaik)
    def get_rank(row):
        status = str(row['Status LHKPN']).strip()
        bulan = str(row['BULAN']).strip().upper()
        
        if status == "Diumumkan Lengkap" and bulan == "JANUARI": return 1, "🟢 ZONA HIJAU"
        if status == "Terverifikasi Lengkap" and bulan == "FEBRUARI": return 2, "🟡 ZONA KUNING"
        if status == "Draft" and bulan == "MARET": return 3, "🔴 ZONA MERAH"
        if status == "Belum Lapor": return 5, "⚫ ZONA HITAM"
        return 4, "⚪ LAINNYA"

    df['rank'], df['PREDIKAT'] = zip(*df.apply(get_rank, axis=1))

    # Jika filter bulan dipilih selain 'GLOBAL'
    if filter_bulan != "GLOBAL":
        df = df[df['BULAN'].astype(str).str.upper() == filter_bulan]
    
    # Proses Unifikasi (1 NIK 1 Data Terbaik)
    df_unik = df.sort_values('rank').drop_duplicates(subset=['NIK'], keep='first')
    return df_unik

# --- 3. SESSION STATE & LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login_page():
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.write("")
        st.markdown("<h1 style='text-align: center;'>🏛️ LHKPN LOGIN</h1>", unsafe_allow_html=True)
        st.info("Gunakan Password: **123456**")
        with st.container():
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Masuk", use_container_width=True):
                if password == "123456":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Password salah!")

# --- 4. DASHBOARD UTAMA ---
def main_dashboard():
    # Sidebar
    st.sidebar.title("🛠️ Control Panel")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    st.sidebar.divider()
    uploaded_file = st.sidebar.file_uploader("Upload Data Gabungan (.xlsx)", type=["xlsx"])
    
    if uploaded_file:
        raw_df = pd.read_excel(uploaded_file)
        
        # Filter Bulan di Sidebar
        list_bulan = ["GLOBAL"] + [str(b).upper() for b in raw_df['BULAN'].unique() if pd.notna(b)]
        selected_bulan = st.sidebar.selectbox("📅 Pilih Periode Laporan:", list_bulan)
        
        # Pencarian Nama
        search_name = st.sidebar.text_input("🔍 Cari Nama Personil:")

        # Proses Data Berdasarkan Filter
        df = proses_data_lhkpn(raw_df, selected_bulan)
        if search_name:
            df = df[df['NAMA'].str.contains(search_name, case=False, na=False)]

        # --- HEADER ---
        st.title(f"📊 Dashboard Kepatuhan - {selected_bulan}")
        st.caption(f"Menampilkan {len(df)} Wajib Lapor yang telah diverifikasi (Satu data per NIK).")

        # --- KPI SECTION ---
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        
        total_wl = len(df)
        h = len(df[df['PREDIKAT'] == "🟢 ZONA HIJAU"])
        k = len(df[df['PREDIKAT'] == "🟡 ZONA KUNING"])
        m = len(df[df['PREDIKAT'] == "🔴 ZONA MERAH"])
        hitam = len(df[df['PREDIKAT'] == "⚫ ZONA HITAM"])
        persen = ((total_wl - hitam) / total_wl * 100) if total_wl > 0 else 0

        m1.metric("Total Individu", total_wl)
        m2.metric("🟢 Hijau", h)
        m3.metric("🟡 Kuning", k)
        m4.metric("🔴 Merah", m)
        m5.metric("⚫ Hitam", hitam, delta_color="inverse")
        m6.metric("Kepatuhan", f"{persen:.1f}%")

        # --- VISUALISASI UTAMA ---
        st.divider()
        c1, c2 = st.columns([1, 1.2])

        with c1:
            st.subheader("📊 Komposisi Predikat")
            fig = px.pie(df, names='PREDIKAT', color='PREDIKAT',
                         color_discrete_map={"🟢 ZONA HIJAU":"#2E7D32", "🟡 ZONA KUNING":"#FBC02D", 
                                             "🔴 ZONA MERAH":"#D32F2F", "⚫ ZONA HITAM":"#212121", "⚪ LAINNYA":"#9E9E9E"})
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("🚨 List Sub-Unit Zona Hitam")
            hitam_df = df[df['PREDIKAT'] == "⚫ ZONA HITAM"]
            if not hitam_df.empty:
                unit_hitam = hitam_df['SUB UNIT KERJA'].value_counts().reset_index()
                unit_hitam.columns = ['Sub Unit', 'Jumlah Personil']
                st.dataframe(unit_hitam, use_container_width=True, height=300)
            else:
                st.success("Luar Biasa! Tidak ada unit di Zona Hitam.")

        # --- LEADERBOARD SECTION ---
        st.divider()
        st.subheader("🏆 Peringkat Sub-Unit Berdasarkan Zona")
        l1, l2, l3 = st.columns(3)

        with l1:
            st.markdown("##### 10 Besar Zona Hijau")
            top_h = df[df['PREDIKAT'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts().head(10)
            if not top_h.empty: st.bar_chart(top_h, color="#2E7D32")
            else: st.write("Data Kosong")

        with l2:
            st.markdown("##### 10 Besar Zona Kuning")
            top_k = df[df['PREDIKAT'] == "🟡 ZONA KUNING"]['SUB UNIT KERJA'].value_counts().head(10)
            if not top_k.empty: st.bar_chart(top_k, color="#FBC02D")
            else: st.write("Data Kosong")

        with l3:
            st.markdown("##### 10 Besar Zona Merah")
            top_m = df[df['PREDIKAT'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().head(10)
            if not top_m.empty: st.bar_chart(top_m, color="#D32F2F")
            else: st.write("Data Kosong")

        # --- TABEL DETAIL ---
        st.divider()
        with st.expander("🔍 Lihat Semua Detail Data (Individu Unik)"):
            st.dataframe(df[['NIK', 'NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'BULAN', 'PREDIKAT']], use_container_width=True)

    else:
        st.warning("Silakan unggah file Excel untuk melihat data.")

# --- ROUTING ---
if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()
