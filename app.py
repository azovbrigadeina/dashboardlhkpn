import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG ---
st.set_page_config(page_title="LHKPN UNJA Monitoring", layout="wide")

# --- 2. DATA ENGINE ---
@st.cache_data
def proses_data_unja(df, filter_bulan):
    # Membersihkan data dasar
    df = df.dropna(subset=['NIK', 'NAMA', 'SUB UNIT KERJA'])
    df['NIK_KEY'] = df['NIK'].astype(str).str.replace(r"[^0-9]", "", regex=True)
    
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
        st.write("# 🏛️ LHKPN Login")
        p = st.text_input("Password Akses", type="password")
        if st.button("Masuk", use_container_width=True):
            if p == "123456": 
                st.session_state['auth'] = True
                st.rerun()
            else:
                st.error("Password Salah!")
    st.stop()

# --- 4. CSS CUSTOM UNTUK CARD ---
st.markdown("""
    <style>
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-top: 5px solid #ececec;
    }
    .metric-label { font-size: 14px; color: #64748b; font-weight: bold; }
    .metric-value { font-size: 32px; font-weight: bold; color: #1e293b; margin: 5px 0; }
    .metric-delta { font-size: 13px; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# --- 5. DASHBOARD AREA ---
with st.sidebar:
    st.header("⚙️ Kontrol")
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

        st.title("🏛️ Dashboard LHKPN Monitoring")
        
        # --- GRID METRIK (CARD TIMBUL) ---
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f'<div class="metric-card" style="border-top-color: #3b82f6;"><div class="metric-label">WAJIB LAPOR</div><div class="metric-value">{total_wl}</div><div class="metric-delta" style="color: #3b82f6;">Orang</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card" style="border-top-color: #22c55e;"><div class="metric-label">🟢 HIJAU</div><div class="metric-value">{h}</div><div class="metric-delta" style="color: #22c55e;">{rate:.1f}% Tuntas</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card" style="border-top-color: #f59e0b;"><div class="metric-label">🟡 KUNING</div><div class="metric-value">{k}</div><div class="metric-delta" style="color: #f59e0b;">Status Draft</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="metric-card" style="border-top-color: #ef4444;"><div class="metric-label">🔴 MERAH</div><div class="metric-value">{m}</div><div class="metric-delta" style="color: #ef4444;">Belum Lapor</div></div>', unsafe_allow_html=True)

        st.write("---")

        # --- PAPAN INFORMASI EKSEKUTIF ---
        unit_stats = data.groupby('SUB UNIT KERJA')['ZONA'].value_counts().unstack().fillna(0)
        for z in ["🟢 ZONA HIJAU", "🟡 ZONA KUNING", "🔴 ZONA MERAH"]:
            if z not in unit_stats.columns: unit_stats[z] = 0
        
        unit_stats['Persen_Hijau'] = (unit_stats['🟢 ZONA HIJAU'] / unit_stats.sum(axis=1)) * 100
        u_100 = unit_stats[unit_stats['Persen_Hijau'] == 100].index.tolist()
        paripurna_txt = ", ".join(u_100[:2]) + ("..." if len(u_100) > 2 else "") if u_100 else "Belum Ada"
        u_rendah = unit_stats[unit_stats['Persen_Hijau'] < 100].sort_values(by='Persen_Hijau')
        atensi_label = f"Unit <b>{u_rendah.index[0]}</b> ({u_rendah.iloc[0]['Persen_Hijau']:.1f}%)" if not u_rendah.empty else "Semua Unit 100%"

        papan_html = f"""
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px;">
            <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 250px; background: white; padding: 15px; border-radius: 8px; border: 1px solid #bbf7d0;">
                    <b style="color: #166534;">🏆 APRESIASI</b><br>
                    <small>Unit Paripurna: {paripurna_txt} ({len(u_100)} Unit)</small>
                </div>
                <div style="flex: 1; min-width: 250px; background: white; padding: 15px; border-radius: 8px; border: 1px solid #fecaca;">
                    <b style="color: #9f1239;">⚠️ ATENSI</b><br>
                    <small>Prioritas: {atensi_label}</small>
                </div>
                <div style="flex: 1; min-width: 250px; background: white; padding: 15px; border-radius: 8px; border: 1px solid #bfdbfe;">
                    <b style="color: #1e40af;">⚡ AKSELERASI</b><br>
                    <small>Potensi Maksimal: {((h+k)/total_wl*100):.1f}% Jika Kuning tuntas.</small>
                </div>
            </div>
        </div>
        """
        st.markdown(papan_html, unsafe_allow_html=True)

        # --- TABEL DETAIL INDIVIDU ---
        st.write("### 📋 Detail Individu")
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            f_zona = st.multiselect("Filter Zona:", options=data['ZONA'].unique(), default=data['ZONA'].unique())
        with col_f2:
            f_cari = st.text_input("Cari Nama/NIK/Unit:")

        df_tabel = data[data['ZONA'].isin(f_zona)]
        if f_cari:
            df_tabel = df_tabel[df_tabel.apply(lambda row: f_cari.lower() in str(row).lower(), axis=1)]

        st.dataframe(
            df_tabel[['NAMA', 'NIK', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']],
            use_container_width=True,
            hide_index=True
        )

        # --- VISUALISASI ---
        st.write("### 📊 Analisis Grafis")
        v1, v2 = st.columns([1, 1.5])
        with v1:
            st.plotly_chart(px.pie(data, names='ZONA', color='ZONA', hole=0.5,
                                  color_discrete_map={"🟢 ZONA HIJAU": "#22C55E", "🟡 ZONA KUNING": "#F59E0B", "🔴 ZONA MERAH": "#EF4444"}), use_container_width=True)
        with v2:
            df_red = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
            if not df_red.empty:
                st.plotly_chart(px.bar(df_red, x='count', y='SUB UNIT KERJA', orientation='h', title="Top 10 Unit Perlu Atensi (Merah)", 
                                     color_discrete_sequence=['#EF4444']), use_container_width=True)
            else:
                st.success("Tidak ada unit di Zona Merah!")

    except Exception as e:
        st.error(f"Terjadi kesalahan pembacaan file: {e}")
else:
    st.info("👋 Selamat Datang! Silakan unggah file database LHKPN di sidebar untuk memulai.")
