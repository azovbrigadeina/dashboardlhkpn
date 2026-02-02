import streamlit as st
import pandas as pd

st.set_page_config(page_title="Zona Kepatuhan LHKPN", layout="wide")

st.markdown(
    "<h2 style='text-align: center; color: #1976D2; margin-bottom: 30px;'>"
    "Predikat Zona Kepatuhan (dirangking)"
    "</h2>",
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader("Unggah file XLS/XLSX LHKPN", type=['xls', 'xlsx'])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()
    df['BULAN'] = df['BULAN'].astype(str).str.strip().str.capitalize()

    def tentukan_predikat(row):
        status = str(row['Status LHKPN']).strip()
        bulan = row['BULAN']
        if status == 'Diumumkan Lengkap' and bulan == 'Januari':
            return 'Hijau'
        if status == 'Terverifikasi Lengkap' and bulan == 'Februari':
            return 'Kuning'
        if status == 'Draft' and bulan == 'Maret':
            return 'Merah'
        if status == 'Belum lapor':
            return 'Hitam'
        return 'Lainnya'

    df['Predikat'] = df.apply(tentukan_predikat, axis=1)

    periode = st.selectbox(
        "Pilih Periode",
        ["Januari", "Februari", "Maret", "Global (kumulatif Jan-Feb-Mar)"],
        index=3
    )

    if periode == "Global (kumulatif Jan-Feb-Mar)":
        df_filter = df[df['BULAN'].isin(['Januari', 'Februari', 'Maret'])]
    else:
        df_filter = df[df['BULAN'] == periode]

    if df_filter.empty:
        st.warning(f"Tidak ada data untuk periode {periode}")
    else:
        # Hitung predikat dominan per Sub Unit Kerja (yang paling banyak)
        grouped = df_filter.groupby(['SUB UNIT KERJA', 'Predikat']).size().unstack(fill_value=0)
        
        zona_dict = {
            'Hijau': [],
            'Kuning': [],
            'Merah': [],
            'Hitam': [],
            'Lainnya': []
        }

        for subunit, row in grouped.iterrows():
            if row.sum() == 0:
                zona_dict['Lainnya'].append(subunit)
            else:
                pred_dominan = row.idxmax()
                zona_dict[pred_dominan].append(subunit)

        # Urutkan alfabetis tiap zona
        for z in zona_dict:
            zona_dict[z].sort()

        # Warna untuk judul zona
        warna = {
            'Hijau': '#2E7D32',
            'Kuning': '#F9A825',
            'Merah': '#C62828',
            'Hitam': '#212121',
            'Lainnya': '#616161'
        }

        # Tampilkan per zona dengan format tabel seperti contoh
        for zona_name, daftar_unit in zona_dict.items():
            if not daftar_unit:
                continue

            st.markdown(f"<h3 style='color: {warna.get(zona_name, '#000')}; margin-top: 30px;'>{zona_name}</h3>", unsafe_allow_html=True)

            data_tabel = {
                'No': list(range(1, len(daftar_unit) + 1)),
                'Sub Unit Kerja': daftar_unit
            }

            df_tabel = pd.DataFrame(data_tabel)

            # Tampilkan tabel dengan style minimalis
            st.table(
                df_tabel.style
                .set_properties(**{'text-align': 'left', 'padding': '8px'})
                .set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#f5f5f5'), ('font-weight', 'bold')]},
                    {'selector': 'td, th', 'props': [('border', '1px solid #ddd')]}
                ])
            )

            st.markdown("<br>", unsafe_allow_html=True)

        st.caption(f"Periode: {periode} | Total Sub Unit Kerja: {len(grouped)} | Diolah pada: {pd.Timestamp.now().strftime('%d %b %Y %H:%M WIB')}")
