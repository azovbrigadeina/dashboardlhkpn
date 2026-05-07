import streamlit as st

def inject_custom_css():
    st.markdown("""
    <style>
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        text-align: center;
        border-top: 5px solid #ececec;
    }
    .metric-label { font-size: 14px; color: #64748b; font-weight: bold; }
    .metric-value { font-size: 32px; font-weight: bold; color: #1e293b; margin: 5px 0; }
    .metric-delta { font-size: 13px; font-weight: 600; }

    .sync-log {
        background: #0f172a;
        color: #22d3ee;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        border-radius: 10px;
        padding: 20px;
        line-height: 2;
        min-height: 200px;
    }
    .sync-ok  { color: #4ade80; }
    .sync-err { color: #f87171; }
    .sync-warn{ color: #fbbf24; }
    .sync-info{ color: #22d3ee; }
    </style>
    """, unsafe_allow_html=True)

def render_metric_card(label, value, delta_text, delta_color, border_color):
    st.markdown(f"""
    <div class="metric-card" style="border-top-color:{border_color};">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-delta" style="color:{delta_color};">{delta_text}</div>
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    st.write("---")
    st.markdown("""
    <div style="text-align:center; color:#94a3b8; font-size:12px; padding: 10px;">
        🏛️ LHKPN Monitoring System — Universitas Jambi &nbsp;|&nbsp; 
        Data bersumber from e-LHKPN KPK &nbsp;|&nbsp; 
        Sistem ini bersifat internal dan rahasia
    </div>
    """, unsafe_allow_html=True)

def render_executive_panel(paripurna_txt, count_u100, atensi_label, potential_pct):
    st.markdown(f"""
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:20px;">
        <div style="display:flex;gap:15px;flex-wrap:wrap;">
            <div style="flex:1;min-width:250px;background:white;padding:15px;border-radius:8px;border:1px solid #bbf7d0;">
                <b style="color:#166534;">🏆 APRESIASI</b><br>
                <small>Unit Paripurna: {paripurna_txt} ({count_u100} Unit)</small>
            </div>
            <div style="flex:1;min-width:250px;background:white;padding:15px;border-radius:8px;border:1px solid #fecaca;">
                <b style="color:#9f1239;">⚠️ ATENSI</b><br>
                <small>Prioritas: {atensi_label}</small>
            </div>
            <div style="flex:1;min-width:250px;background:white;padding:15px;border-radius:8px;border:1px solid #bfdbfe;">
                <b style="color:#1e40af;">⚡ AKSELERASI</b><br>
                <small>Potensi Maksimal: {potential_pct:.1f}% jika Zona Kuning tuntas.</small>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
