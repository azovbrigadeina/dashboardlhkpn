import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Zona LHKPN", layout="wide")

# Judul utama sesuai contoh Anda
st.markdown("<h2 style='text-align: center; color: #1E88E5;'>Predikat Zona Kepatuhan (dirangking)</h2>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Unggah file XLS/XLSX LHKPN", type=['xls', 'xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()
    df['BULAN'] = df['BULAN'].str.strip().str.capitalize()

    def get_predikat(row):
        s = str(row['Status LHKPN']).strip()
        b = row['BULAN']
        if s == 'Diumumkan Lengkap' and b == 'Januari': return 'Hijau'
        if s == 'Terverifikasi Lengkap' and b == 'Februari': return 'Kuning'
        if s == 'Draft' and b == 'Maret': return 'Merah'
        if s == 'Belum lapor': return 'Hitam'
        return 'Lainnya'

    df['Predikat'] = df.apply(get_predikat, axis=1)

    view = st.selectbox("Pilih Periode", ["Januari", "Februari", "Maret", "Global (kumulatif)"])

    if view == "Global":
        df_f = df[df['BULAN'].isin(['Januari', 'Februari', 'Maret'])]
    else:
        df_f = df[df['BULAN'] == view]

    if df_f.empty:
        st.warning(f"Tidak ada data untuk periode {view}")
    else:
        # Hitung predikat dominan per Sub Unit Kerja (yang terbanyak)
        grouped = df_f.groupby(['SUB UNIT KERJA', 'Predikat']).size().unstack(fill_value=0)
        dominant = {}
        for sub, row in grouped.iterrows():
            if row.sum() == 0:
                dominant[sub] = "Lainnya"
            else:
                dominant[sub] = row.idxmax()   # predikat dengan jumlah terbanyak

        # Buat dataframe per zona
        zona_data = {
            'Hijau': [],
            'Kuning': [],
            'Merah': [],
            'Hitam': [],
            'Lainnya': []
        }

        for sub, z in dominant.items():
            if z in zona_data:
                zona_data[z].append(sub)

        # Urutkan alfabetis tiap zona (bisa diganti kriteria lain)
        for z in zona_data:
            zona_data[z].sort()

        # Warna untuk tiap zona
        warna_zona = {
            'Hijau': '#4CAF50',
            'Kuning': '#FFC107',
            'Merah': '#F44336',
            'Hitam': '#212121',
            'Lainnya': '#757575'
        }

        # Tampilkan per zona seperti tabel yang Anda inginkan
        for zona, units in zona_data.items():
            if not units:
                continue

            st.markdown(f"<h3 style='color: {warna_zona.get(zona, '#000000')};'>{zona}</h3>", unsafe_allow_html=True)

            # Buat dataframe untuk tabel
            df_zona = pd.DataFrame({
                'No': range(1, len(units) + 1),
                'Sub Unit Kerja': units
            })

            # Tampilkan tabel tanpa index
            st.table(df_zona.style.set_properties(**{
                'text-align': 'left',
                'font-size': '14px'
            }))

            st.markdown("---")  # garis pemisah antar zona

        # Info tambahan kecil di bawah
        st.caption(f"Data diolah untuk periode: {view} | Total Sub Unit: {len(dominant)} | Tanggal proses: {pd.Timestamp.now().strftime('%d %b %Y %H:%M')}")
