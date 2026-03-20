"""utils/styles.py — Nexus Corporate Dark Theme"""

NEXUS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

/* ── RESET — targeted only, never global button/span ── */
body { font-family: 'Inter', sans-serif !important; -webkit-font-smoothing: antialiased !important; }

/* ── HIDE STREAMLIT CHROME — but NOT header (collapse button lives there) ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }

/* ── APP BACKGROUND ── */
.stApp { background-color: #0b0d12 !important; }
.main .block-container { background-color: #0b0d12; padding: 0.8rem 1.4rem 2rem !important; }

/* ── MAIN CONTENT TEXT ── */
.main p, .main div, .main span, .main label { color: #dde2ee; font-family: 'Inter', sans-serif !important; }

/* ── MAIN BUTTONS only (not sidebar, not header) ── */
.main .stButton > button {
    background: #181d2a !important;
    border: 1.5px solid #2e3a55 !important;
    outline: none !important;
    color: #c8d0e7 !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 0.84rem !important;
    letter-spacing: 0.01em !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.45rem 1rem !important;
    transition:
        background    0.25s cubic-bezier(0.4, 0, 0.2, 1),
        border-color  0.25s cubic-bezier(0.4, 0, 0.2, 1),
        color         0.25s cubic-bezier(0.4, 0, 0.2, 1),
        box-shadow    0.25s cubic-bezier(0.4, 0, 0.2, 1),
        transform     0.2s  cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04),
                0 1px 4px rgba(0,0,0,0.35) !important;
}
.main .stButton > button:hover {
    background: #1e2538 !important;
    border-color: #ff6b47 !important;
    color: #ffffff !important;
    box-shadow: 0 0 0 3px rgba(255,107,71,0.15),
                inset 0 1px 0 rgba(255,255,255,0.06),
                0 4px 12px rgba(0,0,0,0.4) !important;
    transform: translateY(-2px) !important;
}
.main .stButton > button:active {
    background: #232b42 !important;
    border-color: #ff6b47 !important;
    color: #ffffff !important;
    transform: translateY(0px) scale(0.98) !important;
    box-shadow: 0 0 0 3px rgba(255,107,71,0.25),
                inset 0 2px 4px rgba(0,0,0,0.3) !important;
    transition:
        transform  0.1s cubic-bezier(0.4, 0, 0.2, 1),
        box-shadow 0.1s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.main .stButton > button:focus-visible {
    border-color: #ff6b47 !important;
    box-shadow: 0 0 0 3px rgba(255,107,71,0.2) !important;
    outline: none !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #13161e !important;
    border: 1px solid #1e2436 !important;
    border-radius: 6px !important;
    color: #dde2ee !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    transition: border-color 0.15s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #ff6b47 !important;
    box-shadow: 0 0 0 2px rgba(255,107,71,0.1) !important;
    outline: none !important;
}

/* ── SELECTBOX ── */
.stSelectbox > div > div {
    background: #13161e !important;
    border: 1px solid #1e2436 !important;
    border-radius: 6px !important;
    color: #dde2ee !important;
    font-size: 0.85rem !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0f1117 !important;
    border-radius: 7px !important;
    padding: 3px !important;
    border: 1px solid #1a2030 !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 5px !important;
    color: #4a5270 !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    padding: 0.42rem 0.85rem !important;
    transition: all 0.15s ease !important;
    font-family: 'Inter', sans-serif !important;
}
.stTabs [aria-selected="true"] {
    background: #181d2a !important;
    color: #dde2ee !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 0.8rem 0 0 !important; }

/* ── ALERTS ── */
.stSuccess > div { background: rgba(0,200,150,0.08)  !important; border-color: #00c896 !important; color: #00c896 !important; border-radius: 6px !important; }
.stWarning > div { background: rgba(245,166,35,0.08) !important; border-color: #f5a623 !important; color: #f5a623 !important; border-radius: 6px !important; }
.stError   > div { background: rgba(255,79,79,0.08)  !important; border-color: #ff4f4f !important; border-radius: 6px !important; }
.stInfo    > div { background: rgba(124,111,255,0.08) !important; border-color: #7c6fff !important; border-radius: 6px !important; }

/* ── EXPANDER ── */
details > summary {
    background: #13161e !important;
    border: 1px solid #1e2436 !important;
    border-radius: 6px !important;
    color: #dde2ee !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── DIVIDER & SCROLLBAR ── */
hr { border-color: #1a2030 !important; margin: 1rem 0 !important; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #252d42; border-radius: 4px; }

/* ── SECTION LABELS ── */
.nx-sec {
    font-size: 0.62rem; font-weight: 600; letter-spacing: 0.09em;
    text-transform: uppercase; color: #384060;
    font-family: 'Inter', sans-serif;
    display: flex; align-items: center; gap: 6px;
    margin: 1.2rem 0 0.6rem;
}
.nx-sec::after { content: ''; flex: 1; height: 1px; background: #1a2030; }

/* ── CHAT ── */
.nx-chat-wrap {
    display: flex; flex-direction: column; gap: 10px;
    max-height: 420px; overflow-y: auto; padding: 1rem;
    background: #0d0f16; border: 1px solid #1a2030;
    border-radius: 8px; margin-bottom: 0.7rem;
}
.nx-bubble { padding: 0.75rem 1rem; border-radius: 10px; font-size: 0.85rem; line-height: 1.65; max-width: 80%; font-family: 'Inter', sans-serif; }
.nx-bubble.user { align-self: flex-end; background: linear-gradient(135deg,#1c2b56,#141e40); border: 1px solid #253270; color: #bdd0ff; border-bottom-right-radius: 3px; }
.nx-bubble.ai   { align-self: flex-start; background: #12151e; border: 1px solid #1e2436; color: #dde2ee; border-bottom-left-radius: 3px; }
.nx-bubble-who  { font-size: 0.6rem; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase; opacity: 0.4; margin-bottom: 5px; }
.nx-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 150px; color: #384060; text-align: center; gap: 6px; }

/* ── TIMELINE ── */
.nx-tl { background: #12151e; border: 1px solid #1a2030; border-left: 2px solid #252d42; border-radius: 6px; padding: 0.65rem 0.9rem; font-size: 0.83rem; margin-bottom: 5px; transition: transform 0.15s ease; color: #c8d0e7; }
.nx-tl:hover { transform: translateX(2px); }
.nx-tl.decision { border-left-color: #7c6fff; }
.nx-tl.task     { border-left-color: #00c896; }
.nx-tl.role     { border-left-color: #ff6b47; }
.nx-tl.blocker  { border-left-color: #ff4f4f; }
.nx-tl.general  { border-left-color: #384060; }
.nx-tl-meta { font-size: 0.65rem; color: #384060; font-family: 'IBM Plex Mono', monospace; margin-top: 5px; }

/* ── BADGES ── */
.nx-badge { display: inline-block; font-size: 0.57rem; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase; padding: 2px 7px; border-radius: 4px; margin-right: 5px; font-family: 'Inter', sans-serif; }
.nx-badge.decision { background: rgba(124,111,255,0.14); color: #a29bfe; }
.nx-badge.task     { background: rgba(0,200,150,0.12);   color: #00c896; }
.nx-badge.role     { background: rgba(255,107,71,0.12);  color: #ff8a70; }
.nx-badge.blocker  { background: rgba(255,79,79,0.12);   color: #ff6b6b; }
.nx-badge.general  { background: rgba(56,64,96,0.4);     color: #5a6480; }

/* ── LOG ENTRIES ── */
.nx-log { background: #12151e; border: 1px solid #1a2030; border-radius: 6px; padding: 0.6rem 0.85rem; margin-bottom: 5px; display: flex; gap: 9px; font-size: 0.82rem; transition: background 0.15s ease; color: #c8d0e7; }
.nx-log:hover { background: #161b28; }
.nx-dot { width: 6px; height: 6px; border-radius: 50%; margin-top: 6px; flex-shrink: 0; }

/* ── MEMBER PILLS ── */
.nx-member { display: inline-flex; align-items: center; gap: 5px; background: #161b28; border: 1px solid #1e2740; border-radius: 4px; padding: 3px 9px; font-size: 0.72rem; color: #6e7a9a; margin: 3px; font-family: 'Inter', sans-serif; }
.nx-member.leader { background: rgba(245,166,35,0.08); border-color: rgba(245,166,35,0.22); color: #f0c070; }

/* ── CONFLICT ── */
.nx-conflict { background: rgba(245,166,35,0.06); border: 1px solid rgba(245,166,35,0.3); border-left: 3px solid #f5a623; border-radius: 6px; padding: 0.85rem 1rem; margin: 0.7rem 0; font-size: 0.83rem; color: #e0b96a; font-family: 'Inter', sans-serif; }
.nx-conflict strong { color: #f5a623; }

/* ── ANIMATIONS ── */
@keyframes fadeUp { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
.fade-in { animation: fadeUp 0.25s ease forwards; }
</style>
"""
