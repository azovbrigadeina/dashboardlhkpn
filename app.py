import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman
st.set_page_config(page_title="LHKPN Dynamic Dashboard", layout="wide")

st.title("📊 Monitoring Kepatuhan LHKPN Interaktif")
st.markdown("Unggah file Excel LHKPN untuk menganalisis predikat kepatuhan secara otomatis.")

# 2. Fitur Upload File di Sidebar
st.sidebar.header("📁 Unggah Data")
uploaded_file = st.sidebar.file_uploader("Pilih file Excel (xlsx)", type=["xlsx", "csv"])

# Fungsi Logika Predikat (Sama seperti sebelumnya)
def tentukan_predikat(row):
    status = str(row['Status LHKPN']).strip()
    bulan = str(row['BULAN']).strip().upper() # Ubah ke UPPER agar konsisten
    
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

# 3. Alur Utama Dashboard
if uploaded_file is not None:
    # Membaca file berdasarkan format
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Bersihkan spasi di nama kolom
        df.columns = df.columns.str.strip()
        
        # Terapkan Logika Predikat
        df['PREDIKAT'] = df.apply(tentukan_predikat, axis=1)

        # --- Filter Interaktif ---
        list_bulan = ["SEMUA"] + sorted(df['BULAN'].unique().tolist())
        selected_month = st.sidebar.selectbox("Filter Berdasarkan Bulan:", list_bulan)
        
        if selected_month != "SEMUA":
            display_df = df[df['BULAN'] == selected_month]
        else:
            display_df = df

        # --- Bagian Visualisasi (KPIs) ---
        total_wl = len(display_df)
        hitam_count = len(display_df[display_df['PREDIKAT'] == "⚫ ZONA HITAM"])
        kepatuhan = ((total_wl - hitam_count) / total_wl * 100) if total_wl > 0 else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Wajib Lapor", f"{total_wl} Orang")
        c2.metric("Tingkat Kepatuhan", f"{kepatuhan:.1f}%")
        c3.metric("Kritis (Zona Hitam)", hitam_count)

        # --- Grafik ---
        st.divider()
        col_left, col_right = st.columns(2)

        with col_left:
            fig_pie = px.pie(display_df, names='PREDIKAT', title="Komposisi Predikat Kepatuhan",
                             color='PREDIKAT', color_discrete_map={
                                 "🟢 ZONA HIJAU": "#2E7D32", "🟡 ZONA KUNING": "#FBC02D",
                                 "🔴 ZONA MERAH": "#D32F2F", "⚫ ZONA HITAM": "#212121", "⚪ LAINNYA": "#9E9E9E"
                             })
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_right:
            # Sub-Unit dengan Zona Hitam terbanyak
            hitam_df = display_df[display_df['PREDIKAT'] == "⚫ ZONA HITAM"]
            if not hitam_df.empty:
                top_hitam = hitam_df['SUB UNIT KERJA'].value_counts().reset_index().head(10)
                fig_bar = px.bar(top_hitam, x='count', y='SUB UNIT KERJA', orientation='h', 
                                 title="10 Sub-Unit Paling Kritis (Zona Hitam)",
                                 color_discrete_sequence=['#212121'])
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.success("Luar Biasa! Tidak ada personil di Zona Hitam pada filter ini.")

        # --- Tabel Data ---
        st.subheader("📋 Detail Data Wajib Lapor")
        st.dataframe(display_df[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'BULAN', 'PREDIKAT']], use_container_width=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file: {e}")
        st.info("Pastikan kolom file Anda memiliki: 'Status LHKPN', 'BULAN', 'SUB UNIT KERJA', dan 'NAMA'")

else:
    # Tampilan jika belum ada file
    st.info("👋 Selamat Datang! Silakan unggah file Excel Anda melalui sidebar di sebelah kiri untuk memulai analisis.")
    st.image("https://via.placeholder.com/800x400.png?text=Menunggu+Upload+Data+LHKPN...", use_column_width=True)
