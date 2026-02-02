import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & THEME ADAPTIVE ---
st.set_page_config(page_title="LHKPN Universitas Jambi", layout="wide")

st.markdown("""
    <style>
    .stMetric {
        background-color: rgba(151, 166, 195, 0.1);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(151, 166, 195, 0.2);
    }
    /* Kotak Rekomendasi Custom */
    .recom-box {
        background-color: rgba(21, 112, 239, 0.05);
        border-left: 5px solid #1570EF;
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0px 25px 0px;
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA DATA ENGINE ---
def proses_data_unja(df, filter_bulan):
    df.columns = df.columns.str.strip()
    # Cleaning NIK agar unik (Hapus tanda petik)
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

# --- 3. FUNGSI REKOMENDASI OTOMATIS ---
def tampilkan_rekomendasi(data, total, h, k, m, hitam):
    rate = ((total - hitam) / total * 100) if total > 0 else 0
    df_hitam = data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts()
    unit_kritis = df_hitam.index[0] if not df_hitam.empty else "Seluruh Unit"
    jml_kritis = df_hitam.values[0] if not df_hitam.empty else 0

    st.markdown(f"""
    <div class="recom-box">
        <h3 style="margin-top:0;">📝 Rekomendasi Naratif Pimpinan</h3>
        <p>Berdasarkan analisis data saat ini, tingkat kepatuhan personil UNJA berada di angka <b>{rate:.1f}%</b>. 
        Terdapat <b>{hitam} orang</b> yang masih berada di <b>Zona Hitam</b>.</p>
        <hr style="opacity:0.2;">
        <b>Tindakan Strategis:</b>
        <ul>
            <li>Segera lakukan pemanggilan terhadap personil di <b>{unit_kritis}</b> ({jml_kritis} orang belum lapor).</li>
            <li>Berikan asistensi pengisian bagi <b>{m} personil</b> di <b>Zona Merah</b> agar status Draft segera berubah menjadi Terverifikasi.</li>
            <li>Pertahankan tren positif <b>{h} personil</b> di <b>Zona Hijau</b> sebagai standar kepatuhan institusi.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# --- 4. AUTH & SIDEBAR ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.title("Sistem LHKPN UNJA")
        if st.button("Masuk (Password: 123456)", use_container_width=True):
            st.session_state['auth'] = True
            st.rerun()
    st.stop()

with st.sidebar:
    st.title("UNJA MONITORING")
    if st.button("Keluar"):
        st.session_state['auth'] = False
        st.rerun()
    st.divider()
    file = st.file_uploader("Upload Data (CSV/XLSX)", type=["csv", "xlsx"])

# --- 5. MAIN DASHBOARD ---
if file:
    df_raw = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    bln_opt = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in df_raw['BULAN'].unique() if pd.notna(b)])
    sel_bln = st.sidebar.selectbox("Periode:", bln_opt)
    
    data = proses_data_unja(df_raw, sel_bln)

    st.title("🏛️ Dashboard Kepatuhan LHKPN UNJA")
    st.caption(f"Status Data Individu Unik — Periode: {sel_bln}")
    
    # Metrics KPI
    m1, m2, m3, m4, m5 = st.columns(5)
    h = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
    k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
    m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])
    hitam = len(data[data['ZONA'] == "⚫ ZONA HITAM"])
    
    m1.metric("Wajib Lapor", len(data))
    m2.metric("🟢 Hijau", h)
    m3.metric("🟡 Kuning", k)
    m4.metric("🔴 Merah", m)
    m5.metric("⚫ Hitam", hitam)

    # REKOMENDASI BOX
    tampilkan_rekomendasi(data, len(data), h, k, m, hitam)

    # Visualisasi
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.subheader("Distribusi Kepatuhan")
        fig = px.pie(data, names='ZONA', hole=0.5, color='ZONA',
                     color_discrete_map={"🟢 ZONA HIJAU":"#22C55E", "🟡 ZONA KUNING":"#F59E0B", "🔴 ZONA MERAH":"#EF4444", "⚫ ZONA HITAM":"#64748B"})
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.subheader("Unit Kerja - Zona Hitam")
        hitam_count = data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
        st.bar_chart(hitam_count.set_index('SUB UNIT KERJA'), color="#64748B")

    # Leaderboard
    st.divider()
    st.subheader("🏆 Leaderboard Unit Kerja")
    l1, l2 = st.columns(2)
    with l1:
        st.write("✅ **Unit Kerja Paling Patuh (Hijau)**")
        st.dataframe(data[data['ZONA'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts().head(5), use_container_width=True)
    with l2:
        st.write("🚨 **Unit Kerja Perhatian (Hitam)**")
        st.dataframe(data[data['ZONA'] == "⚫ ZONA HITAM"]['SUB UNIT KERJA'].value_counts().head(5), use_container_width=True)

    with st.expander("🔍 Lihat Semua Detail Nama"):
        st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], use_container_width=True, hide_index=True)

else:
    st.info("Silakan unggah database pelaporan di sidebar.")
