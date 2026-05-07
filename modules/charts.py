import streamlit as st
import plotly.express as px
import pandas as pd

COLOR_MAP = {
    "🟢 ZONA HIJAU": "#22C55E",
    "🟡 ZONA KUNING": "#F59E0B",
    "🔴 ZONA MERAH": "#EF4444",
    "⚪ LAINNYA": "#94A3B8"
}

def render_spotlight_section(data, dl, dl_rate, total_wl, dl_sisa):
    st.write("### ⭐ Spotlight: Diumumkan Lengkap")
    
    dl_bar_pct = dl_rate / 100
    bar_color = "#7c3aed" if dl_rate < 50 else ("#f59e0b" if dl_rate < 80 else "#22c55e")
    
    dl_unit = data[data['Status LHKPN'].astype(str).str.strip() == "Diumumkan Lengkap"]['SUB UNIT KERJA'].value_counts()
    top_dl_unit = dl_unit.index[0] if not dl_unit.empty else "—"
    top_dl_val  = int(dl_unit.iloc[0]) if not dl_unit.empty else 0

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#f5f3ff,#ede9fe);border:2px solid #7c3aed;border-radius:14px;padding:24px;margin-bottom:16px;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
            <span style="font-size:36px;">🏅</span>
            <div>
                <div style="font-size:22px;font-weight:800;color:#4c1d95;">STATUS DIUMUMKAN LENGKAP</div>
                <div style="color:#7c3aed;font-size:14px;">Target tertinggi kepatuhan LHKPN — laporan telah diumumkan secara lengkap kepada publik</div>
            </div>
        </div>
        <div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:18px;">
            <div style="background:white;padding:14px 22px;border-radius:10px;border:1px solid #c4b5fd;min-width:140px;text-align:center;">
                <div style="font-size:36px;font-weight:900;color:#7c3aed;">{dl}</div>
                <div style="font-size:12px;color:#6b7280;font-weight:600;">Orang Diumumkan Lengkap</div>
            </div>
            <div style="background:white;padding:14px 22px;border-radius:10px;border:1px solid #c4b5fd;min-width:140px;text-align:center;">
                <div style="font-size:36px;font-weight:900;color:{bar_color};">{dl_rate:.1f}%</div>
                <div style="font-size:12px;color:#6b7280;font-weight:600;">Capaian dari Total Wajib Lapor</div>
            </div>
            <div style="background:white;padding:14px 22px;border-radius:10px;border:1px solid #c4b5fd;min-width:140px;text-align:center;">
                <div style="font-size:36px;font-weight:900;color:#ef4444;">{dl_sisa}</div>
                <div style="font-size:12px;color:#6b7280;font-weight:600;">Orang Belum Diumumkan Lengkap</div>
            </div>
            <div style="background:white;padding:14px 22px;border-radius:10px;border:1px solid #c4b5fd;min-width:180px;text-align:center;">
                <div style="font-size:18px;font-weight:800;color:#7c3aed;">{top_dl_unit}</div>
                <div style="font-size:12px;color:#6b7280;font-weight:600;">Unit Terbanyak ({top_dl_val} orang)</div>
            </div>
        </div>
        <div style="background:#e9d5ff;border-radius:999px;height:18px;overflow:hidden;">
            <div style="background:{bar_color};width:{dl_rate:.1f}%;height:100%;border-radius:999px;transition:width 1s ease;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;">
                <span style="font-size:11px;font-weight:700;color:white;">{dl_rate:.1f}%</span>
            </div>
        </div>
        <div style="display:flex;justify-content:space-between;margin-top:4px;font-size:11px;color:#7c3aed;">
            <span>0%</span><span>Target: 100% ({total_wl} orang)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Charts for Spotlight (ADMIN ONLY)
    if st.session_state.get('role') == 'admin':
        sp1, sp2 = st.columns(2)
        with sp1:
            dl_unit_df = dl_unit.reset_index().head(10)
            dl_unit_df.columns = ['SUB UNIT KERJA', 'Diumumkan Lengkap']
            if not dl_unit_df.empty:
                st.plotly_chart(px.bar(dl_unit_df, x='Diumumkan Lengkap', y='SUB UNIT KERJA', orientation='h', title="Top 10 Unit — Diumumkan Lengkap", color_discrete_sequence=['#7c3aed']), use_container_width=True)

        with sp2:
            dl_per_unit = data.groupby('SUB UNIT KERJA').apply(lambda g: pd.Series({'Total': len(g), 'Diumumkan Lengkap': (g['Status LHKPN'].astype(str).str.strip() == 'Diumumkan Lengkap').sum()})).reset_index()
            dl_per_unit['% Capaian'] = (dl_per_unit['Diumumkan Lengkap'] / dl_per_unit['Total'] * 100).round(1)
            dl_per_unit = dl_per_unit.sort_values('% Capaian', ascending=False)
            st.write("**📊 Capaian Diumumkan Lengkap per Unit**")
            st.dataframe(dl_per_unit[['SUB UNIT KERJA','Total','Diumumkan Lengkap','% Capaian']], use_container_width=True, hide_index=True)

def render_graphical_analysis(data):
    st.write("### 📊 Analisis Grafis per Zona")
    v1, v2 = st.columns([1, 1.5])
    with v1:
        st.plotly_chart(px.pie(data, names='ZONA', color='ZONA', hole=0.5, title="Distribusi Zona Kepatuhan", color_discrete_map=COLOR_MAP), use_container_width=True)
    with v2:
        df_red = data[data['ZONA'] == "🔴 ZONA MERAH"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
        if not df_red.empty:
            st.plotly_chart(px.bar(df_red, x='count', y='SUB UNIT KERJA', orientation='h', title="🔴 Top 10 Unit — Zona Merah", color_discrete_sequence=['#EF4444']), use_container_width=True)
        else:
            st.success("🎉 Tidak ada unit di Zona Merah!")

    g1, g2 = st.columns(2)
    with g1:
        df_grn = data[data['ZONA'] == "🟢 ZONA HIJAU"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
        if not df_grn.empty:
            st.plotly_chart(px.bar(df_grn, x='count', y='SUB UNIT KERJA', orientation='h', title="🟢 Top 10 Unit — Zona Hijau", color_discrete_sequence=['#22C55E']), use_container_width=True)
    with g2:
        df_yel = data[data['ZONA'] == "🟡 ZONA KUNING"]['SUB UNIT KERJA'].value_counts().reset_index().head(10)
        if not df_yel.empty:
            st.plotly_chart(px.bar(df_yel, x='count', y='SUB UNIT KERJA', orientation='h', title="🟡 Top 10 Unit — Zona Kuning", color_discrete_sequence=['#F59E0B']), use_container_width=True)

    st.write("#### 📊 Perbandingan Zona per Unit Kerja (Stacked)")
    unit_zona_df = data.groupby(['SUB UNIT KERJA','ZONA']).size().reset_index(name='Jumlah')
    fig_stacked = px.bar(unit_zona_df, x='SUB UNIT KERJA', y='Jumlah', color='ZONA', color_discrete_map=COLOR_MAP, title="Komposisi Zona Kepatuhan per Unit Kerja", barmode='stack')
    fig_stacked.update_layout(xaxis_tickangle=-40, height=420)
    st.plotly_chart(fig_stacked, use_container_width=True)
