import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="LHKPN UNJA Monitoring", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    /* Background & Font */
    .main { background-color: #f8fafc; }
    
    /* Custom Card for Metrics */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* Header Hide */
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA ENGINE (OPTIMIZED) ---
@st.cache_data
def proses_data_unja(df, filter_bulan):
    # Bersihkan Data
    df = df.dropna(subset=['NIK', 'NAMA', 'SUB UNIT KERJA'])
    
    # Normalisasi NIK agar tidak jadi angka scientific
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[\'\" ]", "", regex=True).str.split('.').str[0]
    
    # Logika Penentuan Zona
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
    
    # Filter Berdasarkan Bulan
    if filter_bulan != "GLOBAL (AKUMULASI)":
        df = df[df['BULAN'].astype(str).str.strip().str.upper() == filter_bulan]
    
    # Ambil 1 NIK 1 Status Terbaik (Deduplikasi)
    df_final = df.sort_values('rank').drop_duplicates(subset=['NIK_KEY'], keep='first')
    return df_final

# --- 3. AKSES LOGIN ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.write("#")
        st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>🏛️ LHKPN UNJA</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Dashboard Informasi Eksekutif</p>", unsafe_allow_html=True)
        pwd = st.text_input("Masukkan Password Akses", type="password")
        if st.button("Masuk ke Dashboard", use_container_width=True):
            if pwd == "123456": # Ganti password sesuai kebutuhan
                st.session_state['auth'] = True
                st.rerun()
            else:
                st.error("Password Salah!")
    st.stop()

# --- 4. DASHBOARD UTAMA ---
with st.sidebar:
    st.title("UNJA MONITORING")
    if st.button("Log Out"):
        st.session_state['auth'] = False
        st.rerun()
    st.divider()
    file_upload = st.file_uploader("Unggah File (Excel/CSV)", type=["xlsx", "csv"])

if file_upload:
    try:
        # Load Data
        raw = pd.read_csv(file_upload) if file_upload.name.endswith('.csv') else pd.read_excel(file_upload)
        
        # Filter Periode
        list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
        sel_bln = st.sidebar.selectbox("Pilih Periode Analisis:", list_bln)
        
        # Proses Data
        data = proses_data_unja(raw, sel_bln)

        # --- KALKULASI STATISTIK ---
        total_wl = len(data)
        h_data = data[data['ZONA'] == "🟢 ZONA HIJAU"]
        h, k, m = len(h_data), len(data[data['ZONA'] == "🟡 ZONA KUNING"]), len(data[data['ZONA'] == "🔴 ZONA MERAH"])
        rate = (h / total_wl * 100) if total_wl > 0 else 0

        # Analisis Per Unit
        unit_stats = data.groupby('SUB UNIT KERJA')['ZONA'].value_counts().unstack().fillna(0)
        for z in ["🟢 ZONA HIJAU", "🟡 ZONA KUNING", "🔴 ZONA MERAH"]:
            if z not in unit_stats.columns: unit_stats[z] = 0
        
        unit_stats['Total'] = unit_stats.sum(axis=1)
        unit_stats['Persen_Hijau'] = (unit_stats['🟢 ZONA HIJAU'] / unit_stats['Total']) * 100
        
        # Kategorisasi Unit untuk Papan Informasi
        unit_paripurna = unit_stats[unit_stats['Persen_Hijau'] == 100].index.tolist()
        paripurna_str = ", ".join(unit_paripurna[:3]) + ("..." if len(unit_paripurna) > 3 else "") if unit_paripurna else "Belum Ada"
        
        unit_progresif = unit_stats[(unit_stats['Persen_Hijau'] >= 80) & (unit_stats['Persen_Hijau'] < 100)].index.tolist()
        progresif_str = ", ".join(unit_progresif[:2]) + ("..." if len(unit_progresif) > 2 else "") if unit_progresif else "-"
        
        unit_dibawah_rata = unit_stats[unit_stats['Persen_Hijau'] < rate].sort_values(by='Persen_Hijau')
        critical_unit = unit_dibawah_rata.index[0] if not unit_dibawah_rata.empty else "-"
        critical_persen = unit_dibawah_rata.iloc[0]['Persen_Hijau'] if not unit_dibawah_rata.empty else 0
        
        lunas_unit_count = len(unit_stats[unit_stats['🔴 ZONA MERAH'] == 0])

        # --- TAMPILAN DASHBOARD ---
        st.title("🏛️ Dashboard Kepatuhan LHKPN")
        st.subheader(f"Universitas Jambi — Periode: {sel_bln}")
        
        # ROW 1: METRIK UTAMA
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Wajib Lapor", f"{total_wl}")
        c2.metric("🟢 Zona Hijau", f"{h}", f"{rate:.1f}%")
        c3.metric("🟡 Zona Kuning", f"{k}", "Draft")
        c4.metric("🔴 Zona Merah", f"{m}", "Belum Lapor", delta_color="inverse")

        # ROW 2: PAPAN INFORMASI EKSEKUTIF
        papan_info_html = f"""
<div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); font-family: sans-serif;">
    <div style="text-align: center; margin-bottom: 25px; border-bottom: 2px solid #f1f5f9; padding-bottom: 15px;">
        <h2 style="margin: 0; color: #1e3a8a; font-size: 24px;">📊 PAPAN INFORMASI STRATEGIS</h2>
        <p style="margin: 5px 0 0 0; color: #64748b; font-size: 14px;">Ringkasan Analisis Performa Unit Kerja</p>
    </div>

    <div style="display: grid; grid-template-columns: 1fr; gap: 15px;">
        <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 15px;">
            <b style="color: #166534; font-size: 16px;">🏆 SEKTOR APRESIASI (PERFORMA TINGGI)</b><br>
            <div style="font-size: 14px; color: #1e293b; margin-top: 8px;">
                • <b>Kategori Paripurna (100%):</b> {paripurna_str}<br>
                • <b>Kategori Progresif (>80%):</b> {progresif_str}<br>
                • <b>Total Unit Tuntas:</b> {lunas_unit_count} Sub-Unit telah mencapai nol Zona Merah.
            </div>
        </div>

        <div style="background-color: #fff1f2; border: 1px solid #fecaca; border-radius: 10px; padding: 15px;">
            <b style="color: #9f1239; font-size: 16px;">⚠️ SEKTOR ATENSI (INTERVENSI PRIORITAS)</b><br>
            <div style="font-size: 14px; color: #1e293b; margin-top: 8px;">
                • <b>Unit Kritis:</b> {critical_unit} (Kepatuhan: {critical_persen:.1f}%) berada di bawah rata-rata universitas.<br>
                • <b>Residu Pelaporan:</b> Terdapat {m} orang yang sama sekali belum memulai pengisian.<br>
                • <b>Tindakan:</b> Diperlukan atensi langsung Pimpinan unit terkait untuk percepatan Zona Merah.
            </div>
        </div>

        <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 15px;">
            <b style="color: #1e40af; font-size: 16px;">⚡ SEKTOR AKSELERASI (POTENSI KENAIKAN)</b><br>
            <div style="font-size: 14px; color: #1e293b; margin-top: 8px;">
                • <b>Quick-Wins:</b> {k} orang di Zona Kuning (Draft) hanya membutuhkan finalisasi submit.<br>
                • <b>Estimasi Proyeksi:</b> Jika Zona Kuning tuntas, kepatuhan total akan naik ke <b>{((h+k)/total_wl*100):.1f}%</b>.<br>
                • <b>Fokus:</b> Dorong penyelesaian status 'Perlu Perbaikan' bagi personel di Zona Hijau.
            </div>
        </div>
    </div>
</div>
"""
        st.markdown(papan_info_html, unsafe_allow_html=True)

        # ROW 3: VISUALISASI
        st.write("---")
        v1, v2 = st.columns([1, 1.5])
        with v1:
            fig_pie = px.pie(data, names='ZONA', hole=0.5, color='ZONA',
                             color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"},
                             title="<b>Proporsi Kepatuhan</b>")
            st.plotly_chart(fig_pie, use_container_width=True)
        with v2:
            df_red = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            df_red.columns = ['Unit', 'Jumlah']
            fig_bar = px.bar(df_red, x='Jumlah', y='Unit', orientation='h', title="<b>10 Unit Terbanyak Belum Lapor</b>", color_discrete_sequence=['#EF4444'])
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)

        # TABEL DETAIL
        with st.expander("🔍 Detail Individu (NAMA & JABATAN)"):
            st.dataframe(data[['NAMA', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], use_container_width=True, hide_index=True)
            csv = data.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Report Lengkap", csv, f"LHKPN_UNJA_{sel_bln}.csv", "text/csv")

    except Exception as e:
        st.error(f"Gagal memproses file. Pastikan kolom sesuai. Detail: {e}")
else:
    st.info("Silakan unggah file database pelaporan LHKPN (Excel/CSV) di sidebar untuk melihat analisis.")
