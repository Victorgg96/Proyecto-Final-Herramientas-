"""Dashboard SSN-UNAM v2 - profesional, dinamico, multi-capa.

Levantar con:
    streamlit run src/dashboard/app_streamlit.py
"""
import sys
from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import HeatMap, MarkerCluster, MiniMap, Fullscreen, MeasureControl
from streamlit_folium import st_folium

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import GOLD_PATH, SILVER_PATH

# ============================================================================
# CONFIG + ESTILO
# ============================================================================
st.set_page_config(
    page_title="SSN-UNAM | Analisis Sismico Mexico",
    layout="wide",
    page_icon="🌋",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    .main {background-color: #0e1117;}
    .block-container {padding-top: 1.2rem; padding-bottom: 0rem; max-width: 1440px;}
    h1, h2, h3, p, span, div {font-family: 'Inter', 'Segoe UI', sans-serif;}
    h1 {color: #fafafa; font-weight: 700; letter-spacing: -0.5px;}
    h2, h3 {color: #e8eaed;}
    .stMetric {
        background: linear-gradient(135deg, #1a1f2e 0%, #232b3b 100%);
        border-radius: 14px; padding: 20px;
        border-left: 4px solid #ff6b35;
        box-shadow: 0 4px 16px rgba(0,0,0,0.35);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stMetric:hover {transform: translateY(-2px); box-shadow: 0 8px 24px rgba(255,107,53,0.15);}
    [data-testid="stMetricValue"] {font-size: 28px; font-weight: 800; color: #ff6b35;}
    [data-testid="stMetricLabel"] {color: #9ca3b0; font-weight: 500; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;}
    [data-testid="stMetricDelta"] {color: #6cc04a;}
    .kpi-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #232b3b 100%);
        border-radius: 14px; padding: 22px 20px; text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border-bottom: 3px solid #ff6b35;
    }
    .kpi-card:hover {transform: translateY(-3px); box-shadow: 0 8px 28px rgba(255,107,53,0.18);}
    .kpi-icon {font-size: 26px; margin-bottom: 6px;}
    .kpi-value {font-size: 30px; font-weight: 800; color: #ff6b35; margin: 4px 0;}
    .kpi-label {font-size: 12px; color: #8b95a5; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600;}
    .stTabs [data-baseweb="tab-list"] {gap: 4px; background: #151a24; padding: 6px; border-radius: 12px;}
    .stTabs [data-baseweb="tab"] {
        height: 44px; padding: 0 24px; background: transparent; color: #8b95a5;
        border-radius: 10px; font-weight: 600; font-size: 13px;
        transition: all 0.25s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {color: #c0c8d4; background: rgba(255,255,255,0.04);}
    .stTabs [aria-selected="true"] {background: linear-gradient(135deg, #ff6b35, #e85d2a) !important; color: white !important;}
    section[data-testid="stSidebar"] {background: linear-gradient(180deg, #13171e 0%, #161b22 100%);}
    section[data-testid="stSidebar"] h2 {color: #ff6b35; font-size: 17px; font-weight: 700;}
    .badge {
        display: inline-block; padding: 5px 12px; border-radius: 8px;
        font-size: 11px; font-weight: 700; margin-right: 6px; letter-spacing: 0.3px;
    }
    .badge-red {background: rgba(217,83,79,0.2); color: #ff6b6b; border: 1px solid rgba(217,83,79,0.3);}
    .badge-orange {background: rgba(240,173,78,0.2); color: #f0ad4e; border: 1px solid rgba(240,173,78,0.3);}
    .badge-yellow {background: rgba(247,199,72,0.15); color: #f7c548; border: 1px solid rgba(247,199,72,0.3);}
    .badge-green {background: rgba(92,184,92,0.2); color: #6cc04a; border: 1px solid rgba(92,184,92,0.3);}
    .footer {color: #4a5568; font-size: 12px; text-align: center; padding: 30px 0 10px 0; border-top: 1px solid #1e2530;}
    div[data-testid="stExpander"] {background: #171c26; border-radius: 12px; border: 1px solid #262f3d;}
    .pipeline-step {
        background: #1a1f2e; border-radius: 10px; padding: 16px; text-align: center;
        border: 1px solid #262f3d;
    }
    .pipeline-step h4 {color: #ff6b35; margin: 0 0 4px 0; font-size: 15px;}
    .pipeline-step p {color: #8b95a5; margin: 0; font-size: 13px;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

PLOTLY_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.02)",
    font=dict(family="Segoe UI", size=12, color="#dadce0"),
    title=dict(font=dict(size=16, color="#ffffff"), x=0.02, xanchor="left"),
    colorway=["#ff6b35", "#f7c548", "#5bc0de", "#5cb85c", "#9b59b6", "#e74c3c", "#3498db"],
    margin=dict(l=20, r=20, t=50, b=20),
)


def style(fig, title=None):
    fig.update_layout(**PLOTLY_THEME)
    if title:
        fig.update_layout(title=title)
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.1)")
    return fig


# ============================================================================
# CARGA DE DATOS (cacheada)
# ============================================================================
@st.cache_data(show_spinner="Cargando capa Gold...")
def cargar_gold():
    def lee(p):
        df = pd.read_parquet(p, engine="pyarrow")
        for c in df.columns:
            if df[c].dtype.name == "category":
                df[c] = df[c].astype(df[c].cat.categories.dtype)
        return df

    return {
        "regional": lee(GOLD_PATH / "gold_sismicidad_regional"),
        "temporal": lee(GOLD_PATH / "gold_patrones_temporales"),
        "significativos": lee(GOLD_PATH / "gold_sismos_significativos"),
        "anual": lee(GOLD_PATH / "gold_evolucion_historica_anual"),
        "mensual": lee(GOLD_PATH / "gold_evolucion_historica_mensual"),
    }


@st.cache_data(show_spinner="Cargando metricas de Silver...")
def cargar_silver_metricas():
    df = pd.read_parquet(SILVER_PATH, engine="pyarrow", columns=["magnitud", "estado", "anio"])
    if df["anio"].dtype.name == "category":
        df["anio"] = df["anio"].astype("int32")
    return {
        "total": len(df),
        "con_magnitud": int(df["magnitud"].notna().sum()),
        "pct_magnitud": float(df["magnitud"].notna().mean() * 100),
        "estados_ok": int((df["estado"] != "DESCONOCIDO").sum()),
        "pct_estados": float((df["estado"] != "DESCONOCIDO").mean() * 100),
        "anio_min": int(df["anio"].min()),
        "anio_max": int(df["anio"].max()),
        "magnitudes": df["magnitud"].dropna().values,
    }


@st.cache_data(show_spinner="Cargando datos temporales de Silver...")
def cargar_silver_temporal():
    df = pd.read_parquet(SILVER_PATH, engine="pyarrow",
                         columns=["anio", "mes", "hora_del_dia", "estacion", "magnitud", "dia_semana"])
    for c in ["anio", "mes", "hora_del_dia"]:
        if df[c].dtype.name == "category":
            df[c] = df[c].astype("int32")
    return df


try:
    G = cargar_gold()
    S = cargar_silver_metricas()
    SILVER_TEMP = cargar_silver_temporal()
except Exception as e:
    st.error(f"❌ No se pudieron cargar los datos. Corre primero `python run_all.py`.\n\nDetalle: {e}")
    st.stop()

# ============================================================================
# HEADER
# ============================================================================
hcol1, hcol2 = st.columns([3, 1])
with hcol1:
    st.markdown("# 🌋 Análisis de Actividad Sísmica en México")
    st.markdown(
        '<span class="badge badge-orange">SSN-UNAM</span>'
        f'<span class="badge badge-red">{S["total"]:,} eventos</span>'
        f'<span class="badge badge-yellow">{S["anio_min"]}–{S["anio_max"]}</span>'
        '<span class="badge badge-green">Pipeline Bronze → Silver → Gold</span>',
        unsafe_allow_html=True,
    )
with hcol2:
    st.markdown(f'<div style="text-align:right; color:#6c757d; padding-top:18px;">Universidad del Caribe<br/>'
                'Herramientas para GVD</div>', unsafe_allow_html=True)
st.markdown("---")

# ============================================================================
# SIDEBAR — FILTROS GLOBALES
# ============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Filtros globales")
    anio_range = st.slider(
        "Rango de años",
        S["anio_min"], S["anio_max"],
        (max(S["anio_min"], 2000), S["anio_max"]),
        help="Aplica a todas las pestañas",
    )
    mag_min, mag_max = st.slider(
        "Rango de magnitud (mapa/significativos)",
        3.0, 8.5, (5.0, 8.5), 0.1,
    )
    regiones = sorted(G["significativos"]["region_sismica"].dropna().unique())
    regiones_sel = st.multiselect("Regiones sísmicas", regiones, default=regiones)

    st.markdown("---")
    st.markdown("## 📊 Calidad del pipeline")
    st.metric("Cobertura magnitud", f"{S['pct_magnitud']:.1f}%")
    st.metric("Extracción de estado", f"{S['pct_estados']:.1f}%")
    st.caption(f"Silver: **{S['total']:,}** registros limpios")

    st.markdown("---")
    with st.expander("ℹ️ Acerca de"):
        st.write(
            "Dashboard del proyecto final de la asignatura *Herramientas para la gestión "
            "de grandes volúmenes de datos*. Implementa arquitectura Medallion con "
            "pandas + pyarrow + DuckDB. Datos del Servicio Sismológico Nacional, UNAM."
        )

# Subsets filtrados
sig = G["significativos"].copy()
sig = sig[(sig["anio"].astype(int) >= anio_range[0]) & (sig["anio"].astype(int) <= anio_range[1])]
sig = sig[(sig["magnitud"] >= mag_min) & (sig["magnitud"] <= mag_max)]
sig = sig[sig["region_sismica"].isin(regiones_sel)]

reg = G["regional"].copy()
reg["anio"] = reg["anio"].astype(int)
reg = reg[(reg["anio"] >= anio_range[0]) & (reg["anio"] <= anio_range[1])]
reg = reg[reg["region_sismica"].isin(regiones_sel)]

anual = G["anual"].copy()
anual["anio"] = anual["anio"].astype(int)
anual = anual[(anual["anio"] >= anio_range[0]) & (anual["anio"] <= anio_range[1])]

# ============================================================================
# KPIs DESTACADOS
# ============================================================================
total_filtrado = int(reg["total_sismos"].sum())
mag5_filtrado = len(sig)
mag7_filtrado = int((sig["magnitud"] >= 7).sum())
mag_max_filtrado = float(sig["magnitud"].max()) if len(sig) else 0.0
estados_activos = sig["estado"].nunique()

def kpi_card(icon, value, label, color="#ff6b35"):
    return f'''
    <div class="kpi-card" style="border-bottom-color: {color};">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value" style="color: {color};">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>'''

k1, k2, k3, k4, k5 = st.columns(5)
k1.markdown(kpi_card("📊", f"{total_filtrado:,}", "Sismos totales"), unsafe_allow_html=True)
k2.markdown(kpi_card("⚡", f"{mag5_filtrado:,}", "Eventos ≥ 5.0", "#f7c548"), unsafe_allow_html=True)
k3.markdown(kpi_card("🔴", f"{mag7_filtrado}", "Eventos ≥ 7.0", "#d9534f"), unsafe_allow_html=True)
k4.markdown(kpi_card("🏔️", f"M{mag_max_filtrado:.1f}" if mag_max_filtrado else "—", "Magnitud máx", "#e74c3c"), unsafe_allow_html=True)
k5.markdown(kpi_card("🗺️", f"{estados_activos}", "Estados afectados", "#5bc0de"), unsafe_allow_html=True)

st.markdown("")

# ============================================================================
# TABS
# ============================================================================
tab_map, tab_temp, tab_reg, tab_sig, tab_pb, tab_cal = st.tabs([
    "🗺️ Mapa interactivo",
    "⏰ Patrones temporales",
    "📍 Análisis regional",
    "⚠️ Sismos significativos",
    "🎯 Preguntas de negocio",
    "📋 Calidad de datos",
])

# ----------------------------------------------------------------------------
# TAB 1 — MAPA
# ----------------------------------------------------------------------------
with tab_map:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        capa = st.radio("Capa", ["Marcadores", "Mapa de calor", "Clusters"], horizontal=True)
    with c2:
        tile = st.selectbox("Tile", ["OpenStreetMap", "CartoDB dark_matter", "CartoDB positron", "Stamen Terrain"])
    with c3:
        st.write(f"**{len(sig):,}** eventos en pantalla")

    tile_map = {
        "OpenStreetMap": "openstreetmap",
        "CartoDB dark_matter": "cartodbdark_matter",
        "CartoDB positron": "cartodbpositron",
        "Stamen Terrain": "Stamen Terrain",
    }[tile]

    m = folium.Map(location=[23.5, -102.0], zoom_start=5, tiles=tile_map, control_scale=True)
    Fullscreen(position="topright").add_to(m)
    MiniMap(toggle_display=True, position="bottomright").add_to(m)
    MeasureControl(primary_length_unit="kilometers").add_to(m)

    # --- Marcadores de referencia de ciudades (para verificar alineación) ---
    ciudades_ref = [
        ("CDMX",        19.4326, -99.1332),
        ("Acapulco",    16.8531, -99.8237),
        ("Oaxaca",      17.0732, -96.7266),
        ("Manzanillo",  19.0524, -104.3148),
        ("Tijuana",     32.5149, -117.0382),
        ("Monterrey",   25.6866, -100.3161),
    ]
    ref_group = folium.FeatureGroup(name="📌 Ciudades de referencia", show=True)
    for nombre, lat, lon in ciudades_ref:
        folium.Marker(
            [lat, lon],
            icon=folium.Icon(color="blue", icon="map-marker"),
            tooltip=f"📌 {nombre} | lat={lat}, lon={lon}",
            popup=folium.Popup(f"<b>📌 {nombre}</b><br/>lat: {lat}<br/>lon: {lon}", max_width=180),
        ).add_to(ref_group)
    ref_group.add_to(m)

    sub = sig.head(3000) if capa == "Marcadores" else sig

    if capa == "Mapa de calor":
        puntos = sub[["latitud", "longitud", "magnitud"]].dropna().values.tolist()
        HeatMap(puntos, radius=15, blur=22, min_opacity=0.35,
                gradient={0.15: "#ffffb2", 0.35: "#fecc5c", 0.5: "#fd8d3c", 0.7: "#f03b20", 0.9: "#bd0026"}).add_to(m)
    elif capa == "Clusters":
        cluster = MarkerCluster(name="Sismos").add_to(m)
        for _, r in sub.iterrows():
            color = "red" if r["magnitud"] >= 7 else "orange" if r["magnitud"] >= 6 else "beige"
            folium.Marker(
                [r["latitud"], r["longitud"]],
                icon=folium.Icon(color=color, icon="info-sign"),
                tooltip=f"M{r['magnitud']:.1f} | lat={r['latitud']:.3f}, lon={r['longitud']:.3f}",
                popup=folium.Popup(
                    f"<b>M{r['magnitud']:.1f}</b> — {r['clasificacion_magnitud']}<br/>"
                    f"📅 {r['fecha_local']}<br/>"
                    f"📍 {r['estado']} ({r['region_sismica']})<br/>"
                    f"🌊 Prof: {r['profundidad_km']:.1f} km<br/>"
                    f"📐 Dist CDMX: {r['distancia_cdmx_km']:.0f} km<br/>"
                    f"<small>🔎 lat={r['latitud']:.4f}, lon={r['longitud']:.4f}</small>", max_width=280),
            ).add_to(cluster)
    else:  # Marcadores
        for _, r in sub.iterrows():
            color = "#d9534f" if r["magnitud"] >= 7 else "#ff6b35" if r["magnitud"] >= 6 else "#f7c548"
            radio = max(3, (r["magnitud"] - 4) * 3)
            folium.CircleMarker(
                [r["latitud"], r["longitud"]],
                radius=radio, color=color, fill=True, fill_opacity=0.65, weight=1,
                tooltip=f"M{r['magnitud']:.1f} | lat={r['latitud']:.3f}, lon={r['longitud']:.3f}",
                popup=folium.Popup(
                    f"<b>M{r['magnitud']:.1f}</b> {r['clasificacion_magnitud']}<br/>"
                    f"📅 {r['fecha_local']}<br/>"
                    f"📍 {r['estado']} ({r['region_sismica']})<br/>"
                    f"🌊 {r['profundidad_km']:.1f} km<br/>"
                    f"<small>🔎 lat={r['latitud']:.4f}, lon={r['longitud']:.4f}</small>", max_width=280),
            ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    st_folium(m, width=None, height=620, returned_objects=[], use_container_width=True)

    leyenda = st.columns(4)
    leyenda[0].markdown('🔴 **M ≥ 7.0** — Mayor / Gran sismo')
    leyenda[1].markdown('🟠 **M 6.0-6.9** — Fuerte')
    leyenda[2].markdown('🟡 **M 5.0-5.9** — Moderado')
    leyenda[3].markdown(f'📊 Mostrando hasta 3,000 eventos')

# ----------------------------------------------------------------------------
# TAB 2 — TEMPORAL
# ----------------------------------------------------------------------------
with tab_temp:
    st.markdown("### Evolución histórica anual")
    anual_plot = anual.dropna(subset=["anio", "total_sismos"]).copy()
    anual_plot["anio"] = anual_plot["anio"].astype(int)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=anual_plot["anio"], y=anual_plot["total_sismos"],
        mode="lines", fill="tozeroy", name="Total sismos",
        line=dict(color="#ff6b35", width=2),
        fillcolor="rgba(255,107,53,0.15)",
        hovertemplate="Año: %{x}<br>Total: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=anual_plot["anio"], y=anual_plot["sismos_mag5_plus"],
        mode="lines", name="Mag ≥ 5.0",
        line=dict(color="#f7c548", width=2),
        yaxis="y2",
        hovertemplate="Año: %{x}<br>Mag≥5: %{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        yaxis=dict(title="Total sismos"),
        yaxis2=dict(title="Mag ≥ 5.0", overlaying="y", side="right", showgrid=False),
        hovermode="x unified", height=380,
        xaxis=dict(dtick=5, tickformat="d"),
    )
    st.plotly_chart(style(fig), use_container_width=True)

    # --- Filtrar Silver temporal por rango de años ---
    st_filt = SILVER_TEMP[(SILVER_TEMP["anio"] >= anio_range[0]) & (SILVER_TEMP["anio"] <= anio_range[1])].copy()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Distribución por hora del día")
        hora = (st_filt[st_filt["hora_del_dia"] >= 0]
                .groupby("hora_del_dia", as_index=False)
                .agg(total=("magnitud", "size"), mag=("magnitud", "mean")))
        fig = px.bar(hora, x="hora_del_dia", y="total", color="mag",
                     color_continuous_scale="OrRd",
                     labels={"hora_del_dia": "Hora", "total": "Eventos", "mag": "Mag prom"})
        fig.update_layout(height=320)
        st.plotly_chart(style(fig), use_container_width=True)
    with c2:
        st.markdown("### Sismos por estación del año")
        est = st_filt.groupby("estacion", as_index=False).agg(total=("magnitud", "size"))
        fig = px.pie(est, names="estacion", values="total", hole=0.55,
                     color_discrete_sequence=PLOTLY_THEME["colorway"])
        fig.update_traces(textposition="outside", textinfo="label+percent")
        fig.update_layout(height=320, showlegend=False)
        st.plotly_chart(style(fig), use_container_width=True)

    st.markdown("### Heatmap: hora del día × mes")
    hm_data = st_filt[st_filt["hora_del_dia"] >= 0].copy()
    pivot = hm_data.pivot_table(index="hora_del_dia", columns="mes",
                                values="magnitud", aggfunc="count", fill_value=0)
    meses_nombre = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                    7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[meses_nombre.get(m, f"M{m}") for m in pivot.columns],
        y=pivot.index,
        colorscale="YlOrRd", colorbar=dict(title="Eventos"),
    ))
    fig.update_layout(height=400, yaxis_title="Hora del día")
    st.plotly_chart(style(fig), use_container_width=True)

# ----------------------------------------------------------------------------
# TAB 3 — REGIONAL
# ----------------------------------------------------------------------------
with tab_reg:
    c1, c2 = st.columns([1.4, 1])
    with c1:
        top = (reg.groupby("estado", as_index=False)
                  .agg(total=("total_sismos", "sum"),
                       mag_max=("magnitud_maxima", "max"),
                       mag_prom=("magnitud_promedio", "mean"))
                  .sort_values("total", ascending=True).tail(15))
        fig = px.bar(top, x="total", y="estado", orientation="h",
                     color="mag_max", color_continuous_scale="Reds",
                     hover_data={"mag_prom": ":.2f"})
        fig.update_layout(height=520, title="Top 15 estados por número de sismos")
        st.plotly_chart(style(fig), use_container_width=True)
    with c2:
        reg_sum = (reg.groupby("region_sismica", as_index=False)
                      .agg(total=("total_sismos", "sum"),
                           mag5=("sismos_mag5_plus", "sum"),
                           mag7=("sismos_mag7_plus", "sum")))
        fig = px.sunburst(reg_sum, path=["region_sismica"], values="total",
                          color="mag7", color_continuous_scale="OrRd")
        fig.update_layout(height=320, title="Distribución por región (CENAPRED)")
        st.plotly_chart(style(fig), use_container_width=True)

        fig = px.scatter(reg_sum, x="total", y="mag5", size="mag7",
                         color="region_sismica", text="region_sismica",
                         labels={"total": "Total", "mag5": "Eventos ≥5", "mag7": "Eventos ≥7"})
        fig.update_traces(textposition="top center")
        fig.update_layout(height=320, showlegend=False, title="Total vs eventos significativos")
        st.plotly_chart(style(fig), use_container_width=True)

# ----------------------------------------------------------------------------
# TAB 4 — SIGNIFICATIVOS
# ----------------------------------------------------------------------------
with tab_sig:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.scatter(
            sig, x="profundidad_km", y="magnitud",
            color="region_sismica", size="magnitud",
            hover_data=["fecha_local", "estado", "distancia_cdmx_km"],
            labels={"profundidad_km": "Profundidad (km)", "magnitud": "Magnitud"},
        )
        fig.update_layout(height=420, title="Magnitud vs Profundidad")
        st.plotly_chart(style(fig), use_container_width=True)
    with c2:
        bins = [5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5]
        sig_b = sig.copy()
        sig_b["bin"] = pd.cut(sig_b["magnitud"], bins=bins, include_lowest=True)
        dist = sig_b["bin"].value_counts().sort_index().reset_index()
        dist["bin"] = dist["bin"].astype(str)
        fig = px.bar(dist, x="bin", y="count",
                     labels={"bin": "Rango de magnitud", "count": "Eventos"})
        fig.update_traces(marker_color="#ff6b35")
        fig.update_layout(height=420, title="Distribución por rango de magnitud")
        st.plotly_chart(style(fig), use_container_width=True)

    st.markdown("### 🏆 Top 25 sismos más fuertes del periodo filtrado")
    top25 = sig.sort_values("magnitud", ascending=False).head(25)[
        ["fecha_local", "magnitud", "clasificacion_magnitud", "estado",
         "region_sismica", "profundidad_km", "distancia_cdmx_km", "tsunami_probable"]
    ]
    st.dataframe(
        top25.style.background_gradient(subset=["magnitud"], cmap="Reds"),
        use_container_width=True, hide_index=True,
    )

# ----------------------------------------------------------------------------
# TAB 5 — PREGUNTAS DE NEGOCIO
# ----------------------------------------------------------------------------
with tab_pb:
    st.markdown("### 🎯 PB-1 — Zonas con mayor concentración (últimos 10 años)")
    pb1 = (reg[reg["anio"] >= max(2016, anio_range[0])]
              .groupby("estado", as_index=False)
              .agg(total=("total_sismos", "sum"),
                   mag_max=("magnitud_maxima", "max"),
                   mag5=("sismos_mag5_plus", "sum"))
              .sort_values("total", ascending=False).head(10))
    fig = px.bar(pb1, x="estado", y="total", color="mag_max",
                 color_continuous_scale="OrRd", hover_data=["mag5"])
    fig.update_layout(height=340)
    st.plotly_chart(style(fig), use_container_width=True)

    st.markdown("### 🎯 PB-2 — Patrones temporales")
    pb2_data = SILVER_TEMP[(SILVER_TEMP["anio"] >= anio_range[0]) & (SILVER_TEMP["anio"] <= anio_range[1])]
    c1, c2 = st.columns(2)
    with c1:
        h = (pb2_data[pb2_data["hora_del_dia"] >= 0]
             .groupby("hora_del_dia", as_index=False).agg(total=("magnitud", "size")))
        fig = px.line(h, x="hora_del_dia", y="total", markers=True)
        fig.update_traces(line_color="#ff6b35")
        fig.update_layout(height=300, title="Frecuencia por hora")
        st.plotly_chart(style(fig), use_container_width=True)
    with c2:
        e = pb2_data.groupby("estacion", as_index=False).agg(total=("magnitud", "size"))
        fig = px.bar(e, x="estacion", y="total", color="estacion",
                     color_discrete_sequence=PLOTLY_THEME["colorway"])
        fig.update_layout(height=300, title="Frecuencia por estación", showlegend=False)
        st.plotly_chart(style(fig), use_container_width=True)

    st.markdown("### 🎯 PB-3 — Riesgo por región (Mag ≥ 5.0)")
    pb3 = (sig.groupby("region_sismica", as_index=False)
              .agg(eventos=("magnitud", "size"),
                   mag_prom=("magnitud", "mean"),
                   mag_max=("magnitud", "max"))
              .sort_values("eventos", ascending=False))
    fig = px.bar(pb3, x="region_sismica", y="eventos",
                 color="mag_max", color_continuous_scale="Reds",
                 hover_data={"mag_prom": ":.2f"})
    fig.update_layout(height=340)
    st.plotly_chart(style(fig), use_container_width=True)

# ----------------------------------------------------------------------------
# TAB 6 — CALIDAD DE DATOS
# ----------------------------------------------------------------------------
with tab_cal:
    st.markdown("### 📋 Pipeline de Calidad: Bronze → Silver → Gold")
    st.markdown("")

    # Pipeline visual
    p1, arrow1, p2, arrow2, p3 = st.columns([1, 0.3, 1, 0.3, 1])
    with p1:
        st.markdown('''<div class="pipeline-step">
            <h4>🥉 Bronze</h4>
            <p>Datos crudos del SSN<br/>Tipos: todo <code>string</code><br/>
            Sin validación<br/>Particionado por <code>anio_evento</code></p>
        </div>''', unsafe_allow_html=True)
    with arrow1:
        st.markdown('<div style="text-align:center; padding-top:40px; font-size:28px; color:#ff6b35;">→</div>', unsafe_allow_html=True)
    with p2:
        st.markdown(f'''<div class="pipeline-step" style="border-color: #ff6b35;">
            <h4>🥈 Silver</h4>
            <p><strong>{S["total"]:,}</strong> registros limpios<br/>
            Tipado, validación geográfica<br/>
            Extracción de estado (regex)<br/>
            Clasificación de magnitud</p>
        </div>''', unsafe_allow_html=True)
    with arrow2:
        st.markdown('<div style="text-align:center; padding-top:40px; font-size:28px; color:#ff6b35;">→</div>', unsafe_allow_html=True)
    with p3:
        st.markdown('''<div class="pipeline-step">
            <h4>🥇 Gold</h4>
            <p>4 tablas agregadas<br/>
            Regional, Temporal,<br/>
            Significativos, Evolución<br/>
            Listas para visualización</p>
        </div>''', unsafe_allow_html=True)

    st.markdown("---")

    # Pasos de limpieza
    st.markdown("### 🔧 Pasos de limpieza (Bronze → Silver)")
    pasos = pd.DataFrame({
        "Paso": ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6", "S-7", "S-8"],
        "Operación": [
            "Lectura de Bronze (Parquet crudo)",
            "Cast de tipos: fecha→datetime, magnitud→float, coords→float",
            "Flag de magnitud disponible (sin imputación)",
            "Filtro geográfico MX: lat [14,33], lon [-119,-86], prof [0,700]",
            "Extracción de estado, región y zona vía regex sobre referencia",
            "Deduplicación por (fecha, hora, lat, lon)",
            "Clasificación de magnitud: Micro → Gran sismo",
            "Columnas derivadas: año, mes, día, hora, estación, década",
        ],
        "Impacto": [
            "Carga de datos crudos",
            "Permite filtros numéricos y temporales",
            "Preserva integridad — no se inventan datos",
            "Elimina registros fuera de territorio mexicano",
            f"Cobertura: {S['pct_estados']:.1f}% con estado identificado",
            "Elimina registros repetidos",
            "7 categorías de severidad",
            "Habilita análisis temporal multidimensional",
        ],
    })
    st.dataframe(pasos, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Métricas de cobertura
    st.markdown("### 📊 Cobertura de campos clave")
    cov1, cov2 = st.columns(2)
    with cov1:
        cobertura = pd.DataFrame({
            "Campo": ["Magnitud", "Estado", "Coordenadas", "Fecha"],
            "Cobertura (%)": [S["pct_magnitud"], S["pct_estados"], 100.0, 100.0],
        })
        fig = px.bar(cobertura, x="Cobertura (%)", y="Campo", orientation="h",
                     color="Cobertura (%)", color_continuous_scale="YlGn",
                     range_x=[0, 105])
        fig.update_layout(height=250, showlegend=False)
        fig.update_traces(texttemplate="%{x:.1f}%", textposition="outside")
        st.plotly_chart(style(fig, "Porcentaje de completitud"), use_container_width=True)
    with cov2:
        mag_vals = S["magnitudes"]
        fig = go.Figure(go.Histogram(x=mag_vals, nbinsx=40,
                                     marker_color="#ff6b35", opacity=0.85))
        fig.update_layout(height=250, xaxis_title="Magnitud", yaxis_title="Frecuencia")
        st.plotly_chart(style(fig, "Distribución de magnitudes (Silver)"), use_container_width=True)

    st.markdown("---")
    st.markdown("### 🏷️ Decisiones técnicas clave")
    c1, c2, c3 = st.columns(3)
    c1.info("**pandas + DuckDB** en lugar de PySpark — dataset de ~50 MB cabe en memoria sin necesidad de cluster")
    c2.info("**Parquet + Snappy** — formato columnar comprimido, compatible con Databricks para migración futura")
    c3.info("**No imputación** de magnitudes nulas — inventar datos sísmicos sesgaría el análisis")

st.markdown('<div class="footer">'
            'Datos: Servicio Sismológico Nacional · UNAM · DOI 10.21766/SSNMX/EC/MX  |  '
            'Universidad del Caribe · IDeIO · 2026'
            '</div>', unsafe_allow_html=True)
