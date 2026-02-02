import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG ---
st.set_page_config(page_title="LHKPN Universitas Jambi", layout="wide")

# --- 2. CSS ADAPTIF (Bisa Terang/Gelap) ---
st.markdown("""
    <style>
    /* Menggunakan variabel warna bawaan Streamlit agar adaptif */
    .stMetric {
        background-color: rgba(151, 166, 195, 0.1);
        padding: 15px;
        border-radius: 10px;
    }
    /* Menghilangkan header default agar bersih */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIKA DATA (NIK CLEANING) ---
def proses_data_unja(df, filter_bulan):
    df.columns = df.columns.str.strip()
    # Membersihkan NIK dari tanda petik satu agar deduplikasi akurat
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[\'\" ]", "", regex=True)
    
    def get_zona(row):
        status = str(row['Status LHKPN']).strip()
        bulan = str(row['BULAN']).strip().upper()
        if status == "Diumumkan Lengkap" and bulan == "JANUARI": return 1, "🟢 ZONA HIJAU"
        if status == "Terverifikasi Lengkap" and bulan == "FEBRUARI": return 2, "🟡 ZONA KUNING"
        if status == "Draft" and bulan == "MARET": return 3, "🔴 ZONA MERAH"
        if status == "Belum Lapor": return 5, "⚫ ZONA HITAM"
        return 4, "⚪ LAINNYA"

    df['rank'], df['ZONA'] = zip(*df.apply(get_zona, axis=1))
    
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.upper() == filter_bulan]
    
    # Ambil status terbaik per individu unik
    return df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')

# --- 4. LOGIN ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.write("#")
        st.write("#")
        st.title("Sistem LHKPN UNJA")
        st.caption("Universitas Jambi - Portal Monitoring")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Log In", use_container_width=True):
            if p == "123456":
                st.session_state['auth'] = True
                st.rerun()
            else: st.error("Akses Ditolak")
    st.stop()

# --- 5. DASHBOARD ---
with st.sidebar:
    st.title("UNJA DASHBOARD")
    if st.button("Log Out"):
        st.session_state['auth'] = False
        st.rerun()
    st.divider()
    file_upload = st.file_uploader("Upload File LHKPN", type=["xlsx", "csv"])

if file_upload:
    try:
        # Deteksi format file
        if file_upload.name.endswith('.csv'):
            raw = pd.read_csv(file_upload)
        else:
            raw = pd.read_excel(file_upload)
            
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Filter Periode:", list_bln)
        
        data = proses_data_unja(raw, sel_bln)

        # Header Utama
        st.title("🏛️ Monitoring Kepatuhan LHKPN")
        st.subheader(f"Universitas Jambi — {sel_bln}")
        st.write("---")

        # Metrik - Menggunakan kolom standar Streamlit
        m1, m2, m3, m4 = st.columns(4)
        total = len(data)
        hitam = len(data[data['ZONA'] == "⚫ ZONA HITAM"])
        rate = ((total - hitam) / total * 100) if total > 0 else 0

        m1.metric("Wajib Lapor", total)
        m2.metric("🟢 Zona Hijau", len(data[data['ZONA'] == "🟢 ZONA HIJAU"]))
        m3.metric("⚫ Zona Hitam", hitam)
        m4.metric("Kepatuhan", f"{rate:.1f}%")

        # Visualisasi (Warna diatur agar kontras di Dark/Light)
        st.write("#")
        c1, c2 = st.columns([1, 1.5])
        with c1:
            st.markdown("### Komposisi Kepatuhan")
            fig = px.pie(data, names='ZONA', hole=0.5, color='ZONA',
                         color_discrete_map={
                             "🟢 ZONA HIJAU":"#22C55E", 
                             "🟡 ZONA KUNING":"#F59E0B", 
                             "🔴 ZONA MERAH":"#EF4444", 
                             "⚫ ZONA HITAM":"#64748B", # Abu-abu gelap agar terlihat di hitam
                             "⚪ LAINNYA":"#94A3B8"})
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                              font_color='gray', legend=dict(font=dict(color='gray')))
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.markdown("### Unit Kerja Belum Lapor")
            df_u = data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            df_u.columns = ['Unit Kerja', 'Jumlah']
            st.dataframe(df_u, use_container_width=True, hide_index=True)

        # Tabel Data
        st.write("---")
        with st.expander("🔍 Klik untuk Detail Individu"):
            st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], 
                         use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan pembacaan data: {e}")
else:
    st.markdown("""
        ### Selamat Datang di Dashboard LHKPN UNJA
        Silakan unggah database pelaporan (format CSV atau Excel) di sidebar untuk melihat analisis.
    """)
