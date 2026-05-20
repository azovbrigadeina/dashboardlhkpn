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
    
    # Hitung rasio DL per unit (adil: berbasis %, bukan jumlah absolut)
    dl_per_unit = data.groupby('SUB UNIT KERJA').apply(
        lambda g: pd.Series({
            'Total': len(g),
            'DL': (g['Status LHKPN'].astype(str).str.strip() == 'Diumumkan Lengkap').sum()
        })
    ).reset_index()
    dl_per_unit['Pct'] = (dl_per_unit['DL'] / dl_per_unit['Total'] * 100).round(1)
    dl_per_unit_sorted = dl_per_unit.sort_values(['Pct', 'DL'], ascending=[False, False])

    top_dl_unit = dl_per_unit_sorted.iloc[0]['SUB UNIT KERJA'] if not dl_per_unit_sorted.empty else "—"
    top_dl_pct  = dl_per_unit_sorted.iloc[0]['Pct'] if not dl_per_unit_sorted.empty else 0
    top_dl_val  = int(dl_per_unit_sorted.iloc[0]['DL']) if not dl_per_unit_sorted.empty else 0
    top_dl_tot  = int(dl_per_unit_sorted.iloc[0]['Total']) if not dl_per_unit_sorted.empty else 0

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
                <div style="font-size:16px;font-weight:800;color:#7c3aed;">{top_dl_unit}</div>
                <div style="font-size:13px;font-weight:900;color:#22c55e;">{top_dl_pct:.1f}% ({top_dl_val}/{top_dl_tot})</div>
                <div style="font-size:11px;color:#6b7280;font-weight:600;">Unit Terbaik (Rasio DL Tertinggi)</div>
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
            # Chart berdasarkan % rasio (adil untuk semua unit)
            dl_chart = dl_per_unit_sorted.head(10).copy()
            dl_chart.columns = ['SUB UNIT KERJA', 'Total', 'Diumumkan Lengkap', '% Capaian']
            dl_chart['Label'] = dl_chart.apply(
                lambda r: f"{int(r['Diumumkan Lengkap'])}/{int(r['Total'])} ({r['% Capaian']:.1f}%)", axis=1
            )
            if not dl_chart.empty:
                fig_top10 = px.bar(
                    dl_chart.sort_values('% Capaian'),
                    x='% Capaian', y='SUB UNIT KERJA', orientation='h',
                    title="🏅 Top 10 Unit — Rasio Diumumkan Lengkap",
                    color='% Capaian',
                    color_continuous_scale=['#a855f7', '#22c55e'],
                    range_color=[0, 100],
                    text='Label',
                    custom_data=['Diumumkan Lengkap', 'Total', 'Label']
                )
                fig_top10.update_traces(
                    texttemplate='%{text}',
                    textposition='outside',
                    hovertemplate=(
                        '<b>%{y}</b><br>'
                        'Diumumkan Lengkap: %{customdata[0]} orang<br>'
                        'Total Wajib Lapor: %{customdata[1]} orang<br>'
                        'Rasio: <b>%{customdata[2]}</b><extra></extra>'
                    )
                )
                fig_top10.update_layout(
                    xaxis=dict(range=[0, 125], title='% Capaian'),
                    yaxis=dict(title=''),
                    coloraxis_showscale=False,
                    margin=dict(r=20),
                    height=360,
                )
                # Garis referensi 100%
                fig_top10.add_vline(
                    x=100, line_dash='dash', line_color='#ef4444', line_width=1.5,
                    annotation_text='100%', annotation_position='top',
                    annotation_font_color='#ef4444'
                )
                st.plotly_chart(fig_top10, use_container_width=True)

        with sp2:
            # Tabel lengkap — diurutkan berdasarkan % rasio
            dl_tabel = dl_per_unit.rename(columns={'DL': 'Diumumkan Lengkap', 'Pct': '% Capaian'}).sort_values('% Capaian', ascending=False)
            st.write("**📊 Capaian Diumumkan Lengkap per Unit (Rasio)**")
            st.dataframe(
                dl_tabel[['SUB UNIT KERJA', 'Total', 'Diumumkan Lengkap', '% Capaian']],
                use_container_width=True, hide_index=True
            )

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
