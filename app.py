import streamlit as st
import pandas as pd
import plotly.express as px

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

# --- 3. LOGIN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if not st.session_state['auth']:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        p = st.text_input("Password Akses", type="password")
        if st.button("Masuk", width='stretch'):
            if p == "123456": st.session_state['auth'] = True; st.rerun()
    st.stop()

# --- 4. DASHBOARD AREA ---
with st.sidebar:
    file_upload = st.file_uploader("Upload Excel/CSV LHKPN", type=["xlsx", "csv"])

if file_upload:
    try:
        raw = pd.read_csv(file_upload) if file_upload.name.endswith('.csv') else pd.read_excel(file_upload)
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Pilih Periode:", list_bln)
        data = proses_data_unja(raw, sel_bln)

        # KALKULASI
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
        paripurna_txt = ", ".join(u_100[:2]) + ("..." if len(u_100) > 2 else "") if u_100 else "Belum Ada"
        
        u_rendah = unit_stats[unit_stats['Persen_Hijau'] < 100].sort_values(by='Persen_Hijau')
        if not u_rendah.empty:
            atensi_label = f"Unit <b>{u_rendah.index[0]}</b> ({u_rendah.iloc[0]['Persen_Hijau']:.1f}%) memerlukan atensi."
        else:
            atensi_label = "Luar biasa! Seluruh unit telah mencapai 100%."

        # METRIK
        st.title("🏛️ Dashboard LHKPN")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Wajib Lapor", total_wl)
        m2.metric("🟢 Hijau", h, f"{rate:.1f}%")
        m3.metric("🟡 Kuning", k)
        m4.metric("🔴 Merah", m, delta_color="inverse")

        # --- PAPAN INFORMASI (TEKNIK RAPAT KIRI) ---
        # Pastikan tidak ada spasi di awal baris HTML di bawah ini
        papan_html = f"""
<div style="background-color: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; font-family: sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
<h3 style="text-align: center; color: #1e3a8a; margin-bottom: 20px;">📊 PAPAN INFORMASI EKSEKUTIF</h3>
<div style="display: flex; flex-direction: column; gap: 15px;">
<div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 15px;">
<b style="color: #166534;">🏆 SEKTOR APRESIASI</b><br>
<span style="font-size: 14px; color: #1e293b;">
• <b>Kategori Paripurna (100%):</b> {paripurna_txt}<br>
• <b>Total Unit Tuntas:</b> {len(u_100)} Sub-Unit.
</span>
</div>
<div style="background-color: #fff1f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px;">
<b style="color: #9f1239;">⚠️ SEKTOR ATENSI</b><br>
<span style="font-size: 14px; color: #1e293b;">
• <b>Fokus:</b> {atensi_label}<br>
• <b>Residu:</b> {m} orang belum melapor.
</span>
</div>
<div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 15px;">
<b style="color: #1e40af;">⚡ SEKTOR AKSELERASI</b><br>
<span style="font-size: 14px; color: #1e293b;">
• <b>Quick-Wins:</b> {k} orang di Zona Kuning (Draft).<br>
• <b>Estimasi:</b> Potensi naik ke <b>{((h+k)/total_wl*100):.1f}%</b>.
</span>
</div>
</div>
</div>
"""
        # Eksekusi Render
        st.markdown(papan_html, unsafe_allow_html=True)

        # VISUALISASI
        st.write("---")
        v1, v2 = st.columns([1, 1.5])
        with v1:
            st.plotly_chart(px.pie(data, names='ZONA', color='ZONA', hole=0.5,
                                  color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"}), width='stretch')
        with v2:
            df_red = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            st.plotly_chart(px.bar(df_red, x='count', y='SUB UNIT KERJA', orientation='h', title="Top 10 Unit Merah", color_discrete_sequence=['#EF4444']), width='stretch')

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Silakan unggah file database LHKPN.")
