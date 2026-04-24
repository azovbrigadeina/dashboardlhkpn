import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="Dashboard LHKPN UNJA", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    .recom-box {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 30px;
        border-radius: 8px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
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
    df = df.dropna(subset=['NIK', 'NAMA', 'SUB UNIT KERJA'])
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[\'\" ]", "", regex=True).str.split('.').str[0]
    
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
        df = df[df['BULAN'].astype(str).str.strip().str.upper() == filter_bulan]
    
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
        if st.button("Masuk", use_container_width=True):
            if p == "123456":
                st.session_state['auth'] = True
                st.rerun()
            else: st.error("Salah!")
    st.stop()

# --- 4. DASHBOARD ---
with st.sidebar:
    st.title("UNJA MONITORING")
    if st.button("Log Out"):
        st.session_state['auth'] = False
        st.rerun()
    file_upload = st.file_uploader("Upload Data", type=["xlsx", "csv"])

if file_upload:
    try:
        raw = pd.read_csv(file_upload) if file_upload.name.endswith('.csv') else pd.read_excel(file_upload)
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Periode:", list_bln)
        
        data = proses_data_unja(raw, sel_bln)

        # Kalkulasi
        total_wl = len(data)
        h_data = data[data['ZONA'] == "🟢 ZONA HIJAU"]
        h, k, m = len(h_data), len(data[data['ZONA'] == "🟡 ZONA KUNING"]), len(data[data['ZONA'] == "🔴 ZONA MERAH"])
        rate = (h / total_wl * 100) if total_wl > 0 else 0

        # Analisis Unit
        unit_stats = data.groupby('SUB UNIT KERJA')['ZONA'].value_counts().unstack().fillna(0)
        for z in ["🟢 ZONA HIJAU", "🟡 ZONA KUNING", "🔴 ZONA MERAH"]:
            if z not in unit_stats.columns: unit_stats[z] = 0
        unit_stats['Persen'] = (unit_stats['🟢 ZONA HIJAU'] / unit_stats.sum(axis=1)) * 100
        unit_teladan = unit_stats.sort_values(by='Persen', ascending=False).index[0]
        unit_kritis_nama = unit_stats.sort_values(by='Persen').index[0]
        unit_kritis_persen = unit_stats.sort_values(by='Persen').iloc[0]['Persen']
        lunas_unit_count = len(unit_stats[unit_stats['🔴 ZONA MERAH'] == 0])

        # METRIK
        st.title("🏛️ Monitoring Kepatuhan LHKPN")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Wajib Lapor", total_wl)
        c2.metric("🟢 Hijau", h, f"{rate:.1f}%")
        c3.metric("🟡 Kuning", k)
        c4.metric("🔴 Merah", m, delta_color="inverse")

        # --- NOTA DINAS (DIPERBAIKI) ---
       # --- BAGIAN NOTA DINAS (PASTIKAN POSISI TEKS RAPAT KIRI) ---
        nota_html = f"""
<div class="recom-box">
<h3 style="margin-top:0; color:#1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom:10px;">
🏛️ NOTA ANALISIS KEPATUHAN LHKPN
</h3>
<p style="font-size: 14px; color: #475569; font-style: italic;">
Kepada Yth: Pimpinan Universitas Jambi<br>
Dari: Admin Pengelola LHKPN Universitas
</p>
<p style="font-size: 15px; line-height: 1.6; color: #1e293b;">
Melaporkan progres kepatuhan periode <b>{sel_bln}</b> dengan tingkat kepatuhan <b>{rate:.1f}%</b>.
</p>

<div style="background-color: #f0fdf4; padding: 18px; border-radius: 8px; border: 1px solid #bbf7d0; margin-bottom:15px; color: #166534;">
<b>1. Penguatan Komitmen (Apresiasi)</b><br>
Apresiasi kepada <b>{unit_teladan}</b> sebagai unit terbaik. 
Sebanyak <b>{lunas_unit_count} Sub-Unit</b> telah mencapai kepatuhan 100%.
</div>

<div style="background-color: #fef2f2; padding: 18px; border-radius: 8px; border: 1px solid #fecaca; margin-bottom:15px; color: #991b1b;">
<b>2. Intervensi Manajerial (Atensi Khusus)</b><br>
Unit <b>{unit_kritis_nama}</b> memerlukan atensi pimpinan karena kepatuhan baru mencapai <b>{unit_kritis_persen:.1f}%</b>.
</div>

<div style="background-color: #fffbeb; padding: 18px; border-radius: 8px; border: 1px solid #fef3c7; margin-bottom:15px; color: #854d0e;">
<b>3. Strategi Quick-Wins</b><br>
Terdapat <b>{k} orang</b> di Zona Kuning (Draft). Jika instruksi submit dilakukan hari ini, kepatuhan naik menjadi <b>{((h+k)/total_wl*100):.1f}%</b>.
</div>

<p style="font-size: 13px; color: #64748b; border-top: 1px dashed #cbd5e1; padding-top: 10px;">
Demikian rekomendasi ini kami sampaikan untuk bahan kebijakan Pimpinan.
</p>
</div>
"""
        # Eksekusi dengan unsafe_allow_html=True
        st.markdown(nota_html, unsafe_allow_html=True)

        # VISUALISASI
        col_v1, col_v2 = st.columns([1, 1.5])
        with col_v1:
            st.plotly_chart(px.pie(data, names='ZONA', color='ZONA', hole=0.5,
                                  color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"}), 
                            use_container_width=True)
        with col_v2:
            df_red = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            st.plotly_chart(px.bar(df_red, x='count', y='SUB UNIT KERJA', orientation='h', title="Top 10 Zona Merah", color_discrete_sequence=['#EF4444']), 
                            use_container_width=True)

        with st.expander("🔍 Detail Data"):
            st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Silakan unggah file database LHKPN.")
