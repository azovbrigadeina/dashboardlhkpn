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
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA DATA ENGINE ---
def proses_data_unja(df, filter_bulan):
    df.columns = df.columns.str.strip()
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[\'\" ]", "", regex=True)
    
    def get_zona(row):
        status = str(row['Status LHKPN']).strip()
        
        hijau_status = [
            "Diumumkan Lengkap", "Diumumkan Tidak Lengkap", 
            "Perlu Perbaikan", "Perlu Verifikasi", 
            "Terverifikasi Lengkap", "Proses Verifikasi"
        ]
        
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
    
    return df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')

# --- 3. STYLE ---
def style_zona(val):
    if "HIJAU" in val: return 'background-color: #dcfce7; color: #166534; font-weight: bold;'
    if "KUNING" in val: return 'background-color: #fef9c3; color: #854d0e; font-weight: bold;'
    if "MERAH" in val: return 'background-color: #fee2e2; color: #991b1b; font-weight: bold;'
    return ''

# --- 4. LOGIN ---
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

# --- 5. DASHBOARD ---
with st.sidebar:
    st.title("UNJA MONITORING")
    if st.button("Log Out"):
        st.session_state['auth'] = False
        st.rerun()
    st.divider()
    file_upload = st.file_uploader("Upload Database", type=["xlsx", "csv"])

if file_upload:
    try:
        raw = pd.read_csv(file_upload) if file_upload.name.endswith('.csv') else pd.read_excel(file_upload)
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Filter Periode:", list_bln)
        
        data = proses_data_unja(raw, sel_bln)

        st.title("🏛️ Monitoring Kepatuhan LHKPN")
        st.subheader(f"Universitas Jambi — {sel_bln}")
        
        # Metrics
        total_wl = len(data)
        h_data = data[data['ZONA'] == "🟢 ZONA HIJAU"]
        h = len(h_data)
        k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
        m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Wajib Lapor", total_wl)
        m2.metric("🟢 Zona Hijau", h)
        m3.metric("🟡 Zona Kuning", k)
        m4.metric("🔴 Zona Merah", m)

        # Recommendation
        rate = (h / total_wl * 100) if total_wl > 0 else 0
        lunas_kpk = len(h_data[h_data['Status LHKPN'] == "Diumumkan Lengkap"])
        
        st.markdown(f"""
        <div class="recom-box">
            <h4 style="margin-top:0; color:#1570EF;">📝 Rekomendasi Naratif Pimpinan</h4>
            <p>Dari total <b>{total_wl}</b> wajib lapor, sebanyak <b>{h} orang ({rate:.1f}%)</b> berada di Zona Hijau. 
            Menariknya, sudah ada <b>{lunas_kpk} orang</b> yang statusnya sudah <b>'Diumumkan Lengkap'</b> oleh KPK.</p>
        </div>
        """, unsafe_allow_html=True)

        # Visualizations
        c1, c2 = st.columns([1, 1.5])
        with c1:
            # Pie Chart Utama
            fig_pie = px.pie(data, names='ZONA', hole=0.5, color='ZONA',
                             color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"},
                             title="<b>Sebaran Zona Kepatuhan</b>")
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            # Chart Tambahan: Bedah Zona Hijau
            if not h_data.empty:
                # Menghitung sub-status di dalam zona hijau
                df_hijau_detail = h_data['Status LHKPN'].value_counts().reset_index()
                df_hijau_detail.columns = ['Status Spesifik', 'Jumlah']
                
                fig_h = px.bar(df_hijau_detail, x='Jumlah', y='Status Spesifik', orientation='h',
                               title="<b>Detail Status di Zona Hijau</b>",
                               color='Status Spesifik',
                               color_discrete_map={"Diumumkan Lengkap": "#15803d"}) # Hijau Tua untuk yang Selesai
                fig_h.update_layout(showlegend=False)
                st.plotly_chart(fig_h, use_container_width=True)

        with st.expander("🔍 Detail Data Individu"):
            st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']].style.map(style_zona, subset=['ZONA']), 
                         use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Gagal memproses data: {e}")
