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
    /* GAYA UNTUK REKOMENDASI NARATIF */
    .recom-box {
        background-color: rgba(21, 112, 239, 0.05);
        border-left: 5px solid #1570EF;
        padding: 20px; border-radius: 10px; margin-bottom: 25px;
    }
    /* GAYA UNTUK KARTU HIGHLIGHT */
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
    
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.upper() == filter_bulan]
    
    # Deduplikasi: Ambil status terbaik per NIK
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
            if p == "123456":
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
        sel_bln = st.sidebar.selectbox("Filter Periode:", list_bln)
        
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

        # --- ROW 2: REKOMENDASI NARATIF PIMPINAN (KEMBALI ADA) ---
        rate = (h / total_wl * 100) if total_wl > 0 else 0
        df_m_count = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts()
        unit_kritis = df_m_count.index[0] if not df_m_count.empty else "-"
        df_g_count = data[data['ZONA'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts()
        unit_teladan = df_g_count.index[0] if not df_g_count.empty else "-"
        
        st.markdown(f"""
        <div class="recom-box">
            <h4 style="margin-top:0; color:#1570EF;">📝 Rekomendasi Naratif Pimpinan</h4>
            <p>Tingkat kepatuhan final saat ini mencapai <b>{rate:.1f}%</b>. 
            Unit <b>{unit_teladan}</b> menunjukkan performa terbaik.</p>
            <hr style="opacity:0.1; margin:10px 0;">
            <b>Langkah Strategis:</b>
            <ul>
                <li><b>Prioritas:</b> Hubungi unit <b>{unit_kritis}</b> karena memiliki jumlah 'Belum Lapor' terbanyak.</li>
                <li><b>Follow Up:</b> Segera ingatkan <b>{k} orang</b> di Zona Kuning (Draft) untuk klik tombol 'Kirim'.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # --- ROW 3: PENANDA KHUSUS DIUMUMKAN LENGKAP ---
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
            st.success(f"Progres Kepatuhan: **{rate:.1f}%**")

        with col_breakdown:
            st.markdown("##### 📋 Rekapitulasi Status Detil")
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
            df_unit = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            df_unit.columns = ['Unit Kerja', 'Jumlah']
            fig_bar = px.bar(df_unit, x='Jumlah', y='Unit Kerja', orientation='h',
                             title="<b>10 Unit Perlu Perhatian (Belum Lapor)</b>", 
                             color_discrete_sequence=['#EF4444'])
            st.plotly_chart(fig_bar, width='stretch')

        with st.expander("🔍 Detail Individu"):
            st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], width='stretch', hide_index=True)

    except Exception as e:
        st.error(f"Gagal memproses data: {e}")
else:
    st.info("Silakan unggah database pelaporan melalui sidebar.")
