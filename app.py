import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="LHKPN Universitas Jambi", layout="wide")

st.markdown("""
    <style>
    /* Desain Kotak Login Center */
    .login-container {
        background-color: rgba(151, 166, 195, 0.05);
        padding: 40px;
        border-radius: 20px;
        border: 1px solid rgba(151, 166, 195, 0.2);
        text-align: center;
    }
    .stMetric {
        background-color: rgba(151, 166, 195, 0.1);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(151, 166, 195, 0.2);
    }
    .recom-box {
        background-color: rgba(21, 112, 239, 0.05);
        border-left: 5px solid #1570EF;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 25px;
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION (CENTERED UI) ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    # Membuat 3 kolom, login diletakkan di kolom tengah (col2) agar center
    empty_l, col_login, empty_r = st.columns([1, 1.2, 1])
    
    with col_login:
        st.write("#") # Spasi atas
        st.write("#")
        with st.container():
            st.markdown("""
                <div style='text-align: center;'>
                    <h1 style='margin-bottom:0;'>🏛️ LHKPN UNJA</h1>
                    <p style='color: gray;'>Monitoring Kepatuhan Pelaporan</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("---")
            user = st.text_input("Username", placeholder="Masukkan Username")
            pw = st.text_input("Password", type="password", placeholder="Masukkan Password")
            
            if st.button("Masuk Ke Dashboard", use_container_width=True):
                if pw == "123456":
                    st.session_state['auth'] = True
                    st.rerun()
                else:
                    st.error("Akses Ditolak: Password Salah!")
            
            st.markdown("<p style='text-align: center; font-size: 12px; color: gray; margin-top: 20px;'>Universitas Jambi &copy; 2024</p>", unsafe_allow_html=True)
    st.stop()

# --- 3. LOGIKA DATA & REKOMENDASI (Sama Seperti Sebelumnya) ---
def proses_data_unja(df, filter_bulan):
    df.columns = df.columns.str.strip()
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
    return df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')

# --- 4. DASHBOARD CONTENT ---
with st.sidebar:
    st.title("UNJA DASHBOARD")
    if st.button("Keluar / Logout"):
        st.session_state['auth'] = False
        st.rerun()
    st.divider()
    file = st.file_uploader("Upload Data (CSV/XLSX)", type=["csv", "xlsx"])

if file:
    # Memastikan file dibaca dengan benar
    df_raw = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    bln_opt = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in df_raw['BULAN'].unique() if pd.notna(b)])
    sel_bln = st.sidebar.selectbox("Pilih Periode Laporan:", bln_opt)
    
    data = proses_data_unja(df_raw, sel_bln)

    st.title("🏛️ Dashboard Kepatuhan Pelaporan LHKPN")
    st.markdown(f"**Universitas Jambi** — Periode Tampilan: `{sel_bln}`")
    
    # KPI Row
    m1, m2, m3, m4, m5 = st.columns(5)
    h = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
    k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
    m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])
    hitam = len(data[data['ZONA'] == "⚫ ZONA HITAM"])
    
    m1.metric("Wajib Lapor", len(data))
    m2.metric("Hijau", h)
    m3.metric("Kuning", k)
    m4.metric("Merah", m)
    m5.metric("Hitam", hitam)

    # Rekomendasi Naratif
    rate = ((len(data) - hitam) / len(data) * 100) if len(data) > 0 else 0
    unit_kritis = data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts().index[0] if hitam > 0 else "-"
    
    st.markdown(f"""
    <div class="recom-box">
        <h4 style="margin-top:0;">📝 Kesimpulan & Rekomendasi Strategis</h4>
        <p>Tingkat kepatuhan personil saat ini adalah <b>{rate:.1f}%</b>. Unit kerja <b>{unit_kritis}</b> menjadi prioritas utama untuk segera ditindaklanjuti karena memiliki angka 'Belum Lapor' tertinggi.</p>
        <p>Disarankan pimpinan memberikan instruksi khusus kepada para personil di <b>Zona Merah ({m} orang)</b> untuk segera melakukan submit LHKPN yang masih berstatus draft.</p>
    </div>
    """, unsafe_allow_html=True)

    # Charts Row
    c1, c2 = st.columns([1, 1.5])
    with c1:
        fig = px.pie(data, names='ZONA', hole=0.5, color='ZONA',
                     color_discrete_map={"🟢 ZONA HIJAU":"#22C55E", "🟡 ZONA KUNING":"#F59E0B", "🔴 ZONA MERAH":"#EF4444", "⚫ ZONA HITAM":"#64748B"})
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        hitam_count = data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
        st.bar_chart(hitam_count.set_index('SUB UNIT KERJA'), color="#64748B")

    # Leaderboard
    st.divider()
    l1, l2 = st.columns(2)
    with l1:
        st.subheader("🏆 Unit Kerja Terpatuh (Hijau)")
        st.dataframe(data[data['ZONA'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts().head(5), use_container_width=True)
    with l2:
        st.subheader("🚨 Unit Kerja Perhatian (Hitam)")
        st.dataframe(data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts().head(5), use_container_width=True)

    with st.expander("🔍 Lihat Detail Data Individu"):
        st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], use_container_width=True, hide_index=True)

else:
    st.info("Silakan unggah database pelaporan di sidebar untuk memuat Dashboard.")
