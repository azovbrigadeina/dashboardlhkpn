import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman
st.set_page_config(page_title="LHKPN Monitoring Dashboard", layout="wide")

# 2. Fungsi Load Data & Logika Predikat
@st.cache_data
def load_data():
    # Mengasumsikan file csv ada di direktori yang sama
    df = pd.read_csv('GLOBAl.xlsx - Daftar Wajib Lapor.csv')
    df.columns = df.columns.str.strip()
    
    # Fungsi Logika Predikat Kepatuhan
    def tentukan_predikat(row):
        status = str(row['Status LHKPN']).strip()
        bulan = str(row['BULAN']).strip().lower()
        
        if status == "Diumumkan Lengkap" and bulan == "januari":
            return "🟢 ZONA HIJAU"
        elif status == "Terverifikasi Lengkap" and bulan == "februari":
            return "🟡 ZONA KUNING"
        elif status == "Draft" and bulan == "maret":
            return "🔴 ZONA MERAH"
        elif status == "Belum Lapor":
            return "⚫ ZONA HITAM"
        else:
            return "⚪ LAINNYA"

    df['PREDIKAT'] = df.apply(tentukan_predikat, axis=1)
    return df

df = load_data()

# 3. Sidebar untuk Filter
st.sidebar.title("🎛️ Panel Kendali Pimpinan")
st.sidebar.markdown("Filter data di bawah ini:")

# Filter Global vs Per Bulan
mode_view = st.sidebar.selectbox("Pilih Mode Tampilan:", ["Global", "Per Bulan"])

if mode_view == "Per Bulan":
    list_bulan = df['BULAN'].unique().tolist()
    selected_month = st.sidebar.selectbox("Pilih Bulan:", list_bulan)
    filtered_df = df[df['BULAN'] == selected_month]
else:
    filtered_df = df

# Filter Sub Unit Kerja
sub_units = ["Semua"] + df['SUB UNIT KERJA'].unique().tolist()
selected_sub = st.sidebar.selectbox("Filter Sub Unit:", sub_units)
if selected_sub != "Semua":
    filtered_df = filtered_df[filtered_df['SUB UNIT KERJA'] == selected_sub]

# 4. Header Dashboard
st.title("📊 Dashboard Monitoring Kepatuhan LHKPN")
st.markdown(f"Status Kepatuhan: **{mode_view}** | Sub-Unit: **{selected_sub}**")
st.divider()

# 5. Ringkasan Metric (KPI)
col1, col2, col3, col4 = st.columns(4)
total_wl = len(filtered_df)
hitam_count = len(filtered_df[filtered_df['PREDIKAT'] == "⚫ ZONA HITAM"])
hijau_count = len(filtered_df[filtered_df['PREDIKAT'] == "🟢 ZONA HIJAU"])
compliance_rate = ((total_wl - hitam_count) / total_wl) * 100 if total_wl > 0 else 0

col1.metric("Total Wajib Lapor", f"{total_wl} Jiwa")
col2.metric("Tingkat Kepatuhan", f"{compliance_rate:.1f}%")
col3.metric("Zona Hitam (Kritis)", hitam_count, delta_color="inverse")
col4.metric("Zona Hijau (Teladan)", hijau_count)

# 6. Visualisasi Utama
st.subheader("Visualisasi Distribusi Kepatuhan")
c1, c2 = st.columns([1, 1])

with c1:
    # Chart Distribusi Predikat
    fig_pie = px.pie(filtered_df, names='PREDIKAT', title="Persentase Predikat Kepatuhan",
                     color='PREDIKAT', color_discrete_map={
                         "🟢 ZONA HIJAU": "#4CAF50", "🟡 ZONA KUNING": "#FFC107",
                         "🔴 ZONA MERAH": "#F44336", "⚫ ZONA HITAM": "#212121", "⚪ LAINNYA": "#BDBDBD"
                     })
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    # Chart Sub Unit Paling Kritis (Hitam Terbanyak)
    hitam_df = filtered_df[filtered_df['PREDIKAT'] == "⚫ ZONA HITAM"]
    top_kritis = hitam_df['SUB UNIT KERJA'].value_counts().reset_index().head(10)
    fig_bar = px.bar(top_kritis, x='count', y='SUB UNIT KERJA', orientation='h',
                     title="Top 10 Sub-Unit (Zona Hitam Terbanyak)",
                     color_discrete_sequence=['#212121'])
    st.plotly_chart(fig_bar, use_container_width=True)

# 7. Insight Khusus Pimpinan
st.warning("### ⚠️ Perhatian Khusus Pimpinan")
if hitam_count > 0:
    st.write(f"Terdapat **{hitam_count} Wajib Lapor** yang masuk dalam **ZONA HITAM** (Belum Lapor). Mohon segera instruksikan Kepala Sub-Unit terkait untuk melakukan pembinaan.")
else:
    st.success("Selamat! Tidak ada Wajib Lapor di Zona Hitam pada filter ini.")

# 8. Tabel Detail Data
st.subheader("Daftar Detail Wajib Lapor")
st.dataframe(filtered_df[['NAMA', 'JABATAN', 'SUB UNIT KERJA', 'Status LHKPN', 'PREDIKAT']], use_container_width=True)
