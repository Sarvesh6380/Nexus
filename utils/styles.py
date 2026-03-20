"""
utils/styles.py — Nexus dark UI theme.
Fonts: Syne (headings) + DM Sans (body) + DM Mono (code)
Palette: Deep dark navy base · Coral/Amber accents · Teal/Violet highlights
"""

NEXUS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');

:root {
    --bg:           #0d0f14;
    --bg2:          #13161f;
    --surface:      #161a24;
    --surface2:     #1c2030;
    --navy:         #1f2537;
    --navy2:        #252d42;
    --coral:        #ff6b47;
    --coral-dim:    rgba(255,107,71,0.12);
    --amber:        #f5a623;
    --amber-dim:    rgba(245,166,35,0.12);
    --teal:         #00b894;
    --teal-dim:     rgba(0,184,148,0.12);
    --violet:       #7c6fff;
    --violet-dim:   rgba(124,111,255,0.12);
    --text:         #e8eaf0;
    --text2:        #9ba3b8;
    --text3:        #5a6278;
    --border:       #1e2538;
    --border2:      #2e3750;
    --shadow:       0 2px 12px rgba(0,0,0,0.4);
    --shadow-lg:    0 8px 32px rgba(0,0,0,0.55);
    --radius:       14px;
    --radius-sm:    8px;
    --font:         'DM Sans', sans-serif;
    --font-head:    'Syne', sans-serif;
    --font-mono:    'DM Mono', monospace;
}

/* ── Global ── */
html, body, [class*="css"] {
    font-family: var(--font) !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.2rem !important; padding-bottom: 2rem !important; max-width: 1200px !important; }

/* ── Background glow ── */
.stApp {
    background-image:
        radial-gradient(circle at 15% 15%, rgba(255,107,71,0.05) 0%, transparent 45%),
        radial-gradient(circle at 85% 85%, rgba(124,111,255,0.05) 0%, transparent 45%) !important;
}

