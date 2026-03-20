"""
NEXUS — AI Group Project Manager
Run: streamlit run app.py
"""
import datetime
import streamlit as st

from config import (
    GROQ_API_KEY, HINDSIGHT_API_KEY, HINDSIGHT_API_URL,
    HINDSIGHT_BANK_ID, GROQ_MODEL, VALID_CATEGORIES, VALID_CATS_SET,
    SUPABASE_URL, SUPABASE_KEY,
)
from utils.styles import NEXUS_CSS
from utils.hindsight_helper import hs_retain, hs_recall, hs_recent, parse_memory_meta
from utils.groq_agent import detect_conflict, chat_with_nexus

# ── Page config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(NEXUS_CSS, unsafe_allow_html=True)

# ── Sidebar styling ──
st.markdown("""
<style>
/* Sidebar background */
[data-testid="stSidebar"] { background-color: #080a0e !important; }
[data-testid="stSidebar"] > div:first-child { background-color: #080a0e !important; }

/* Nav buttons in sidebar — fixed position, dim to bright on hover */
[data-testid="stSidebar"] .stButton > button {
    position: relative !important;
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-left: 2px solid transparent !important;
    border-radius: 6px !important;
    color: rgba(255,255,255,0.35) !important;
    font-size: 0.84rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.01em !important;
    padding: 0.52rem 0.9rem !important;
    width: 100% !important;
    text-align: left !important;
    margin-bottom: 3px !important;
    box-shadow: none !important;
    overflow: hidden !important;
    transform: none !important;
    /* Only fade color, background, border — NO position/padding movement */
    transition:
        color            0.3s cubic-bezier(0.4, 0, 0.2, 1),
        background       0.3s cubic-bezier(0.4, 0, 0.2, 1),
        border-color     0.3s cubic-bezier(0.4, 0, 0.2, 1),
        border-left-color 0.3s cubic-bezier(0.4, 0, 0.2, 1),
        box-shadow       0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Shimmer sweep on hover */
[data-testid="stSidebar"] .stButton > button::before {
    content: "" !important;
    position: absolute !important;
    inset: 0 !important;
    background: linear-gradient(
        105deg,
        transparent 40%,
        rgba(255,107,71,0.07) 50%,
        transparent 60%
    ) !important;
    background-size: 200% 100% !important;
    background-position: 200% 0 !important;
    transition: background-position 0.55s cubic-bezier(0.4, 0, 0.2, 1) !important;
    pointer-events: none !important;
    border-radius: 6px !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.05) !important;
    border-color: rgba(255,107,71,0.4) !important;
    border-left: 2px solid #ff6b47 !important;
    color: rgba(255,255,255,0.92) !important;
    padding: 0.52rem 0.9rem !important;
    box-shadow: inset 0 0 14px rgba(255,107,71,0.05) !important;
    transform: none !important;
}

[data-testid="stSidebar"] .stButton > button:hover::before {
    background-position: -200% 0 !important;
}

[data-testid="stSidebar"] .stButton > button:active {
    background: rgba(255,107,71,0.1) !important;
    border-color: rgba(255,107,71,0.55) !important;
    border-left: 2px solid #ff6b47 !important;
    color: #ffcfc4 !important;
    transform: none !important;
    transition:
        background    0.1s cubic-bezier(0.4, 0, 0.2, 1),
        border-color  0.1s cubic-bezier(0.4, 0, 0.2, 1),
        color         0.1s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Inputs */
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stTextArea textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: rgba(255,255,255,0.8) !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: rgba(255,255,255,0.8) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────
for k, v in {
    "chat_history": [], "conflict_info": None, "last_retained": None,
    "timeline_memories": [], "_pending_content": None, "_pending_meta": None,
    "current_user": None, "current_team": None,
    "teams": {}, "logbook": [], "current_page": "🏠 Dashboard",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Load shared data on every page refresh
_shared_teams, _shared_logbook = load_shared()
if _shared_teams:
    st.session_state.teams   = _shared_teams
if _shared_logbook:
    st.session_state.logbook = _shared_logbook

# ── Helpers ───────────────────────────────────────────────────────
def get_team():
    t = st.session_state.current_team
    return st.session_state.teams.get(t) if t else None

def is_leader():
    u, team = st.session_state.current_user, get_team()
    return bool(u and team and team.get("leader") == u["name"])

def is_teacher():
    u = st.session_state.current_user
    return bool(u and u.get("role") == "teacher")

def is_logged_in():
    return st.session_state.current_user is not None

def add_logbook(content, category, author, team):
    entry = {
        "team": team, "author": author, "content": content,
        "category": category,
        "timestamp": datetime.datetime.utcnow().strftime("%b %d %Y · %H:%M UTC"),
    }
    st.session_state.logbook.append(entry)
    save_logbook_entry(entry)

def dot_color(cat):
    return {"decision":"#7c6fff","task":"#00c896","role":"#ff6b47",
            "blocker":"#ff4f4f","general":"#3e4660"}.get(cat,"#3e4660")

def role_emoji(role):
    r = role.lower()
    if "frontend" in r: return "🎨"
    if "backend"  in r: return "⚙️"
    if "full"     in r: return "🔧"
    if "design"   in r: return "✏️"
    if "doc"      in r: return "📝"
    if "devops"   in r: return "🚀"
    if "ml" in r or "ai" in r: return "🤖"
    if "leader"   in r: return "👑"
    if "teacher"  in r: return "🎓"
    if "test" in r or "qa" in r: return "🧪"
    return "💼"

# ── Shared Storage (Supabase — persists across sessions & deployments) ──
import json

@st.cache_resource
def get_supabase():
    """Get cached Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

def load_shared():
    """Load teams + logbook from Supabase."""
    sb = get_supabase()
    if sb is None:
        return {}, []
    try:
        # Load teams
        t_res = sb.table("teams").select("data").limit(1).execute()
        teams = t_res.data[0]["data"] if t_res.data else {}

        # Load logbook
        l_res = sb.table("logbook").select("*").order("id").execute()
        logbook = [
            {k: v for k, v in row.items() if k != "id"}
            for row in (l_res.data or [])
        ]
        return teams, logbook
    except Exception:
        return {}, []

def save_shared():
    """Save teams + logbook to Supabase."""
    sb = get_supabase()
    if sb is None:
        return
    try:
        # Upsert teams
        t_res = sb.table("teams").select("id").limit(1).execute()
        if t_res.data:
            sb.table("teams").update({"data": st.session_state.teams}).eq("id", t_res.data[0]["id"]).execute()
        else:
            sb.table("teams").insert({"data": st.session_state.teams}).execute()
    except Exception:
        pass

def save_logbook_entry(entry: dict):
    """Save a single logbook entry to Supabase."""
    sb = get_supabase()
    if sb is None:
        return
    try:
        sb.table("logbook").insert({
            "team":      entry.get("team", ""),
            "author":    entry.get("author", ""),
            "content":   entry.get("content", ""),
            "category":  entry.get("category", "general"),
            "timestamp": entry.get("timestamp", ""),
        }).execute()
    except Exception:
        pass

# ════════════════════════════════════════════════════════════════
#  SIDEBAR  — rendered FIRST before any page content
# ════════════════════════════════════════════════════════════════
def render_sidebar():
    user = st.session_state.current_user

    with st.sidebar:
        # ── Brand ──
        st.markdown(
            '<div style="text-align:center;padding:1rem 0 0.6rem;">'
            '<div style="width:42px;height:42px;background:linear-gradient(135deg,#ff6b47,#f5a623);'
            'border-radius:10px;display:flex;align-items:center;justify-content:center;'
            'font-size:1.3rem;margin:0 auto 0.5rem;">🔗</div>'
            '<div style="font-size:1rem;font-weight:700;color:#ffffff;font-family:IBM Plex Sans,sans-serif;letter-spacing:0.04em;">NEXUS</div>'
            '<div style="font-size:0.58rem;color:rgba(255,255,255,0.3);letter-spacing:0.1em;text-transform:uppercase;">Project Memory Engine</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        # ── User info ──
        role_icon  = {"member":"🧑‍💻","leader":"👑","teacher":"🎓"}.get(user["role"],"👤")
        role_label = {"member":"Member","leader":"Leader","teacher":"Teacher"}.get(user["role"],"Member")
        team_info  = f" · {st.session_state.current_team}" if st.session_state.current_team else ""
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);'
            f'border-radius:8px;padding:0.55rem 0.8rem;margin-bottom:0.8rem;">'
            f'<span style="font-size:1rem;">{role_icon}</span> '
            f'<span style="font-size:0.84rem;font-weight:600;color:rgba(255,255,255,0.9);">{user["name"]}</span><br>'
            f'<span style="font-size:0.62rem;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:0.05em;">'
            f'{role_label}{team_info}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Navigation ──
        st.markdown('<p style="font-size:0.6rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:rgba(255,255,255,0.25);margin:0 0 0.3rem;">Navigation</p>', unsafe_allow_html=True)

        pages = [("🏠 Dashboard","🏠","Dashboard"),("👥 Team","👥","Team"),
                 ("💬 AI Chat","💬","AI Chat"),("🕰 Timeline","🕰","Timeline")]
        if is_teacher():
            pages.append(("🎓 Teacher View","🎓","Teacher View"))

        for page_key, icon, label in pages:
            active = st.session_state.current_page == page_key
            if active:
                # Active page — styled div, no button needed
                st.markdown(
                    f'<div style="'
                    f'background:rgba(255,107,71,0.12);'
                    f'border-left:2px solid #ff6b47;'
                    f'border-radius:0 6px 6px 0;'
                    f'padding:0.5rem 0.9rem;'
                    f'font-size:0.84rem;font-weight:600;'
                    f'color:#ffcfc4;margin-bottom:2px;'
                    f'font-family:Inter,sans-serif;'
                    f'letter-spacing:0.01em;">'
                    f'{icon}&nbsp;&nbsp;{label}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                # Inactive — clickable button with hover animation from CSS
                if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
                    st.session_state.current_page = page_key
                    st.rerun()

        st.divider()

        # ── Quick Log ──
        st.markdown('<p style="font-size:0.6rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:rgba(255,255,255,0.25);margin:0 0 0.3rem;">Quick Log</p>', unsafe_allow_html=True)
        event_text = st.text_area("Log", placeholder="What happened? Decision, task, update...",
                                   height=85, label_visibility="collapsed", key="sidebar_event")
        c1, c2 = st.columns(2)
        with c1:
            cat  = st.selectbox("cat",  VALID_CATEGORIES, label_visibility="collapsed", key="sidebar_cat")
        with c2:
            auth = st.text_input("auth", value=user["name"], label_visibility="collapsed", key="sidebar_auth")

        if st.button("⚡ Log Entry", use_container_width=True, key="sidebar_log"):
            if event_text.strip():
                meta = {"category": cat, "author": auth,
                        "timestamp": datetime.datetime.utcnow().isoformat()}
                with st.spinner("Checking…"):
                    existing = hs_recall(event_text, top_k=10)
                    conflict = detect_conflict(event_text, existing)
                if conflict.get("conflict"):
                    st.session_state.conflict_info    = conflict
                    st.session_state._pending_content = event_text
                    st.session_state._pending_meta    = meta
                    st.warning("⚠️ Conflict found!")
                else:
                    st.session_state.conflict_info = None
                    hs_retain(event_text, meta)
                    add_logbook(event_text, cat, auth, st.session_state.current_team or "General")
                    st.session_state.last_retained     = "✅ Logged!"
                    st.session_state.timeline_memories = hs_recent(top_k=5)
                    st.rerun()
            else:
                st.warning("Write something first!")

        if st.session_state.last_retained:
            st.success(st.session_state.last_retained)

        st.divider()
        st.markdown(
            f'<div style="font-size:0.65rem;color:rgba(255,255,255,0.2);line-height:1.8;">'
            f'Groq {"✅" if GROQ_API_KEY else "❌"} &nbsp; Hindsight {"✅" if HINDSIGHT_API_KEY else "⬜"}'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("🚪 Sign Out", use_container_width=True, key="signout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ════════════════════════════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════════════════════════════
def render_header(title, subtitle):
    user      = st.session_state.current_user
    team      = get_team()
    uname     = user["name"]
    team_name = st.session_state.current_team or ""
    mrole     = team.get("roles",{}).get(uname,"Member") if (team and team_name) else ""

    team_chip = (
        f'<span style="background:rgba(255,107,71,0.12);border:1px solid rgba(255,107,71,0.25);'
        f'border-radius:20px;padding:4px 12px;font-size:0.72rem;color:#ffb8a8;font-weight:600;">'
        f'🏆 {team_name} · {mrole}</span>'
    ) if team_name else ""

    user_chip = (
        f'<span style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);'
        f'border-radius:20px;padding:4px 12px;font-size:0.72rem;color:rgba(255,255,255,0.55);">'
        f'👤 {uname}</span>'
    )

    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'background:linear-gradient(135deg,#13161e,#181c28);border:1px solid #1e2436;'
        f'border-radius:10px;padding:0.85rem 1.2rem;margin-bottom:1rem;">'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<div style="width:36px;height:36px;background:linear-gradient(135deg,#ff6b47,#f5a623);'
        f'border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;">🔗</div>'
        f'<div>'
        f'<div style="font-family:IBM Plex Sans,sans-serif;font-size:1.25rem;font-weight:800;color:#fff;">{title}</div>'
        f'<div style="font-size:0.7rem;color:rgba(255,255,255,0.3);">{subtitle}</div>'
        f'</div></div>'
        f'<div style="display:flex;align-items:center;gap:7px;">{team_chip}{user_chip}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════════════
def render_dashboard():
    render_header("Dashboard", "Your project at a glance")
    user    = st.session_state.current_user
    team    = get_team()
    logbook = st.session_state.logbook
    t_name  = st.session_state.current_team

    # Conflict banner
    if st.session_state.conflict_info and st.session_state.conflict_info.get("conflict"):
        ci = st.session_state.conflict_info
        try:    dstr = datetime.datetime.fromisoformat(ci.get("conflicting_date","")).strftime("%b %d %Y")
        except: dstr = ci.get("conflicting_date","earlier")
        st.markdown(
            f'<div class="nx-conflict fade-in"><strong>⚠️ Conflict!</strong> '
            f'Contradicts a decision from {dstr}.<br>'
            f'<em>{ci.get("conflicting_memory","")}</em><br>'
            f'<small>{ci.get("reason","")}</small></div>',
            unsafe_allow_html=True,
        )
        oc, dc = st.columns(2)
        with oc:
            if st.button("✅ Override & Save", key="ov_btn"):
                if st.session_state._pending_content:
                    hs_retain(st.session_state._pending_content, st.session_state._pending_meta or {})
                    add_logbook(st.session_state._pending_content,
                                st.session_state._pending_meta.get("category","general"),
                                st.session_state._pending_meta.get("author", user["name"]),
                                t_name or "General")
                st.session_state.conflict_info = None
                st.session_state._pending_content = None
                st.session_state._pending_meta = None
                st.rerun()
        with dc:
            if st.button("✕ Dismiss", key="dm_btn"):
                st.session_state.conflict_info = None
                st.session_state._pending_content = None
                st.session_state._pending_meta = None
                st.rerun()

    # Stats
    team_logs    = [l for l in logbook if l["team"] == t_name] if t_name else logbook
    members      = len(team.get("members",[])) if team else 0
    roles_set    = len([v for v in team.get("roles",{}).values() if v != "Member"]) if team else 0
    today_str    = datetime.datetime.utcnow().strftime("%b %d")
    active_today = len([l for l in team_logs if today_str in l["timestamp"]])

    c1,c2,c3,c4 = st.columns(4)
    for col, accent, val, label, icon in [
        (c1,"#ff6b47", len(team_logs), "Log Entries",    "📋"),
        (c2,"#7c6fff", members,        "Team Members",   "👥"),
        (c3,"#00c896", roles_set,      "Roles Assigned", "🎭"),
        (c4,"#f5a623", active_today,   "Active Today",   "⚡"),
    ]:
        col.markdown(
            f'<div style="background:#13161e;border:1px solid #1e2436;border-radius:10px;'
            f'padding:1.2rem 1rem;text-align:center;position:relative;overflow:hidden;">'
            f'<div style="position:absolute;top:0;left:0;right:0;height:3px;'
            f'background:linear-gradient(90deg,{accent},{accent}88);"></div>'
            f'<div style="font-size:1.8rem;margin-bottom:4px;">{icon}</div>'
            f'<div style="font-size:1.9rem;font-weight:800;color:{accent};line-height:1;margin-bottom:4px;">{val}</div>'
            f'<div style="font-size:0.62rem;color:#3e4660;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1.6, 1])

    with left:
        st.markdown('<div class="nx-sec">📋 Recent Activity</div>', unsafe_allow_html=True)
        if not team_logs:
            st.markdown(
                '<div style="background:#13161e;border:1px dashed #2a3348;border-radius:10px;'
                'padding:2rem;text-align:center;color:#3e4660;">'
                '<div style="font-size:2rem;margin-bottom:8px;">📭</div>'
                '<div style="font-size:0.88rem;">No activity yet. Log your first entry!</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            for log in reversed(team_logs[-8:]):
                cat  = log.get("category","general")
                safe = log["content"].replace("<","&lt;").replace(">","&gt;")
                st.markdown(
                    f'<div class="nx-log fade-in">'
                    f'<div class="nx-dot" style="background:{dot_color(cat)};"></div>'
                    f'<div style="flex:1;">'
                    f'<div style="font-size:0.84rem;color:#e4e8f2;line-height:1.5;">{safe}</div>'
                    f'<div style="font-size:0.69rem;color:#5a6278;margin-top:3px;">'
                    f'<span class="nx-badge {cat}">{cat}</span>'
                    f'{log["author"]} · {log["timestamp"]}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

    with right:
        st.markdown('<div class="nx-sec">👥 Team Snapshot</div>', unsafe_allow_html=True)
        if not team:
            st.markdown(
                '<div style="background:#13161e;border:1px dashed #2a3348;border-radius:10px;'
                'padding:1.5rem;text-align:center;color:#3e4660;">'
                '<div style="font-size:1.8rem;margin-bottom:6px;">🤝</div>'
                '<div style="font-size:0.82rem;">Create or join a team first.</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button("Go to Team →", key="goto_team"):
                st.session_state.current_page = "👥 Team"
                st.rerun()
        else:
            for m in team.get("members",[]):
                role_t  = team.get("roles",{}).get(m,"Member")
                is_lead = m == team["leader"]
                st.markdown(
                    f'<div class="nx-member {"leader" if is_lead else ""}" '
                    f'style="display:flex;align-items:center;justify-content:space-between;'
                    f'width:100%;margin:4px 0;border-radius:8px;padding:6px 10px;">'
                    f'<span>{role_emoji(role_t)} <strong>{m}</strong></span>'
                    f'<span style="background:#1e2436;color:#7a84a0;border-radius:4px;'
                    f'padding:2px 8px;font-size:0.68rem;">{role_t}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<div class="nx-sec" style="margin-top:1rem;">⚡ Quick Actions</div>', unsafe_allow_html=True)
        if st.button("💬 Ask Nexus AI",       use_container_width=True, key="qa_chat"):
            st.session_state.current_page = "💬 AI Chat"; st.rerun()
        if st.button("🕰 View Timeline",       use_container_width=True, key="qa_tl"):
            st.session_state.current_page = "🕰 Timeline"; st.rerun()
        if not team:
            if st.button("👥 Create / Join Team", use_container_width=True, key="qa_team"):
                st.session_state.current_page = "👥 Team"; st.rerun()


# ════════════════════════════════════════════════════════════════
#  TEAM PAGE
# ════════════════════════════════════════════════════════════════
def render_team_page():
    render_header("Team Manager", "Create teams, assign roles, collaborate")
    user  = st.session_state.current_user
    teams = st.session_state.teams

    tab1, tab2, tab3 = st.tabs(["🏗 Create Team", "🚪 Join Team", "📋 My Team"])

    with tab1:
        if user["role"] == "member":
            st.info("🔒 Only Team Leaders and Teachers can create teams.")
        else:
            _, mc, _ = st.columns([0.3,2,0.3])
            with mc:
                st.markdown(
                    '<div style="background:#13161e;border:1px solid #1e2436;border-radius:12px;padding:1.5rem;margin-top:0.5rem;">'
                    '<div style="font-size:0.95rem;font-weight:700;color:#e4e8f2;margin-bottom:1rem;">🚀 Start a New Team</div>',
                    unsafe_allow_html=True,
                )
                t_name   = st.text_input("Team Name",    placeholder="e.g. Team Phoenix 🔥")
                p_name   = st.text_input("Project Name", placeholder="e.g. AI Food Delivery App")
                p_desc   = st.text_area("Description",   placeholder="What are you building? (optional)", height=80)
                create_b = st.button("🚀 Create Team", use_container_width=True, key="create_team_btn")
                st.markdown("</div>", unsafe_allow_html=True)
            if create_b:
                if not t_name.strip():
                    st.warning("Enter a team name.")
                elif t_name in teams:
                    st.error("Team name already taken!")
                else:
                    teams[t_name] = {
                        "leader": user["name"], "project": p_name.strip() or "Untitled",
                        "desc": p_desc.strip(), "members": [user["name"]],
                        "roles": {user["name"]: "Team Leader"},
                        "created_at": datetime.datetime.utcnow().strftime("%b %d %Y"),
                    }
                    st.session_state.teams        = teams
                    st.session_state.current_team = t_name
                    save_shared()
                    st.success(f"✅ Team **{t_name}** created!")
                    st.balloons(); st.rerun()

    with tab2:
        if not teams:
            st.info("No teams yet. Ask your leader to create one.")
        else:
            for t_name, team in teams.items():
                already_in = user["name"] in team["members"]
                st.markdown(
                    f'<div style="background:#13161e;border:1px solid #1e2436;border-radius:10px;'
                    f'padding:1rem;margin-bottom:8px;">'
                    f'<div style="font-weight:700;color:#e4e8f2;font-size:0.95rem;">🏆 {t_name}</div>'
                    f'<div style="font-size:0.78rem;color:#5a6278;">📁 {team["project"]} · 👑 {team["leader"]} · 👥 {len(team["members"])} members</div>'
                    f'{"<div style=\'color:#00c896;font-size:0.78rem;margin-top:4px;\'>✅ You are in this team</div>" if already_in else ""}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if not already_in:
                    if st.button(f"🚪 Join {t_name}", key=f"join_{t_name}"):
                        teams[t_name]["members"].append(user["name"])
                        teams[t_name]["roles"][user["name"]] = "Member"
                        st.session_state.current_team = t_name
                        save_shared()
                        st.success(f"✅ Joined {t_name}!"); st.rerun()
                elif st.session_state.current_team != t_name:
                    if st.button(f"Switch to {t_name}", key=f"sw_{t_name}"):
                        st.session_state.current_team = t_name; st.rerun()

    with tab3:
        if not st.session_state.current_team:
            st.info("You haven't joined a team yet.")
        else:
            team   = get_team()
            t_name = st.session_state.current_team
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#13161e,#181c28);border:1px solid #1e2436;'
                f'border-radius:12px;padding:1.3rem;margin-bottom:1rem;">'
                f'<div style="font-family:IBM Plex Sans,sans-serif;font-family:IBM Plex Sans,sans-serif;font-size:1.15rem;font-weight:700;color:#fff;letter-spacing:-0.01em;">{t_name}</div>'
                f'<div style="font-size:0.82rem;color:rgba(255,255,255,0.4);margin-top:4px;">'
                f'📁 {team["project"]} · 👑 {team["leader"]} · 📅 {team.get("created_at","—")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="nx-sec">👥 Members</div>', unsafe_allow_html=True)
            cols = st.columns(min(len(team["members"]), 3))
            for i, m in enumerate(team["members"]):
                role_t  = team.get("roles",{}).get(m,"Member")
                is_lead = m == team["leader"]
                with cols[i % 3]:
                    st.markdown(
                        f'<div style="background:{"rgba(245,166,35,0.1)" if is_lead else "#13161e"};'
                        f'border:1px solid {"rgba(245,166,35,0.3)" if is_lead else "#1e2436"};'
                        f'border-radius:10px;padding:0.9rem;text-align:center;margin-bottom:8px;">'
                        f'<div style="font-size:1.8rem;">{role_emoji(role_t)}</div>'
                        f'<div style="font-weight:600;font-size:0.85rem;color:#e4e8f2;margin-top:4px;">{m}</div>'
                        f'<div style="font-size:0.7rem;color:#5a6278;">{role_t}</div>'
                        f'{"<div style=\'font-size:0.6rem;color:#f5a623;font-weight:700;margin-top:2px;\'>LEADER</div>" if is_lead else ""}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            if is_leader():
                st.markdown('<div class="nx-sec">✏️ Assign Roles</div>', unsafe_allow_html=True)
                role_opts = ["Frontend Developer","Backend Developer","Full Stack Developer",
                             "UI/UX Designer","Documentation","DevOps Engineer","ML Engineer",
                             "QA Tester","Database Admin","Scrum Master","Custom..."]
                rc1,rc2,rc3 = st.columns([2,2,1])
                with rc1: target      = st.selectbox("Member", team["members"], key="rm_sel", label_visibility="collapsed")
                with rc2: picked_role = st.selectbox("Role",   role_opts,       key="role_sel", label_visibility="collapsed")
                with rc3: assign_b    = st.button("Assign ✓", use_container_width=True, key="assign_role_btn")
                custom_r = st.text_input("Custom role", key="custom_role_inp") if picked_role == "Custom..." else ""
                if assign_b:
                    final = custom_r.strip() if picked_role == "Custom..." else picked_role
                    if final:
                        team["roles"][target] = final
                        st.session_state.teams[t_name] = team
                        add_logbook(f"{target} assigned as {final}", "role", user["name"], t_name)
                        hs_retain(f"{target} assigned as {final}",
                                  {"category":"role","author":user["name"],
                                   "timestamp":datetime.datetime.utcnow().isoformat()})
                        save_shared()
                        st.success(f"✅ {target} → {final}"); st.rerun()


# ════════════════════════════════════════════════════════════════
#  AI CHAT
# ════════════════════════════════════════════════════════════════
def render_chat_page():
    render_header("AI Chat", "Ask Nexus anything about your project")
    user = st.session_state.current_user

    if st.session_state.chat_history:
        html = '<div class="nx-chat-wrap">'
        for turn in st.session_state.chat_history:
            name  = user["name"] if turn["role"] == "user" else "🤖 Nexus AI"
            css   = "user" if turn["role"] == "user" else "ai"
            body  = turn["content"].replace("<","&lt;").replace(">","&gt;")
            html += f'<div class="nx-bubble {css}"><div class="nx-bubble-who">{name}</div>{body}</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="nx-chat-wrap"><div class="nx-empty">'
            '<div style="font-size:2rem;">💡</div>'
            '<div style="font-weight:600;color:#5a6278;">Ask me anything!</div>'
            '<div style="font-size:0.82rem;color:#3e4660;">"Who handles the frontend?"<br>"Why did we pick Python?"<br>"What\'s our deadline?"</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )

    ic, bc = st.columns([5.5,1])
    with ic:
        user_input = st.text_input("msg", placeholder="Ask about your project...",
                                    label_visibility="collapsed", key="chat_msg_input")
    with bc:
        send = st.button("Send ➤", use_container_width=True, key="send_chat")

    if send and user_input.strip():
        with st.spinner("Nexus is thinking…"):
            reply = chat_with_nexus(user_input, st.session_state.chat_history)
        st.session_state.chat_history.append({"role":"user",      "content":user_input})
        st.session_state.chat_history.append({"role":"assistant", "content":reply})
        st.rerun()

    if not st.session_state.chat_history:
        st.markdown('<div class="nx-sec">💡 Suggestions</div>', unsafe_allow_html=True)
        sugs = ["Who handles the frontend?","What tech stack?","Current deadline?","Any blockers?","Summarize decisions"]
        cols = st.columns(len(sugs))
        for i, s in enumerate(sugs):
            with cols[i]:
                if st.button(s, key=f"sug_{i}", use_container_width=True):
                    with st.spinner("Thinking…"):
                        reply = chat_with_nexus(s, st.session_state.chat_history)
                    st.session_state.chat_history.append({"role":"user",      "content":s})
                    st.session_state.chat_history.append({"role":"assistant", "content":reply})
                    st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑 Clear Chat", key="clear_chat_btn"):
            st.session_state.chat_history = []; st.rerun()


# ════════════════════════════════════════════════════════════════
#  TIMELINE
# ════════════════════════════════════════════════════════════════
def render_timeline_page():
    render_header("Truth Timeline", "Full history of all project decisions")

    # Check Hindsight availability
    from utils.hindsight_helper import get_hindsight_client
    hs_available = get_hindsight_client() is not None

    if not hs_available:
        st.markdown(
            '<div style="background:rgba(245,166,35,0.08);border:1px solid rgba(245,166,35,0.25);'
            'border-radius:8px;padding:0.6rem 1rem;margin-bottom:0.8rem;font-size:0.82rem;color:#f5a623;">'
            '⚠️ <strong>Hindsight not connected</strong> — showing session log only. '
            'Run <code>pip install hindsight-client</code> and start the backend to enable persistent memory.'
            '</div>',
            unsafe_allow_html=True,
        )

    rc, _ = st.columns([1,5])
    with rc:
        if st.button("🔄 Refresh", key="tl_refresh"):
            st.session_state.timeline_memories = hs_recent(top_k=5); st.rerun()

    if not st.session_state.timeline_memories:
        st.session_state.timeline_memories = hs_recent(top_k=5)

    cat_filter = st.selectbox("Filter", ["All Categories"]+VALID_CATEGORIES,
                               label_visibility="collapsed", key="tl_filter")
    t_name    = st.session_state.current_team
    local_log = [l for l in st.session_state.logbook if not t_name or l["team"]==t_name]
    if cat_filter != "All Categories":
        local_log = [l for l in local_log if l["category"]==cat_filter]

    left, right = st.columns([1.5,1])

    with left:
        st.markdown('<div class="nx-sec">📜 Hindsight Memory</div>', unsafe_allow_html=True)
        mems = st.session_state.timeline_memories
        if mems:
            for mem in mems:
                parsed = parse_memory_meta(mem)
                cat    = parsed["category"] if parsed["category"] in VALID_CATS_SET else "general"
                if cat_filter != "All Categories" and cat != cat_filter: continue
                safe = parsed["content"].replace("<","&lt;").replace(">","&gt;")
                st.markdown(
                    f'<div class="nx-tl {cat} fade-in">'
                    f'<span class="nx-badge {cat}">{cat}</span>{safe}'
                    f'<div class="nx-tl-meta">👤 {parsed["author"]} · 🕓 {parsed["ts"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div style="background:#13161e;border:1px dashed #2a3348;border-radius:10px;'
                'padding:1.5rem;text-align:center;color:#3e4660;font-size:0.85rem;">'
                '🔌 Connect Hindsight backend to see persistent memories.</div>',
                unsafe_allow_html=True,
            )

    with right:
        st.markdown('<div class="nx-sec">📋 Session Log</div>', unsafe_allow_html=True)
        if local_log:
            for log in reversed(local_log[-10:]):
                cat  = log.get("category","general")
                safe = log["content"].replace("<","&lt;").replace(">","&gt;")
                st.markdown(
                    f'<div class="nx-tl {cat} fade-in">'
                    f'<span class="nx-badge {cat}">{cat}</span>{safe}'
                    f'<div class="nx-tl-meta">👤 {log["author"]} · 🕓 {log["timestamp"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div style="background:#13161e;border:1px dashed #2a3348;border-radius:10px;'
                'padding:1.5rem;text-align:center;color:#3e4660;font-size:0.85rem;">'
                'No entries yet. Log something from the sidebar!</div>',
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════════════════════════
#  TEACHER VIEW
# ════════════════════════════════════════════════════════════════
def render_teacher_page():
    render_header("Teacher Dashboard", "Monitor all teams and student progress")
    teams   = st.session_state.teams
    logbook = st.session_state.logbook

    if not teams:
        st.markdown(
            '<div style="text-align:center;padding:3rem;color:#3e4660;">'
            '<div style="font-size:3rem;margin-bottom:1rem;">🏫</div>'
            '<div style="font-size:1rem;font-weight:600;color:#5a6278;">No teams yet</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    total_members = sum(len(t["members"]) for t in teams.values())
    today_str     = datetime.datetime.utcnow().strftime("%b %d")
    active_today  = len([l for l in logbook if today_str in l["timestamp"]])

    c1,c2,c3,c4 = st.columns(4)
    for col, accent, val, lbl, icon in [
        (c1,"#ff6b47",len(teams),        "Total Teams",    "🏆"),
        (c2,"#7c6fff",total_members,     "Total Students", "👥"),
        (c3,"#00c896",len(logbook),      "Log Entries",    "📋"),
        (c4,"#f5a623",active_today,      "Active Today",   "⚡"),
    ]:
        col.markdown(
            f'<div style="background:#13161e;border:1px solid #1e2436;border-radius:10px;'
            f'padding:1.1rem;text-align:center;position:relative;overflow:hidden;">'
            f'<div style="position:absolute;top:0;left:0;right:0;height:2px;'
            f'background:linear-gradient(90deg,{accent},{accent}88);"></div>'
            f'<div style="font-size:1.6rem;margin-bottom:3px;">{icon}</div>'
            f'<div style="font-size:1.8rem;font-weight:800;color:{accent};line-height:1;margin-bottom:3px;">{val}</div>'
            f'<div style="font-size:0.62rem;color:#3e4660;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;">{lbl}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    team_filter   = st.selectbox("Filter", ["📊 All Teams"]+[f"🏆 {t}" for t in teams],
                                  label_visibility="collapsed", key="teacher_filter")
    selected      = teams if team_filter=="📊 All Teams" else {team_filter.replace("🏆 ",""):teams[team_filter.replace("🏆 ","")]}

    for t_name, team in selected.items():
        team_logs = [l for l in logbook if l["team"]==t_name]
        progress  = min(100, len(team_logs)*10)
        prog_col  = "#00c896" if progress>=60 else "#f5a623" if progress>=30 else "#ff6b47"

        with st.expander(f"🏆 {t_name}  ·  {team['project']}  ·  {len(team['members'])} members", expanded=True):
            hc, pc = st.columns([2,1])
            with hc:
                st.markdown(
                    f'<div style="background:#0f1117;border-radius:8px;padding:0.9rem;margin-bottom:0.8rem;">'
                    f'<div style="font-size:0.8rem;color:#5a6278;">👑 <strong style="color:#e4e8f2">{team["leader"]}</strong>'
                    f' &nbsp;·&nbsp; 📅 {team.get("created_at","—")} &nbsp;·&nbsp; 📝 {len(team_logs)} logs</div>'
                    f'<div style="margin-top:8px;">',
                    unsafe_allow_html=True,
                )
                for m in team["members"]:
                    role_t  = team.get("roles",{}).get(m,"Member")
                    is_lead = m == team["leader"]
                    st.markdown(
                        f'<span class="nx-member {"leader" if is_lead else ""}">'
                        f'{role_emoji(role_t)} {m} <span style="opacity:0.5;font-size:0.65rem;">· {role_t}</span></span>',
                        unsafe_allow_html=True,
                    )
                st.markdown("</div></div>", unsafe_allow_html=True)

            with pc:
                st.markdown(
                    f'<div style="background:#13161e;border:1px solid #1e2436;border-radius:10px;padding:1rem;text-align:center;">'
                    f'<div style="font-size:0.6rem;font-weight:700;color:#3e4660;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">Progress</div>'
                    f'<div style="font-size:1.8rem;font-weight:800;color:{prog_col};">{progress}%</div>'
                    f'<div style="background:#1e2436;border-radius:4px;height:5px;margin-top:6px;">'
                    f'<div style="background:{prog_col};width:{progress}%;height:5px;border-radius:4px;"></div></div>'
                    f'<div style="font-size:0.68rem;color:#3e4660;margin-top:4px;">{len(team_logs)} activities</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown('<div style="font-size:0.6rem;font-weight:700;color:#3e4660;text-transform:uppercase;letter-spacing:0.1em;margin:0.8rem 0 0.4rem;">📖 Activity Logbook</div>', unsafe_allow_html=True)
            if not team_logs:
                st.markdown('<div style="color:#3e4660;font-size:0.84rem;padding:0.5rem;">No activity yet.</div>', unsafe_allow_html=True)
            else:
                lc1,lc2 = st.columns(2)
                for i, log in enumerate(reversed(team_logs[-10:])):
                    cat  = log.get("category","general")
                    safe = log["content"].replace("<","&lt;").replace(">","&gt;")
                    card = (
                        f'<div class="nx-log">'
                        f'<div class="nx-dot" style="background:{dot_color(cat)};"></div>'
                        f'<div><div style="font-size:0.83rem;color:#e4e8f2;">{safe}</div>'
                        f'<div style="font-size:0.69rem;color:#5a6278;margin-top:2px;">'
                        f'<span class="nx-badge {cat}">{cat}</span>{log["author"]} · {log["timestamp"]}</div>'
                        f'</div></div>'
                    )
                    (lc1 if i%2==0 else lc2).markdown(card, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  LOGIN
# ════════════════════════════════════════════════════════════════
def render_login():
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown(
            '<div class="fade-in" style="background:#13161e;border:1px solid #1e2436;'
            'border-radius:16px;padding:2.2rem 2rem;text-align:center;margin-top:2rem;'
            'box-shadow:0 16px 48px rgba(0,0,0,0.5);">'
            '<div style="width:60px;height:60px;background:linear-gradient(135deg,#ff6b47,#f5a623);'
            'border-radius:14px;display:flex;align-items:center;justify-content:center;'
            'font-size:1.8rem;margin:0 auto 1rem;">🔗</div>'
            '<div style="font-family:IBM Plex Sans,sans-serif;font-size:2rem;font-weight:800;color:#e4e8f2;">Nexus</div>'
            '<div style="font-size:0.85rem;color:#3e4660;margin:0.4rem 0 1.4rem;">'
            'Your team\'s AI-powered project brain.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<p style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#5a6278;margin:0.8rem 0 0.3rem;">Your Name</p>', unsafe_allow_html=True)
        name = st.text_input("name", placeholder="e.g. Rahul Sharma",
                              label_visibility="collapsed", key="login_name")
        st.markdown('<p style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#5a6278;margin:0.8rem 0 0.3rem;">I am joining as</p>', unsafe_allow_html=True)
        role_sel = st.radio("role",
                             ["🧑‍💻 Student / Member","👑 Team Leader","🎓 Teacher / Mentor"],
                             label_visibility="collapsed", horizontal=True, key="login_role")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Continue to Nexus →", use_container_width=True, key="login_btn"):
            if not name.strip():
                st.warning("Please enter your name.")
            else:
                role_map = {"🧑‍💻 Student / Member":"member","👑 Team Leader":"leader","🎓 Teacher / Mentor":"teacher"}
                st.session_state.current_user = {
                    "name": name.strip(),
                    "role": role_map.get(role_sel, "member"),
                    "joined": datetime.datetime.utcnow().strftime("%b %d %Y"),
                }
                st.rerun()


# ════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════

if not is_logged_in():
    render_login()
    st.stop()

render_sidebar()

page = st.session_state.get("current_page", "🏠 Dashboard")

if   page == "🏠 Dashboard":   render_dashboard()
elif page == "👥 Team":         render_team_page()
elif page == "💬 AI Chat":      render_chat_page()
elif page == "🕰 Timeline":     render_timeline_page()
elif page == "🎓 Teacher View":
    render_teacher_page() if is_teacher() else st.error("🔒 Teachers only.")
