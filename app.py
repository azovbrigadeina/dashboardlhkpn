import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Dashboard Kepatuhan LHKPN - Zona Sederhana + Chart")

uploaded_file = st.file_uploader("Unggah file XLS/XLSX", type=['xls', 'xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()
    df['BULAN'] = df['BULAN'].str.strip().str.capitalize()

    def get_predikat(row):
        s = row['Status LHKPN'].strip()
        b = row['BULAN']
        if s == 'Diumumkan Lengkap' and b == 'Januari': return 'Hijau'
        if s == 'Terverifikasi Lengkap' and b == 'Februari': return 'Kuning'
        if s == 'Draft' and b == 'Maret': return 'Merah'
        if s == 'Belum lapor': return 'Hitam'
        return 'Lainnya'

    df['Predikat'] = df.apply(get_predikat, axis=1)

    view = st.selectbox("Pilih periode", ["Januari", "Februari", "Maret", "Global"])

    if view == "Global":
        df_f = df[df['BULAN'].isin(['Januari', 'Februari', 'Maret'])]
    else:
        df_f = df[df['BULAN'] == view]

    if df_f.empty:
        st.warning(f"Tidak ada data untuk {view}")
    else:
        # Hitung dominan per sub unit (predikat terbanyak)
        grouped = df_f.groupby(['SUB UNIT KERJA', 'Predikat']).size().unstack(fill_value=0)
        dominant = {}
        for sub, row in grouped.iterrows():
            if row.sum() == 0:
                dominant[sub] = "Tidak ada data"
            else:
                dominant[sub] = row.idxmax()  # predikat dengan jumlah terbanyak

        # Grouping zona
        zona = {"Hijau": [], "Kuning": [], "Merah": [], "Hitam": [], "Lainnya": [], "Tidak ada data": []}
        for sub, z in dominant.items():
            zona[z].append(sub)

        st.subheader(f"Zona Kepatuhan - {view}")
        for z, units in zona.items():
            if units:
                st.markdown(f"**Zona {z}**: {', '.join(sorted(units))}")
            else:
                st.markdown(f"**Zona {z}**: -")

        # --- CHART 1: Pie Chart Global (semua data di view ini) ---
        st.subheader(f"Pie Chart Distribusi Predikat - {view}")
        pred_count = df_f['Predikat'].value_counts()
        fig_pie, ax_pie = plt.subplots(figsize=(6, 6))
        colors = {'Hijau': '#4CAF50', 'Kuning': '#FFEB3B', 'Merah': '#F44336', 'Hitam': '#212121', 'Lainnya': '#9E9E9E'}
        ax_pie.pie(pred_count, labels=pred_count.index, autopct='%1.1f%%',
                   colors=[colors.get(p, '#9E9E9E') for p in pred_count.index],
                   startangle=90, textprops={'fontsize': 12})
        ax_pie.axis('equal')
        st.pyplot(fig_pie)

        # --- CHART 2: Pie Chart per Sub Unit (jika ada lebih dari 1 sub unit) ---
        if len(grouped) > 1:
            st.subheader("Pie Chart per Sub Unit Kerja")
            col1, col2 = st.columns(2)
            for i, (sub, row) in enumerate(grouped.iterrows()):
                if row.sum() == 0: continue
                with (col1 if i % 2 == 0 else col2):
                    fig_sub, ax_sub = plt.subplots(figsize=(5, 5))
                    ax_sub.pie(row, labels=row.index, autopct='%1.0f%%',
                               colors=[colors.get(p, '#9E9E9E') for p in row.index],
                               startangle=90)
                    ax_sub.set_title(sub, fontsize=11)
                    st.pyplot(fig_sub)

        # --- CHART 3: Bar Chart distribusi per Sub Unit ---
        st.subheader(f"Bar Chart Distribusi Predikat per Sub Unit - {view}")
        fig_bar, ax_bar = plt.subplots(figsize=(10, 6))
        grouped.plot(kind='bar', stacked=True, ax=ax_bar, color=[colors.get(c, '#9E9E9E') for c in grouped.columns])
        ax_bar.set_title("Jumlah per Predikat per Sub Unit Kerja")
        ax_bar.set_ylabel("Jumlah Pegawai")
        ax_bar.set_xlabel("Sub Unit Kerja")
        ax_bar.legend(title="Predikat", bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig_bar)
