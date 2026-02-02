import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG ---
st.set_page_config(page_title="LHKPN Universitas Jambi", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: rgba(151, 166, 195, 0.1); padding: 15px; border-radius: 12px; }
    .recom-box { background-color: rgba(21, 112, 239, 0.05); border-left: 5px solid #1570EF; padding: 20px; border-radius: 8px; margin-bottom: 25px; }
    /* Memperkecil padding tabel agar dimensi lebih compact */
    .stDataFrame { font-size: 13px; }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIN (CENTERED) ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if not st.session_state['auth']:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.write("#")
        st.markdown("<h1 style='text-align: center;'>🏛️ LHKPN UNJA</h1>", unsafe_allow_html=True)
        pw = st.text_input("Password", type="password")
        if st.button("Masuk", width='stretch'):
            if pw == "123456": st.session_state['auth'] = True; st.rerun()
    st.stop()

# --- 3. DATA ENGINE ---
def proses_data_unja(df, filter_bulan):
    df.columns = df.columns.str.strip()
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[\'\" ]", "", regex=True)
    
    def get_zona(row):
        status = str(row['Status LHKPN']).strip()
        bulan = str(row['BULAN']).strip().upper()
        if status == "Diumumkan Lengkap" and bulan == "JANUARI": return 1, "HIJAU"
        if status == "Terverifikasi Lengkap" and bulan == "FEBRUARI": return 2, "KUNING"
        if status == "Draft" and bulan == "MARET": return 3, "MERAH"
        if status == "Belum Lapor": return 5, "HITAM"
        return 4, "LAINNYA"

    df['rank'], df['ZONA'] = zip(*df.apply(get_zona, axis=1))
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.upper() == filter_bulan]
    return df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')

# --- 4. STYLE FUNCTION (MODERN MAP) ---
def highlight_zona(val):
    color = ''
    if val == 'HIJAU': color = 'background-color: #22C55E; color: white; font-weight: bold;'
    elif val == 'KUNING': color = 'background-color: #F59E0B; color: white; font-weight: bold;'
    elif val == 'MERAH': color = 'background-color: #EF4444; color: white; font-weight: bold;'
    elif val == 'HITAM': color = 'background-color: #475569; color: white; font-weight: bold;'
    return color

# --- 5. MAIN DASHBOARD ---
with st.sidebar:
    st.title("UNJA MONITORING")
    if st.button("Logout"): st.session_state['auth'] = False; st.rerun()
    st.divider()
    file = st.file_uploader("Upload Data", type=["csv", "xlsx"])

if file:
    df_raw = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    bln_opt = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in df_raw['BULAN'].unique() if pd.notna(b)])
    sel_bln = st.sidebar.selectbox("Periode:", bln_opt)
    data = proses_data_unja(df_raw, sel_bln)

    # Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)
    h = len(data[data['ZONA'] == "HIJAU"])
    k = len(data[data['ZONA'] == "KUNING"])
    m = len(data[data['ZONA'] == "MERAH"])
    hitam = len(data[data['ZONA'] == "HITAM"])
    m1.metric("Wajib Lapor", len(data))
    m2.metric("🟢 Hijau", h); m3.metric("🟡 Kuning", k); m4.metric("🔴 Merah", m); m5.metric("⚫ Hitam", hitam)

    # Recommendation Box
    unit_kritis = data[data['ZONA'] == "HITAM"]['SUB UNIT KERJA'].value_counts().index[0] if hitam > 0 else "-"
    st.markdown(f"""<div class="recom-box"><h4>📝 Rekomendasi Naratif</h4><p>Prioritas utama: Tindak lanjut unit <b>{unit_kritis}</b> dan asistensi <b>{m} orang</b> di Zona Merah agar segera menyelesaikan laporan.</p></div>""", unsafe_allow_html=True)

    # Charts Row
    c1, c2 = st.columns([1, 1.5])
    with c1:
        fig = px.pie(data, names='ZONA', hole=0.5, color='ZONA', color_discrete_map={"HIJAU":"#22C55E", "KUNING":"#F59E0B", "MERAH":"#EF4444", "HITAM":"#475569"})
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig, width='stretch')
    with c2:
        hitam_count = data[data['ZONA'] == "HITAM"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
        st.bar_chart(hitam_count.set_index('index'), color="#475569", height=300)

    # --- LEADERBOARD UNIT KERJA (SMALL DIMENSION) ---
    st.divider()
    st.subheader("🏆 Peringkat Kepemimpinan Unit Kerja")
    l1, l2 = st.columns(2)
    
    with l1:
        st.write("✅ **Unit Kerja Terpatuh**")
        df_l1 = data[data['ZONA'] == "HIJAU"]['SUB UNIT KERJA'].value_counts().reset_index().head(5)
        st.dataframe(df_l1, height=210, width='stretch', hide_index=True)

    with l2:
        st.write("🚨 **Unit Kerja Perhatian**")
        df_l2 = data[data['ZONA'] == "HITAM"]['SUB UNIT KERJA'].value_counts().reset_index().head(5)
        st.dataframe(df_l2, height=210, width='stretch', hide_index=True)

    # --- FULL DETAIL TABLE ---
    st.write("#")
    with st.expander("🔍 Detail Seluruh Data Individu"):
        df_view = data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']].reset_index(drop=True)
        st.dataframe(
            df_view.style.map(highlight_zona, subset=['ZONA']),
            width='stretch',
            hide_index=True
        )

else:
    st.info("Silakan unggah data di sidebar.")
