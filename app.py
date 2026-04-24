import streamlit as st
import pandas as pd
import plotly.express as px
import textwrap

# --- 1. CONFIG ---
st.set_page_config(page_title="LHKPN UNJA Monitoring", layout="wide")

# --- 2. DATA ENGINE ---
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

# --- 3. DASHBOARD LOGIC ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if p == "123456": st.session_state['auth'] = True; st.rerun()
    st.stop()

with st.sidebar:
    file_upload = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])

if file_upload:
    raw = pd.read_csv(file_upload) if file_upload.name.endswith('.csv') else pd.read_excel(file_upload)
    list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
    sel_bln = st.sidebar.selectbox("Periode:", list_bln)
    data = proses_data_unja(raw, sel_bln)

    # --- KALKULASI TAJAM ---
    total_wl = len(data)
    h = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
    k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
    m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])
    rate = (h / total_wl * 100) if total_wl > 0 else 0

    unit_stats = data.groupby('SUB UNIT KERJA')['ZONA'].value_counts().unstack().fillna(0)
    for z in ["🟢 ZONA HIJAU", "🟡 ZONA KUNING", "🔴 ZONA MERAH"]:
        if z not in unit_stats.columns: unit_stats[z] = 0
    unit_stats['Persen'] = (unit_stats['🟢 ZONA HIJAU'] / unit_stats.sum(axis=1)) * 100
    
    # Unit Paripurna (100%)
    u_100 = unit_stats[unit_stats['Persen'] == 100].index.tolist()
    u_100_str = ", ".join(u_100[:3]) if u_100 else "Belum ada"
    
    # Unit Kritis (Hanya jika ada yang belum 100%)
    u_kritis_df = unit_stats[unit_stats['Persen'] < 100].sort_values(by='Persen')
    if not u_kritis_df.empty:
        critical_name = u_kritis_df.index[0]
        critical_pct = u_kritis_df.iloc[0]['Persen']
        atensi_msg = f"Unit <b>{critical_name}</b> ({critical_pct:.1f}%) di bawah target."
    else:
        atensi_msg = "Seluruh unit telah mencapai target 100% kepatuhan."

    # --- RENDER PAPAN (MENGGUNAKAN DEDENT AGAR TIDAK ERROR) ---
    papan_info = textwrap.dedent(f"""
        <div style="background-color: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; font-family: sans-serif;">
            <h3 style="text-align: center; color: #1e3a8a; margin-bottom: 20px;">📊 PAPAN INFORMASI EKSEKUTIF</h3>
            
            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                <b style="color: #166534;">🏆 SEKTOR APRESIASI</b><br>
                <span style="font-size: 14px;">
                    • <b>Kategori Paripurna (100%):</b> {u_100_str}<br>
                    • <b>Total Unit Tuntas:</b> {len(u_100)} Sub-Unit.
                </span>
            </div>

            <div style="background-color: #fff1f2; border: 1px solid #fecaca; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                <b style="color: #9f1239;">⚠️ SEKTOR ATENSI</b><br>
                <span style="font-size: 14px;">
                    • <b>Status:</b> {atensi_msg}<br>
                    • <b>Residu:</b> {m} orang belum melapor.
                </span>
            </div>

            <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 15px;">
                <b style="color: #1e40af;">⚡ SEKTOR AKSELERASI</b><br>
                <span style="font-size: 14px;">
                    • <b>Quick-Wins:</b> {k} orang di Zona Kuning (Draft).<br>
                    • <b>Proyeksi:</b> Potensi kepatuhan naik ke <b>{((h+k)/total_wl*100):.1f}%</b>.
                </span>
            </div>
        </div>
    """)

    st.markdown(papan_info, unsafe_allow_html=True)
    
    # --- VISUALISASI ---
    st.plotly_chart(px.pie(data, names='ZONA', color='ZONA', hole=0.5, 
                          color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"}))
