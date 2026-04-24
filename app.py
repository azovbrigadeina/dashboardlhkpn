import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="Dashboard LHKPN UNJA", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    /* Global Background */
    .main { background-color: #f8fafc; }
    
    /* Metric Styling */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    
    /* Recommendation Box (Nota Dinas) */
    .recom-box {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 30px;
        border-radius: 8px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Highlight Card */
    .highlight-card {
        background-color: #f0fdf4;
        border: 2px solid #22c55e;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
    }
    
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA DATA ENGINE ---
@st.cache_data
def proses_data_unja(df, filter_bulan):
    # Membersihkan baris kosong
    df = df.dropna(subset=['NIK', 'NAMA', 'SUB UNIT KERJA'])
    
    # Normalisasi NIK (Menghindari format scientific/float)
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[\'\" ]", "", regex=True).str.split('.').str[0]
    df = df[~df['NIK_KEY'].isin(['nan', '', 'None'])]
    
    # Penentuan Zona
    def get_zona(row):
        status = str(row['Status LHKPN']).strip()
        hijau_status = ["Diumumkan Lengkap", "Diumumkan Tidak Lengkap", "Perlu Perbaikan", 
                        "Perlu Verifikasi", "Terverifikasi Lengkap", "Proses Verifikasi"]
        if status in hijau_status: return 1, "🟢 ZONA HIJAU"
        elif status == "Draft": return 2, "🟡 ZONA KUNING"
        elif status == "Belum Lapor": return 3, "🔴 ZONA MERAH"
        return 4, "⚪ LAINNYA"

    res = df.apply(get_zona, axis=1)
    df['rank'] = [x[0] for x in res]
    df['ZONA'] = [x[1] for x in res]
    
    # Filter Bulan
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.strip().str.upper() == filter_bulan]
    
    # Deduplikasi (Ambil status terbaik per NIK)
    df_final = df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')
    return df_final

# --- 3. SISTEM LOGIN ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.write("#")
        st.markdown("<h1 style='text-align: center;'>🏛️ LHKPN UNJA</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Sistem Monitoring Kepatuhan Internal</p>", unsafe_allow_html=True)
        p = st.text_input("Password Akses", type="password")
        if st.button("Masuk Ke Dashboard", use_container_width=True):
            if p == "123456": # Silakan ganti password di sini
                st.session_state['auth'] = True
                st.rerun()
            else: st.error("Akses Ditolak: Password Salah!")
    st.stop()

# --- 4. DASHBOARD UTAMA ---
with st.sidebar:
    st.title("UNJA MONITORING")
    st.info(f"User: Administrator\nStatus: Terautentikasi")
    if st.button("Log Out"):
        st.session_state['auth'] = False
        st.rerun()
    st.divider()
    file_upload = st.file_uploader("Unggah Database LHKPN (Excel/CSV)", type=["xlsx", "csv"])

if file_upload:
    try:
        # Load Data
        raw = pd.read_csv(file_upload) if file_upload.name.endswith('.csv') else pd.read_excel(file_upload)
        
        # Validasi Kolom
        required = ['NIK', 'Status LHKPN', 'BULAN', 'SUB UNIT KERJA', 'NAMA']
        if not all(c in raw.columns for c in required):
            st.error(f"Format file tidak sesuai. Pastikan terdapat kolom: {', '.join(required)}")
            st.stop()

        # Filter Periode
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Pilih Periode Analisis:", list_bln)
        
        data = proses_data_unja(raw, sel_bln)

        # --- KALKULASI STATISTIK ---
        total_wl = len(data)
        h_data = data[data['ZONA'] == "🟢 ZONA HIJAU"]
        h = len(h_data)
        k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
        m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])
        rate = (h / total_wl * 100) if total_wl > 0 else 0

        # Analisis Per Unit
        unit_stats = data.groupby('SUB UNIT KERJA')['ZONA'].value_counts().unstack().fillna(0)
        for z in ["🟢 ZONA HIJAU", "🟡 ZONA KUNING", "🔴 ZONA MERAH"]:
            if z not in unit_stats.columns: unit_stats[z] = 0
        
        unit_stats['Total'] = unit_stats.sum(axis=1)
        unit_stats['Persen_Hijau'] = (unit_stats['🟢 ZONA HIJAU'] / unit_stats['Total']) * 100
        
        # Unit Teladan & Kritis
        unit_teladan = unit_stats.sort_values(by=['Persen_Hijau', 'Total'], ascending=False).index[0]
        unit_kritis_data = unit_stats.sort_values(by=['Persen_Hijau', '🔴 ZONA MERAH'], ascending=[True, False])
        unit_terendah_nama = unit_kritis_data.index[0]
        unit_terendah_persen = unit_kritis_data.iloc[0]['Persen_Hijau']
        jumlah_lunas = len(unit_stats[unit_stats['🔴 ZONA MERAH'] == 0])

        # --- DISPLAY UI ---
        st.title("🏛️ Monitoring Kepatuhan LHKPN")
        st.subheader(f"Universitas Jambi — Periode: {sel_bln}")
        
        # ROW 1: METRIK
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Wajib Lapor", f"{total_wl} Personel")
        m2.metric("🟢 Zona Hijau", h, f"{rate:.1f}%")
        m3.metric("🟡 Zona Kuning", k, f"{((k/total_wl)*100):.1f}%")
        m4.metric("🔴 Zona Merah", m, f"-{((m/total_wl)*100):.1f}%", delta_color="inverse")

        # ROW 2: NOTA DINAS FORMAL
        st.markdown(f"""
        <div class="recom-box">
            <h3 style="margin-top:0; color:#1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom:10px;">
                🏛️ NOTA ANALISIS KEPATUHAN LHKPN
            </h3>
            <p style="font-size: 14px; color: #475569; font-style: italic;">
                Kepada Yth: Pimpinan Universitas Jambi<br>
                Dari: Admin Pengelola LHKPN Universitas
            </p>
            <p style="font-size: 15px; line-height: 1.6; color: #1e293b;">
                Melaporkan progres kepatuhan LHKPN periode <b>{sel_bln}</b>. Saat ini tingkat kepatuhan kolektif berada pada angka <b>{rate:.1f}%</b>. 
                Guna mencapai target kepatuhan 100%, berikut kami sampaikan rekomendasi langkah strategis:
            </p>
            
            <div style="background-color: #f0fdf4; padding: 18px; border-radius: 8px; border: 1px solid #bbf7d0; margin-bottom:15px;">
                <b style="color: #166534; font-size: 16px;">1. Penguatan Komitmen (Apresiasi)</b><br>
                Memberikan apresiasi kepada <b>{unit_teladan}</b> yang telah menunjukkan performa pelaporan terbaik. 
                Tercatat sebanyak <b>{jumlah_lunas} Sub-Unit</b> telah menyelesaikan seluruh kewajiban pelaporan (Bebas Zona Merah).
            </div>

            <div style="background-color: #fef2f2; padding: 18px; border-radius: 8px; border: 1px solid #fecaca; margin-bottom:15px;">
                <b style="color: #991b1b; font-size: 16px;">2. Intervensi Manajerial (Atensi Khusus)</b><br>
                Dibutuhkan perhatian pimpinan pada unit <b>{unit_terendah_nama}</b> dengan tingkat kepatuhan terendah (<b>{unit_terendah_persen:.1f}%</b>). 
                Disarankan adanya instruksi langsung kepada pimpinan unit terkait untuk mendorong <b>{int(unit_kritis_data.iloc[0]['🔴 ZONA MERAH'])} orang</b> yang masih berada di Zona Merah.
            </div>

            <div style="background-color: #fffbeb; padding: 18px; border-radius: 8px; border: 1px solid #fef3c7; margin-bottom:15px;">
                <b style="color: #854d0e; font-size: 16px;">3. Strategi Percepatan (Quick-Wins)</b><br>
                Terdapat <b>{k} orang</b> pada posisi <i>Draft (Zona Kuning)</i>. Personel ini hanya membutuhkan tindakan 'Submit' final. 
                Apabila instruksi ini dilaksanakan hari ini, tingkat kepatuhan Universitas akan meningkat menjadi <b>{((h+k)/total_wl*100):.1f}%</b>.
            </div>

            <p style="font-size: 13px; color: #64748b; margin-top: 15px; border-top: 1px dashed #cbd5e1; padding-top: 10px;">
                Demikian rekomendasi ini kami sampaikan untuk dapat dipergunakan sebagai bahan pengambilan kebijakan Pimpinan.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ROW 3: VISUALISASI & TABEL
        st.write("---")
        c1, c2 = st.columns([1, 1.5])
        
        with c1:
            lunas_kpk = len(h_data[h_data['Status LHKPN'] == "Diumumkan Lengkap"])
            st.markdown(f"""
                <div class="highlight-card">
                    <p style="margin:0; color:#166534; font-size: 14px; font-weight: bold;">TARGET FINAL KPK</p>
                    <h2 style="margin:0; color:#166534; font-size: 52px;">{lunas_kpk}</h2>
                    <p style="margin:0; color:#166534;">Status: <b>Diumumkan Lengkap</b></p>
                </div>
            """, unsafe_allow_html=True)
            
            fig_pie = px.pie(data, names='ZONA', hole=0.5, 
                             color='ZONA',
                             color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"},
                             title="Proporsi Kepatuhan Real-time")
            st.plotly_chart(fig_pie, use_container_width=True)

        with c2:
            # Bar Chart Unit Kritis
            df_unit_red = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            df_unit_red.columns = ['Unit Kerja', 'Jumlah']
            fig_bar = px.bar(df_unit_red, x='Jumlah', y='Unit Kerja', orientation='h',
                             title="10 Unit dengan Beban Zona Merah Terbanyak",
                             color_discrete_sequence=['#EF4444'])
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)

        # DETAIL DATA
        with st.expander("🔍 Lihat Detail Data Personel & Status"):
            st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], 
                         use_container_width=True, hide_index=True)
            
            # Download Button
            csv = data.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Unduh Laporan Lengkap (.csv)", csv, f"LHKPN_UNJA_{sel_bln}.csv", "text/csv")

    except Exception as e:
        st.error(f"Terjadi kesalahan pemrosesan data: {e}")
        st.info("Pastikan file memiliki kolom: NIK, NAMA, Status LHKPN, SUB UNIT KERJA, BULAN")

else:
    st.warning("Menunggu unggahan database LHKPN untuk memulai analisis.")
    st.image("https://www.unja.ac.id/wp-content/uploads/2022/03/LOGO-UNJA-768x772.png", width=150)
