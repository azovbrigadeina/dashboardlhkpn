import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Zona Kepatuhan LHKPN", layout="wide")

# Judul utama
st.markdown(
    "<h2 style='text-align: center; color: #1976D2; margin-bottom: 30px;'>"
    "Predikat Zona Kepatuhan (dirangking)"
    "</h2>",
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader("Unggah file XLS/XLSX LHKPN", type=['xls', 'xlsx'])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()

        # Normalisasi kolom penting (trim spasi & ubah ke title case)
        if 'BULAN' in df.columns:
            df['BULAN'] = df['BULAN'].astype(str).str.strip().str.title()
        if 'Status LHKPN' in df.columns:
            df['Status LHKPN'] = df['Status LHKPN'].astype(str).str.strip().str.title()

        # Fungsi predikat dengan toleransi lebih baik
        def tentukan_predikat(row):
            status = str(row.get('Status LHKPN', '')).strip().title()
            bulan = str(row.get('BULAN', '')).strip().title()

            if 'Diumumkan Lengkap' in status and bulan == 'Januari':
                return 'Hijau'
            if 'Terverifikasi Lengkap' in status and bulan == 'Februari':
                return 'Kuning'
            if 'Draft' in status and bulan == 'Maret':
                return 'Merah'
            if 'Belum' in status and 'Lapor' in status:
                return 'Hitam'
            return 'Lainnya'

        df['Predikat'] = df.apply(tentukan_predikat, axis=1)

        # --- DEBUG: Tampilkan info data untuk cek kenapa Lainnya ---
        with st.expander("🔍 Debug: Cek Data & Unique Values (klik untuk buka)"):
            st.subheader("5 Baris Pertama Data Penting")
            cols_debug = ['SUB UNIT KERJA', 'Status LHKPN', 'BULAN', 'Predikat']
            if all(c in df.columns for c in cols_debug):
                st.dataframe(df[cols_debug].head(10))
            else:
                st.warning("Beberapa kolom tidak ditemukan. Pastikan ada: SUB UNIT KERJA, Status LHKPN, BULAN")

            st.subheader("Nilai Unik yang Ada")
            st.write("Status LHKPN unik:", df['Status LHKPN'].unique().tolist())
            st.write("BULAN unik:", df['BULAN'].unique().tolist())
            st.write("Predikat unik (setelah diproses):", df['Predikat'].unique().tolist())
            st.write(f"Total baris data: {len(df)}")

        # Pilih periode
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
            st.error(f"Tidak ada data untuk periode '{periode}'. Cek kolom BULAN di file Anda.")
        else:
            # Hitung jumlah per predikat per sub unit
            grouped = df_filter.groupby(['SUB UNIT KERJA', 'Predikat']).size().unstack(fill_value=0)

            # Tentukan zona dominan
            zona_dict = {'Hijau': [], 'Kuning': [], 'Merah': [], 'Hitam': [], 'Lainnya': []}

            for subunit, row in grouped.iterrows():
                if row.sum() == 0:
                    zona_dict['Lainnya'].append(subunit)
                else:
                    pred_dominan = row.idxmax()
                    zona_dict[pred_dominan].append(subunit)

            # Sort alfabetis tiap zona
            for z in zona_dict:
                zona_dict[z].sort()

            # Warna judul zona
            warna_zona = {
                'Hijau': '#2E7D32',    # hijau gelap
                'Kuning': '#F9A825',   # kuning
                'Merah': '#C62828',    # merah
                'Hitam': '#212121',    # hitam
                'Lainnya': '#616161'   # abu-abu
            }

            # Tampilkan tabel per zona
            ada_data = False
            for zona_name, daftar_unit in zona_dict.items():
                if not daftar_unit:
                    continue
                ada_data = True

                st.markdown(
                    f"<h3 style='color: {warna_zona.get(zona_name, '#000')}; margin-top: 40px; border-bottom: 2px solid {warna_zona.get(zona_name, '#000')}; padding-bottom: 8px;'>"
                    f"{zona_name}"
                    "</h3>",
                    unsafe_allow_html=True
                )

                df_tabel = pd.DataFrame({
                    'No': range(1, len(daftar_unit) + 1),
                    'Sub Unit Kerja': daftar_unit
                })

                st.table(
                    df_tabel.style
                    .set_properties(**{'text-align': 'left', 'padding': '10px', 'font-size': '15px'})
                    .set_table_styles([
                        {'selector': 'th', 'props': [('background-color', '#f0f0f0'), ('font-weight', 'bold'), ('border', '1px solid #ccc')]},
                        {'selector': 'td', 'props': [('border', '1px solid #ddd')]},
                        {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#f9f9f9')]}
                    ])
                )

                st.markdown("<br>", unsafe_allow_html=True)

            if not ada_data:
                st.info("Tidak ada sub unit dengan data yang cukup untuk dikategorikan.")

            st.markdown("---")
            st.caption(
                f"Periode: **{periode}**  |  "
                f"Total Sub Unit Kerja: **{len(grouped)}**  |  "
                f"Jumlah pegawai diproses: **{len(df_filter)}**  |  "
                f"Diolah: {pd.Timestamp.now().strftime('%d %b %Y %H:%M WIB')}"
            )

    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file: {str(e)}\nPastikan file XLS/XLSX valid dan punya kolom yang diperlukan.")
