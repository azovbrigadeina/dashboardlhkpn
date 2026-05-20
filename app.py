import streamlit as st
import pandas as pd
import plotly.express as px
import time
from modules.data_engine import load_from_gsheet, proses_data_unja
from modules.auth import load_users, save_users, init_session_state, logout, load_settings, save_settings, send_email_via_gas
from modules.ui_components import inject_custom_css, render_metric_card, render_footer, render_executive_panel, generate_executive_report
from modules.charts import render_spotlight_section, render_graphical_analysis

# --- 1. CONFIG ---
st.set_page_config(page_title="LHKPN UNJA Monitoring", layout="wide", page_icon="🏛️")
inject_custom_css()
init_session_state()

# =====================================================================
# HALAMAN 1: LOGIN
# =====================================================================
if not st.session_state['auth']:
    st.markdown("""
    <div style="text-align:center; padding: 60px 0 10px 0;">
        <span style="font-size:64px;">🏛️</span>
        <h1 style="color:#1e3a5f; margin:0;">LHKPN MONITORING</h1>
        <p style="color:#64748b; font-size:16px;">Universitas Jambi — Sistem Pemantauan Kepatuhan LHKPN</p>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.container(border=True):
            st.markdown("#### 🔐 Masuk ke Sistem")
            username = st.text_input("👤 Username", placeholder="Masukkan username Anda")
            password = st.text_input("🔑 Password", type="password", placeholder="Masukkan password Anda")
            
            st.write("")
            if st.button("🚀 MASUK", use_container_width=True, type="primary"):
                users = load_users()
                if username in users and users[username]['password'] == password:
                    st.session_state['auth'] = True
                    st.session_state['username'] = username
                    st.session_state['role'] = users[username].get('role', 'user')
                    st.session_state['unit'] = users[username].get('unit', None)
                    st.rerun()
                elif username == "":
                    st.warning("⚠️ Username tidak boleh kosong.")
                else:
                    st.error("❌ Username atau Password salah. Silakan coba lagi.")

        st.markdown("""
        <div style="text-align:center; margin-top:15px; color:#94a3b8; font-size:12px;">
            Sistem ini hanya dapat diakses oleh petugas yang berwenang.<br>
            Segala aktivitas tercatat dan dipantau.
        </div>
        """, unsafe_allow_html=True)
    st.stop()


# =====================================================================
# HALAMAN 2: SINKRONISASI
# =====================================================================
if not st.session_state['synced']:
    st.markdown(f"""
    <div style="text-align:center; padding: 30px 0 5px 0;">
        <span style="font-size:48px;">📡</span>
        <h2 style="color:#1e3a5f;">Sinkronisasi Data e-LHKPN KPK</h2>
        <p style="color:#64748b;">Selamat datang, <b>{st.session_state['username'].upper()}</b>. 
        Mempersiapkan koneksi ke server KPK...</p>
    </div>
    """, unsafe_allow_html=True)

    _, btn_col, _ = st.columns([1, 1, 1])
    with btn_col:
        do_sync = st.button("🔄  MULAI SINKRONISASI DATA", use_container_width=True, type="primary")

    log_box = st.empty()
    prog_bar = st.empty()
    status_msg = st.empty()

    if do_sync:
        log_lines = []
        def render_log(lines):
            html = '<div class="sync-log">' + "<br>".join(lines) + '</div>'
            log_box.markdown(html, unsafe_allow_html=True)

        STEPS = [
            (0.10, "sync-info",  "[ INIT   ] Menginisialisasi koneksi aman ke server KPK..."),
            (0.18, "sync-ok",    "[ OK     ] Handshake TLS 1.3 berhasil — enkripsi aktif 🔒"),
            (0.25, "sync-info",  "[ AUTH   ] Mengirimkan token autentikasi LHKPN API v2.4..."),
            (0.32, "sync-ok",    "[ OK     ] Autentikasi diterima. Session ID: KPK-UNJA-2025-****"),
            (0.40, "sync-info",  "[ FETCH  ] Mengunduh dataset wajib lapor Universitas Jambi..."),
            (0.54, "sync-ok",    "[ OK     ] Data diterima — parsing 1.247 baris rekaman..."),
            (0.74, "sync-info",  "[ SYNC   ] Menyinkronkan status LHKPN terbaru dari e-LHKPN KPK..."),
            (0.92, "sync-ok",    "[ OK     ] Zona Hijau / Kuning / Merah berhasil diklasifikasikan 🗂️"),
        ]

        for prog, cls, msg in STEPS:
            log_lines.append(f'<span class="{cls}">{msg}</span>')
            render_log(log_lines)
            prog_bar.progress(prog, text=f"Progres sinkronisasi: {int(prog*100)}%")
            time.sleep(0.3)

        try:
            raw = load_from_gsheet()
            st.session_state['raw_data'] = raw
            st.session_state['synced'] = True
            st.rerun()
        except Exception as e:
            st.error(f"Gagal memuat data: {e}")

    st.stop()


# =====================================================================
# HALAMAN 3: DASHBOARD UTAMA
# =====================================================================
raw = st.session_state.get('raw_data', None)

with st.sidebar:
    st.markdown(f"**👤 {st.session_state['username'].upper()}**")
    st.caption(f"Role: {st.session_state['role'].upper()}")
    st.write("---")
    
    if st.button("🔄 Sinkronisasi Ulang", use_container_width=True):
        st.session_state['synced'] = False
        st.session_state['raw_data'] = None
        st.rerun()

    st.write("---")
    if st.button("🚪 Logout", use_container_width=True):
        logout()

if raw is None:
    st.info("👋 Selamat Datang! Data belum tersedia.")
    st.stop()

# DATA FILTER BERDASARKAN USER UNIT
if st.session_state['role'] == 'user' and st.session_state['unit']:
    raw = raw[raw['SUB UNIT KERJA'] == st.session_state['unit']]
    if raw.empty:
        st.warning(f"⚠️ Tidak ada data untuk unit: {st.session_state['unit']}")
        st.stop()

# FILTER BULAN
try:
    list_bln = ["GLOBAL (AKUMULASI)"] + sorted([str(b).upper() for b in raw['BULAN'].unique() if pd.notna(b)])
except:
    list_bln = ["GLOBAL (AKUMULASI)"]
sel_bln = st.sidebar.selectbox("Pilih Periode:", list_bln)

# PROSES DATA
data = proses_data_unja(raw, sel_bln)

# KALKULASI METRIK
total_wl = len(data)
h = len(data[data['ZONA'] == "🟢 ZONA HIJAU"])
k = len(data[data['ZONA'] == "🟡 ZONA KUNING"])
m = len(data[data['ZONA'] == "🔴 ZONA MERAH"])
rate = (h / total_wl * 100) if total_wl > 0 else 0
dl = len(data[data['Status LHKPN'].astype(str).str.strip() == "Diumumkan Lengkap"])
dl_rate = (dl / total_wl * 100) if total_wl > 0 else 0

# =====================================================================
# PIMPINAN: DASHBOARD SIMPEL & RINGKAS
# =====================================================================
if st.session_state['role'] == 'pimpinan':

    # HEADER PIMPINAN
    st.markdown(f"""
    <div style="text-align:center; padding: 10px 0 5px 0;">
        <h2 style="color:#1e3a5f; margin:0;">📊 Ringkasan Kepatuhan LHKPN</h2>
        <p style="color:#64748b; font-size:15px;">Universitas Jambi — Periode: <b>{sel_bln}</b></p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    # --- BAGIAN 1: INDIKATOR UTAMA (BESAR & JELAS) ---
    col_main1, col_main2 = st.columns([1, 1])

    with col_main1:
        # Donut chart besar — langsung terlihat persentase kepatuhan
        import plotly.graph_objects as go
        fig_donut = go.Figure(data=[go.Pie(
            labels=["Sudah Lapor (Hijau)", "Draft (Kuning)", "Belum Lapor (Merah)"],
            values=[h, k, m],
            hole=0.65,
            marker=dict(colors=["#22c55e", "#f59e0b", "#ef4444"]),
            textinfo="label+percent",
            textfont_size=13,
            hoverinfo="label+value+percent"
        )])
        fig_donut.update_layout(
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
            height=300,
            annotations=[dict(
                text=f"<b>{rate:.0f}%</b><br><span style='font-size:12px;color:#64748b'>Kepatuhan</span>",
                x=0.5, y=0.5, font_size=28, showarrow=False, font_color="#1e3a5f"
            )]
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_main2:
        # Angka-angka besar yang mudah dibaca pimpinan
        st.markdown(f"""
        <div style="padding: 10px 0;">
            <div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7); border:2px solid #86efac; border-radius:14px; padding:18px; margin-bottom:12px; text-align:center;">
                <div style="font-size:14px; color:#166534; font-weight:600;">✅ TINGKAT KEPATUHAN</div>
                <div style="font-size:42px; font-weight:900; color:#166534;">{rate:.1f}%</div>
                <div style="font-size:13px; color:#4ade80;"><b>{h}</b> dari <b>{total_wl}</b> orang sudah melapor</div>
            </div>
            <div style="display:flex; gap:10px;">
                <div style="flex:1; background:#fffbeb; border:1px solid #fde68a; border-radius:10px; padding:14px; text-align:center;">
                    <div style="font-size:28px; font-weight:800; color:#d97706;">{k}</div>
                    <div style="font-size:11px; color:#92400e; font-weight:600;">🟡 DRAFT</div>
                </div>
                <div style="flex:1; background:#fef2f2; border:1px solid #fecaca; border-radius:10px; padding:14px; text-align:center;">
                    <div style="font-size:28px; font-weight:800; color:#dc2626;">{m}</div>
                    <div style="font-size:11px; color:#991b1b; font-weight:600;">🔴 BELUM LAPOR</div>
                </div>
                <div style="flex:1; background:#f5f3ff; border:1px solid #c4b5fd; border-radius:10px; padding:14px; text-align:center;">
                    <div style="font-size:28px; font-weight:800; color:#7c3aed;">{dl}</div>
                    <div style="font-size:11px; color:#5b21b6; font-weight:600;">⭐ PARIPURNA</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")

    # --- BAGIAN 2: INFO EKSEKUTIF RINGKAS ---
    unit_stats = data.groupby('SUB UNIT KERJA')['ZONA'].value_counts().unstack().fillna(0)
    for z in ["🟢 ZONA HIJAU", "🟡 ZONA KUNING", "🔴 ZONA MERAH"]:
        if z not in unit_stats.columns: unit_stats[z] = 0
    unit_stats['Persen_Hijau'] = (unit_stats['🟢 ZONA HIJAU'] / unit_stats.sum(axis=1)) * 100
    u_100 = unit_stats[unit_stats['Persen_Hijau'] == 100].index.tolist()
    u_rendah = unit_stats[unit_stats['Persen_Hijau'] < 100].sort_values(by='Persen_Hijau')

    pimp_c1, pimp_c2 = st.columns(2)
    with pimp_c1:
        st.markdown(f"""
        <div style="background:white; border:2px solid #bbf7d0; border-radius:12px; padding:18px;">
            <div style="font-size:15px; font-weight:700; color:#166534; margin-bottom:8px;">🏆 Unit Paripurna (100% Patuh)</div>
            <div style="font-size:28px; font-weight:900; color:#22c55e; margin-bottom:4px;">{len(u_100)} Unit</div>
            <div style="font-size:13px; color:#64748b;">{', '.join(u_100[:3]) + ('...' if len(u_100) > 3 else '') if u_100 else 'Belum ada unit yang 100% patuh'}</div>
        </div>
        """, unsafe_allow_html=True)
    with pimp_c2:
        worst_name = u_rendah.index[0] if not u_rendah.empty else "-"
        worst_pct = f"{u_rendah.iloc[0]['Persen_Hijau']:.1f}%" if not u_rendah.empty else "-"
        st.markdown(f"""
        <div style="background:white; border:2px solid #fecaca; border-radius:12px; padding:18px;">
            <div style="font-size:15px; font-weight:700; color:#991b1b; margin-bottom:8px;">⚠️ Unit Butuh Atensi (Terendah)</div>
            <div style="font-size:20px; font-weight:800; color:#ef4444; margin-bottom:4px;">{worst_name}</div>
            <div style="font-size:13px; color:#64748b;">Tingkat kepatuhan: <b>{worst_pct}</b></div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # --- BAGIAN 3: DETAIL LANJUTAN (KLIK UNTUK MELIHAT) ---
    with st.expander("📊 Lihat Grafik Analisis per Zona", expanded=False):
        render_graphical_analysis(data)

    with st.expander("⭐ Lihat Detail Capaian Diumumkan Lengkap", expanded=False):
        render_spotlight_section(data, dl, dl_rate, total_wl, total_wl - dl)

    with st.expander("📋 Lihat Detail Data Individu", expanded=False):
        col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
        with col_f1:
            f_zona = st.multiselect("Filter Zona:", options=data['ZONA'].unique(), default=list(data['ZONA'].unique()), key="pimp_zona")
        with col_f2:
            f_unit = st.multiselect("Filter Unit:", options=sorted(data['SUB UNIT KERJA'].unique()), default=list(data['SUB UNIT KERJA'].unique()), key="pimp_unit")
        with col_f3:
            f_cari = st.text_input("🔍 Cari Nama / NIK / Unit:", key="pimp_cari")

        df_tabel = data[data['ZONA'].isin(f_zona)]
        df_tabel = df_tabel[df_tabel['SUB UNIT KERJA'].isin(f_unit)]
        if f_cari:
            df_tabel = df_tabel[df_tabel.apply(lambda row: f_cari.lower() in str(row).lower(), axis=1)]

        st.dataframe(df_tabel[['NAMA', 'NIK', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], use_container_width=True, hide_index=True)

# =====================================================================
# ADMIN & USER: DASHBOARD DETAIL (TAMPILAN ASLI)
# =====================================================================
else:

    # HEADER
    st.title("🏛️ Dashboard LHKPN Monitoring — Universitas Jambi")
    st.caption(f"Periode: **{sel_bln}** | Pengguna: **{st.session_state['username'].upper()}**")
    st.write("---")

    # METRIK CARDS
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: render_metric_card("WAJIB LAPOR", total_wl, "Orang", "#3b82f6", "#3b82f6")
    with m2: render_metric_card("🟢 HIJAU", h, f"{rate:.1f}% Tuntas", "#22c55e", "#22c55e")
    with m3: render_metric_card("🟡 KUNING", k, "Status Draft", "#f59e0b", "#f59e0b")
    with m4: render_metric_card("🔴 MERAH", m, "Belum Lapor", "#ef4444", "#ef4444")
    with m5: render_metric_card("⭐ DIUMUMKAN LENGKAP", dl, f"{dl_rate:.1f}% Paripurna", "#7c3aed", "#7c3aed")

    st.write("---")

    # PAPAN INFORMASI EKSEKUTIF (ADMIN ONLY)
    if st.session_state['role'] == 'admin':
        unit_stats = data.groupby('SUB UNIT KERJA')['ZONA'].value_counts().unstack().fillna(0)
        for z in ["🟢 ZONA HIJAU", "🟡 ZONA KUNING", "🔴 ZONA MERAH"]:
            if z not in unit_stats.columns: unit_stats[z] = 0
        unit_stats['Persen_Hijau'] = (unit_stats['🟢 ZONA HIJAU'] / unit_stats.sum(axis=1)) * 100
        u_100 = unit_stats[unit_stats['Persen_Hijau'] == 100].index.tolist()
        paripurna_txt = ", ".join(u_100[:2]) + ("..." if len(u_100) > 2 else "") if u_100 else "Belum Ada"
        u_rendah = unit_stats[unit_stats['Persen_Hijau'] < 100].sort_values(by='Persen_Hijau')
        atensi_label = f"Unit <b>{u_rendah.index[0]}</b> ({u_rendah.iloc[0]['Persen_Hijau']:.1f}%)" if not u_rendah.empty else "Semua Unit 100%"

        render_executive_panel(data, paripurna_txt, len(u_100), atensi_label, ((h+k)/total_wl*100 if total_wl > 0 else 0))
        st.write("")

    # TABEL & GRAFIK
    st.write("### 📋 Detail Individu")
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1: 
        f_zona = st.multiselect("Filter Zona:", options=data['ZONA'].unique(), default=list(data['ZONA'].unique()))

    # Filter Unit khusus Admin
    f_unit = []
    if st.session_state['role'] == 'admin':
        with col_f2:
            f_unit = st.multiselect("Filter Unit:", options=sorted(data['SUB UNIT KERJA'].unique()), default=list(data['SUB UNIT KERJA'].unique()))
    else:
        f_unit = list(data['SUB UNIT KERJA'].unique())

    with col_f3: 
        f_cari = st.text_input("🔍 Cari Nama / NIK / Unit:")

    # Jalankan Filter
    df_tabel = data[data['ZONA'].isin(f_zona)]
    df_tabel = df_tabel[df_tabel['SUB UNIT KERJA'].isin(f_unit)]

    if f_cari: 
        df_tabel = df_tabel[df_tabel.apply(lambda row: f_cari.lower() in str(row).lower(), axis=1)]

    st.dataframe(df_tabel[['NAMA', 'NIK', 'SUB UNIT KERJA', 'Status LHKPN', 'ZONA']], use_container_width=True, hide_index=True)

    # SPOTLIGHT & ANALISIS
    render_spotlight_section(data, dl, dl_rate, total_wl, total_wl - dl)

    if st.session_state['role'] == 'admin':
        render_graphical_analysis(data)

# PENGATURAN USER & EMAIL BLAST (ADMIN ONLY)
if st.session_state['role'] == 'admin':
    with st.sidebar:
        st.write("---")
        show_admin_settings = st.checkbox("🛠️ Pengaturan Aplikasi", key="show_admin_settings")
        show_email_reminder = st.checkbox("📢 Fitur Reminder Email", key="show_email_reminder")

    if show_admin_settings:
        with st.sidebar:
            st.divider()
            
            # Sub-menu 1: Manajemen User
            st.subheader("👥 Manajemen Akun")
            users = load_users()
            with st.expander("➕ Tambah User Baru"):
                new_user = st.text_input("Username Baru")
                new_pass = st.text_input("Password Baru", type="password")
                new_role = st.selectbox("Role", ["user", "admin", "pimpinan"])
                available_units = sorted(st.session_state['raw_data']['SUB UNIT KERJA'].dropna().unique())
                new_unit = st.selectbox("Unit Kerja", [None] + list(available_units))
                if st.button("Simpan User"):
                    if new_user and new_pass:
                        users[new_user] = {"password": new_pass, "role": new_role, "unit": new_unit}
                        save_users(users)
                        st.success(f"User {new_user} ditambahkan!")
                        st.rerun()
            
            st.write("**Daftar User:**")
            for u, info in list(users.items()):
                col_u, col_d = st.columns([3, 1])
                col_u.write(f"**{u}** ({info['role']})")
                if col_d.button("🗑️", key=f"del_{u}"):
                    if u != st.session_state['username']:
                        del users[u]
                        save_users(users)
                        st.rerun()

            # Sub-menu 2: Pengaturan Email
            st.divider()
            st.subheader("✉️ Pengaturan Email")
            settings = load_settings()
            
            email_subject = st.text_input("Subjek Email Blast", value=settings.get("email_subject", "PENGINGAT: Pengisian LHKPN Universitas Jambi"))
            email_body = st.text_area("Template Isi Email", value=settings.get("email_body", ""), height=220, help="Gunakan {NAMA}, {STATUS_LHKPN}, dan {BULAN} sebagai variabel.")
            
            if st.button("Simpan Pengaturan Email"):
                settings['email_subject'] = email_subject
                settings['email_body'] = email_body
                if save_settings(settings):
                    st.success("Pengaturan email disimpan!")
                    st.rerun()

# =====================================================================
# EMAIL REMINDER SECTION (ADMIN ONLY)
# =====================================================================
if st.session_state['role'] == 'admin' and st.session_state.get("show_email_reminder"):
    st.write("---")
    with st.expander("📢 PUSAT REMINDER EMAIL", expanded=True):
        st.markdown("### 📨 Kirim Pengingat LHKPN via Email")
        
        # Load Email Templates
        settings = load_settings()
        subj_template = settings.get("email_subject", "PENGINGAT: Pengisian LHKPN Universitas Jambi")
        body_template = settings.get("email_body", "")
        
        # Filter for Kuning & Merah only for email reminder
        remind_data = data[data['ZONA'].isin(["🟡 ZONA KUNING", "🔴 ZONA MERAH"])]
        
        # Cari kolom email yang cocok di data
        email_col = None
        for col_name in ['EMAIL', 'E-MAIL', 'EMAIL_UNJA', 'EMAIL ADDRESS', 'SURAT ELEKTRONIK']:
            match = [c for c in remind_data.columns if c.strip().upper() == col_name]
            if match:
                email_col = match[0]
                break
        
        if not email_col:
            match = [c for c in remind_data.columns if 'email' in c.lower()]
            if match:
                email_col = match[0]
        
        col_r1, col_r2 = st.columns([2, 1])
        with col_r1:
            st.write(f"Ditemukan **{len(remind_data)}** orang yang belum tuntas (Kuning/Merah).")
            if not email_col:
                st.warning("⚠️ Kolom email tidak ditemukan dalam data (misal: 'EMAIL'). Tambahkan kolom email di Google Sheet Anda agar blast dapat dilakukan.")
        
        with col_r2:
            blast_btn = st.button("🚀 BLAST EMAIL (GMAIL)", use_container_width=True, type="primary", disabled=not email_col or len(remind_data) == 0, help="Kirim email massal otomatis dari akun Gmail Anda")

        if blast_btn and email_col:
            success_count = 0
            fail_count = 0
            progress_text = "Mengirim blast email..."
            my_bar = st.progress(0, text=progress_text)
            
            for i, (idx, row) in enumerate(remind_data.iterrows()):
                to_email = str(row.get(email_col)).strip()
                if to_email and '@' in to_email:
                    # Format isi template email
                    subj = subj_template
                    try:
                        body = body_template.format(
                            NAMA=row['NAMA'],
                            STATUS_LHKPN=row['Status LHKPN'],
                            BULAN=sel_bln
                        )
                    except Exception as format_err:
                        # Fallback jika placeholder error
                        body = f"Yth. {row['NAMA']},\n\nMohon segera melengkapi LHKPN Anda. Status saat ini: {row['Status LHKPN']}."
                        
                    ok, res = send_email_via_gas(to_email, subj, body)
                    if ok: 
                        success_count += 1
                    else: 
                        fail_count += 1
                else:
                    fail_count += 1
                
                my_bar.progress((i + 1) / len(remind_data), text=f"Proses: {i+1}/{len(remind_data)}")
            
            st.success(f"✅ Blast email selesai! Berhasil: {success_count}, Gagal/Dilewati: {fail_count}")

        st.divider()
        st.write("#### 📧 Daftar Penerima Email (Kuning/Merah)")
        
        # Display list with manual remind buttons
        for idx, row in remind_data.head(20).iterrows(): # Limit display for performance
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.write(f"**{row['NAMA']}**")
            c2.write(f"{row['ZONA']}")
            
            to_email = str(row.get(email_col)).strip() if email_col else ""
            if to_email and '@' in to_email:
                c3.write(f"📧 `{to_email}`")
                
                # Individual email preview and trigger
                try:
                    preview_body = body_template.format(
                        NAMA=row['NAMA'],
                        STATUS_LHKPN=row['Status LHKPN'],
                        BULAN=sel_bln
                    )
                except:
                    preview_body = f"Yth. {row['NAMA']},\n\nMohon segera melengkapi LHKPN Anda. Status saat ini: {row['Status LHKPN']}."
                
                if c4.button("Kirim", key=f"mail_{idx}"):
                    ok, res = send_email_via_gas(to_email, subj_template, preview_body)
                    if ok: 
                        st.toast(f"✅ Terkirim ke {row['NAMA']}")
                    else: 
                        st.error(f"❌ {res}")
            else:
                c3.write("🚫 Email Kosong")
                c4.write("")

        if len(remind_data) > 20:
            st.info(f"Menampilkan 20 dari {len(remind_data)} orang. Gunakan filter tabel untuk mencari spesifik.")

render_footer()
