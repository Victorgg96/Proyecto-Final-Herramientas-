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
    .main {background-color: #0e1117;}
    .block-container {padding-top: 1.5rem; padding-bottom: 0rem; max-width: 1400px;}
    h1, h2, h3 {color: #fafafa; font-family: 'Segoe UI', sans-serif;}
    h1 {font-weight: 600; letter-spacing: -0.5px;}
    .stMetric {
        background: linear-gradient(135deg, #1e2530 0%, #2a3441 100%);
        border-radius: 12px;
        padding: 18px;
        border-left: 4px solid #ff6b35;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }
    [data-testid="stMetricValue"] {font-size: 28px; font-weight: 700; color: #ff6b35;}
    [data-testid="stMetricLabel"] {color: #c0c8d4; font-weight: 500;}
    [data-testid="stMetricDelta"] {color: #6cc04a;}
    .stTabs [data-baseweb="tab-list"] {gap: 4px; background: #1a1f29; padding: 6px; border-radius: 10px;}
    .stTabs [data-baseweb="tab"] {
        height: 42px; padding: 0 22px; background: transparent; color: #b0b8c4;
        border-radius: 8px; font-weight: 500; font-size: 14px;
    }
    .stTabs [aria-selected="true"] {background: #ff6b35 !important; color: white !important;}
    section[data-testid="stSidebar"] {background: #161b22;}
    section[data-testid="stSidebar"] h2 {color: #ff6b35; font-size: 18px;}
    .badge {
        display: inline-block; padding: 4px 10px; border-radius: 6px;
        font-size: 11px; font-weight: 600; margin-right: 6px;
    }
    .badge-red {background: #d9534f; color: white;}
    .badge-orange {background: #f0ad4e; color: white;}
    .badge-yellow {background: #f7e733; color: #333;}
    .badge-green {background: #5cb85c; color: white;}
    .footer {color: #6c757d; font-size: 12px; text-align: center; padding: 20px 0;}
    div[data-testid="stExpander"] {background: #1a1f29; border-radius: 10px; border: 1px solid #2a3441;}
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


try:
    G = cargar_gold()
    S = cargar_silver_metricas()
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
        '<span class="badge badge-red">379,024 eventos</span>'
        f'<span class="badge badge-yellow">{S["anio_min"]}–{S["anio_max"]}</span>'
        '<span class="badge badge-green">Pipeline Bronze→Silver→Gold</span>',
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
k1, k2, k3, k4, k5 = st.columns(5)
total_filtrado = int(reg["total_sismos"].sum())
mag5_filtrado = len(sig)
mag7_filtrado = int((sig["magnitud"] >= 7).sum())
mag_max_filtrado = float(sig["magnitud"].max()) if len(sig) else 0.0
estados_activos = sig["estado"].nunique()

k1.metric("Sismos totales", f"{total_filtrado:,}", help="Suma para el rango filtrado")
k2.metric("Eventos ≥ 5.0", f"{mag5_filtrado:,}")
k3.metric("Eventos ≥ 7.0", f"{mag7_filtrado}")
k4.metric("Magnitud máx", f"M{mag_max_filtrado:.1f}" if mag_max_filtrado else "—")
k5.metric("Estados afectados", f"{estados_activos}")

st.markdown("")

# ============================================================================
# TABS
# ============================================================================
tab_map, tab_temp, tab_reg, tab_sig, tab_pb = st.tabs([
    "🗺️ Mapa interactivo",
    "⏰ Patrones temporales",
    "📍 Análisis regional",
    "⚠️ Sismos significativos",
    "🎯 Preguntas de negocio",
])

# ----------------------------------------------------------------------------
# TAB 1 — MAPA
# ----------------------------------------------------------------------------
with tab_map:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        capa = st.radio("Capa", ["Marcadores", "Mapa de calor", "Clusters"], horizontal=True)
    with c2:
        tile = st.selectbox("Tile", ["CartoDB dark_matter", "CartoDB positron", "OpenStreetMap", "Stamen Terrain"])
    with c3:
        st.write(f"**{len(sig):,}** eventos en pantalla")

    tile_map = {
        "CartoDB dark_matter": "cartodbdark_matter",
        "CartoDB positron": "cartodbpositron",
        "OpenStreetMap": "openstreetmap",
        "Stamen Terrain": "Stamen Terrain",
    }[tile]

    m = folium.Map(location=[23.5, -102.0], zoom_start=5, tiles=tile_map, control_scale=True)
    Fullscreen(position="topright").add_to(m)
    MiniMap(toggle_display=True, position="bottomright").add_to(m)
    MeasureControl(primary_length_unit="kilometers").add_to(m)

    sub = sig.head(3000) if capa == "Marcadores" else sig

    if capa == "Mapa de calor":
        puntos = sub[["latitud", "longitud", "magnitud"]].dropna().values.tolist()
        HeatMap(puntos, radius=12, blur=18, min_opacity=0.4,
                gradient={0.2: "#3a8df5", 0.4: "#f7c548", 0.6: "#ff6b35", 0.9: "#d9534f"}).add_to(m)
    elif capa == "Clusters":
        cluster = MarkerCluster(name="Sismos").add_to(m)
        for _, r in sub.iterrows():
            color = "red" if r["magnitud"] >= 7 else "orange" if r["magnitud"] >= 6 else "beige"
            folium.Marker(
                [r["latitud"], r["longitud"]],
                icon=folium.Icon(color=color, icon="info-sign"),
                tooltip=f"M{r['magnitud']:.1f}",
                popup=folium.Popup(
                    f"<b>M{r['magnitud']:.1f}</b> — {r['clasificacion_magnitud']}<br/>"
                    f"📅 {r['fecha_local']}<br/>"
                    f"📍 {r['estado']} ({r['region_sismica']})<br/>"
                    f"🌊 Prof: {r['profundidad_km']:.1f} km<br/>"
                    f"📐 Dist CDMX: {r['distancia_cdmx_km']:.0f} km", max_width=260),
            ).add_to(cluster)
    else:  # Marcadores
        for _, r in sub.iterrows():
            color = "#d9534f" if r["magnitud"] >= 7 else "#ff6b35" if r["magnitud"] >= 6 else "#f7c548"
            radio = max(3, (r["magnitud"] - 4) * 3)
            folium.CircleMarker(
                [r["latitud"], r["longitud"]],
                radius=radio, color=color, fill=True, fill_opacity=0.65, weight=1,
                tooltip=f"M{r['magnitud']:.1f} - {r['estado']}",
                popup=folium.Popup(
                    f"<b>M{r['magnitud']:.1f}</b> {r['clasificacion_magnitud']}<br/>"
                    f"📅 {r['fecha_local']}<br/>"
                    f"📍 {r['estado']} ({r['region_sismica']})<br/>"
                    f"🌊 {r['profundidad_km']:.1f} km", max_width=260),
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
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=anual["anio"], y=anual["total_sismos"],
        mode="lines", fill="tozeroy", name="Total sismos",
        line=dict(color="#ff6b35", width=2),
        fillcolor="rgba(255,107,53,0.2)",
    ))
    fig.add_trace(go.Scatter(
        x=anual["anio"], y=anual["sismos_mag5_plus"],
        mode="lines", name="Mag ≥ 5.0",
        line=dict(color="#f7c548", width=2),
        yaxis="y2",
    ))
    fig.update_layout(
        yaxis=dict(title="Total sismos"),
        yaxis2=dict(title="Mag ≥ 5.0", overlaying="y", side="right", showgrid=False),
        hovermode="x unified", height=380,
    )
    st.plotly_chart(style(fig), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Distribución por hora del día")
        tmp = G["temporal"]
        hora = (tmp[tmp["hora_del_dia"] >= 0].groupby("hora_del_dia", as_index=False)
                                              .agg(total=("total_sismos", "sum"),
                                                   mag=("magnitud_promedio", "mean")))
        fig = px.bar(hora, x="hora_del_dia", y="total", color="mag",
                     color_continuous_scale="Oranges",
                     labels={"hora_del_dia": "Hora", "total": "Eventos", "mag": "Mag prom"})
        fig.update_layout(height=320)
        st.plotly_chart(style(fig), use_container_width=True)
    with c2:
        st.markdown("### Sismos por estación del año")
        est = tmp.groupby("estacion", as_index=False)["total_sismos"].sum()
        fig = px.pie(est, names="estacion", values="total_sismos", hole=0.55,
                     color_discrete_sequence=PLOTLY_THEME["colorway"])
        fig.update_traces(textposition="outside", textinfo="label+percent")
        fig.update_layout(height=320, showlegend=False)
        st.plotly_chart(style(fig), use_container_width=True)

    st.markdown("### Heatmap: hora del día × mes")
    pivot = (tmp[tmp["hora_del_dia"] >= 0]
             .pivot_table(index="hora_del_dia", columns="mes",
                          values="total_sismos", aggfunc="sum", fill_value=0))
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=[f"Mes {m}" for m in pivot.columns], y=pivot.index,
        colorscale="Inferno", colorbar=dict(title="Eventos"),
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
    tmp = G["temporal"]
    c1, c2 = st.columns(2)
    with c1:
        h = (tmp[tmp["hora_del_dia"] >= 0]
             .groupby("hora_del_dia", as_index=False)["total_sismos"].sum())
        fig = px.line(h, x="hora_del_dia", y="total_sismos", markers=True)
        fig.update_traces(line_color="#ff6b35")
        fig.update_layout(height=300, title="Frecuencia por hora")
        st.plotly_chart(style(fig), use_container_width=True)
    with c2:
        e = tmp.groupby("estacion", as_index=False)["total_sismos"].sum()
        fig = px.bar(e, x="estacion", y="total_sismos", color="estacion",
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

st.markdown('<div class="footer">'
            'Datos: Servicio Sismológico Nacional · UNAM · DOI 10.21766/SSNMX/EC/MX  |  '
            'Universidad del Caribe · IDeIO · 2026'
            '</div>', unsafe_allow_html=True)
