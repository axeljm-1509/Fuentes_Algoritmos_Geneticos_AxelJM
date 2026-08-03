"""Tema visual y pequeños componentes HTML del centro de mando."""

from __future__ import annotations

from html import escape

import streamlit as st


def apply_theme() -> None:
    """Inyecta un tema oscuro, legible y adaptable sin recursos externos."""

    st.markdown(
        """
        <style>
        :root { --bg:#080B14; --panel:#111827; --cyan:#22D3EE; --violet:#8B5CF6;
                --green:#34D399; --yellow:#FBBF24; --text:#E5E7EB; --muted:#94A3B8; }
        .stApp {
            background-color: var(--bg);
            background-image: linear-gradient(rgba(34,211,238,.025) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(34,211,238,.025) 1px, transparent 1px);
            background-size: 32px 32px; color: var(--text);
            font-family: Inter, "Segoe UI", sans-serif;
        }
        [data-testid="stSidebar"] { background: rgba(13,19,33,.98); border-right:1px solid rgba(34,211,238,.16); }
        [data-testid="stHeader"] { background: rgba(8,11,20,.78); }
        [data-testid="stVerticalBlockBorderWrapper"] { border-color:rgba(34,211,238,.14)!important; border-radius:16px; background:rgba(17,24,39,.68); }
        h1,h2,h3 { letter-spacing:.02em; }
        .command-header { padding:1.35rem 1.45rem; margin:.2rem 0 1rem; border:1px solid rgba(34,211,238,.25);
            border-radius:18px; background:linear-gradient(120deg,rgba(17,24,39,.96),rgba(26,18,52,.82));
            box-shadow:0 0 35px rgba(34,211,238,.07), inset 0 0 24px rgba(139,92,246,.05); }
        .eyebrow { color:var(--cyan); font-size:.72rem; text-transform:uppercase; letter-spacing:.18em; font-weight:700; }
        .command-title { color:var(--text); font-size:clamp(1.65rem,4vw,2.7rem); line-height:1.05; font-weight:800; margin:.35rem 0; }
        .command-subtitle { color:var(--muted); font-size:1rem; margin:0; }
        .status-chip { display:inline-flex; align-items:center; gap:.5rem; color:var(--green); border:1px solid rgba(52,211,153,.3);
            background:rgba(52,211,153,.08); border-radius:99px; padding:.35rem .7rem; font-size:.75rem; font-weight:700; }
        .status-dot { width:7px; height:7px; border-radius:50%; background:var(--green); box-shadow:0 0 9px var(--green); }
        .metric-card { min-height:106px; padding:1rem; border:1px solid rgba(148,163,184,.14); border-radius:14px;
            background:linear-gradient(145deg,rgba(17,24,39,.96),rgba(8,11,20,.9)); box-shadow:inset 3px 0 0 var(--accent); }
        .metric-label { color:var(--muted); font-size:.72rem; letter-spacing:.08em; text-transform:uppercase; }
        .metric-value { color:var(--text); font-size:1.38rem; font-weight:750; margin:.35rem 0 .15rem; }
        .metric-detail { color:var(--accent); font-size:.76rem; }
        .route-sequence { max-height:125px; overflow:auto; padding:1rem 1.1rem; border-radius:12px; border:1px solid rgba(139,92,246,.25);
            color:#DDD6FE; background:rgba(139,92,246,.06); line-height:1.8; font-family:"Segoe UI",sans-serif; }
        .section-kicker { color:var(--cyan); font-size:.72rem; font-weight:700; letter-spacing:.13em; text-transform:uppercase; margin-bottom:.15rem; }
        div.stButton > button, div.stDownloadButton > button { min-height:2.7rem; border-radius:10px; border:1px solid rgba(34,211,238,.38);
            background:linear-gradient(115deg,rgba(34,211,238,.16),rgba(139,92,246,.19)); color:var(--text); font-weight:750; letter-spacing:.035em; }
        div.stButton > button:hover, div.stDownloadButton > button:hover { border-color:var(--cyan); color:white; box-shadow:0 0 18px rgba(34,211,238,.18); transform:translateY(-1px); }
        [data-testid="stMetricValue"] { color:var(--text); }
        [data-testid="stFileUploaderDropzone"] { background:rgba(17,24,39,.72); border-color:rgba(34,211,238,.22); }
        hr { border-color:rgba(148,163,184,.12); }
        @media (max-width:700px) { .command-header{padding:1rem}.metric-card{min-height:92px}.command-subtitle{font-size:.88rem} }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="command-header">
          <div class="eyebrow">Caso de estudio — Algoritmos Genéticos</div>
          <div class="command-title">GENETIC ROUTE COMMANDER</div>
          <p class="command-subtitle">Sistema evolutivo para optimización de rutas</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status(text: str = "SISTEMA LISTO") -> None:
    st.markdown(
        f'<span class="status-chip"><span class="status-dot"></span>{escape(text)}</span>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, detail: str, accent: str = "#22D3EE") -> None:
    st.markdown(
        f"""<div class="metric-card" style="--accent:{escape(accent)}">
        <div class="metric-label">{escape(label)}</div><div class="metric-value">{escape(value)}</div>
        <div class="metric-detail">{escape(detail)}</div></div>""",
        unsafe_allow_html=True,
    )


def section_title(kicker: str, title: str) -> None:
    st.markdown(f'<div class="section-kicker">{escape(kicker)}</div>', unsafe_allow_html=True)
    st.subheader(title)
