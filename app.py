import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="LHKPN Universitas Jambi", layout="wide")

# CSS untuk mempercantik tampilan UI
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
    .stDataFrame { font-size: 13px; }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA DATA ENGINE ---
def proses_data_unja(df, filter_bulan):
    # Bersihkan nama kolom dari spasi yang tidak terlihat
    df.columns = df.columns.str.strip()
    
    # Bersihkan NIK dari karakter kutip (') yang sering muncul dari file Excel/CSV
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[\'\" ]", "", regex=True)
    
    def get_zona(row):
        # Mengambil status dari kolom Status LHKPN
        status = str(row['Status LHKPN']).strip()
        
        # Kriteria Hijau: Selesai lapor atau sedang tahap verifikasi
        hijau_status = [
            "Diumumkan Lengkap", 
            "Diumumkan Tidak Lengkap", 
            "Perlu Perbaikan", 
            "Perlu Verifikasi", 
            "Terverifikasi Lengkap",
            "Proses Verifikasi"
        ]
        
        if status in hijau_status:
            return 1, "🟢 ZONA HIJAU"
        elif status == "Draft":
            return 2, "🟡 ZONA KUNING"
        elif status == "Belum Lapor":
            return 3, "🔴 ZONA MERAH"
        return 4, "⚪ LAINNYA"

    # Terapkan fungsi zona ke setiap baris
    res = df.apply(get_zona, axis=1)
    df['rank'] = [x[0] for x in res]
    df['ZONA'] = [x[1] for x in res]
    
    # Logika Filter Bulan
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.upper() == filter_bulan]
    
    # DEDUPLIKASI: Urutkan berdasarkan rank (1-4) lalu ambil 1 data terbaik per NIK
    # Ini memastikan jika Si A pernah Hijau di Jan, dia tetap Hijau di tampilan Global
    df_final = df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')
    
    return df_final

# --- 3. STYLE HIGHLIGHT TABEL ---
def style_zona(val):
    if "HIJAU" in val: return 'background-color: #dcfce7; color: #166534; font-weight: bold;'
    if "KUNING" in val: return 'background-color: #fef9c3; color: #854d0e; font-weight: bold;'
    if "MERAH" in val: return 'background-color: #fee2e2; color: #991b1b; font-weight: bold;'
    return ''

# --- 4. SISTEM LOGIN ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.write("#")
        st.markdown("<h1 style='text-align: center;'>🏛️ LHKPN UNJA</h1>", unsafe_allow_html=True)
        u = st.text_input("Username", placeholder="Admin LHKPN")
        p = st.text_input("Password", type="password", placeholder="******")
        if st.button("Masuk Ke Dashboard", use_container_width=True):
            if p == "123456": # Ganti dengan password yang diinginkan
                st.session_state['auth'] = True
                st.rerun()
            else: st.error("Password Salah!")
    st.stop()

# --- 5. DASHBOARD UTAMA ---
with st.sidebar:
    st.title("UNJA MONITORING")
    if st.button("Log Out"):
        st.session_state['auth'] = False
        st.rerun()
    st.divider()
    file_upload = st.file_uploader("Upload Database LHKPN (CSV/Excel)", type=["xlsx", "csv"])

if file_upload:
    try:
        # Load data berdasarkan ekstensi file
        if file_upload.name.endswith('.csv'):
            raw = pd.read_csv(file_upload)
        else:
            raw = pd.read_excel(file_upload)
            
        # List bulan untuk filter (Ambil dari kolom BULAN)
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Filter Periode Analisis:", list_bln)
        
        # Jalankan mesin pemroses data
        data = proses_data_unja(raw, sel_bln)

        # Header Dashboard
        st.title("🏛️ Monitoring Kepatuhan LHKPN")
        st.subheader(f"Universitas Jambi — Periode {sel_bln}")
        
        # Row 1: KPI Metrics
        total_wl = len(data)
        h = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
        k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
        m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Wajib Lapor", total_wl)
        m2.metric("🟢 Hijau (Selesai)", h)
        m3.metric("🟡 Kuning (Draft)", k)
        m4.metric("🔴 Merah (Belum)", m)

        # Row 2: Rekomendasi Naratif
        rate = (h / total_wl * 100) if total_wl > 0 else 0
        df_m_count = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts()
        unit_kritis = df_m_count.index[0] if not df_m_count.empty else "-"
        df_g_count = data[data['ZONA'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts()
        unit_teladan = df_g_count.index[0] if not df_g_count.empty else "-"
        
        st.markdown(f"""
        <div class="recom-box">
            <h4 style="margin-top:0; color:#1570EF;">📝 Rekomendasi Naratif Pimpinan</h4>
            <p>Tingkat kepatuhan (Zona Hijau) saat ini mencapai <b>{rate:.1f}%</b>. 
            Unit <b>{unit_teladan}</b> menunjukkan performa teladan.</p>
            <hr style="opacity:0.1; margin:10px 0;">
            <b>Langkah Strategis:</b>
            <ul>
                <li><b>Intervensi:</b> Prioritaskan koordinasi dengan unit <b>{unit_kritis}</b> yang memiliki angka Belum Lapor tertinggi.</li>
                <li><b>Asistensi:</b> Segera ingatkan <b>{k} orang</b> di Zona Kuning agar melakukan 'Submit' laporan.</li>
                <li><b>Target:</b> Dibutuhkan penambahan {m} orang lagi ke Zona Hijau untuk mencapai kepatuhan 100%.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Row 3: Visualisasi
        c1, c2 = st.columns([1, 1.5])
        with c1:
            fig_pie = px.pie(data, names='ZONA', hole=0.5, color='ZONA',
                             color_discrete_map={
                                 "🟢 ZONA HIJAU": "#22C55E", 
                                 "🟡 ZONA KUNING": "#F59E0B", 
                                 "🔴 ZONA MERAH": "#EF4444"
                             }, title="<b>Sebaran Status Kepatuhan</b>")
            fig_pie.update_layout(height=400, title_x=0.5)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            df_bar = df_m_count.reset_index().head(10)
            df_bar.columns = ['Unit Kerja', 'Jumlah']
            fig_bar = px.bar(df_bar, x='Jumlah', y='Unit Kerja', orientation='h',
                             title="<b>10 Unit dengan Belum Lapor Terbanyak</b>",
                             color_discrete_sequence=['#EF4444'])
            fig_bar.update_layout(height=400, title_x=0.5)
            st.plotly_chart(fig_bar, use_container_width=True)

        # Row 4: Tabel Detail
        st.divider()
        with st.expander("🔍 Detail Data Individu (Gunakan pencarian untuk filter nama/unit)"):
            cols_show = ['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']
            st.dataframe(
                data[cols_show].style.map(style_zona, subset=['ZONA']), 
                use_container_width=True, 
                hide_index=True
            )

    except Exception as e:
        st.error(f"Gagal memproses data. Pastikan format kolom sesuai. Error: {e}")
else:
    st.info("Silakan unggah database pelaporan melalui sidebar untuk memulai analisis.")