/* ── App Header ── */
.nexus-header {
    display: flex; align-items: center; gap: 12px;
    padding: 1rem 1.4rem;
    background: linear-gradient(135deg, #1a1f2e 0%, #1f2537 100%);
    border: 1px solid var(--border2);
    border-radius: var(--radius);
    margin-bottom: 1.2rem;
    box-shadow: var(--shadow-lg);
    position: relative; overflow: hidden;
}
.nexus-header::before {
    content: ''; position: absolute; top: -50px; right: -30px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(255,107,71,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.nexus-logo-wrap {
    width: 40px; height: 40px; flex-shrink: 0;
    background: linear-gradient(135deg, var(--coral), var(--amber));
    border-radius: 10px; display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; box-shadow: 0 4px 14px rgba(255,107,71,0.4);
}
.nexus-title {
    font-family: var(--font-head) !important; font-size: 1.4rem !important;
    font-weight: 800 !important; color: #fff !important;
    margin: 0 !important; letter-spacing: -0.02em;
}
.nexus-subtitle { font-size: 0.74rem !important; color: rgba(255,255,255,0.38) !important; margin: 0 !important; }

/* ── Section labels ── */
.section-label {
    font-size: 0.67rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--text3);
    margin: 1.3rem 0 0.55rem; display: flex; align-items: center; gap: 6px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); margin-left: 6px; }

/* ── Stat cards ── */
.stat-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.2rem 1rem; text-align: center;
    position: relative; overflow: hidden;
    box-shadow: var(--shadow); transition: transform 0.2s, box-shadow 0.2s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
.stat-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.stat-card.coral::before  { background: linear-gradient(90deg, var(--coral), var(--amber)); }
.stat-card.violet::before { background: linear-gradient(90deg, var(--violet), #a29bfe); }
.stat-card.teal::before   { background: linear-gradient(90deg, var(--teal), #00cec9); }
.stat-card.amber::before  { background: linear-gradient(90deg, var(--amber), #fdcb6e); }
.stat-number { font-family: var(--font-head) !important; font-size: 2.2rem; font-weight: 800; line-height: 1; margin-bottom: 4px; }
.stat-label  { font-size: 0.67rem; color: var(--text3); font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; }

/* ── Chat ── */
.chat-wrap {
    display: flex; flex-direction: column; gap: 12px;
    max-height: 440px; overflow-y: auto; padding: 1.2rem;
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: var(--radius); margin-bottom: 0.8rem;
}
.bubble { padding: 0.8rem 1rem; border-radius: 12px; font-size: 0.88rem; line-height: 1.6; max-width: 80%; animation: bubblePop 0.2s ease; }
.bubble-user      { align-self: flex-end; background: linear-gradient(135deg,#2a3a6e,#1e2d5a); color: #cce0ff; border: 1px solid #3a4f8a; border-bottom-right-radius: 3px; }
.bubble-assistant { align-self: flex-start; background: var(--surface); color: var(--text); border: 1px solid var(--border2); border-bottom-left-radius: 3px; box-shadow: var(--shadow); }
.bubble-role { font-size: 0.63rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.45; margin-bottom: 5px; }
.chat-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 160px; color: var(--text3); text-align: center; gap: 8px; }
.chat-empty-icon { width: 46px; height: 46px; background: var(--coral-dim); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; }
@keyframes bubblePop { from { opacity: 0; transform: scale(0.95) translateY(4px); } to { opacity: 1; transform: scale(1) translateY(0); } }

/* ── Conflict banner ── */
.conflict-banner {
    background: linear-gradient(135deg,#2d1f0a,#3d2810);
    border: 1.5px solid var(--amber); border-radius: var(--radius);
    padding: 1rem 1.2rem; margin: 0.8rem 0; font-size: 0.87rem; color: #fbd38d;
    position: relative;
}
.conflict-banner strong { color: var(--amber); }

/* ── Timeline cards ── */
.timeline-wrap { display: flex; flex-direction: column; gap: 7px; margin-top: 0.4rem; }
.timeline-card {
    background: var(--surface); border: 1px solid var(--border);
    border-left: 4px solid var(--border2); border-radius: var(--radius-sm);
    padding: 0.7rem 1rem; font-size: 0.84rem; color: var(--text);
    box-shadow: var(--shadow); transition: transform 0.15s;
}
.timeline-card:hover { transform: translateX(3px); }
.timeline-card.decision { border-left-color: var(--violet); }
.timeline-card.task     { border-left-color: var(--teal);   }
.timeline-card.role     { border-left-color: var(--coral);  }
.timeline-card.blocker  { border-left-color: #e74c3c;       }
.timeline-card.general  { border-left-color: var(--text3);  }
.timeline-meta { font-size: 0.69rem; color: var(--text3); font-family: var(--font-mono); margin-top: 5px; }

/* ── Badges ── */
.badge { display: inline-block; font-size: 0.59rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; padding: 2px 7px; border-radius: 20px; margin-right: 5px; }
.badge-decision { background: var(--violet-dim); color: #a29bfe; }
.badge-task     { background: var(--teal-dim);   color: var(--teal); }
.badge-role     { background: var(--coral-dim);  color: var(--coral); }
.badge-blocker  { background: rgba(231,76,60,0.15); color: #ff7675; }
.badge-general  { background: rgba(90,98,120,0.2);  color: var(--text3); }

/* ── Member pills ── */
.member-pill { display: inline-flex; align-items: center; gap: 5px; background: var(--navy); border: 1px solid var(--border2); border-radius: 20px; padding: 4px 10px; font-size: 0.74rem; color: var(--text2); margin: 3px; font-weight: 500; }
.member-pill.leader { background: rgba(245,166,35,0.12); border-color: rgba(245,166,35,0.3); color: #fbd38d; }
.role-tag { background: rgba(255,255,255,0.07); color: var(--text2); border-radius: 4px; padding: 2px 7px; font-size: 0.67rem; font-weight: 600; }

/* ── Team cards ── */
.team-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.1rem; box-shadow: var(--shadow); margin-bottom: 10px; transition: box-shadow 0.2s, border-color 0.2s; }
.team-card:hover { box-shadow: var(--shadow-lg); border-color: var(--border2); }
.team-name    { font-family: var(--font-head) !important; font-size: 1.02rem; font-weight: 700; color: var(--text); }
.team-project { font-size: 0.77rem; color: var(--text3); margin-top: 2px; }

/* ── Log entries ── */
.log-entry { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 0.7rem 0.95rem; margin-bottom: 5px; font-size: 0.83rem; display: flex; gap: 10px; align-items: flex-start; transition: background 0.15s; }
.log-entry:hover { background: var(--surface2); border-color: var(--border2); }
.log-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 5px; flex-shrink: 0; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #080b11 !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.75) !important; }
[data-testid="stSidebar"] .stTextArea textarea,
[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 7px !important; color: rgba(255,255,255,0.85) !important; font-family: var(--font) !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.09) !important; color: rgba(255,255,255,0.85) !important;
}
.sidebar-section-label { font-size: 0.6rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(255,255,255,0.22); margin: 1.1rem 0 0.4rem; padding-bottom: 0.35rem; border-bottom: 1px solid rgba(255,255,255,0.06); }
.sidebar-user-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 9px; padding: 0.7rem 0.9rem; margin-bottom: 0.5rem; }

/* ── Sidebar buttons ── */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important; border: 1px solid rgba(255,255,255,0.07) !important;
    color: rgba(255,255,255,0.5) !important; border-radius: 7px !important;
    font-size: 0.85rem !important; font-weight: 400 !important;
    padding: 0.5rem 0.85rem !important; text-align: left !important;
    width: 100% !important; margin-bottom: 2px !important; box-shadow: none !important;
    transition: all 0.2s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.07) !important; color: rgba(255,255,255,0.9) !important;
    border-color: rgba(255,107,71,0.35) !important; border-left: 2px solid var(--coral) !important;
    transform: none !important; box-shadow: none !important;
}

/* ── Main buttons ── */
.stButton > button {
    background: var(--surface2) !important; color: var(--text) !important;
    border: 1px solid var(--border2) !important; border-radius: var(--radius-sm) !important;
    font-weight: 500 !important; font-family: var(--font) !important; transition: all 0.2s !important;
}
.stButton > button:hover {
    background: var(--navy2) !important; border-color: var(--coral) !important;
    color: white !important; transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(255,107,71,0.18) !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {
    background: var(--surface) !important; border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important; color: var(--text) !important; font-family: var(--font) !important;
    transition: border-color 0.2s !important;
}
.stTextInput input:focus, .stTextArea textarea:focus { border-color: var(--coral) !important; box-shadow: 0 0 0 3px rgba(255,107,71,0.1) !important; }
.stSelectbox > div > div { background: var(--surface) !important; border: 1.5px solid var(--border) !important; border-radius: var(--radius-sm) !important; color: var(--text) !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background: var(--surface) !important; border-radius: 10px !important; padding: 4px !important; border: 1px solid var(--border) !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; border-radius: 7px !important; color: var(--text3) !important; font-weight: 500 !important; font-family: var(--font) !important; font-size: 0.84rem !important; padding: 0.45rem 1rem !important; }
.stTabs [aria-selected="true"] { background: var(--navy2) !important; color: var(--text) !important; font-weight: 600 !important; box-shadow: var(--shadow) !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 1rem 0 0 !important; }

/* ── Expander ── */
.streamlit-expanderHeader { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-sm) !important; font-weight: 600 !important; color: var(--text) !important; }
.streamlit-expanderContent { background: var(--bg2) !important; border: 1px solid var(--border) !important; border-top: none !important; }

/* ── Alerts ── */
.stSuccess { background: var(--teal-dim) !important; border-color: var(--teal) !important; color: var(--teal) !important; border-radius: var(--radius-sm) !important; }
.stWarning { background: var(--amber-dim) !important; border-color: var(--amber) !important; border-radius: var(--radius-sm) !important; }
.stError   { background: rgba(231,76,60,0.1) !important; border-color: #e74c3c !important; border-radius: var(--radius-sm) !important; }
.stInfo    { background: var(--violet-dim) !important; border-color: var(--violet) !important; border-radius: var(--radius-sm) !important; }

/* ── Misc ── */
hr { border-color: var(--border) !important; margin: 1.1rem 0 !important; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 10px; }

/* ── Animations ── */
@keyframes fadeSlideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.fade-in { animation: fadeSlideUp 0.3s ease forwards; }
</style>
"""
