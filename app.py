import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG ---
st.set_page_config(page_title="LHKPN UNJA Monitoring", layout="wide", page_icon="🏛️")

# --- 2. DATA ENGINE ---
@st.cache_data
def proses_data_unja(df, filter_bulan):
    # Standarisasi nama kolom (menghapus spasi liar)
    df.columns = [c.strip().upper() for c in df.columns]
    
    # Drop data krusial yang kosong
    df = df.dropna(subset=['NIK', 'NAMA', 'SUB UNIT KERJA'])
    
    # Optimasi pembersihan NIK
    df['NIK_KEY'] = df['NIK'].astype(str).str.extract(r'(\d+)')
    
    def get_zona(status):
        status = str(status).strip()
        hijau_status = [
            "Diumumkan Lengkap", "Diumumkan Tidak Lengkap", "Perlu Perbaikan", 
            "Perlu Verifikasi", "Terverifikasi Lengkap", "Proses Verifikasi"
        ]
        if status in hijau_status: return 1, "🟢 ZONA HIJAU"
        if status == "Draft": return 2, "🟡 ZONA KUNING"
        if status == "Belum Lapor": return 3, "🔴 ZONA MERAH"
        return 4, "⚪ LAINNYA"

    # Lebih cepat memetakan satu kolom daripada apply(axis=1)
    res = df['STATUS LHKPN'].apply(get_zona)
    df['rank'] = [x[0] for x in res]
    df['ZONA'] = [x[1] for x in res]
    
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.strip().str.upper() == filter_bulan]
    
    # Hapus duplikat NIK (ambil status terbaik)
    return df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')

# --- 3. LOGIN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if not st.session_state['auth']:
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("<h2 style='text-align: center;'>🔐 Monitoring LHKPN</h2>", unsafe_allow_html=True)
        p = st.text_input("Password Akses", type="password")
        if st.button("Masuk", use_container_width=True):
            if p == "123456": 
                st.session_state['auth'] = True
                st.rerun()
            else:
                st.error("Password Salah")
    st.stop()

# --- 4. DASHBOARD AREA ---
with st.sidebar:
    st.header("⚙️ Panel Kontrol")
    file_upload = st.file_uploader("Upload Excel/CSV LHKPN", type=["xlsx", "csv"])
    st.divider()
    if st.button("Log Out"):
        st.session_state['auth'] = False
        st.rerun()

if file_upload:
    try:
        raw = pd.read_csv(file_upload) if file_upload.name.endswith('.csv') else pd.read_excel(file_upload)
        raw.columns = [c.strip().upper() for c in raw.columns] # Pre-clean columns
        
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Pilih Periode Lapor:", list_bln)
        
        data = proses_data_unja(raw, sel_bln)

        # KALKULASI METRIK UTAMA
        total_wl = len(data)
        h = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
        k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
        m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])
        rate = (h / total_wl * 100) if total_wl > 0 else 0

        # STATISTIK PER UNIT
        unit_stats = data.groupby('SUB UNIT KERJA')['ZONA'].value_counts().unstack().fillna(0)
        for z in ["🟢 ZONA HIJAU", "🟡 ZONA KUNING", "🔴 ZONA MERAH"]:
            if z not in unit_stats.columns: unit_stats[z] = 0
            
        unit_stats['Total'] = unit_stats.sum(axis=1)
        unit_stats['Persen_Hijau'] = (unit_stats['🟢 ZONA HIJAU'] / unit_stats['Total']) * 100
        
        # LOGIKA PAPAN INFORMASI
        u_100 = unit_stats[unit_stats['Persen_Hijau'] == 100].index.tolist()
        paripurna_txt = ", ".join(u_100[:3]) + ("..." if len(u_100) > 3 else "") if u_100 else "Belum Ada"
        
        u_rendah = unit_stats.sort_values(by='Persen_Hijau')
        atensi_label = f"<b>{u_rendah.index[0]}</b> ({u_rendah.iloc[0]['Persen_Hijau']:.1f}%)" if not u_rendah.empty and h < total_wl else "Semua Unit Aman"

        # --- RENDER UI ---
        st.title("🏛️ Dashboard Monitoring LHKPN UNJA")
        st.caption(f"Periode Data: {sel_bln}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Wajib Lapor", f"{total_wl} Jiwa")
        m2.metric("🟢 Zona Hijau", h, f"{rate:.1f}%")
        m3.metric("🟡 Zona Kuning", k, help="Status Draft")
        m4.metric("🔴 Zona Merah", m, delta=f"{m} Orang", delta_color="inverse")

        # PAPAN INFORMASI EKSEKUTIF
        papan_html = f"""
        <div style="background-color: #ffffff; border-radius: 15px; padding: 25px; border: 1px solid #e6e9ef; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);">
            <h3 style="text-align: center; color: #0f172a; margin-top: 0;">📊 RINGKASAN EKSEKUTIF</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                <div style="padding: 15px; border-left: 5px solid #22c55e; background: #f0fdf4; border-radius: 8px;">
                    <b style="color: #15803d;">🏆 APRESIASI (UNIT 100%)</b><br>
                    <small style="color: #1e293b;">{paripurna_txt}</small>
                </div>
                <div style="padding: 15px; border-left: 5px solid #ef4444; background: #fef2f2; border-radius: 8px;">
                    <b style="color: #b91c1c;">⚠️ PRIORITAS ATENSI</b><br>
                    <small style="color: #1e293b;">Unit Terendah: {atensi_label}</small>
                </div>
                <div style="padding: 15px; border-left: 5px solid #3b82f6; background: #eff6ff; border-radius: 8px;">
                    <b style="color: #1d4ed8;">⚡ POTENSI AKSELERASI</b><br>
                    <small style="color: #1e293b;">Target Terdekat: <b>{((h+k)/total_wl*100):.1f}%</b> (Jika Kuning tuntas)</small>
                </div>
            </div>
        </div>
        """
        st.markdown(papan_html, unsafe_allow_html=True)

        # VISUALISASI
        st.markdown("<br>", unsafe_allow_html=True)
        v1, v2 = st.columns([1, 1.5])
        
        with v1:
            fig_pie = px.pie(data, names='ZONA', color='ZONA', hole=0.5,
                             title="Komposisi Kepatuhan",
                             color_discrete_map={
                                 "🟢 ZONA HIJAU": "#22C55E", 
                                 "🟡 ZONA KUNING": "#F59E0B", 
                                 "🔴 ZONA MERAH": "#EF4444",
                                 "⚪ LAINNYA": "#94A3B8"
                             })
            fig_pie.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with v2:
            df_red = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            fig_bar = px.bar(df_red, x='count', y='SUB UNIT KERJA', orientation='h', 
                             title="10 Unit dengan Residu Merah Terbanyak",
                             labels={'count': 'Jumlah Belum Lapor', 'SUB UNIT KERJA': ''},
                             color_discrete_sequence=['#EF4444'])
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan pemrosesan: {e}")
        st.warning("Pastikan format file memiliki kolom: NIK, NAMA, SUB UNIT KERJA, STATUS LHKPN, dan BULAN")
else:
    st.info("👋 Selamat Datang! Silakan unggah file Excel/CSV LHKPN melalui sidebar untuk memulai analisis.")
