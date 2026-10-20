import hmac
import html
import os
from datetime import date, timedelta

import mysql.connector
import pandas as pd
import streamlit as st
from mysql.connector import Error
from streamlit.runtime.scriptrunner import get_script_run_ctx

# This file is a Streamlit app: it must be started with `streamlit run`,
# not `python lab_equipment_app.py` (which has no browser session / login state).
if get_script_run_ctx() is None:
    raise SystemExit(
        "\nThis is a Streamlit app. Start it with:\n\n"
        "    streamlit run lab_equipment_app.py\n\n"
        "(or:  python -m streamlit run lab_equipment_app.py)\n"
    )

# ------------------------------------------------------------
# Lab Equipment Management System  —  "Midnight Lab" interface
# Database: lab_equipment_db (from the supplied SQL file)
# Only the UI layer was redesigned; all database logic is unchanged.
# ------------------------------------------------------------

st.set_page_config(
    page_title="Lab Equipment Manager",
    page_icon="🧪",
    layout="wide",
)

# ============================================================
# THEME  (dark background, bright text, animated hover effects)
# ============================================================
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #060a14;
  --surface: #0e1527;
  --surface-2: #141d36;
  --surface-3: #1a2547;
  --border: rgba(148, 163, 184, 0.16);
  --text: #eaf0fb;
  --muted: #9fb0cf;
  --cyan: #22d3ee;
  --violet: #8b5cf6;
  --green: #34d399;
  --amber: #fbbf24;
  --red: #f87171;
  --grey: #94a3b8;
  color-scheme: dark;
}

/* ---------- Base ---------- */
html, body, .stApp, [data-testid="stAppViewContainer"] {
  font-family: 'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif !important;
  color: var(--text);
}
.stApp {
  background:
    radial-gradient(900px 500px at 8% -8%, rgba(139, 92, 246, 0.20), transparent 60%),
    radial-gradient(800px 480px at 100% 0%, rgba(34, 211, 238, 0.14), transparent 60%),
    radial-gradient(700px 500px at 50% 115%, rgba(52, 211, 153, 0.08), transparent 60%),
    var(--bg) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] *, [data-testid="stHeader"] * { color: var(--muted) !important; }
footer, #MainMenu { visibility: hidden; }
.block-container { padding-top: 1.4rem !important; padding-bottom: 3rem !important; max-width: 1400px; }

.stApp :is(p, li, label, summary, h1, h2, h3, h4, h5, h6) { color: var(--text); }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] * { color: var(--muted) !important; }
.stApp [data-testid="stWidgetLabel"], .stApp [data-testid="stWidgetLabel"] * {
  color: #c9d6f0 !important; font-weight: 600; font-size: 0.86rem;
}
.stApp a { color: var(--cyan); }

/* ---------- Scrollbars ---------- */
* { scrollbar-width: thin; scrollbar-color: #2b3a66 transparent; }
::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-thumb { background: #2b3a66; border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: #3c5191; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0a1124 0%, #0c1530 100%) !important;
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text); }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * { color: var(--muted) !important; }
.side-title {
  font-weight: 800; font-size: 1.05rem; letter-spacing: .02em;
  display: flex; align-items: center; gap: 10px; margin-bottom: 4px;
}
.side-title .ico {
  width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center;
  background: linear-gradient(135deg, var(--cyan), var(--violet));
  box-shadow: 0 6px 18px -6px rgba(34, 211, 238, .7);
}
.conn-pill {
  display: inline-flex; align-items: center; gap: 8px; padding: 7px 14px; border-radius: 999px;
  font-size: .8rem; font-weight: 700; margin: 6px 0 2px;
  background: rgba(52, 211, 153, .12); border: 1px solid rgba(52, 211, 153, .35); color: var(--green) !important;
}
.conn-pill.bad { background: rgba(248, 113, 113, .12); border-color: rgba(248, 113, 113, .35); color: var(--red) !important; }
.conn-pill .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; animation: pulse 1.8s infinite; }

