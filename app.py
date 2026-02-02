import pandas as pd
import streamlit as st

# Fungsi untuk menentukan kategori warna berdasarkan bulan pertama lapor
def get_color(jan_status, feb_status, mar_status):
    positive_statuses = ['diumumkan lengkap', 'terverifikasi lengkap', 'proses verifikasi', 'diumumkan tidak lengkap']
    jan_status = jan_status.lower().strip() if isinstance(jan_status, str) else ''
    feb_status = feb_status.lower().strip() if isinstance(feb_status, str) else ''
    mar_status = mar_status.lower().strip() if isinstance(mar_status, str) else ''
    
    if jan_status in positive_statuses:
        return 'Hijau'
    elif feb_status in positive_statuses:
        return 'Kuning'
    elif mar_status in positive_statuses:
        return 'Merah'
    else:
        return 'Hitam'

# Judul Dashboard
st.title('Dashboard Kepatuhan Pelaporan LHKPN (Periode Januari - Maret 2026)')

# Upload file
jan_file = st.file_uploader('Upload File Januari (Excel)', type=['xlsx'])
feb_file = st.file_uploader('Upload File Februari (Excel)', type=['xlsx'])
mar_file = st.file_uploader('Upload File Maret (Excel)', type=['xlsx'])

if jan_file and feb_file and mar_file:
    # Baca file Excel (asumsikan baris pertama adalah header)
    jan_df = pd.read_excel(jan_file, header=0)
    feb_df = pd.read_excel(feb_file, header=0)
    mar_df = pd.read_excel(mar_file, header=0)
    
    # Merge berdasarkan NIK
    merged = jan_df.merge(feb_df, on='NIK', suffixes=('_jan', '_feb'))
    merged = merged.merge(mar_df, on='NIK', suffixes=('', '_mar'))
    
    # Tentukan kategori
    merged['Kategori'] = merged.apply(lambda row: get_color(row['Status LHKPN_jan'], row['Status LHKPN_feb'], row['Status LHKPN']), axis=1)
    
    # Hitung skor individu
    merged['Score'] = merged['Kategori'].map({'Hijau': 3, 'Kuning': 2, 'Merah': 1, 'Hitam': 0})
    
    # Statistik global
    total = len(merged)
    hijau = (merged['Kategori'] == 'Hijau').sum()
    kuning = (merged['Kategori'] == 'Kuning').sum()
    merah = (merged['Kategori'] == 'Merah').sum()
    hitam = (merged['Kategori'] == 'Hitam').sum()
    compliance_rate = round(((hijau + kuning + merah) / total) * 100, 2) if total > 0 else 0
    
    st.write(f'**Total Entri:** {total}')
    st.write(f'**Distribusi:** Hijau ({hijau}), Kuning ({kuning}), Merah ({merah}), Hitam ({hitam})')
    st.write(f'**Tingkat Kepatuhan Global:** {compliance_rate}%')
    
    # 1. Perangkingan Sub Unit Kerja
    sub_unit_group = merged.groupby('SUB UNIT KERJA').agg(
        Total=('NIK', 'count'),
        Hijau=('Kategori', lambda x: (x == 'Hijau').sum()),
        Kuning=('Kategori', lambda x: (x == 'Kuning').sum()),
        Merah=('Kategori', lambda x: (x == 'Merah').sum()),
        Hitam=('Kategori', lambda x: (x == 'Hitam').sum()),
        Avg_Score=('Score', 'mean')
    ).sort_values('Avg_Score', ascending=False).reset_index()
    
    st.subheader('1. Perangkingan Sub Unit Kerja')
    st.dataframe(sub_unit_group)
    
    # 2. Perangkingan Unit Kerja (Global)
    unit_group = merged.groupby('UNIT KERJA').agg(
        Total=('NIK', 'count'),
        Hijau=('Kategori', lambda x: (x == 'Hijau').sum()),
        Kuning=('Kategori', lambda x: (x == 'Kuning').sum()),
        Merah=('Kategori', lambda x: (x == 'Merah').sum()),
        Hitam=('Kategori', lambda x: (x == 'Hitam').sum()),
        Avg_Score=('Score', 'mean')
    ).sort_values('Avg_Score', ascending=False).reset_index()
    
    st.subheader('2. Perangkingan Unit Kerja (Global)')
    st.dataframe(unit_group)
    
    # 3. Perangkingan Individu
    individu = merged.sort_values('Score', ascending=False)[['NAMA', 'JABATAN', 'SUB UNIT KERJA', 'UNIT KERJA', 'Kategori']].reset_index(drop=True)
    
    st.subheader('3. Perangkingan Individu (Full List)')
    st.dataframe(individu)
    
    # Rekomendasi DSS
    st.subheader('Rekomendasi DSS')
    st.write('- Prioritaskan sub unit dengan skor rendah untuk reminder.')
    st.write('- Targetkan individu Hitam untuk meningkatkan kepatuhan.')
    
    # Export hasil ke CSV (opsional)
    csv = individu.to_csv(index=False).encode('utf-8')
    st.download_button('Download Data Individu (CSV)', csv, 'individu_lhkpn.csv', 'text/csv')
else:
    st.info('Silakan upload ketiga file Excel untuk memproses dashboard.')
