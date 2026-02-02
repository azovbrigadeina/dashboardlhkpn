import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title('Dashboard Kepatuhan LHKPN - View Per Bulan & Global')

# Upload file
uploaded_file = st.file_uploader("Unggah File XLS", type=['xls', 'xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()  # Bersihkan spasi di header
    df['BULAN'] = df['BULAN'].str.strip().str.capitalize()  # Normalisasi bulan (e.g., 'januari' -> 'Januari')

    # Fungsi assign predikat (diperketat agar match bulan spesifik)
    def assign_predicate(row):
        status = row['Status LHKPN'].strip()
        bulan = row['BULAN']
        if status == 'Diumumkan Lengkap' and bulan == 'Januari':
            return 'Hijau'
        elif status == 'Terverifikasi Lengkap' and bulan == 'Februari':
            return 'Kuning'
        elif status == 'Draft' and bulan == 'Maret':
            return 'Merah'
        elif status == 'Belum lapor':
            return 'Hitam'
        else:
            return 'Lainnya'

    df['Predikat'] = df.apply(assign_predicate, axis=1)

    # Dropdown untuk pilih view
    view_option = st.selectbox('Pilih View', ['Januari', 'Februari', 'Maret', 'Global'])

    # Filter data berdasarkan view
    if view_option != 'Global':
        df_filtered = df[df['BULAN'] == view_option]
    else:
        df_filtered = df[df['BULAN'].isin(['Januari', 'Februari', 'Maret'])]

    if not df_filtered.empty:
        # Group per Sub Unit Kerja
        grouped_sub = df_filtered.groupby(['SUB UNIT KERJA', 'Predikat']).size().unstack(fill_value=0)
        grouped_sub['Total'] = grouped_sub.sum(axis=1)
        grouped_sub_perc = grouped_sub.drop('Total', axis=1).div(grouped_sub['Total'], axis=0) * 100

        # Hitung skor untuk ranking (Hijau=4, Kuning=3, Merah=2, Hitam=1, Lainnya=0)
        scores = {'Hijau': 4, 'Kuning': 3, 'Merah': 2, 'Hitam': 1, 'Lainnya': 0}
        grouped_sub['Score'] = grouped_sub.apply(lambda row: sum(row.get(col, 0) * scores.get(col, 0) for col in scores) / row['Total'], axis=1)
        grouped_sub['Rank'] = grouped_sub['Score'].rank(ascending=False, method='min')

        # Group per Unit Kerja (global level)
        grouped_unit = df_filtered.groupby(['UNIT KERJA', 'Predikat']).size().unstack(fill_value=0)
        grouped_unit['Total'] = grouped_unit.sum(axis=1)
        grouped_unit_perc = grouped_unit.drop('Total', axis=1).div(grouped_unit['Total'], axis=0) * 100
        grouped_unit['Score'] = grouped_unit.apply(lambda row: sum(row.get(col, 0) * scores.get(col, 0) for col in scores) / row['Total'], axis=1)
        grouped_unit['Global Rank'] = grouped_unit['Score'].rank(ascending=False, method='min')

        # Tampilkan hasil
        st.subheader(f'Persentase Predikat per Sub Unit Kerja - {view_option}')
        st.dataframe(grouped_sub_perc.style.format("{:.2f}%"))

        st.subheader(f'Ranking Sub Unit Kerja - {view_option}')
        st.dataframe(grouped_sub[['Score', 'Rank', 'Total']].sort_values('Rank'))

        st.subheader(f'Persentase Predikat per Unit Kerja - {view_option}')
        st.dataframe(grouped_unit_perc.style.format("{:.2f}%"))

        st.subheader(f'Ranking Global Unit Kerja - {view_option}')
        st.dataframe(grouped_unit[['Score', 'Global Rank', 'Total']].sort_values('Global Rank'))

        # Chart: Distribusi predikat per Sub Unit
        st.subheader(f'Chart Distribusi Predikat per Sub Unit Kerja - {view_option}')
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        grouped_sub.drop(['Total', 'Score', 'Rank'], axis=1, errors='ignore').plot(kind='bar', stacked=True, ax=ax1)
        ax1.set_title(f'Distribusi Predikat per Sub Unit Kerja - {view_option}')
        ax1.set_ylabel('Jumlah')
        ax1.set_xlabel('Sub Unit Kerja')
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig1)

        # Chart: Skor ranking per Sub Unit
        st.subheader(f'Chart Skor Ranking per Sub Unit Kerja - {view_option}')
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        grouped_sub['Score'].plot(kind='bar', ax=ax2, color='skyblue')
        ax2.set_title(f'Skor Rata-rata per Sub Unit Kerja - {view_option}')
        ax2.set_ylabel('Skor')
        ax2.set_xlabel('Sub Unit Kerja')
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig2)

        # Serupa untuk Unit Kerja
        st.subheader(f'Chart Distribusi Predikat per Unit Kerja - {view_option}')
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        grouped_unit.drop(['Total', 'Score', 'Global Rank'], axis=1, errors='ignore').plot(kind='bar', stacked=True, ax=ax3)
        ax3.set_title(f'Distribusi Predikat per Unit Kerja - {view_option}')
        ax3.set_ylabel('Jumlah')
        ax3.set_xlabel('Unit Kerja')
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig3)

        st.subheader(f'Chart Skor Ranking per Unit Kerja - {view_option}')
        fig4, ax4 = plt.subplots(figsize=(8, 5))
        grouped_unit['Score'].plot(kind='bar', ax=ax4, color='lightgreen')
        ax4.set_title(f'Skor Rata-rata per Unit Kerja - {view_option}')
        ax4.set_ylabel('Skor')
        ax4.set_xlabel('Unit Kerja')
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig4)
    else:
        st.warning(f'Tidak ada data untuk {view_option}. Pastikan file XLS punya data di bulan tersebut.')
