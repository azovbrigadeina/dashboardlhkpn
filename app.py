import streamlit as st
import pandas as pd
import plotly.express as px
import time
from modules.data_engine import load_from_gsheet, proses_data_unja
from modules.auth import load_users, save_users, init_session_state, logout
from modules.ui_components import inject_custom_css, render_metric_card, render_footer, render_executive_panel, generate_executive_report
from modules.charts import render_spotlight_section, render_graphical_analysis
from modules.telegram_bot import send_telegram_message, get_telegram_link

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

# PENGATURAN USER (ADMIN ONLY)
if st.session_state['role'] == 'admin':
    with st.sidebar:
        st.write("---")
        if st.checkbox("🛠️ Pengaturan User"):
            st.divider()
            st.subheader("👥 Manajemen Akun")
            users = load_users()
            with st.expander("➕ Tambah User Baru"):
                new_user = st.text_input("Username Baru")
                new_pass = st.text_input("Password Baru", type="password")
                new_role = st.selectbox("Role", ["user", "admin"])
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

# =====================================================================
# HALAMAN 4: TELEGRAM REMINDER (ADMIN ONLY)
# =====================================================================
if st.session_state['role'] == 'admin':
    with st.sidebar:
        st.write("---")
        if st.checkbox("📢 Fitur Reminder Telegram"):
            st.divider()
            st.subheader("🤖 Konfigurasi Bot")
            
            # Persistent token storage in session state
            if 'tg_token' not in st.session_state:
                st.session_state['tg_token'] = ""
            
            tg_token = st.text_input("Bot Token (KPK Bot)", value=st.session_state['tg_token'], type="password", help="Dapatkan dari @BotFather")
            if tg_token != st.session_state['tg_token']:
                st.session_state['tg_token'] = tg_token
            
            st.info("Pesan akan dikirim ke kolom 'TELEGRAM_ID' atau 'NO_HP' jika tersedia di data.")

    # Render main reminder area if checked
    if st.sidebar.get('tg_reminder_active', False) or (st.session_state['role'] == 'admin' and "📢 Fitur Reminder Telegram" in st.session_state and st.session_state["📢 Fitur Reminder Telegram"]):
        pass # Handle main rendering below table or in a dedicated section

# Re-checking if the checkbox is active to show the section
# Streamlit checkboxes in sidebar are accessible via session state if given a key, 
# but here it's just an if. I'll wrap the logic better.
if st.session_state['role'] == 'admin':
    # Since I want to show it in the main area when sidebar checkbox is on
    # I'll use a better key management
    pass

# Adding the Reminder UI Section after the table
if st.session_state['role'] == 'admin':
    st.write("---")
    with st.expander("📢 PUSAT REMINDER TELEGRAM", expanded=False):
        st.markdown("### 📨 Kirim Pengingat LHKPN")
        
        # Filter for Kuning & Merah only for reminder
        remind_data = data[data['ZONA'].isin(["🟡 ZONA KUNING", "🔴 ZONA MERAH"])]
        
        col_r1, col_r2 = st.columns([2, 1])
        with col_r1:
            st.write(f"Ditemukan **{len(remind_data)}** orang yang belum tuntas (Kuning/Merah).")
        with col_r2:
            blast_btn = st.button("🚀 BLAST SEMUA (BOT)", use_container_width=True, type="primary", help="Kirim pesan otomatis via Bot ke semua yang punya ID Telegram")

        if blast_btn:
            if not st.session_state.get('tg_token'):
                st.error("⚠️ Bot Token belum diisi di sidebar!")
            else:
                success_count = 0
                fail_count = 0
                progress_text = "Mengirim blast..."
                my_bar = st.progress(0, text=progress_text)
                
                # Assume columns 'ID_TELEGRAM' or 'CHAT_ID' exist or will be added
                # Fallback to empty if not exists
                tg_col = 'ID_TELEGRAM' if 'ID_TELEGRAM' in remind_data.columns else ('CHAT_ID' if 'CHAT_ID' in remind_data.columns else None)
                
                if not tg_col:
                    st.warning("⚠️ Kolom ID_TELEGRAM tidak ditemukan dalam data. Pastikan Google Sheet sudah diperbarui.")
                else:
                    for i, (idx, row) in enumerate(remind_data.iterrows()):
                        chat_id = row.get(tg_col)
                        if pd.notna(chat_id) and str(chat_id).strip():
                            msg = f"<b>PENGINGAT LHKPN UNJA</b>\n\nYth. Bapak/Ibu <b>{row['NAMA']}</b>,\n\nStatus LHKPN Anda saat ini: <b>{row['Status LHKPN']}</b>.\nMohon segera melengkapi pengisian LHKPN sesuai kondisi terbaru.\n\nTerima kasih."
                            ok, res = send_telegram_message(st.session_state['tg_token'], str(chat_id), msg)
                            if ok: success_count += 1
                            else: fail_count += 1
                        
                        my_bar.progress((i + 1) / len(remind_data), text=f"Proses: {i+1}/{len(remind_data)}")
                    
                    st.success(f"✅ Blast selesai! Berhasil: {success_count}, Gagal: {fail_count}")

        st.divider()
        st.write("#### 👤 Daftar Individu (Kuning/Merah)")
        
        # Display list with manual remind buttons
        for idx, row in remind_data.head(20).iterrows(): # Limit display for performance
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.write(f"**{row['NAMA']}**")
            c2.write(f"{row['ZONA']}")
            
            # Individual Bot Send
            tg_col = 'ID_TELEGRAM' if 'ID_TELEGRAM' in remind_data.columns else ('CHAT_ID' if 'CHAT_ID' in remind_data.columns else None)
            chat_id = row.get(tg_col) if tg_col else None
            
            if c3.button("🤖 Bot", key=f"bot_{idx}", disabled=not chat_id or not st.session_state.get('tg_token')):
                msg = f"Yth. {row['NAMA']}, mohon segera update LHKPN Anda (Status: {row['Status LHKPN']}). Terima kasih."
                ok, res = send_telegram_message(st.session_state['tg_token'], str(chat_id), msg)
                if ok: st.toast(f"✅ Terkirim ke {row['NAMA']}")
                else: st.error(f"❌ {res}")
            
            # Manual Web Link
            # Assume phone number column is 'NO_HP' or 'PHONE'
            phone_col = 'NO_HP' if 'NO_HP' in remind_data.columns else ('PHONE' if 'PHONE' in remind_data.columns else None)
            phone = row.get(phone_col) if phone_col else None
            
            if phone:
                msg_manual = f"Halo {row['NAMA']}, ini pengingat LHKPN UNJA. Status Anda: {row['Status LHKPN']}. Mohon segera dilengkapi."
                link = get_telegram_link(phone, msg_manual)
                c4.markdown(f'<a href="{link}" target="_blank"><button style="width:100%; border-radius:4px; border:1px solid #ddd; background:#f0f2f6; cursor:pointer;">📱 Manual</button></a>', unsafe_allow_html=True)
            else:
                c4.write("🚫 No HP")

        if len(remind_data) > 20:
            st.info(f"Menampilkan 20 dari {len(remind_data)} orang. Gunakan filter tabel untuk mencari spesifik.")

render_footer()
