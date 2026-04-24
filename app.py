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
    .stDataFrame { font-size: 13px; }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA DATA ENGINE ---
def proses_data_unja(df, filter_bulan):
    df.columns = df.columns.str.strip()
    # Pembersihan NIK agar unifikasi status akurat
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[\'\" ]", "", regex=True)
    
    def get_zona(row):
    status = str(row['STATUS LHKPN']).strip()
    
    # Kriteria Hijau: Semua status yang menunjukkan laporan sudah dikirim/diproses
    hijau_status = [
        "Diumumkan Lengkap", 
        "Diumumkan Tidak Lengkap", 
        "Perlu Perbaikan", 
        "Perlu Verifikasi", 
        "Terverifikasi Lengkap"
    ]
    
    if status in hijau_status:
        return 1, "🟢 ZONA HIJAU"
    
    # Kategori Kuning: Masih disimpan sebagai draft
    elif status == "Draft":
        return 2, "🟡 ZONA KUNING"
    
    # Kategori Merah: Belum ada tindakan sama sekali
    elif status == "Belum Lapor":
        return 3, "🔴 ZONA MERAH"
    
    # Jika ada status di luar itu
    return 4, "⚪ LAINNYA"

    df['rank'], df['ZONA'] = zip(*df.apply(get_zona, axis=1))
    
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.upper() == filter_bulan]
    
    # Ambil 1 NIK dengan status terbaik (Deduplikasi)
    return df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')

# --- 3. STYLE HIGHLIGHT TABEL ---
def style_zona(val):
    if "HIJAU" in val: return 'background-color: #dcfce7; color: #166534; font-weight: bold;'
    if "KUNING" in val: return 'background-color: #fef9c3; color: #854d0e; font-weight: bold;'
    if "MERAH" in val: return 'background-color: #fee2e2; color: #991b1b; font-weight: bold;' # Sekarang Merah = Belum Lapor
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
        if st.button("Masuk Ke Dashboard", width='stretch'):
            if p == "123456":
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
    file_upload = st.file_uploader("Upload Database LHKPN", type=["xlsx", "csv"])

if file_upload:
    try:
        # Load data
        raw = pd.read_csv(file_upload) if file_upload.name.endswith('.csv') else pd.read_excel(file_upload)
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Filter Periode Analisis:", list_bln)
        
        data = proses_data_unja(raw, sel_bln)

        # UI Header
        st.title("🏛️ Monitoring Kepatuhan LHKPN")
        st.subheader(f"Universitas Jambi — Periode {sel_bln}")
        
        # Row 1: KPI Metrics (Ganti variabel m5/hitam menjadi merah)
        h = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
        k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
        m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])

        m1.metric("Wajib Lapor", len(data))
        m2.metric("🟢 Hijau", h)
        m3.metric("🟡 Kuning", k)
        m4.metric("🔴 Merah", m)

        # Row 2: Smart Recommendation Box
        rate = ((total - hitam) / total * 100) if total > 0 else 0
        df_h_count = data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts()
        unit_kritis = df_h_count.index[0] if not df_h_count.empty else "-"
        df_g_count = data[data['ZONA'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts()
        unit_teladan = df_g_count.index[0] if not df_g_count.empty else "-"
        
        st.markdown(f"""
        <div class="recom-box">
            <h4 style="margin-top:0; color:#1570EF;">📝 Rekomendasi Naratif Pimpinan</h4>
            <p>Tingkat kepatuhan global saat ini mencapai <b>{rate:.1f}%</b>. 
            Unit <b>{unit_teladan}</b> menunjukkan performa teladan di Zona Hijau.</p>
            <hr style="opacity:0.1; margin:10px 0;">
            <b>Langkah Strategis:</b>
            <ul>
                <li><b>Intervensi:</b> Prioritaskan koordinasi dengan Pimpinan unit <b>{unit_kritis}</b> karena menyumbang angka Zona Hitam tertinggi.</li>
                <li><b>Asistensi:</b> Sebanyak <b>{m} orang</b> di Zona Merah (Status Draft) perlu diingatkan untuk klik 'Submit'.</li>
                <li><b>Target:</b> Mengingat periode {sel_bln}, percepatan dibutuhkan untuk mencapai target kepatuhan nasional.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Row 3: Visualizations
        c1, c2 = st.columns([1, 1.5])
        with c1:
            fig_pie = px.pie(data, names='ZONA', hole=0.5, color='ZONA',
                 title="<b>Sebaran Status Kepatuhan</b>",
                 color_discrete_map={
                     "🟢 ZONA HIJAU": "#22C55E", 
                     "🟡 ZONA KUNING": "#F59E0B", 
                     "🔴 ZONA MERAH": "#EF4444"
                 })
            fig_pie.update_layout(height=380, margin=dict(t=60, b=0, l=0, r=0), title_x=0.5)
            st.plotly_chart(fig_pie, width='stretch')
            
        with c2:
            df_hitam_bar = df_h_count.reset_index().head(10)
            df_hitam_bar.columns = ['Unit Kerja', 'Jumlah']
            fig_bar = px.bar(df_hitam_bar, x='Jumlah', y='Unit Kerja', orientation='h', 
                             title="<b>10 Unit Kerja Terkritis (Zona Hitam)</b>",
                             color_discrete_sequence=['#64748B'])
            fig_bar.update_layout(height=380, margin=dict(t=60, b=20, l=0, r=20), title_x=0.5)
            st.plotly_chart(fig_bar, width='stretch')

        # Row 4: Leadership Leaderboard
        st.divider()
        st.markdown("### 🏆 Peringkat Kepemimpinan Unit Kerja")
        l1, l2 = st.columns(2)
        with l1:
            st.markdown("<h6 style='color: #22C55E; margin-bottom:5px;'>✅ Top 5 Unit Terpatuh (Hijau)</h6>", unsafe_allow_html=True)
            st.dataframe(df_g_count.reset_index().head(5), width='stretch', hide_index=True, height=210)
        with l2:
            st.markdown("<h6 style='color: #EF4444; margin-bottom:5px;'>🚨 Top 5 Unit Perhatian (Hitam)</h6>", unsafe_allow_html=True)
            st.dataframe(df_h_count.reset_index().head(5), width='stretch', hide_index=True, height=210)

        # Row 5: Detailed Data Table
        st.write("#")
        with st.expander("🔍 Detail Data Individu (Cari nama atau unit di kolom pencarian tabel)"):
            df_final = data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']]
            st.dataframe(df_final.style.map(style_zona, subset=['ZONA']), width='stretch', hide_index=True)

    except Exception as e:
        st.error(f"Gagal memproses data. Pastikan format kolom sesuai. Error: {e}")
else:
    st.info("Silakan unggah database pelaporan melalui sidebar untuk menyusun rekomendasi naratif pimpinan.")
