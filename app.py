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
    /* GAYA BARU UNTUK KARTU HIGHLIGHT */
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

# --- 2. DATA ENGINE ---
def proses_data_unja(df, filter_bulan):
    df.columns = df.columns.str.strip()
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[\'\" ]", "", regex=True)
    
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
    
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.upper() == filter_bulan]
    
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
        if st.button("Masuk Ke Dashboard", use_container_width=True):
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
    file_upload = st.file_uploader("Upload File CSV/Excel", type=["xlsx", "csv"])

if file_upload:
    try:
        raw = pd.read_csv(file_upload) if file_upload.name.endswith('.csv') else pd.read_excel(file_upload)
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Pilih Periode:", list_bln)
        
        data = proses_data_unja(raw, sel_bln)

        st.title("🏛️ Monitoring Kepatuhan LHKPN")
        st.subheader(f"Universitas Jambi — {sel_bln}")
        
        # ROW 1: METRIK UTAMA
        h_data = data[data['ZONA'] == "🟢 ZONA HIJAU"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Wajib Lapor", len(data))
        m2.metric("🟢 Zona Hijau", len(h_data))
        m3.metric("🟡 Zona Kuning", len(data[data['ZONA'] == "🟡 ZONA KUNING"]))
        m4.metric("🔴 Zona Merah", len(data[data['ZONA'] == "🔴 ZONA MERAH"]))

        st.write("---")

        # ROW 2: PENANDA KHUSUS "DIUMUMKAN LENGKAP" (TARGET ANDA)
        col_highlight, col_breakdown = st.columns([1, 1.5])
        
        with col_highlight:
            # Hitung spesifik yang "Diumumkan Lengkap"
            lunas_kpk = len(h_data[h_data['Status LHKPN'] == "Diumumkan Lengkap"])
            st.markdown(f"""
                <div class="highlight-card">
                    <p style="margin:0; color:#166534; font-size: 14px;">STATUS PENCAPAIAN TERTINGGI</p>
                    <h2 style="margin:0; color:#166534; font-size: 42px;">{lunas_kpk}</h2>
                    <p style="margin:0; color:#166534; font-weight: bold;">Personel: Diumumkan Lengkap</p>
                </div>
            """, unsafe_allow_html=True)
            
            persen = (len(h_data)/len(data)*100) if len(data)>0 else 0
            st.success(f"Tingkat Kepatuhan: **{persen:.1f}%**")

        with col_breakdown:
            st.markdown("##### 📋 Rekapitulasi Status Detail")
            rekap = data['Status LHKPN'].value_counts().reset_index()
            rekap.columns = ['Status Spesifik', 'Jumlah']
            
            # Highlight baris "Diumumkan Lengkap" di tabel
            def highlight_row(s):
                return ['background-color: #dcfce7; font-weight: bold;' if s['Status Spesifik'] == 'Diumumkan Lengkap' else '' for _ in s]
            
            st.dataframe(rekap.style.apply(highlight_row, axis=1), use_container_width=True, hide_index=True)

        # ROW 3: VISUALISASI
        st.write("---")
        c1, c2 = st.columns([1, 1.5])
        with c1:
            fig_pie = px.pie(data, names='ZONA', hole=0.5, color='ZONA',
                             color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"},
                             title="<b>Proporsi Kepatuhan</b>")
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            # Unit terbanyak Belum Lapor
            df_unit = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            df_unit.columns = ['Unit Kerja', 'Jumlah']
            fig_bar = px.bar(df_unit, x='Jumlah', y='Unit Kerja', orientation='h',
                             title="<b>10 Unit Perhatian (Belum Lapor)</b>", color_discrete_sequence=['#EF4444'])
            st.plotly_chart(fig_bar, use_container_width=True)

        with st.expander("🔍 Cari Nama Per Individu"):
            st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Silakan unggah database pelaporan melalui sidebar.")
