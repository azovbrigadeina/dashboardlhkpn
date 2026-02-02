import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman
st.set_page_config(page_title="LHKPN Executive Dashboard", layout="wide")

st.title("🏛️ Dashboard Kepatuhan LHKPN (Pimpinan View)")
st.markdown("Analisis real-time berdasarkan predikat kepatuhan sub-unit kerja.")

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

# 3. Sidebar: Upload & Filter
st.sidebar.header("📁 Manajemen Data")
uploaded_file = st.sidebar.file_uploader("Unggah file Excel LHKPN", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()
    df['PREDIKAT'] = df.apply(tentukan_predikat, axis=1)

    # Filter Bulan
    list_bulan = ["SEMUA"] + sorted(df['BULAN'].unique().tolist())
    sel_month = st.sidebar.selectbox("Pilih Bulan Target:", list_bulan)
    
    dff = df if sel_month == "SEMUA" else df[df['BULAN'] == sel_month]

    # --- BAGIAN 1: METRIC CARDS (KPI) ---
    st.subheader("📌 Ringkasan Statistik Global")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    
    total = len(dff)
    hijau = len(dff[dff['PREDIKAT'] == "🟢 ZONA HIJAU"])
    kuning = len(dff[dff['PREDIKAT'] == "🟡 ZONA KUNING"])
    merah = len(dff[dff['PREDIKAT'] == "🔴 ZONA MERAH"])
    hitam = len(dff[dff['PREDIKAT'] == "⚫ ZONA HITAM"])
    persen = ((total - hitam) / total * 100) if total > 0 else 0

    m1.metric("Total WL", f"{total}")
    m2.metric("🟢 Hijau", hijau)
    m3.metric("🟡 Kuning", kuning)
    m4.metric("🔴 Merah", merah)
    m5.metric("⚫ Hitam", hitam, delta_color="inverse")
    m6.metric("Kepatuhan", f"{persen:.1f}%")

    st.divider()

    # --- BAGIAN 2: DAFTAR UNIT KRITIS (ZONA HITAM) ---
    st.subheader("🚨 Daftar Semua Sub-Unit Kritis (ZONA HITAM)")
    st.write("Daftar ini menampilkan semua unit yang memiliki 'Belum Lapor' untuk segera ditindaklanjuti.")
    
    hitam_df = dff[dff['PREDIKAT'] == "⚫ ZONA HITAM"]
    if not hitam_df.empty:
        # Menghitung semua unit di zona hitam
        all_hitam = hitam_df['SUB UNIT KERJA'].value_counts().reset_index()
        all_hitam.columns = ['Sub Unit Kerja', 'Jumlah Belum Lapor']
        st.dataframe(all_hitam, use_container_width=True)
    else:
        st.success("Hebat! Tidak ada sub-unit di Zona Hitam.")

    st.divider()

    # --- BAGIAN 3: LEADERBOARD 10 BESAR PER ZONA ---
    st.subheader("🏆 Leaderboard Sub-Unit Berdasarkan Zona")
    col_h, col_k, col_m = st.columns(3)

    with col_h:
        st.markdown("### 10 Besar Zona Hijau")
        top_h = dff[dff['PREDIKAT'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts().head(10)
        if not top_h.empty:
            st.bar_chart(top_h, color="#2E7D32")
        else:
            st.write("Belum ada data.")

    with col_k:
        st.markdown("### 10 Besar Zona Kuning")
        top_k = dff[dff['PREDIKAT'] == "🟡 ZONA KUNING"]['SUB UNIT KERJA'].value_counts().head(10)
        if not top_k.empty:
            st.bar_chart(top_k, color="#FBC02D")
        else:
            st.write("Belum ada data.")

    with col_m:
        st.markdown("### 10 Besar Zona Merah")
        top_m = dff[dff['PREDIKAT'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().head(10)
        if not top_m.empty:
            st.bar_chart(top_m, color="#D32F2F")
        else:
            st.write("Belum ada data.")

    # --- BAGIAN 4: DETAIL DATA ---
    with st.expander("🔍 Lihat Detail Data Mentah"):
        st.dataframe(dff[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'PREDIKAT']])

else:
    st.info("Silakan unggah file Excel di sidebar untuk memproses dashboard.")
