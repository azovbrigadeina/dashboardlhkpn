import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="LHKPN Universitas Jambi", layout="wide")

st.markdown("""
    <style>
    .stMetric {
        background-color: rgba(151, 166, 195, 0.1);
        padding: 15px; border-radius: 12px;
        border: 1px solid rgba(151, 166, 195, 0.2);
    }
    .recom-box {
        background-color: rgba(21, 112, 239, 0.05);
        border-left: 5px solid #1570EF;
        padding: 20px; border-radius: 10px; margin-bottom: 25px;
    }
    .highlight-card {
        background-color: #f0fdf4;
        border: 2px solid #22c55e;
        padding: 20px; border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA DATA ENGINE ---
def proses_data_unja(df, filter_bulan):
    # Membersihkan nama kolom dan NIK
    df.columns = df.columns.str.strip()
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[\'\" ]", "", regex=True)
    
    def get_zona(row):
        status = str(row['Status LHKPN']).strip()
        hijau_status = ["Diumumkan Lengkap", "Diumumkan Tidak Lengkap", "Perlu Perbaikan", 
                        "Perlu Verifikasi", "Terverifikasi Lengkap", "Proses Verifikasi"]
        
        if status in hijau_status:
            return 1, "🟢 ZONA HIJAU"
        elif status == "Draft":
            return 2, "🟡 ZONA KUNING"
        elif status == "Belum Lapor":
            return 3, "🔴 ZONA MERAH"
        return 4, "⚪ LAINNYA"

    res = df.apply(get_zona, axis=1)
    df['rank'] = [x[0] for x in res]
    df['ZONA'] = [x[1] for x in res]
    
    # Filter Berdasarkan Bulan (Jika bukan Global)
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.upper() == filter_bulan]
    
    # DEDUPLIKASI: Mengambil status terbaik per orang (Rank terkecil)
    return df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')

# --- 3. LOGIN ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.write("#")
        st.markdown("<h1 style='text-align: center;'>🏛️ LHKPN UNJA</h1>", unsafe_allow_html=True)
        p = st.text_input("Password", type="password")
        if st.button("Masuk Ke Dashboard", width='stretch'):
            if p == "123456": # Silakan ganti password di sini
                st.session_state['auth'] = True
                st.rerun()
            else: st.error("Password Salah!")
    st.stop()

# --- 4. DASHBOARD UTAMA ---
with st.sidebar:
    st.title("UNJA MONITORING")
    if st.button("Log Out"):
        st.session_state['auth'] = False
        st.rerun()
    st.divider()
    file_upload = st.file_uploader("Upload Database LHKPN", type=["xlsx", "csv"])

if file_upload:
    try:
        raw = pd.read_csv(file_upload) if file_upload.name.endswith('.csv') else pd.read_excel(file_upload)
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Filter Periode Analisis:", list_bln)
        
        data = proses_data_unja(raw, sel_bln)

        st.title("🏛️ Monitoring Kepatuhan LHKPN")
        st.subheader(f"Universitas Jambi — {sel_bln}")
        
        # --- ROW 1: METRIK UTAMA ---
        h_data = data[data['ZONA'] == "🟢 ZONA HIJAU"]
        total_wl = len(data)
        h = len(h_data)
        k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
        m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Wajib Lapor", total_wl)
        m2.metric("🟢 Zona Hijau", h)
        m3.metric("🟡 Zona Kuning", k)
        m4.metric("🔴 Zona Merah", m)

        # --- ROW 2: REKOMENDASI NARATIF PIMPINAN ---
        rate = (h / total_wl * 100) if total_wl > 0 else 0
        df_m_count = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts()
        unit_kritis = df_m_count.index[0] if not df_m_count.empty else "-"
        df_g_count = data[data['ZONA'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts()
        unit_teladan = df_g_count.index[0] if not df_g_count.empty else "-"
        
        # Hitung Unit yang sudah 100%
        unit_stats = data.groupby('SUB UNIT KERJA')['ZONA'].value_counts().unstack().fillna(0)
        jumlah_lunas = len(unit_stats[unit_stats['🔴 ZONA MERAH'] == 0]) if '🔴 ZONA MERAH' in unit_stats.columns else len(unit_stats)

        st.markdown(f"""
        <div class="recom-box">
            <h4 style="margin-top:0; color:#1570EF;">📑 Laporan Eksekutif Kepatuhan LHKPN</h4>
            <p style="font-size: 15px; line-height: 1.6;">
                Tingkat kepatuhan civitas Universitas Jambi posisi saat ini mencapai <b>{rate:.1f}%</b>. 
                Terdapat <b>{h} orang</b> yang telah memenuhi kewajiban pelaporan.
            </p>
            <div style="background-color: white; padding: 12px; border-radius: 8px; border: 1px solid #e0e0e0; margin-bottom:10px;">
                <b style="color: #166534;">✅ Capaian Positif:</b><br>
                Unit <b>{unit_teladan}</b> memimpin sebagai unit paling responsif. 
                Sebanyak <b>{jumlah_lunas} Sub-Unit</b> telah mencapai status bebas 'Zona Merah'.
            </div>
            <div style="background-color: white; padding: 12px; border-radius: 8px; border: 1px solid #e0e0e0;">
                <b style="color: #991b1b;">⚠️ Area Atensi Pimpinan:</b><br>
                Konsentrasi 'Belum Lapor' terbesar berada pada unit <b>{unit_kritis}</b>. 
                Disarankan tindakan persuasif pada pimpinan unit terkait untuk mengejar sisa <b>{m} orang</b> lagi.
            </div>
            <hr style="opacity:0.1; margin:15px 0;">
            <p style="font-size: 13px; color: #666;">
                <i>*Potensi: Jika <b>{k} orang</b> di Zona Kuning melakukan submit hari ini, kepatuhan naik menjadi <b>{((h+k)/total_wl*100):.1f}%</b>.</i>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # --- ROW 3: HIGHLIGHT DIUMUMKAN LENGKAP & REKAP TABEL ---
        col_highlight, col_breakdown = st.columns([1, 1.5])
        
        with col_highlight:
            lunas_kpk = len(h_data[h_data['Status LHKPN'] == "Diumumkan Lengkap"])
            st.markdown(f"""
                <div class="highlight-card">
                    <p style="margin:0; color:#166534; font-size: 14px;">TARGET UTAMA (KPK)</p>
                    <h2 style="margin:0; color:#166534; font-size: 48px;">{lunas_kpk}</h2>
                    <p style="margin:0; color:#166534; font-weight: bold;">Status: Diumumkan Lengkap</p>
                </div>
            """, unsafe_allow_html=True)
            st.success(f"Progres Verifikasi Terakhir: **{lunas_kpk} Personel**")

        with col_breakdown:
            st.markdown("##### 📊 Rekapitulasi Status Detil")
            rekap = data['Status LHKPN'].value_counts().reset_index()
            rekap.columns = ['Status Spesifik', 'Jumlah']
            
            def highlight_lunas(s):
                return ['background-color: #dcfce7; font-weight: bold;' if s['Status Spesifik'] == 'Diumumkan Lengkap' else '' for _ in s]
            
            st.dataframe(rekap.style.apply(highlight_lunas, axis=1), width='stretch', hide_index=True)

        # --- ROW 4: VISUALISASI ---
        st.write("---")
        c1, c2 = st.columns([1, 1.5])
        with c1:
            fig_pie = px.pie(data, names='ZONA', hole=0.5, color='ZONA',
                             color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"},
                             title="<b>Proporsi Kepatuhan</b>")
            st.plotly_chart(fig_pie, width='stretch')
            
        with c2:
            df_unit_red = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            df_unit_red.columns = ['Unit Kerja', 'Jumlah']
            fig_bar = px.bar(df_unit_red, x='Jumlah', y='Unit Kerja', orientation='h',
                             title="<b>10 Unit Terbanyak Belum Lapor</b>", 
                             color_discrete_sequence=['#EF4444'])
            st.plotly_chart(fig_bar, width='stretch')

        with st.expander("🔍 Detail Individu (Nama & Jabatan)"):
            st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], width='stretch', hide_index=True)

    except Exception as e:
        st.error(f"Gagal memproses file. Error: {e}")
else:
    st.info("Silakan unggah database pelaporan (CSV/Excel) untuk menampilkan analisis.")