/* ---------- Hero ---------- */
.hero {
  position: relative; overflow: hidden; padding: 30px 34px; margin-bottom: 22px; border-radius: 24px;
  background: linear-gradient(135deg, rgba(20, 29, 54, .92), rgba(14, 21, 39, .92));
  border: 1px solid var(--border);
  box-shadow: 0 24px 60px -30px rgba(0, 0, 0, .8);
  animation: fadeUp .7s ease both;
}
.hero::before {
  content: ""; position: absolute; inset: -60% -10% auto auto; width: 520px; height: 520px; border-radius: 50%;
  background: radial-gradient(circle, rgba(34, 211, 238, .28), transparent 65%);
  animation: float 9s ease-in-out infinite;
}
.hero::after {
  content: ""; position: absolute; inset: auto auto -70% -8%; width: 460px; height: 460px; border-radius: 50%;
  background: radial-gradient(circle, rgba(139, 92, 246, .30), transparent 65%);
  animation: float 11s ease-in-out infinite reverse;
}
.hero > * { position: relative; z-index: 1; }
.hero-tag {
  display: inline-flex; align-items: center; gap: 8px; font-size: .72rem; font-weight: 800; letter-spacing: .16em;
  padding: 6px 14px; border-radius: 999px; color: var(--cyan);
  background: rgba(34, 211, 238, .10); border: 1px solid rgba(34, 211, 238, .30);
}
.hero-tag .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--cyan); animation: pulse 1.8s infinite; }
.hero h1 { font-size: 2.5rem; font-weight: 800; margin: 14px 0 6px; line-height: 1.12; letter-spacing: -.02em; padding: 0; }
.hero h1 .grad {
  background: linear-gradient(90deg, var(--cyan), var(--violet) 60%, #f0abfc);
  background-size: 200% auto; -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; color: transparent; animation: shine 6s linear infinite;
}
.hero p { color: var(--muted) !important; font-size: 1.02rem; margin: 0; max-width: 720px; }

/* ---------- Section headings ---------- */
.sec { margin: 6px 0 16px; animation: fadeUp .5s ease both; }
.sec h3 { font-size: 1.35rem; font-weight: 800; margin: 0; padding: 0; letter-spacing: -.01em; display: flex; align-items: center; gap: 10px; }
.sec h3::before { content: ""; width: 5px; height: 22px; border-radius: 4px; background: linear-gradient(180deg, var(--cyan), var(--violet)); }
.sec p { color: var(--muted) !important; margin: 4px 0 0 15px; font-size: .92rem; }

/* ---------- Stat cards ---------- */
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 16px; margin-bottom: 18px; }
.stat {
  --c: var(--cyan);
  position: relative; overflow: hidden; padding: 20px 20px 18px; border-radius: 20px;
  background: linear-gradient(160deg, var(--surface-2), var(--surface));
  border: 1px solid var(--border);
  transition: transform .3s cubic-bezier(.2, .8, .2, 1), box-shadow .3s, border-color .3s;
  animation: fadeUp .6s ease both;
}
.stat:nth-child(2) { animation-delay: .06s; } .stat:nth-child(3) { animation-delay: .12s; }
.stat:nth-child(4) { animation-delay: .18s; } .stat:nth-child(5) { animation-delay: .24s; }
.stat::before { content: ""; position: absolute; left: 0; top: 0; right: 0; height: 3px; background: var(--c); opacity: .9; }
.stat::after {
  content: ""; position: absolute; right: -40px; top: -40px; width: 130px; height: 130px; border-radius: 50%;
  background: radial-gradient(circle, var(--c), transparent 70%); opacity: .14; transition: opacity .3s, transform .4s;
}
.stat:hover { transform: translateY(-6px) scale(1.02); border-color: var(--c); box-shadow: 0 22px 40px -22px var(--c); }
.stat:hover::after { opacity: .30; transform: scale(1.25); }
.stat .ico { font-size: 1.5rem; display: inline-block; transition: transform .3s; }
.stat:hover .ico { transform: scale(1.25) rotate(-8deg); }
.stat .lbl { color: var(--muted) !important; font-size: .78rem; font-weight: 700; text-transform: uppercase; letter-spacing: .09em; margin-top: 10px; }
.stat .val { font-size: 2.3rem; font-weight: 800; line-height: 1.1; color: #fff !important; margin-top: 2px; }
.stat.c-green { --c: var(--green); } .stat.c-amber { --c: var(--amber); }
.stat.c-violet { --c: var(--violet); } .stat.c-grey { --c: var(--grey); }

/* ---------- Availability bar ---------- */
.dist { padding: 16px 18px 14px; border-radius: 18px; background: var(--surface); border: 1px solid var(--border); margin-bottom: 22px; animation: fadeUp .7s ease both; }
.dist-bar { display: flex; height: 12px; border-radius: 99px; overflow: hidden; background: #0a1020; gap: 2px; }
.dist-bar span { display: block; transition: filter .25s, transform .25s; transform-origin: bottom; }
.dist-bar span:hover { filter: brightness(1.3); transform: scaleY(1.5); }
.dist-legend { display: flex; flex-wrap: wrap; gap: 8px 22px; margin-top: 12px; font-size: .82rem; color: var(--muted); }
.dist-legend i { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 7px; }
.dist-legend b { color: var(--text); }

/* ---------- Tabs ---------- */
[data-baseweb="tab-list"] {
  gap: 8px; background: var(--surface); padding: 8px; border-radius: 16px; border: 1px solid var(--border);
  overflow-x: auto;
}
[data-baseweb="tab-list"] button[role="tab"] {
  border-radius: 11px !important; padding: 10px 18px !important; background: transparent !important;
  transition: transform .22s ease, background .22s, box-shadow .22s;
}
[data-baseweb="tab-list"] button[role="tab"] * { color: var(--muted) !important; font-weight: 600; transition: color .2s; }
[data-baseweb="tab-list"] button[role="tab"]:hover {
  transform: translateY(-2px); background: rgba(34, 211, 238, .09) !important;
}
[data-baseweb="tab-list"] button[role="tab"]:hover * { color: #fff !important; }
[data-baseweb="tab-list"] button[role="tab"][aria-selected="true"] {
  background: linear-gradient(135deg, rgba(34, 211, 238, .20), rgba(139, 92, 246, .24)) !important;
  box-shadow: inset 0 0 0 1px rgba(34, 211, 238, .38), 0 8px 20px -10px rgba(34, 211, 238, .6);
}
[data-baseweb="tab-list"] button[role="tab"][aria-selected="true"] * { color: #fff !important; }
[data-baseweb="tab-highlight"] { background: transparent !important; }
[data-baseweb="tab-border"] { display: none !important; }
[data-baseweb="tab-panel"] { padding-top: 1.4rem !important; animation: fadeUp .5s ease both; }

/* ---------- Inputs ---------- */
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
  background: #0a1122 !important; border-color: var(--border) !important; border-radius: 12px !important;
  transition: border-color .2s, box-shadow .2s, transform .2s;
}
[data-baseweb="input"]:hover, [data-baseweb="select"] > div:hover { border-color: rgba(34, 211, 238, .55) !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="select"]:focus-within > div {
  border-color: var(--cyan) !important; box-shadow: 0 0 0 3px rgba(34, 211, 238, .20);
}
input, textarea { color: var(--text) !important; -webkit-text-fill-color: var(--text) !important; caret-color: var(--cyan); }
input::placeholder, textarea::placeholder { color: #6f7fa3 !important; -webkit-text-fill-color: #6f7fa3 !important; }
[data-baseweb="select"] * { color: var(--text) !important; }
[data-baseweb="select"] svg { fill: var(--muted) !important; }
[data-testid="stNumberInput"] button { background: #121b33 !important; color: var(--text) !important; }
[data-testid="stNumberInput"] button:hover { background: var(--surface-3) !important; }

/* Dropdown menus & calendar (rendered in a portal) */
[data-baseweb="popover"], [data-baseweb="popover"] > div, [data-baseweb="menu"], ul[role="listbox"] {
  background: #0f1830 !important; color: var(--text) !important; border-radius: 12px !important;
}
[data-baseweb="popover"] { border: 1px solid var(--border); box-shadow: 0 22px 50px -12px rgba(0, 0, 0, .85) !important; }
li[role="option"], [data-baseweb="menu"] li { background: transparent !important; color: var(--text) !important; transition: background .15s, padding-left .15s; }
li[role="option"] *, [data-baseweb="menu"] li * { color: var(--text) !important; }
li[role="option"]:hover, li[role="option"][aria-selected="true"], [data-baseweb="menu"] li:hover {
  background: rgba(34, 211, 238, .14) !important; padding-left: 20px !important;
}
[data-baseweb="calendar"] { background: #0f1830 !important; color: var(--text) !important; }
[data-baseweb="calendar"] * { color: var(--text) !important; }
[data-baseweb="calendar"] [role="gridcell"] > div:hover, [data-baseweb="calendar"] button:hover { background: rgba(34, 211, 238, .2) !important; }

/* Checkbox */
[data-baseweb="checkbox"] > span:first-child { border-color: var(--cyan) !important; background-color: #0a1122 !important; transition: transform .2s; }
[data-baseweb="checkbox"]:hover > span:first-child { transform: scale(1.15); }
[data-baseweb="checkbox"] input:checked + div { background: linear-gradient(135deg, var(--cyan), var(--violet)) !important; border-color: transparent !important; }

/* ---------- Forms ---------- */
[data-testid="stForm"] {
  background: linear-gradient(160deg, var(--surface-2), var(--surface)) !important;
  border: 1px solid var(--border) !important; border-radius: 20px !important; padding: 26px 26px 20px !important;
  transition: border-color .3s, box-shadow .3s;
}
[data-testid="stForm"]:hover { border-color: rgba(34, 211, 238, .38) !important; box-shadow: 0 24px 50px -30px rgba(34, 211, 238, .55); }

/* ---------- Buttons (hover animation) ---------- */
.stButton > button, [data-testid="stFormSubmitButton"] > button, [data-testid="stDownloadButton"] > button {
  position: relative; overflow: hidden; border: 0 !important; border-radius: 13px !important;
  padding: .72rem 1.7rem !important; font-weight: 700 !important; letter-spacing: .02em;
  background: linear-gradient(135deg, #06b6d4 0%, #6366f1 55%, #8b5cf6 100%) !important;
  background-size: 160% 160% !important; background-position: 0% 50%;
  box-shadow: 0 10px 24px -12px rgba(34, 211, 238, .75), inset 0 1px 0 rgba(255, 255, 255, .25);
  transition: transform .28s cubic-bezier(.2, .9, .3, 1.4), box-shadow .28s, background-position .5s;
}
.stButton > button *, [data-testid="stFormSubmitButton"] > button *, [data-testid="stDownloadButton"] > button * {
  color: #fff !important; font-weight: 700 !important; position: relative; z-index: 1;
}
.stButton > button::before, [data-testid="stFormSubmitButton"] > button::before, [data-testid="stDownloadButton"] > button::before {
  content: ""; position: absolute; top: 0; left: -90%; width: 55%; height: 100%;
  background: linear-gradient(110deg, transparent, rgba(255, 255, 255, .45), transparent);
  transform: skewX(-22deg); transition: left .65s ease;
}
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover, [data-testid="stDownloadButton"] > button:hover {
  transform: translateY(-4px) scale(1.05); background-position: 100% 50% !important;
  box-shadow: 0 18px 34px -10px rgba(139, 92, 246, .85), 0 0 0 3px rgba(34, 211, 238, .22);
}
.stButton > button:hover::before, [data-testid="stFormSubmitButton"] > button:hover::before, [data-testid="stDownloadButton"] > button:hover::before { left: 140%; }
.stButton > button:active, [data-testid="stFormSubmitButton"] > button:active, [data-testid="stDownloadButton"] > button:active {
  transform: translateY(-1px) scale(.97); transition-duration: .08s;
}
.stButton > button:focus-visible, [data-testid="stFormSubmitButton"] > button:focus-visible { outline: 3px solid rgba(34, 211, 238, .5) !important; }

/* ---------- Expander ---------- */
[data-testid="stExpander"] details {
  background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 16px !important;
  transition: border-color .25s, box-shadow .25s;
}
[data-testid="stExpander"] details:hover { border-color: rgba(34, 211, 238, .45) !important; box-shadow: 0 14px 30px -22px rgba(34, 211, 238, .6); }
[data-testid="stExpander"] summary { font-weight: 700; }
[data-testid="stExpander"] summary:hover * { color: var(--cyan) !important; }
[data-testid="stExpander"] svg { fill: var(--muted); color: var(--muted); }

/* ---------- Notices ---------- */
.note {
  --c: var(--cyan);
  display: flex; align-items: flex-start; gap: 14px; padding: 15px 18px; margin: 4px 0 16px; border-radius: 14px;
  background: color-mix(in srgb, var(--c) 11%, #0b1223); border: 1px solid color-mix(in srgb, var(--c) 40%, transparent);
  border-left: 4px solid var(--c); color: var(--text); font-size: .94rem; line-height: 1.5;
  animation: slideIn .45s cubic-bezier(.2, .8, .2, 1) both; transition: transform .2s, box-shadow .2s;
}
.note:hover { transform: translateX(4px); box-shadow: 0 12px 28px -18px var(--c); }
.note .n-ico { font-size: 1.15rem; line-height: 1.4; }
.note .n-txt { color: var(--text) !important; word-break: break-word; }
.note.success { --c: var(--green); } .note.warning { --c: var(--amber); } .note.error { --c: var(--red); }

/* ---------- Tables ---------- */
.tbl-wrap {
  max-height: 480px; overflow: auto; border-radius: 16px; background: var(--surface);
  border: 1px solid var(--border); margin-bottom: 14px; animation: fadeUp .6s ease both;
}
table.tbl { width: 100%; border-collapse: separate; border-spacing: 0; font-size: .875rem; margin: 0 !important; }
table.tbl th {
  position: sticky; top: 0; z-index: 2; text-align: left; white-space: nowrap; padding: 13px 16px;
  background: #16203f !important; color: #a9bbe0 !important; font-size: .7rem; font-weight: 800;
  text-transform: uppercase; letter-spacing: .09em; border: 0 !important; border-bottom: 1px solid var(--border) !important;
}
table.tbl td {
  padding: 12px 16px; white-space: nowrap; color: var(--text) !important; background: transparent !important;
  border: 0 !important; border-top: 1px solid rgba(148, 163, 184, .09) !important; transition: background .18s;
}
table.tbl tbody tr:nth-child(even) td { background: rgba(255, 255, 255, .018) !important; }
table.tbl tbody tr:hover td { background: rgba(34, 211, 238, .10) !important; }
table.tbl tbody tr:hover td:first-child { box-shadow: inset 3px 0 0 var(--cyan); }
table.tbl td.dim { color: #62729a !important; }
table.tbl td.late { color: var(--red) !important; font-weight: 800; }
.tbl-foot { color: var(--muted); font-size: .8rem; margin: -4px 4px 14px; }

.badge {
  --c: var(--grey);
  display: inline-flex; align-items: center; gap: 7px; padding: 4px 12px; border-radius: 999px; font-size: .76rem; font-weight: 700;
  color: var(--c) !important; background: color-mix(in srgb, var(--c) 15%, transparent);
  border: 1px solid color-mix(in srgb, var(--c) 40%, transparent); transition: transform .2s, box-shadow .2s;
}
.badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: var(--c); }
.badge:hover { transform: scale(1.1); box-shadow: 0 0 16px -2px var(--c); }
.badge.ok { --c: var(--green); } .badge.busy { --c: var(--amber); } .badge.maint { --c: var(--violet); }
.badge.retired { --c: var(--grey); } .badge.late { --c: var(--red); } .badge.info { --c: var(--cyan); }

/* ---------- Keyframes ---------- */
@keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
@keyframes slideIn { from { opacity: 0; transform: translateX(-18px); } to { opacity: 1; transform: none; } }
@keyframes float { 0%, 100% { transform: translate(0, 0); } 50% { transform: translate(-30px, 24px); } }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 currentColor; } 70% { box-shadow: 0 0 0 7px transparent; } 100% { box-shadow: 0 0 0 0 transparent; } }
@keyframes shine { to { background-position: 200% center; } }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
@media (max-width: 700px) { .hero h1 { font-size: 1.75rem; } .hero { padding: 22px; } }
</style>
"""
st.markdown(THEME_CSS, unsafe_allow_html=True)


# ============================================================
# UI HELPERS (presentation only)
# ============================================================
def hero():
    st.markdown(
        '<div class="hero">'
        '<span class="hero-tag"><span class="dot"></span>LAB OPERATIONS</span>'
        '<h1>🧪 Lab Equipment <span class="grad">Management</span></h1>'
        '<p>Find equipment by lab, check availability, borrow items, and record returns — all in one place.</p>'
        "</div>",
        unsafe_allow_html=True,
    )


def section(title, subtitle=""):
    sub = f"<p>{html.escape(subtitle)}</p>" if subtitle else ""
    st.markdown(f'<div class="sec"><h3>{html.escape(title)}</h3>{sub}</div>', unsafe_allow_html=True)


NOTE_ICONS = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "⛔"}


def notice(kind, text):
    st.markdown(
        f'<div class="note {kind}"><span class="n-ico">{NOTE_ICONS[kind]}</span>'
        f'<span class="n-txt">{html.escape(str(text)).replace(chr(10), "<br>")}</span></div>',
        unsafe_allow_html=True,
    )


def flash(kind, text):
    """Remember a message across st.rerun() so the user actually sees it."""
    st.session_state["_flash"] = (kind, text)


def stat_card(icon, label, value, tone=""):
    return (
        f'<div class="stat {tone}"><span class="ico">{icon}</span>'
        f'<div class="lbl">{html.escape(label)}</div><div class="val">{int(value)}</div></div>'
    )


BADGE_CLASS = {
    "available": "ok", "new": "ok", "good": "ok", "returned": "ok",
    "issued": "busy", "fair": "busy",
    "under maintenance": "maint",
    "retired": "retired",
    "overdue": "late", "poor": "late",
}
BADGE_COLUMNS = {"Availability_Status", "Current_Status", "Allocation_Status", "Equipment_Condition"}


def render_table(df, max_rows=500):
    """Dark, hover-highlighted HTML table with colour-coded status badges."""
    if df is None or df.empty:
        return
    shown = df.head(max_rows)
    head = "".join(f"<th>{html.escape(str(c).replace('_', ' '))}</th>" for c in shown.columns)
    body = []
    for row in shown.itertuples(index=False):
        cells = []
        for col, val in zip(shown.columns, row):
            if val is None or (not isinstance(val, str) and pd.isna(val)):
                cells.append('<td class="dim">—</td>')
                continue
            text = html.escape(str(val))
            if col in BADGE_COLUMNS:
                cls = BADGE_CLASS.get(str(val).strip().lower(), "info")
                cells.append(f'<td><span class="badge {cls}">{text}</span></td>')
            elif col == "Days_Past_Due":
                late = float(val) > 0
                cells.append(f'<td class="{"late" if late else "dim"}">{text}</td>')
            else:
                cells.append(f"<td>{text}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    st.markdown(
        f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>',
        unsafe_allow_html=True,
    )
    extra = f" (showing first {max_rows})" if len(df) > max_rows else ""
    st.markdown(f'<div class="tbl-foot">{len(df)} record{"s" if len(df) != 1 else ""}{extra}</div>', unsafe_allow_html=True)


hero()


def login_screen():
    """First page: ask for the database password before showing the app."""
    st.markdown(
        "<style>[data-testid='stSidebar'], [data-testid='stSidebarCollapsedControl'], "
        "[data-testid='collapsedControl'] {display: none !important;}</style>",
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 1.5, 1])
    with mid:
        section("🔐 Sign in", "Enter your MySQL credentials to open the equipment manager.")
        if "_login_error" in st.session_state:
            notice("error", st.session_state.pop("_login_error"))
        # Deployed mode: DB details live in Streamlit "Secrets"; visitors only enter an access password.
        try:
            cfg = dict(st.secrets["db"])
        except Exception:
            cfg = None
        if cfg:
            with st.form("access_form"):
                access = st.text_input("Access password", type="password", placeholder="Ask the owner for the password")
                go_access = st.form_submit_button("🔓  Enter", type="primary")
            if go_access:
                expected = str(cfg.get("access_password", ""))
                if not expected or not hmac.compare_digest(access.encode(), expected.encode()):
                    st.session_state["_login_error"] = "Incorrect access password."
                    st.rerun()
                try:
                    test = mysql.connector.connect(
                        host=cfg["host"], port=int(cfg.get("port", 3306)), user=cfg["user"],
                        password=cfg["password"], database=cfg.get("database", "lab_equipment_db"),
                    )
                    test.close()
                except Error as exc:
                    st.session_state["_login_error"] = f"The database is not reachable right now. Details: {exc}"
                    st.rerun()
                st.session_state["auth"] = {
                    "host": cfg["host"], "port": int(cfg.get("port", 3306)), "user": cfg["user"],
                    "password": cfg["password"], "database": cfg.get("database", "lab_equipment_db"),
                    "managed": True,
                }
                flash("success", "Welcome! You are connected.")
                st.rerun()
            return

        with st.form("login_form"):
            user = st.text_input("Username", value=os.getenv("DB_USER", "root"))
            pwd = st.text_input(
                "Password", value=os.getenv("DB_PASSWORD", ""), type="password",
                placeholder="Enter your MySQL password",
            )
            with st.expander("⚙️ Advanced connection settings"):
                host = st.text_input("Host", value=os.getenv("DB_HOST", "localhost"))
                port = st.number_input("Port", min_value=1, max_value=65535,
                                       value=int(os.getenv("DB_PORT", "3306")))
                dbname = st.text_input("Database", value=os.getenv("DB_NAME", "lab_equipment_db"))
            go = st.form_submit_button("🔓  Connect", type="primary")
        st.caption("For a shared deployment, use environment variables/secrets rather than hardcoding passwords.")

        if go:
            try:
                test = mysql.connector.connect(
                    host=host, port=int(port), user=user, password=pwd, database=dbname,
                )
                test.close()
            except Error as exc:
                st.session_state["_login_error"] = (
                    "Could not connect. Check that MySQL is running, the SQL file has been imported, "
                    f"and your username, password and database name are correct.\n\nDetails: {exc}"
                )
                st.rerun()
            st.session_state["auth"] = {
                "host": host, "port": int(port), "user": user, "password": pwd, "database": dbname,
            }
            flash("success", "Connected successfully. Welcome!")
            st.rerun()


if not st.session_state.get("auth"):
    login_screen()
    st.stop()

_auth = st.session_state["auth"]
db_host, db_port, db_name = _auth["host"], _auth["port"], _auth["database"]
db_user, db_password = _auth["user"], _auth["password"]

# Show any message saved before the last st.rerun()
if "_flash" in st.session_state:
    _kind, _text = st.session_state.pop("_flash")
    notice(_kind, _text)

with st.sidebar:
    st.markdown(
        '<div class="side-title"><span class="ico">🗄️</span>Database connection</div>',
        unsafe_allow_html=True,
    )
    conn_status = st.empty()
    if not _auth.get("managed"):
        st.caption(f"Server: {db_host}:{db_port}")
        st.caption(f"User: {db_user}")
    if st.button("🚪  Log out"):
        st.session_state.pop("auth", None)
        st.rerun()


# ============================================================
# DATABASE LAYER  (unchanged)
# ============================================================
def get_connection():
    return mysql.connector.connect(
        host=db_host,
        port=int(db_port),
        user=db_user,
        password=db_password,
        database=db_name,
        autocommit=False,
    )


def query_df(sql, params=None):
    conn = get_connection()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


def query_rows(sql, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()


def issue_equipment(equipment_id, student_id, staff_id, expected_return):
    """Atomically checks and issues equipment to avoid two users borrowing it at once."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        conn.start_transaction()

        # Lock this equipment row while checking and updating its status.
        cur.execute(
            "SELECT Availability_Status FROM Equipment WHERE Equipment_ID=%s FOR UPDATE",
            (equipment_id,),
        )
        equipment = cur.fetchone()
        if not equipment:
            raise ValueError("That equipment item could not be found.")
        if equipment["Availability_Status"] != "Available":
            raise ValueError(
                f"This item is currently '{equipment['Availability_Status']}' and cannot be borrowed."
            )

        cur.execute(
            """
            INSERT INTO Equipment_Allocation
                (Equipment_ID, Student_ID, Staff_ID, Allocation_Date,
                 Expected_Return_Date, Allocation_Status)
            VALUES (%s, %s, %s, %s, %s, 'Issued')
            """,
            (equipment_id, student_id, staff_id, date.today(), expected_return),
        )
        cur.execute(
            "UPDATE Equipment SET Availability_Status='Issued' WHERE Equipment_ID=%s",
            (equipment_id,),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def return_equipment(allocation_id, return_condition, remarks):
    """Records a return and marks the equipment available in one transaction."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        conn.start_transaction()

        cur.execute(
            """
            SELECT a.Equipment_ID, a.Allocation_Status, r.Return_ID
            FROM Equipment_Allocation a
            LEFT JOIN Equipment_Return r ON r.Allocation_ID=a.Allocation_ID
            WHERE a.Allocation_ID=%s
            FOR UPDATE
            """,
            (allocation_id,),
        )
        allocation = cur.fetchone()
        if not allocation:
            raise ValueError("Allocation record not found.")
        if allocation["Return_ID"] is not None or allocation["Allocation_Status"] == "Returned":
            raise ValueError("This allocation has already been returned.")

        cur.execute(
            """
            INSERT INTO Equipment_Return
                (Allocation_ID, Return_Date, Return_Condition, Remarks)
            VALUES (%s, %s, %s, %s)
            """,
            (allocation_id, date.today(), return_condition, remarks.strip() or None),
        )
        cur.execute(
            "UPDATE Equipment_Allocation SET Allocation_Status='Returned' WHERE Allocation_ID=%s",
            (allocation_id,),
        )
        cur.execute(
            "SELECT Availability_Status FROM Equipment WHERE Equipment_ID=%s FOR UPDATE",
            (allocation["Equipment_ID"],),
        )
        current_status = cur.fetchone()
        if current_status and current_status["Availability_Status"] != "Under Maintenance":
            cur.execute(
                "UPDATE Equipment SET Availability_Status='Available' WHERE Equipment_ID=%s",
                (allocation["Equipment_ID"],),
            )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def show_db_error(error):
    conn_status.markdown(
        '<span class="conn-pill bad"><span class="dot"></span>Not connected</span>',
        unsafe_allow_html=True,
    )
    notice(
        "error",
        "Could not connect to or query MySQL. Check that MySQL is running, "
        "the SQL file has been imported, and the host, port, username, password, "
        f"and database name are correct.\n\nDetails: {error}",
    )


# ============================================================
# MAIN APP
# ============================================================
try:
    # Check connection and load reference data.
    labs = query_df("SELECT Lab_ID, Lab_Name, Location, Lab_Type FROM Lab ORDER BY Lab_Name")
    students = query_df(
        "SELECT Student_ID, Student_Name, Register_Number, Department "
        "FROM Student ORDER BY Student_Name"
    )
    staff = query_df(
        "SELECT Staff_ID, Staff_Name, Designation FROM Lab_Staff ORDER BY Staff_Name"
    )

    conn_status.markdown(
        f'<span class="conn-pill"><span class="dot"></span>Connected · {html.escape(str(db_name))}</span>',
        unsafe_allow_html=True,
    )

    if labs.empty:
        notice("warning", "No labs are in the database yet. Import the supplied SQL file with its sample data.")
        st.stop()

    # Dashboard metrics
    metrics = query_rows(
        """
        SELECT
          COUNT(*) AS total,
          COALESCE(SUM(Availability_Status='Available'), 0) AS available,
          COALESCE(SUM(Availability_Status='Issued'), 0) AS issued,
          COALESCE(SUM(Availability_Status='Under Maintenance'), 0) AS maintenance,
          COALESCE(SUM(Availability_Status='Retired'), 0) AS retired
        FROM Equipment
        """
    )[0]

    st.markdown(
        '<div class="stats">'
        + stat_card("🧰", "Total equipment", metrics["total"], "")
        + stat_card("✅", "Available", metrics["available"], "c-green")
        + stat_card("📤", "Issued / Busy", metrics["issued"], "c-amber")
        + stat_card("🛠️", "Under maintenance", metrics["maintenance"], "c-violet")
        + stat_card("📦", "Retired", metrics["retired"], "c-grey")
        + "</div>",
        unsafe_allow_html=True,
    )

    total = max(int(metrics["total"]), 1)
    segments = [
        ("Available", metrics["available"], "var(--green)"),
        ("Issued", metrics["issued"], "var(--amber)"),
        ("Maintenance", metrics["maintenance"], "var(--violet)"),
        ("Retired", metrics["retired"], "var(--grey)"),
    ]
    bar = "".join(
        f'<span title="{n}: {int(v)}" style="width:{int(v) / total * 100:.2f}%;background:{c}"></span>'
        for n, v, c in segments if int(v) > 0
    )
    legend = "".join(
        f'<span><i style="background:{c}"></i>{n} <b>{int(v)}</b> ({int(v) / total * 100:.0f}%)</span>'
        for n, v, c in segments
    )
    st.markdown(
        f'<div class="dist"><div class="dist-bar">{bar}</div><div class="dist-legend">{legend}</div></div>',
        unsafe_allow_html=True,
    )

    tab_inventory, tab_borrow, tab_return, tab_active, tab_lifecycle = st.tabs(
        ["🔎 Equipment explorer", "📤 Borrow equipment", "📥 Return equipment", "📋 Current loans", "🛠️ Maintenance & retirement"]
    )

    # ---------------------------------------------------------- Explorer
    with tab_inventory:
        section("Equipment by lab", "Filter by lab, status, or search across every column.")
        lab_options = {"All labs": None}
        lab_options.update({
            row["Lab_Name"]: int(row["Lab_ID"])
            for _, row in labs.iterrows()
        })
        status_options = ["All statuses", "Available", "Issued", "Under Maintenance", "Retired"]

        f1, f2 = st.columns(2)
        with f1:
            chosen_lab_name = st.selectbox("Choose a lab", list(lab_options.keys()), key="inventory_lab")
        with f2:
            chosen_status = st.selectbox("Availability", status_options)
        search = st.text_input(
            "Search equipment name, serial number, category, or status",
            placeholder="Type to search…",
        )

        inventory_sql = """
            SELECT e.Equipment_ID, e.Equipment_Name, l.Lab_Name, l.Location,
                   c.Category_Name, e.Serial_Number, e.Equipment_Condition,
                   e.Availability_Status,
                   active.Student_Name AS Borrowed_By,
                   active.Register_Number AS Borrower_Register
            FROM Equipment e
            JOIN Lab l ON l.Lab_ID=e.Lab_ID
            JOIN Equipment_Category c ON c.Category_ID=e.Category_ID
            LEFT JOIN (
                SELECT a.Equipment_ID, s.Student_Name, s.Register_Number
                FROM Equipment_Allocation a
                JOIN Student s ON s.Student_ID=a.Student_ID
                LEFT JOIN Equipment_Return r ON r.Allocation_ID=a.Allocation_ID
                WHERE r.Return_ID IS NULL AND a.Allocation_Status IN ('Issued','Overdue')
            ) active ON active.Equipment_ID=e.Equipment_ID
            WHERE 1=1
        """
        params = []
        if lab_options[chosen_lab_name] is not None:
            inventory_sql += " AND e.Lab_ID=%s"
            params.append(lab_options[chosen_lab_name])
        if chosen_status != "All statuses":
            inventory_sql += " AND e.Availability_Status=%s"
            params.append(chosen_status)
        inventory_sql += " ORDER BY l.Lab_Name, e.Equipment_Name"

        inventory = query_df(inventory_sql, tuple(params))
        if search.strip():
            mask = inventory.astype(str).apply(
                lambda col: col.str.contains(search.strip(), case=False, na=False, regex=False)
            ).any(axis=1)
            inventory = inventory[mask]

        st.caption("Items marked Issued are busy. Borrower details are shown when an active allocation exists.")
        if inventory.empty:
            notice("info", "No equipment matches these filters.")
        else:
            render_table(inventory)

        with st.expander("📍 View lab locations"):
            render_table(labs)

    # ---------------------------------------------------------- Borrow
    with tab_borrow:
        section("Borrow an equipment item", "Issue an available item to a student.")
        notice("info", "Only items marked Available can be issued. The database is checked again when you submit.")
        available_items = query_df(
            """
            SELECT e.Equipment_ID, e.Equipment_Name, e.Serial_Number, l.Lab_Name
            FROM Equipment e JOIN Lab l ON l.Lab_ID=e.Lab_ID
            WHERE e.Availability_Status='Available'
            ORDER BY l.Lab_Name, e.Equipment_Name
            """
        )

        if students.empty or staff.empty:
            notice("warning", "Add at least one student and one lab staff member before issuing equipment.")
        elif available_items.empty:
            notice("warning", "There is currently no available equipment to borrow.")
        else:
            student_labels = {
                f'{row.Student_Name} ({row.Register_Number})': int(row.Student_ID)
                for row in students.itertuples()
            }
            staff_labels = {
                f'{row.Staff_Name} — {row.Designation}': int(row.Staff_ID)
                for row in staff.itertuples()
            }
            equipment_labels = {
                f'{row.Equipment_Name} | {row.Lab_Name} | {row.Serial_Number}': int(row.Equipment_ID)
                for row in available_items.itertuples()
            }

            with st.form("borrow_form"):
                b1, b2 = st.columns(2)
                with b1:
                    selected_student = st.selectbox("Student borrowing the item", list(student_labels.keys()))
                    selected_staff = st.selectbox("Issuing staff member", list(staff_labels.keys()))
                with b2:
                    selected_equipment = st.selectbox("Equipment (available only)", list(equipment_labels.keys()))
                    expected_return = st.date_input(
                        "Expected return date",
                        value=date.today() + timedelta(days=7),
                        min_value=date.today(),
                    )
                submitted = st.form_submit_button("📤  Confirm borrow", type="primary")

            if submitted:
                try:
                    issue_equipment(
                        equipment_labels[selected_equipment],
                        student_labels[selected_student],
                        staff_labels[selected_staff],
                        expected_return,
                    )
                    flash("success", "Equipment issued successfully. Its status is now Issued / Busy.")
                    st.rerun()
                except ValueError as exc:
                    notice("warning", str(exc))
                except Error as exc:
                    notice("error", f"Could not issue equipment: {exc}")

    # ---------------------------------------------------------- Return
    with tab_return:
        section("Return borrowed equipment", "Record a returned item and its condition.")
        active_loans = query_df(
            """
            SELECT a.Allocation_ID, e.Equipment_Name, e.Serial_Number,
                   l.Lab_Name, s.Student_Name, s.Register_Number,
                   a.Allocation_Date, a.Expected_Return_Date, a.Allocation_Status
            FROM Equipment_Allocation a
            JOIN Equipment e ON e.Equipment_ID=a.Equipment_ID
            JOIN Lab l ON l.Lab_ID=e.Lab_ID
            JOIN Student s ON s.Student_ID=a.Student_ID
            LEFT JOIN Equipment_Return r ON r.Allocation_ID=a.Allocation_ID
            WHERE r.Return_ID IS NULL AND a.Allocation_Status IN ('Issued','Overdue')
            ORDER BY a.Expected_Return_Date
            """
        )

        if active_loans.empty:
            notice("success", "There are no active loans to return.")
        else:
            render_table(active_loans)
            loan_labels = {
                f'#{row.Allocation_ID} — {row.Equipment_Name} — {row.Student_Name} ({row.Register_Number})':
                    int(row.Allocation_ID)
                for row in active_loans.itertuples()
            }
            with st.form("return_form"):
                selected_loan = st.selectbox("Select the item being returned", list(loan_labels.keys()))
                r1, r2 = st.columns([1, 2])
                with r1:
                    return_condition = st.selectbox("Condition on return", ["Good", "New", "Fair", "Poor"])
                with r2:
                    remarks = st.text_input("Remarks (optional)", placeholder="e.g. Returned with all accessories")
                return_submitted = st.form_submit_button("📥  Confirm return", type="primary")

            if return_submitted:
                try:
                    return_equipment(loan_labels[selected_loan], return_condition, remarks)
                    flash("success", "Return recorded. The equipment is now marked Available.")
                    st.rerun()
                except ValueError as exc:
                    notice("warning", str(exc))
                except Error as exc:
                    notice("error", f"Could not record return: {exc}")

    # ---------------------------------------------------------- Current loans
    with tab_active:
        section("Current loans", "Everything that is out right now, with overdue days highlighted.")
        current_loans = query_df(
            """
            SELECT a.Allocation_ID, e.Equipment_Name, l.Lab_Name,
                   s.Student_Name, s.Register_Number, s.Department,
                   st.Staff_Name AS Issued_By,
                   a.Allocation_Date, a.Expected_Return_Date,
                   CASE WHEN a.Expected_Return_Date < CURDATE() THEN 'Overdue'
                        ELSE a.Allocation_Status END AS Current_Status,
                   GREATEST(DATEDIFF(CURDATE(), a.Expected_Return_Date), 0) AS Days_Past_Due
            FROM Equipment_Allocation a
            JOIN Equipment e ON e.Equipment_ID=a.Equipment_ID
            JOIN Lab l ON l.Lab_ID=e.Lab_ID
            JOIN Student s ON s.Student_ID=a.Student_ID
            JOIN Lab_Staff st ON st.Staff_ID=a.Staff_ID
            LEFT JOIN Equipment_Return r ON r.Allocation_ID=a.Allocation_ID
            WHERE r.Return_ID IS NULL AND a.Allocation_Status IN ('Issued','Overdue')
            ORDER BY a.Expected_Return_Date
            """
        )
        if current_loans.empty:
            notice("success", "No equipment is currently on loan.")
        else:
            render_table(current_loans)
            st.download_button(
                "⬇️  Download current loans as CSV",
                data=current_loans.to_csv(index=False).encode("utf-8"),
                file_name="current_lab_equipment_loans.csv",
                mime="text/csv",
            )

    # ---------------------------------------------------------- Lifecycle
    with tab_lifecycle:
        section(
            "Maintenance and retirement",
            "Send equipment for maintenance, make repaired or retired equipment available again, or retire it.",
        )

        lifecycle_items = query_df("""
            SELECT e.Equipment_ID, e.Equipment_Name, e.Serial_Number,
                   l.Lab_Name, e.Equipment_Condition, e.Availability_Status
            FROM Equipment e
            JOIN Lab l ON l.Lab_ID = e.Lab_ID
            ORDER BY l.Lab_Name, e.Equipment_Name
        """)
        render_table(lifecycle_items)

        eligible = lifecycle_items
        if eligible.empty:
            notice("info", "There is no equipment to manage.")
        else:
            item_options = {
                f"{r.Equipment_Name} | {r.Lab_Name} | {r.Serial_Number} | {r.Availability_Status}": int(r.Equipment_ID)
                for r in eligible.itertuples()
            }
            with st.form("lifecycle_form"):
                l1, l2 = st.columns(2)
                with l1:
                    chosen_item = st.selectbox("Select equipment", list(item_options.keys()))
                with l2:
                    action = st.selectbox("Choose action", [
                        "Mark Under Maintenance",
                        "Maintenance Completed — Make Available",
                        "Retire Permanently",
                        "Reactivate Retired — Make Available",
                    ])
                confirm = st.checkbox("I confirm this status change.")
                apply_action = st.form_submit_button("⚙️  Apply status change", type="primary")

            if apply_action:
                equipment_id = item_options[chosen_item]
                target_status = {
                    "Mark Under Maintenance": "Under Maintenance",
                    "Maintenance Completed — Make Available": "Available",
                    "Retire Permanently": "Retired",
                    "Reactivate Retired — Make Available": "Available",
                }[action]
                conn = None
                try:
                    conn = get_connection()
                    cur = conn.cursor(dictionary=True)
                    conn.start_transaction()
                    cur.execute("SELECT Availability_Status FROM Equipment WHERE Equipment_ID=%s FOR UPDATE", (equipment_id,))
                    item = cur.fetchone()
                    if not item:
                        raise ValueError("Equipment not found.")
                    current_status = item["Availability_Status"]
                    cur.execute("""
                        SELECT COUNT(*) AS active_count
                        FROM Equipment_Allocation a
                        LEFT JOIN Equipment_Return r ON r.Allocation_ID=a.Allocation_ID
                        WHERE a.Equipment_ID=%s AND r.Return_ID IS NULL
                          AND a.Allocation_Status IN ('Issued','Overdue')
                    """, (equipment_id,))
                    has_active_loan = cur.fetchone()["active_count"] > 0

                    if not confirm:
                        raise ValueError("Please tick the confirmation box first.")
                    if action == "Reactivate Retired — Make Available":
                        if current_status != "Retired":
                            raise ValueError("This item is not retired.")
                    elif current_status == "Retired":
                        raise ValueError(
                            "This equipment is retired. Choose 'Reactivate Retired — Make Available' to bring it back."
                        )
                    if has_active_loan:
                        raise ValueError("This equipment has an active loan. Record its return before changing its status.")
                    if action == "Mark Under Maintenance" and current_status != "Available":
                        raise ValueError("Only Available equipment can be sent for maintenance.")
                    if action == "Maintenance Completed — Make Available" and current_status != "Under Maintenance":
                        raise ValueError("This item is not marked Under Maintenance.")
                    if action == "Retire Permanently" and current_status not in ("Available", "Under Maintenance"):
                        raise ValueError("Only Available or Under Maintenance equipment can be retired.")

                    cur.execute("UPDATE Equipment SET Availability_Status=%s WHERE Equipment_ID=%s", (target_status, equipment_id))
                    conn.commit()
                    if target_status == "Under Maintenance":
                        flash("success", "Equipment marked Under Maintenance. It cannot be borrowed.")
                    elif action == "Reactivate Retired — Make Available":
                        flash("success", "Retired equipment reactivated. It is now Available for borrowing.")
                    elif target_status == "Available":
                        flash("success", "Maintenance completed. Equipment is now Available for borrowing.")
                    else:
                        flash("success", "Equipment retired permanently. It will no longer be available for borrowing.")
                    st.rerun()
                except ValueError as exc:
                    if conn:
                        conn.rollback()
                    notice("warning", str(exc))
                except Error as exc:
                    if conn:
                        conn.rollback()
                    notice("error", f"Could not update equipment status: {exc}")
                finally:
                    if conn:
                        conn.close()

except Error as exc:
    show_db_error(exc)
except Exception as exc:
    notice("error", f"Something went wrong: {exc}")
    st.caption("Check the setup steps and ensure the SQL file has been imported into MySQL.")
