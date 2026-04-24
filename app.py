import streamlit as st
import pandas as pd
import plotly.express as px
import textwrap

# --- 1. CONFIG DASHBOARD ---
st.set_page_config(page_title="LHKPN UNJA Monitoring", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    header, footer {visibility: hidden;}
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA PEMROSESAN DATA ---
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

# --- 3. SISTEM LOGIN ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.write("#")
        st.markdown("<h2 style='text-align: center;'>🏛️ Monitoring LHKPN</h2>", unsafe_allow_html=True)
        pwd = st.text_input("Password Akses", type="password")
        if st.button("Masuk", width='stretch'):
            if pwd == "123456":
                st.session_state['auth'] = True
                st.rerun()
            else:
                st.error("Password Salah!")
    st.stop()

# --- 4. AREA DASHBOARD ---
with st.sidebar:
    st.title("UNJA MONITORING")
    if st.button("Log Out"):
        st.session_state['auth'] = False
        st.rerun()
    st.divider()
    file_upload = st.file_uploader("Upload File LHKPN (Excel/CSV)", type=["xlsx", "csv"])

if file_upload:
    try:
        raw = pd.read_csv(file_upload) if file_upload.name.endswith('.csv') else pd.read_excel(file_upload)
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Pilih Periode:", list_bln)
        
        data = proses_data_unja(raw, sel_bln)

        # --- KALKULASI DATA ---
        total_wl = len(data)
        h = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
        k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
        m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])
        rate = (h / total_wl * 100) if total_wl > 0 else 0

        unit_stats = data.groupby('SUB UNIT KERJA')['ZONA'].value_counts().unstack().fillna(0)
        for z in ["🟢 ZONA HIJAU", "🟡 ZONA KUNING", "🔴 ZONA MERAH"]:
            if z not in unit_stats.columns: unit_stats[z] = 0
        
        unit_stats['Persen_Hijau'] = (unit_stats['🟢 ZONA HIJAU'] / unit_stats.sum(axis=1)) * 100
        
        u_100 = unit_stats[unit_stats['Persen_Hijau'] == 100].index.tolist()
        paripurna_txt = ", ".join(u_100[:3]) + ("..." if len(u_100) > 3 else "") if u_100 else "Belum ada unit 100%"
        
        u_rendah = unit_stats[unit_stats['Persen_Hijau'] < 100].sort_values(by='Persen_Hijau')
        if not u_rendah.empty:
            kritis_nama = u_rendah.index[0]
            kritis_persen = u_rendah.iloc[0]['Persen_Hijau']
            atensi_label = f"Unit <b>{kritis_nama}</b> ({kritis_persen:.1f}%) memerlukan percepatan."
        else:
            atensi_label = "Luar biasa! Seluruh unit kerja telah mencapai target kepatuhan 100%."

        # --- UI DISPLAY ---
        st.title("🏛️ Dashboard Informasi LHKPN")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Wajib Lapor", total_wl)
        m2.metric("🟢 Zona Hijau", h, f"{rate:.1f}%")
        m3.metric("🟡 Zona Kuning", k, "Draft")
        m4.metric("🔴 Zona Merah", m, "Belum Lapor", delta_color="inverse")

        # --- PAPAN INFORMASI EKSEKUTIF ---
        papan_html = textwrap.dedent(f"""
            <div style="background-color: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); font-family: sans-serif;">
                <h3 style="text-align: center; color: #1e3a8a; margin-top: 0; margin-bottom: 20px;">📊 PAPAN INFORMASI STRATEGIS</h3>
                
                <div style="display: grid; grid-template-columns: 1fr; gap: 15px;">
                    <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 15px;">
                        <b style="color: #166534; font-size: 16px;">🏆 SEKTOR APRESIASI (PERFORMA TINGGI)</b><br>
                        <div style="font-size: 14px; color: #1e293b; margin-top: 8px;">
                            • <b>Kategori Paripurna (100%):</b> {paripurna_txt}<br>
                            • <b>Total Unit Tuntas:</b> {len(u_100)} Sub-Unit kerja telah mencapai kepatuhan penuh.
                        </div>
                    </div>

                    <div style="background-color: #fff1f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px;">
                        <b style="color: #9f1239; font-size: 16px;">⚠️ SEKTOR ATENSI (INTERVENSI PRIORITAS)</b><br>
                        <div style="font-size: 14px; color: #1e293b; margin-top: 8px;">
                            • <b>Fokus Utama:</b> {atensi_label}<br>
                            • <b>Residu Pelaporan:</b> Masih terdapat {m} orang yang berada di Zona Merah.
                        </div>
                    </div>

                    <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 15px;">
                        <b style="color: #1e40af; font-size: 16px;">⚡ SEKTOR AKSELERASI (POTENSI INSTAN)</b><br>
                        <div style="font-size: 14px; color: #1e293b; margin-top: 8px;">
                            • <b>Quick-Wins:</b> Terdapat {k} orang di Zona Kuning (Draft).<br>
                            • <b>Proyeksi Kepatuhan:</b> Jika Zona Kuning tuntas hari ini, total kepatuhan naik ke <b>{((h+k)/total_wl*100):.1f}%</b>.
                        </div>
                    </div>
                </div>
            </div>
        """)
        
        st.markdown(papan_html, unsafe_allow_html=True)

        st.write("---")
        v1, v2 = st.columns([1, 1.5])
        with v1:
            fig_pie = px.pie(data, names='ZONA', color='ZONA', hole=0.5,
                             color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"},
                             title="<b>Proporsi Kepatuhan</b>")
            st.plotly_chart(fig_pie, width='stretch')
        with v2:
            df_red = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            df_red.columns = ['Unit', 'Jumlah']
            fig_bar = px.bar(df_red, x='Jumlah', y='Unit', orientation='h', title="<b>Top 10 Unit (Zona Merah)</b>", color_discrete_sequence=['#EF4444'])
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, width='stretch')

        with st.expander("🔍 Lihat Detail Data Individu"):
            st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], width='stretch', hide_index=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
else:
    st.info("Silakan unggah database LHKPN melalui sidebar.")
