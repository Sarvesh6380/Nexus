"""
╔═══════════════════════════════════════════════════════════════╗
║   NEXUS — AI Group Project Manager                            ║
║   Supabase persistence · Dark UI · All features               ║
╚═══════════════════════════════════════════════════════════════╝
Run:  streamlit run app.py
Deps: pip install streamlit hindsight-client groq python-dotenv supabase
"""

import os
import datetime
import json
import streamlit as st

from config import (
    GROQ_API_KEY, HINDSIGHT_API_KEY, HINDSIGHT_API_URL,
    HINDSIGHT_BANK_ID, GROQ_MODEL, VALID_CATEGORIES, VALID_CATS_SET,
    SUPABASE_URL, SUPABASE_KEY,
)
from utils.styles import NEXUS_CSS
from utils.hindsight_helper import hs_retain, hs_recall, hs_recent, parse_memory_meta
from utils.groq_agent import detect_conflict, chat_with_nexus


# ════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Nexus — Project Manager",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(NEXUS_CSS, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  PERSISTENCE — Supabase + Local File Fallback
# ════════════════════════════════════════════════════════════════

# Use absolute paths for reliable file access across all environments
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEAMS_BACKUP_FILE = os.path.join(_SCRIPT_DIR, "teams_data.json")
LOGBOOK_BACKUP_FILE = os.path.join(_SCRIPT_DIR, "logbook_data.json")

@st.cache_resource
def _get_sb():
    """
    Return cached Supabase client.
    Uses SUPABASE_URL/KEY from config.py which already handles
    st.secrets (Streamlit Cloud) and .env (local) automatically.
    """
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return None
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

def load_teams_from_file() -> dict:
    """Load teams from local JSON file (fallback when Supabase unavailable)."""
    try:
        if os.path.exists(TEAMS_BACKUP_FILE):
            with open(TEAMS_BACKUP_FILE, "r") as f:
                return json.load(f) or {}
    except Exception:
        pass
    return {}

def save_teams_to_file(teams: dict):
    """Save teams to local JSON file (fallback when Supabase unavailable)."""
    try:
        with open(TEAMS_BACKUP_FILE, "w") as f:
            json.dump(teams, f, indent=2)
    except Exception:
        pass

def sb_load_teams() -> dict:
    """Load all teams from Supabase. Falls back to local JSON file. Returns {} if both unavailable."""
    sb = _get_sb()
    if sb is not None:
        try:
            res = sb.table("teams").select("data").limit(1).execute()
            if res.data and res.data[0].get("data"):
                return res.data[0]["data"]
        except Exception as e:
            pass  # Fall through to file backup
    # Fallback to local file
    return load_teams_from_file()

def sb_save_teams(teams: dict):
    """Upsert teams dict into Supabase AND save to local file as backup."""
    # Always save to local file (fast, reliable)
    save_teams_to_file(teams)
    
    # Try Supabase
    sb = _get_sb()
    if sb is not None:
        try:
            res = sb.table("teams").select("id").limit(1).execute()
            if res.data:
                sb.table("teams").update({"data": teams}).eq("id", res.data[0]["id"]).execute()
            else:
                sb.table("teams").insert({"data": teams}).execute()
        except Exception:
            pass

def load_logbook_from_file() -> list:
    """Load logbook from local JSON file (fallback)."""
    try:
        if os.path.exists(LOGBOOK_BACKUP_FILE):
            with open(LOGBOOK_BACKUP_FILE, "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception:
        pass
    return []

def save_logbook_to_file(logbook: list):
    """Save logbook to local JSON file (fallback)."""
    try:
        with open(LOGBOOK_BACKUP_FILE, "w") as f:
            json.dump(logbook, f, indent=2)
    except Exception:
        pass

def sb_load_logbook() -> list:
    """Load all logbook entries from Supabase. Falls back to local file. Returns [] if both unavailable."""
    sb = _get_sb()
    if sb is not None:
        try:
            res = sb.table("logbook").select(
                "team,author,content,category,timestamp"
            ).order("id").execute()
            return res.data or []
        except Exception:
            pass  # Fall through to file backup
    # Fallback to local file
    return load_logbook_from_file()

def sb_save_log_entry(entry: dict):
    """Insert a single logbook entry AND save all logbook to local file as backup."""
    # Load current logbook, add entry, save to file
    current_logbook = st.session_state.get("logbook", [])
    if entry not in current_logbook:
        current_logbook.append(entry)
        save_logbook_to_file(current_logbook)
    
    # Try Supabase
    sb = _get_sb()
    if sb is not None:
        try:
            sb.table("logbook").insert({
                "team":      entry.get("team",      ""),
                "author":    entry.get("author",    ""),
                "content":   entry.get("content",   ""),
                "category":  entry.get("category",  "general"),
                "timestamp": entry.get("timestamp", ""),
            }).execute()
        except Exception:
            pass



def sb_debug_status() -> dict:
    """
    Returns a dict with full Supabase connection status for debugging.
    Shown in Teacher View and sidebar.
    """
    status = {
        "url_set":    bool(SUPABASE_URL),
        "key_set":    bool(SUPABASE_KEY),
        "connected":  False,
        "teams_rows": 0,
        "log_rows":   0,
        "error":      "",
    }
    sb = _get_sb()
    if sb is None:
        status["error"] = "Client is None — check URL/KEY"
        return status
    try:
        t = sb.table("teams").select("id").execute()
        l = sb.table("logbook").select("id", count="exact").execute()
        status["connected"]  = True
        status["teams_rows"] = len(t.data) if t.data else 0
        status["log_rows"]   = l.count if hasattr(l, "count") else 0
    except Exception as e:
        status["error"] = str(e)
    return status


# ════════════════════════════════════════════════════════════════
#  SESSION STATE
# ════════════════════════════════════════════════════════════════

# User-only keys — cleared on sign out
_USER_KEYS = [
    "chat_history", "conflict_info", "last_retained",
    "timeline_memories", "_pending_content", "_pending_meta",
    "current_user", "current_team", "current_page",
]

_defaults = {
    "chat_history":      [],
    "conflict_info":     None,
    "last_retained":     None,
    "timeline_memories": [],
    "_pending_content":  None,
    "_pending_meta":     None,
    "current_user":      None,
    "current_team":      None,
    "current_page":      "🏠 Dashboard",
    # Shared — always overwritten from Supabase on load
    "teams":             {},
    "logbook":           [],
    "_sb_loaded":        False,   # default False → guarantees Supabase fetch on every cold start
}

for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Load shared data from Supabase — runs on first load AND after every sign-out
if not st.session_state.get("_sb_loaded"):
    _teams_db   = sb_load_teams()
    _logbook_db = sb_load_logbook()
    # Always write from Supabase — this is the cross-user sync point
    st.session_state.teams   = _teams_db   if _teams_db   else {}
    st.session_state.logbook = _logbook_db if _logbook_db else []
    st.session_state._sb_loaded = True

# ── DEBUG: show Supabase status in console ──
# Uncomment below to debug connection issues:
# import sys
# print(f"Supabase: {_get_sb() is not None}, Teams: {len(st.session_state.teams)}, Logs: {len(st.session_state.logbook)}", file=sys.stderr)


# ════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════

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
        "team": team, "author": author,
        "content": content, "category": category,
        "timestamp": datetime.datetime.utcnow().strftime("%b %d %Y · %H:%M UTC"),
    }
    st.session_state.logbook.append(entry)
    sb_save_log_entry(entry)   # persist to Supabase immediately

def dot_color(cat):
    return {
        "decision": "#7c6fff", "task": "#00b894",
        "role": "#ff6b47", "blocker": "#ff4f4f", "general": "#5a6278",
    }.get(cat, "#5a6278")

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


# ════════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ════════════════════════════════════════════════════════════════

def render_login():
    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        st.markdown("""
        <div class="fade-in" style="background:#161a24;border:1px solid #1e2538;
            border-radius:20px;padding:2.5rem 2rem 1rem;
            box-shadow:0 16px 48px rgba(0,0,0,0.6);margin-top:2rem;text-align:center;">
            <div style="width:72px;height:72px;background:linear-gradient(135deg,#ff6b47,#f5a623);
                border-radius:18px;display:flex;align-items:center;justify-content:center;
                font-size:2.2rem;margin:0 auto 1.2rem;box-shadow:0 8px 24px rgba(255,107,71,0.45);">🔗</div>
            <div style="font-family:'Syne',sans-serif;font-size:2.2rem;font-weight:800;
                color:#e8eaf0;letter-spacing:-0.03em;margin-bottom:0.4rem;">Nexus</div>
            <div style="font-size:0.87rem;color:#5a6278;line-height:1.6;margin-bottom:0.5rem;">
                Your team's AI-powered project brain.<br>Sign in to get started.</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<p style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#5a6278;margin:0.8rem 0 0.3rem;">Your Name</p>', unsafe_allow_html=True)
        name = st.text_input("name_input", placeholder="e.g. Rahul Sharma",
                             label_visibility="collapsed", key="login_name")

        st.markdown('<p style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#5a6278;margin:1rem 0 0.3rem;">I am joining as</p>', unsafe_allow_html=True)
        role_sel = st.radio(
            "role_radio",
            ["🧑‍💻  Student / Member", "👑  Team Leader", "🎓  Teacher / Mentor"],
            label_visibility="collapsed", horizontal=True, key="login_role",
        )

        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        login_btn = st.button("Continue to Nexus →", use_container_width=True, key="login_btn")

        if login_btn:
            if not name.strip():
                st.warning("Please enter your name to continue.")
            else:
                role_map = {
                    "🧑‍💻  Student / Member": "member",
                    "👑  Team Leader":        "leader",
                    "🎓  Teacher / Mentor":   "teacher",
                }
                st.session_state.current_user = {
                    "name":   name.strip(),
                    "role":   role_map[role_sel],
                    "joined": datetime.datetime.utcnow().strftime("%b %d %Y"),
                }
                st.rerun()


# ════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════

def render_sidebar():
    user = st.session_state.current_user

    with st.sidebar:
        # Brand
        st.markdown("""
        <div style="text-align:center;padding:1rem 0 0.6rem;">
            <div style="width:44px;height:44px;background:linear-gradient(135deg,#ff6b47,#f5a623);
                 border-radius:11px;display:flex;align-items:center;justify-content:center;
                 font-size:1.3rem;margin:0 auto 0.5rem;box-shadow:0 4px 12px rgba(255,107,71,0.4);">🔗</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:800;
                 color:#fff;letter-spacing:0.03em;">NEXUS</div>
            <div style="font-size:0.58rem;color:rgba(255,255,255,0.28);
                 letter-spacing:0.1em;text-transform:uppercase;">Project Memory Engine</div>
        </div>
        """, unsafe_allow_html=True)

        # User card
        role_icons  = {"member": "🧑‍💻", "leader": "👑", "teacher": "🎓"}
        role_labels = {"member": "Member", "leader": "Leader", "teacher": "Teacher"}
        team_line   = f'<div style="margin-top:5px;font-size:0.7rem;color:rgba(255,107,71,0.75);">🏆 {st.session_state.current_team}</div>' if st.session_state.current_team else ""
        st.markdown(f"""
        <div class="sidebar-user-card">
            <div style="display:flex;align-items:center;gap:8px;">
                <div style="width:30px;height:30px;background:rgba(255,107,71,0.2);border-radius:50%;
                     display:flex;align-items:center;justify-content:center;font-size:0.95rem;">
                     {role_icons.get(user['role'],'👤')}</div>
                <div>
                    <div style="font-size:0.84rem;font-weight:600;color:rgba(255,255,255,0.88);">{user['name']}</div>
                    <div style="font-size:0.62rem;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:0.05em;">{role_labels.get(user['role'],'Member')}</div>
                </div>
            </div>
            {team_line}
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        st.markdown('<div class="sidebar-section-label">Navigation</div>', unsafe_allow_html=True)

        pages = [
            ("🏠 Dashboard", "🏠", "Dashboard"),
            ("👥 Team",       "👥", "Team"),
            ("💬 AI Chat",   "💬", "AI Chat"),
            ("🕰 Timeline",  "🕰", "Timeline"),
        ]
        if is_teacher():
            pages.append(("🎓 Teacher View", "🎓", "Teacher View"))

        for page_key, icon, label in pages:
            is_active = st.session_state.current_page == page_key
            if is_active:
                st.markdown(f"""
                <div style="background:rgba(255,107,71,0.12);border-left:2px solid #ff6b47;
                     border-radius:0 7px 7px 0;padding:0.5rem 0.85rem;font-size:0.85rem;
                     font-weight:600;color:#ffcfc4;margin-bottom:2px;">
                     {icon}&nbsp;&nbsp;{label}</div>
                """, unsafe_allow_html=True)
            else:
                if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
                    st.session_state.current_page = page_key
                    st.rerun()

        # Quick Log
        st.markdown('<div class="sidebar-section-label">Quick Log</div>', unsafe_allow_html=True)

        event_text = st.text_area(
            "Log", placeholder="What happened? Decision, task, update...",
            height=85, label_visibility="collapsed", key="sidebar_event",
        )
        c1, c2 = st.columns(2)
        with c1:
            cat  = st.selectbox("cat",  VALID_CATEGORIES, label_visibility="collapsed", key="sidebar_cat")
        with c2:
            auth = st.text_input("auth", value=user["name"], label_visibility="collapsed", key="sidebar_auth")

        if st.button("⚡  Log Entry", use_container_width=True, key="sidebar_log"):
            if event_text.strip():
                meta = {
                    "category": cat, "author": auth,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
                with st.spinner("Checking for conflicts…"):
                    existing = hs_recall(event_text, top_k=10)
                    conflict = detect_conflict(event_text, existing)

                if conflict.get("conflict"):
                    st.session_state.conflict_info    = conflict
                    st.session_state._pending_content = event_text
                    st.session_state._pending_meta    = meta
                    st.warning("⚠️ Conflict found! See Dashboard.")
                else:
                    st.session_state.conflict_info = None
                    hs_retain(event_text, meta)
                    add_logbook(event_text, cat, auth,
                                st.session_state.current_team or "General")
                    st.session_state.last_retained     = "✅ Logged!"
                    st.session_state.timeline_memories = hs_recent(top_k=5)
                    st.rerun()
            else:
                st.warning("Write something first!")

        if st.session_state.last_retained:
            st.success(st.session_state.last_retained)

        # Footer
        st.markdown("---")
        groq_ok = "✅" if GROQ_API_KEY else "❌"
        hs_ok   = "✅" if HINDSIGHT_API_KEY else "⬜"
        sb_ok   = "✅" if (SUPABASE_URL and SUPABASE_KEY) else "❌"
        teams_count = len(st.session_state.get("teams", {}))
        
        # Check if local JSON files exist
        teams_file_exists = "✅" if os.path.exists(TEAMS_BACKUP_FILE) else "❌"
        logbook_file_exists = "✅" if os.path.exists(LOGBOOK_BACKUP_FILE) else "❌"
        
        st.markdown(f"""
        <div style="font-size:0.65rem;color:rgba(255,255,255,0.25);line-height:2;">
            Groq {groq_ok} &nbsp; Hindsight {hs_ok} &nbsp; Supabase {sb_ok}<br>
            <span style="color:rgba(255,255,255,0.15);">
            Teams in DB: {teams_count} · {GROQ_MODEL.split("-")[0].upper()}<br>
            Files: Teams {teams_file_exists} · Logbook {logbook_file_exists}
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:0.4rem;'></div>", unsafe_allow_html=True)
        if st.button("🚪  Sign Out", use_container_width=True, key="signout"):
            # Save current teams to Supabase before clearing session
            sb_save_teams(st.session_state.get("teams", {}))

            # Wipe EVERYTHING — shared + user keys — so next login gets fresh DB data
            keys_to_delete = list(st.session_state.keys())
            for k in keys_to_delete:
                del st.session_state[k]

            # Force Supabase re-fetch on next page load
            st.session_state._sb_loaded = False
            st.rerun()


# ════════════════════════════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════════════════════════════

def render_header(title: str, subtitle: str):
    user      = st.session_state.current_user
    team      = get_team()
    team_name = st.session_state.current_team or ""
    member_role = team.get("roles", {}).get(user["name"], "Member") if team and team_name else ""

    left_col, right_col = st.columns([2.5, 1])
    with left_col:
        st.markdown(f"""
        <div class="nexus-header fade-in">
            <div class="nexus-logo-wrap">🔗</div>
            <div>
                <p class="nexus-title">{title}</p>
                <p class="nexus-subtitle">{subtitle}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with right_col:
        team_chip = f'<div style="background:rgba(255,107,71,0.15);border:1px solid rgba(255,107,71,0.3);border-radius:20px;padding:5px 12px;font-size:0.73rem;color:#ffb8a8;font-weight:600;">🏆 {team_name} · {member_role}</div>' if team_name else ""
        st.markdown(f"""
        <div style="display:flex;justify-content:flex-end;align-items:center;gap:8px;padding-top:0.5rem;flex-wrap:wrap;">
            {team_chip}
            <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1);
                 border-radius:20px;padding:5px 12px;font-size:0.73rem;color:rgba(255,255,255,0.6);">
                 👤 {user["name"]}</div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ════════════════════════════════════════════════════════════════

def render_dashboard():
    render_header("Dashboard", "Your project at a glance")
    user    = st.session_state.current_user
    team    = get_team()
    logbook = st.session_state.logbook
    t_name  = st.session_state.current_team

    # ── Conflict Banner ──
    if st.session_state.conflict_info and st.session_state.conflict_info.get("conflict"):
        ci = st.session_state.conflict_info
        try:
            date_str = datetime.datetime.fromisoformat(ci.get("conflicting_date","")).strftime("%b %d %Y")
        except Exception:
            date_str = ci.get("conflicting_date","") or "earlier"

        st.markdown(f"""
        <div class="conflict-banner fade-in">
            <strong>⚠️ Conflict Detected!</strong><br>
            This may contradict a decision from <strong>{date_str}</strong>.<br>
            <em style="opacity:0.8;">{ci.get('conflicting_memory','—')}</em><br>
            <span style="font-size:0.79rem;opacity:0.7;">{ci.get('reason','—')}</span>
        </div>
        """, unsafe_allow_html=True)
        oc, dc = st.columns(2)
        with oc:
            if st.button("✅ Override & Save", key="ov_btn"):
                if st.session_state._pending_content:
                    hs_retain(st.session_state._pending_content, st.session_state._pending_meta or {})
                    add_logbook(
                        st.session_state._pending_content,
                        st.session_state._pending_meta.get("category","general"),
                        st.session_state._pending_meta.get("author", user["name"]),
                        t_name or "General",
                    )
                st.session_state.conflict_info    = None
                st.session_state._pending_content = None
                st.session_state._pending_meta    = None
                st.session_state.last_retained    = "✅ Override saved."
                st.session_state.timeline_memories = hs_recent(top_k=5)
                st.rerun()
        with dc:
            if st.button("✕ Dismiss", key="dm_btn"):
                st.session_state.conflict_info    = None
                st.session_state._pending_content = None
                st.session_state._pending_meta    = None
                st.rerun()

    # ── Stats ──
    team_logs = [l for l in logbook if l["team"] == t_name] if t_name else logbook
    members   = len(team.get("members",[])) if team else 0
    roles_set = len([v for v in team.get("roles",{}).values() if v not in ("Member","Team Leader")]) if team else 0
    today_str = datetime.datetime.utcnow().strftime("%b %d")
    active_today = len([l for l in team_logs if today_str in l["timestamp"]])

    c1, c2, c3, c4 = st.columns(4)
    for col, var, val, lbl, accent in [
        (c1, "coral",  len(team_logs), "Log Entries",    "#ff6b47"),
        (c2, "violet", members,        "Team Members",   "#7c6fff"),
        (c3, "teal",   roles_set,      "Roles Assigned", "#00b894"),
        (c4, "amber",  active_today,   "Active Today",   "#f5a623"),
    ]:
        col.markdown(f"""
        <div style="background:#161b26;border:1px solid #1e2538;border-radius:14px;
             padding:1.3rem 1rem;text-align:center;position:relative;overflow:hidden;
             box-shadow:0 2px 16px rgba(0,0,0,0.4);">
            <div style="position:absolute;top:0;left:0;right:0;height:3px;
                 background:linear-gradient(90deg,{accent},{accent}88);"></div>
            <div style="font-family:Syne,sans-serif;font-size:2.4rem;font-weight:800;
                 color:{accent};line-height:1;margin-bottom:5px;">{val}</div>
            <div style="font-size:0.67rem;color:#444e66;font-weight:600;
                 text-transform:uppercase;letter-spacing:0.07em;">{lbl}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:0.6rem;'></div>", unsafe_allow_html=True)

    # ── Two columns: Activity + Team Snapshot ──
    left, right = st.columns([1.6, 1])

    with left:
        st.markdown('<div class="section-label">📋 Recent Activity</div>', unsafe_allow_html=True)
        if not team_logs:
            st.markdown("""
            <div style="background:#161a24;border:1px dashed #1e2538;border-radius:12px;
                 padding:2rem;text-align:center;color:#5a6278;">
                <div style="font-size:2rem;margin-bottom:8px;">📭</div>
                <div style="font-size:0.87rem;">No activity yet. Log your first entry!</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for log in reversed(team_logs[-8:]):
                cat  = log.get("category","general")
                safe = log["content"].replace("<","&lt;").replace(">","&gt;")
                st.markdown(f"""
                <div class="log-entry fade-in">
                    <div class="log-dot" style="background:{dot_color(cat)};width:8px;height:8px;border-radius:50%;margin-top:5px;flex-shrink:0;"></div>
                    <div style="flex:1;">
                        <div style="font-size:0.84rem;color:#e8eaf0;line-height:1.5;">{safe}</div>
                        <div style="font-size:0.69rem;color:#5a6278;margin-top:3px;font-family:'DM Mono',monospace;">
                            <span class="badge badge-{cat}">{cat}</span>
                            {log['author']} · {log['timestamp']}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-label">👥 Team Snapshot</div>', unsafe_allow_html=True)
        if not team:
            st.markdown("""
            <div style="background:#161a24;border:1px dashed #1e2538;border-radius:12px;
                 padding:1.5rem;text-align:center;color:#5a6278;">
                <div style="font-size:1.8rem;margin-bottom:6px;">🤝</div>
                <div style="font-size:0.82rem;">Create or join a team first.</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Go to Team →", key="goto_team"):
                st.session_state.current_page = "👥 Team"
                st.rerun()
        else:
            for m in team.get("members",[]):
                role_t  = team.get("roles",{}).get(m,"Member")
                is_lead = m == team["leader"]
                st.markdown(f"""
                <div class="member-pill {'leader' if is_lead else ''}"
                     style="display:flex;align-items:center;justify-content:space-between;
                     width:100%;margin:4px 0;border-radius:8px;padding:6px 10px;">
                    <span>{role_emoji(role_t)} <strong>{m}</strong></span>
                    <span class="role-tag">{role_t}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="section-label" style="margin-top:1rem;">⚡ Quick Actions</div>', unsafe_allow_html=True)
        if st.button("💬 Ask Nexus AI", use_container_width=True, key="qa_chat"):
            st.session_state.current_page = "💬 AI Chat"; st.rerun()
        if st.button("🕰 View Timeline", use_container_width=True, key="qa_tl"):
            st.session_state.current_page = "🕰 Timeline"; st.rerun()
        if not team:
            if st.button("👥 Create / Join Team", use_container_width=True, key="qa_team"):
                st.session_state.current_page = "👥 Team"; st.rerun()


# ════════════════════════════════════════════════════════════════
#  PAGE: TEAM MANAGER
# ════════════════════════════════════════════════════════════════

def render_team_page():
    render_header("Team Manager", "Create teams, assign roles, collaborate")
    user  = st.session_state.current_user
    teams = st.session_state.teams

    tab1, tab2, tab3 = st.tabs(["🏗  Create Team", "🚪  Join Team", "📋  My Team"])

    # ── CREATE ──
    with tab1:
        if user["role"] == "member":
            st.info("🔒 Only Team Leaders and Teachers can create teams.")
        else:
            _, mc, _ = st.columns([0.3, 2, 0.3])
            with mc:
                st.markdown("""
                <div style="background:#161a24;border:1px solid #1e2538;border-radius:14px;
                     padding:1.8rem;box-shadow:0 4px 16px rgba(0,0,0,0.4);margin-top:0.5rem;">
                    <div style="font-size:1rem;font-weight:700;color:#e8eaf0;margin-bottom:1rem;">🚀 Start a New Team</div>
                """, unsafe_allow_html=True)
                t_name   = st.text_input("Team Name",            placeholder="e.g. Team Phoenix 🔥")
                p_name   = st.text_input("Project Name",         placeholder="e.g. AI Food Delivery App")
                p_desc   = st.text_area("Project Description",   placeholder="What are you building? (optional)", height=80)
                create_b = st.button("🚀 Create Team", use_container_width=True, key="create_team_btn")
                st.markdown("</div>", unsafe_allow_html=True)

            if create_b:
                if not t_name.strip():
                    st.warning("Enter a team name.")
                elif t_name in teams:
                    st.error("Team name already taken!")
                else:
                    teams[t_name] = {
                        "leader":     user["name"],
                        "project":    p_name.strip() or "Untitled Project",
                        "desc":       p_desc.strip(),
                        "members":    [user["name"]],
                        "roles":      {user["name"]: "Team Leader"},
                        "created_at": datetime.datetime.utcnow().strftime("%b %d %Y"),
                    }
                    st.session_state.teams        = teams
                    st.session_state.current_team = t_name
                    sb_save_teams(teams)           # ← persist to Supabase
                    st.success(f"✅ Team **{t_name}** created!")
                    st.balloons()
                    st.rerun()

    # ── JOIN ──
    with tab2:
        # Always offer a refresh — teams created by other users only appear after reload
        rfc1, rfc2 = st.columns([3, 1])
        with rfc1:
            st.markdown('<div style="font-size:0.78rem;color:#5a6278;padding-top:0.5rem;">Teams are loaded from the server. Click Refresh to see teams created by other users.</div>', unsafe_allow_html=True)
        with rfc2:
            if st.button("🔄 Refresh", key="refresh_join_top", use_container_width=True):
                st.session_state._sb_loaded = False
                fresh = sb_load_teams()
                st.session_state.teams = fresh if fresh else {}
                st.session_state._sb_loaded = True
                st.rerun()

        teams = st.session_state.teams   # re-read after possible refresh

        if not teams:
            st.info("No teams yet. Ask your Team Leader to create one first.")
        else:
            for t_name, team in teams.items():
                already_in = user["name"] in team["members"]
                st.markdown(f"""
                <div class="team-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
                        <div>
                            <div class="team-name">🏆 {t_name}</div>
                            <div class="team-project">📁 {team['project']}</div>
                            {f'<div style="font-size:0.76rem;color:#5a6278;margin-top:3px;">{team["desc"][:80]}</div>' if team.get("desc") else ""}
                        </div>
                        <div style="text-align:right;font-size:0.71rem;color:#5a6278;">
                            👑 {team['leader']}<br>👥 {len(team['members'])} members
                        </div>
                    </div>
                    {'<span style="color:#00b894;font-size:0.77rem;font-weight:600;">✅ You are in this team</span>' if already_in else ''}
                </div>
                """, unsafe_allow_html=True)

                if not already_in:
                    if st.button(f"🚪 Join {t_name}", key=f"join_{t_name}"):
                        teams[t_name]["members"].append(user["name"])
                        teams[t_name]["roles"][user["name"]] = "Member"
                        st.session_state.current_team = t_name
                        sb_save_teams(st.session_state.teams)  # ← persist to Supabase
                        st.success(f"✅ Joined **{t_name}**!")
                        st.rerun()
                elif st.session_state.current_team != t_name:
                    if st.button(f"Switch to {t_name}", key=f"sw_{t_name}"):
                        st.session_state.current_team = t_name
                        st.rerun()

    # ── MY TEAM ──
    with tab3:
        if not st.session_state.current_team:
            st.info("You haven't joined a team yet. Go to **Join Team** above.")
        else:
            team   = get_team()
            t_name = st.session_state.current_team

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a1f2e,#252c3f);border-radius:14px;
                 padding:1.5rem;color:white;margin-bottom:1rem;position:relative;overflow:hidden;">
                <div style="position:absolute;top:-20px;right:-20px;width:100px;height:100px;
                     background:radial-gradient(circle,rgba(255,107,71,0.18),transparent);"></div>
                <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;">{t_name}</div>
                <div style="font-size:0.84rem;color:rgba(255,255,255,0.5);margin-top:2px;">📁 {team['project']}</div>
                {f'<div style="font-size:0.78rem;color:rgba(255,255,255,0.35);margin-top:4px;">{team.get("desc","")}</div>' if team.get("desc") else ""}
                <div style="display:flex;gap:16px;margin-top:12px;font-size:0.73rem;color:rgba(255,255,255,0.35);">
                    <span>👑 {team['leader']}</span>
                    <span>📅 {team.get('created_at','—')}</span>
                    <span>👥 {len(team['members'])} members</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Members grid
            st.markdown('<div class="section-label">👥 Members</div>', unsafe_allow_html=True)
            cols = st.columns(min(len(team["members"]), 3))
            for i, m in enumerate(team["members"]):
                role_t  = team.get("roles",{}).get(m,"Member")
                is_lead = m == team["leader"]
                with cols[i % 3]:
                    bg = "linear-gradient(135deg,rgba(245,166,35,0.12),rgba(245,166,35,0.06))" if is_lead else "#161a24"
                    bd = "rgba(245,166,35,0.3)" if is_lead else "#1e2538"
                    st.markdown(f"""
                    <div style="background:{bg};border:1px solid {bd};border-radius:12px;
                         padding:1rem;text-align:center;margin-bottom:8px;">
                        <div style="font-size:2rem;">{role_emoji(role_t)}</div>
                        <div style="font-weight:600;font-size:0.87rem;color:#e8eaf0;margin-top:4px;">{m}</div>
                        <div style="font-size:0.71rem;color:#5a6278;">{role_t}</div>
                        {'<div style="font-size:0.63rem;color:#f5a623;font-weight:700;margin-top:2px;">LEADER</div>' if is_lead else ''}
                    </div>
                    """, unsafe_allow_html=True)

            # Assign roles — leader only
            if is_leader():
                st.markdown('<div class="section-label">✏️ Assign Roles</div>', unsafe_allow_html=True)
                role_options = [
                    "Frontend Developer","Backend Developer","Full Stack Developer",
                    "UI/UX Designer","Documentation","DevOps Engineer","ML Engineer",
                    "QA Tester","Database Admin","Scrum Master","Custom...",
                ]
                rc1, rc2, rc3 = st.columns([2,2,1])
                with rc1:
                    target = st.selectbox("Member", team["members"], key="rm_sel", label_visibility="collapsed")
                with rc2:
                    picked = st.selectbox("Role", role_options, key="role_sel", label_visibility="collapsed")
                with rc3:
                    assign_b = st.button("Assign ✓", use_container_width=True, key="assign_role_btn")

                custom_r = st.text_input("Type custom role", key="custom_role_inp") if picked == "Custom..." else ""

                if assign_b:
                    final = custom_r.strip() if picked == "Custom..." else picked
                    if final:
                        team["roles"][target] = final
                        st.session_state.teams[t_name] = team
                        sb_save_teams(st.session_state.teams)   # ← persist to Supabase
                        log_c = f"{target} assigned as {final}"
                        add_logbook(log_c, "role", user["name"], t_name)
                        hs_retain(log_c, {"category":"role","author":user["name"],
                                          "timestamp":datetime.datetime.utcnow().isoformat()})
                        st.success(f"✅ {target} → {final}")
                        st.rerun()


# ════════════════════════════════════════════════════════════════
#  PAGE: AI CHAT
# ════════════════════════════════════════════════════════════════

def render_chat_page():
    render_header("AI Chat", "Ask Nexus anything about your project")
    user = st.session_state.current_user

    if st.session_state.chat_history:
        bubbles = '<div class="chat-wrap">'
        for turn in st.session_state.chat_history:
            name_label = user["name"] if turn["role"] == "user" else "🤖 Nexus AI"
            css        = "bubble-user" if turn["role"] == "user" else "bubble-assistant"
            content    = turn["content"].replace("<","&lt;").replace(">","&gt;")
            bubbles   += f'<div class="bubble {css}"><div class="bubble-role">{name_label}</div>{content}</div>'
        bubbles += '</div>'
        st.markdown(bubbles, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="chat-wrap">
            <div class="chat-empty">
                <div class="chat-empty-icon">💡</div>
                <div style="font-weight:600;color:#4a5162;">Ask me anything!</div>
                <div style="font-size:0.81rem;color:#5a6278;">
                    "Who is handling the frontend?"<br>
                    "Why did we choose Python?"<br>
                    "What's our current deadline?"
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    ic, bc = st.columns([5.5, 1])
    with ic:
        user_input = st.text_input("msg",
            placeholder="Ask about your project, decisions, roles, deadlines...",
            label_visibility="collapsed", key="chat_msg_input")
    with bc:
        send = st.button("Send ➤", use_container_width=True, key="send_chat")

    if send and user_input.strip():
        with st.spinner("Nexus is thinking…"):
            reply = chat_with_nexus(user_input, st.session_state.chat_history)
        st.session_state.chat_history.append({"role":"user",      "content":user_input})
        st.session_state.chat_history.append({"role":"assistant", "content":reply})
        st.rerun()

    # Suggested questions
    if not st.session_state.chat_history:
        st.markdown('<div class="section-label">💡 Suggested Questions</div>', unsafe_allow_html=True)
        suggestions = [
            "Who is handling the frontend?",
            "What tech stack did we decide on?",
            "What's our project deadline?",
            "What blockers do we have?",
            "Summarize our recent decisions",
        ]
        cols = st.columns(len(suggestions))
        for i, sug in enumerate(suggestions):
            with cols[i]:
                if st.button(sug, key=f"sug_{i}", use_container_width=True):
                    with st.spinner("Nexus is thinking…"):
                        reply = chat_with_nexus(sug, st.session_state.chat_history)
                    st.session_state.chat_history.append({"role":"user",      "content":sug})
                    st.session_state.chat_history.append({"role":"assistant", "content":reply})
                    st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑 Clear Chat", key="clear_chat_btn"):
            st.session_state.chat_history = []
            st.rerun()


# ════════════════════════════════════════════════════════════════
#  PAGE: TIMELINE
# ════════════════════════════════════════════════════════════════

def render_timeline_page():
    render_header("Truth Timeline", "Full history of all project decisions")

    rc, _ = st.columns([1, 5])
    with rc:
        if st.button("🔄 Refresh", key="tl_refresh"):
            st.session_state.timeline_memories = hs_recent(top_k=5)
            st.rerun()

    if not st.session_state.timeline_memories:
        st.session_state.timeline_memories = hs_recent(top_k=5)

    cat_filter = st.selectbox("Filter", ["All Categories"] + VALID_CATEGORIES,
                              label_visibility="collapsed", key="tl_filter")

    t_name    = st.session_state.current_team
    local_log = [l for l in st.session_state.logbook if (not t_name or l["team"] == t_name)]
    if cat_filter != "All Categories":
        local_log = [l for l in local_log if l["category"] == cat_filter]

    left, right = st.columns([1.5, 1])

    with left:
        st.markdown('<div class="section-label">📜 Hindsight Memory</div>', unsafe_allow_html=True)
        memories = st.session_state.timeline_memories
        if memories:
            for mem in memories:
                parsed = parse_memory_meta(mem)
                cat    = parsed["category"] if parsed["category"] in VALID_CATS_SET else "general"
                if cat_filter != "All Categories" and cat != cat_filter:
                    continue
                safe = parsed["content"].replace("<","&lt;").replace(">","&gt;")
                st.markdown(f"""
                <div class="timeline-card {cat} fade-in">
                    <span class="badge badge-{cat}">{cat}</span>
                    <span style="font-size:0.86rem;color:#e8eaf0;">{safe}</span>
                    <div class="timeline-meta">👤 {parsed['author']} · 🕓 {parsed['ts']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#161a24;border:1px dashed #1e2538;border-radius:12px;
                 padding:1.5rem;text-align:center;color:#5a6278;font-size:0.84rem;">
                🔌 Connect Hindsight backend to see persistent memories.
            </div>
            """, unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-label">📋 Session Log (Supabase)</div>', unsafe_allow_html=True)
        if local_log:
            for log in reversed(local_log[-10:]):
                cat  = log.get("category","general")
                safe = log["content"].replace("<","&lt;").replace(">","&gt;")
                st.markdown(f"""
                <div class="timeline-card {cat} fade-in">
                    <span class="badge badge-{cat}">{cat}</span>
                    <span style="font-size:0.83rem;color:#e8eaf0;">{safe}</span>
                    <div class="timeline-meta">👤 {log['author']} · 🕓 {log['timestamp']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#161a24;border:1px dashed #1e2538;border-radius:12px;
                 padding:1.5rem;text-align:center;color:#5a6278;font-size:0.84rem;">
                No entries yet. Log something from the sidebar!
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  PAGE: TEACHER VIEW
# ════════════════════════════════════════════════════════════════

def render_teacher_page():
    render_header("Teacher Dashboard", "Monitor all teams and student progress")

    # ── Force fresh load for teacher — they need cross-user data ──
    tc1, tc2 = st.columns([4, 1])
    with tc1:
        st.markdown('<div style="font-size:0.78rem;color:#5a6278;padding:0.3rem 0 0.6rem;">Teacher view shows all teams from the server. Reload to get the latest data.</div>', unsafe_allow_html=True)
    with tc2:
        if st.button("🔄 Reload", key="teacher_reload", use_container_width=True):
            st.session_state._sb_loaded = False
            fresh_teams = sb_load_teams()
            fresh_logs  = sb_load_logbook()
            st.session_state.teams   = fresh_teams if fresh_teams else {}
            st.session_state.logbook = fresh_logs  if fresh_logs  else []
            st.session_state._sb_loaded = True
            st.rerun()

    teams   = st.session_state.teams
    logbook = st.session_state.logbook

    # ── Supabase Debug Panel (always visible to teacher) ──
    with st.expander("🔌 Supabase Connection Status", expanded=not bool(teams)):
        dbg = sb_debug_status()
        col1, col2, col3 = st.columns(3)
        col1.metric("URL Set",    "✅ Yes" if dbg["url_set"]   else "❌ No")
        col2.metric("Key Set",    "✅ Yes" if dbg["key_set"]   else "❌ No")
        col3.metric("Connected",  "✅ Yes" if dbg["connected"] else "❌ No")
        if dbg["connected"]:
            c1, c2 = st.columns(2)
            c1.metric("Teams in DB",   dbg["teams_rows"])
            c2.metric("Log entries",   dbg["log_rows"])
            st.success("✅ Supabase is connected and working!")
        else:
            st.warning("⚠️ Supabase not connected. Using local JSON files for storage.")
    
    # ── Local File Debug Panel ──
    with st.expander("📁 Local File Storage Status", expanded=False):
        file_col1, file_col2 = st.columns(2)
        with file_col1:
            st.write("**Teams File**")
            st.code(TEAMS_BACKUP_FILE)
            if os.path.exists(TEAMS_BACKUP_FILE):
                st.success("✅ File exists")
                try:
                    with open(TEAMS_BACKUP_FILE, "r") as f:
                        teams_data = json.load(f)
                    st.metric("Teams count", len(teams_data))
                    st.json(teams_data)
                except Exception as e:
                    st.error(f"Error reading file: {e}")
            else:
                st.warning("❌ File doesn't exist yet")
        
        with file_col2:
            st.write("**Logbook File**")
            st.code(LOGBOOK_BACKUP_FILE)
            if os.path.exists(LOGBOOK_BACKUP_FILE):
                st.success("✅ File exists")
                try:
                    with open(LOGBOOK_BACKUP_FILE, "r") as f:
                        logbook_data = json.load(f)
                    st.metric("Entries count", len(logbook_data))
                    if logbook_data:
                        st.json(logbook_data[:3])  # Show first 3 entries
                        if len(logbook_data) > 3:
                            st.caption(f"... and {len(logbook_data) - 3} more entries")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
            else:
                st.warning("❌ File doesn't exist yet")
        elif dbg["error"]:
            st.error(f"❌ Error: {dbg['error']}")
            st.info("Check your SUPABASE_URL and SUPABASE_KEY in Streamlit secrets.")
        else:
            st.warning("⬜ Supabase not configured. Add SUPABASE_URL and SUPABASE_KEY to Streamlit secrets.")
            st.code("""
# Add these to Streamlit Cloud → Settings → Secrets:
SUPABASE_URL = "https://xxxxxxxxxxxx.supabase.co"
SUPABASE_KEY = "your_anon_public_key_here"
            """, language="toml")

        # Manual force-reload button
        if st.button("🔄 Force Reload from Supabase", key="force_reload"):
            st.session_state._sb_loaded = False
            fresh_teams = sb_load_teams()
            fresh_logs  = sb_load_logbook()
            st.session_state.teams   = fresh_teams
            st.session_state.logbook = fresh_logs
            st.session_state._sb_loaded = True
            st.success(f"Reloaded! Found {len(fresh_teams)} teams, {len(fresh_logs)} log entries.")
            st.rerun()

    if not teams:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#5a6278;">
            <div style="font-size:3rem;margin-bottom:1rem;">🏫</div>
            <div style="font-size:1rem;font-weight:600;color:#9ba3b8;">No teams created yet</div>
            <div style="font-size:0.84rem;margin-top:6px;">Teams will appear here once students create them.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Stats
    total_members = sum(len(t["members"]) for t in teams.values())
    today_str     = datetime.datetime.utcnow().strftime("%b %d")
    active_today  = len([l for l in logbook if today_str in l["timestamp"]])

    c1, c2, c3, c4 = st.columns(4)
    for col, var, val, lbl, accent in [
        (c1, "coral",  len(teams),        "Total Teams",    "#ff6b47"),
        (c2, "violet", total_members,     "Total Students", "#7c6fff"),
        (c3, "teal",   len(logbook),      "Log Entries",    "#00b894"),
        (c4, "amber",  active_today,      "Active Today",   "#f5a623"),
    ]:
        col.markdown(f"""
        <div style="background:#161b26;border:1px solid #1e2538;border-radius:14px;
             padding:1.2rem 1rem;text-align:center;position:relative;overflow:hidden;
             box-shadow:0 2px 16px rgba(0,0,0,0.4);">
            <div style="position:absolute;top:0;left:0;right:0;height:3px;
                 background:linear-gradient(90deg,{accent},{accent}88);"></div>
            <div style="font-family:Syne,sans-serif;font-size:2.2rem;font-weight:800;
                 color:{accent};line-height:1;margin-bottom:5px;">{val}</div>
            <div style="font-size:0.67rem;color:#444e66;font-weight:600;
                 text-transform:uppercase;letter-spacing:0.07em;">{lbl}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

    team_filter = st.selectbox("Filter",
        ["📊 All Teams"] + [f"🏆 {t}" for t in teams.keys()],
        label_visibility="collapsed", key="teacher_filter")
    selected = teams if team_filter == "📊 All Teams" else {
        team_filter.replace("🏆 ",""): teams[team_filter.replace("🏆 ","")]
    }

    for t_name, team in selected.items():
        team_logs = [l for l in logbook if l["team"] == t_name]
        progress  = min(100, len(team_logs) * 10)
        p_color   = "#00b894" if progress >= 60 else "#f5a623" if progress >= 30 else "#ff6b47"

        with st.expander(f"🏆  {t_name}  ·  {team['project']}  ·  {len(team['members'])} members", expanded=True):
            hi_col, prog_col = st.columns([2, 1])

            with hi_col:
                st.markdown(f"""
                <div style="background:#13161f;border-radius:10px;padding:1rem;margin-bottom:0.8rem;">
                    <div style="display:flex;gap:18px;flex-wrap:wrap;font-size:0.79rem;color:#5a6278;">
                        <span>👑 <strong style="color:#9ba3b8;">{team['leader']}</strong></span>
                        <span>📅 {team.get('created_at','—')}</span>
                        <span>📝 {len(team_logs)} logs</span>
                    </div>
                    <div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:4px;">
                """, unsafe_allow_html=True)
                for m in team["members"]:
                    role_t  = team.get("roles",{}).get(m,"Member")
                    is_lead = m == team["leader"]
                    st.markdown(f"""
                    <span class="member-pill {'leader' if is_lead else ''}">
                        {role_emoji(role_t)} {m}
                        <span style="opacity:0.55;font-size:0.63rem;">· {role_t}</span>
                    </span>
                    """, unsafe_allow_html=True)
                st.markdown("</div></div>", unsafe_allow_html=True)

            with prog_col:
                st.markdown(f"""
                <div style="background:#161a24;border:1px solid #1e2538;border-radius:10px;
                     padding:1rem;text-align:center;">
                    <div style="font-size:0.63rem;font-weight:700;color:#5a6278;
                         text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">Progress</div>
                    <div style="font-size:2rem;font-weight:800;color:{p_color};">{progress}%</div>
                    <div style="background:#1e2538;border-radius:4px;height:6px;margin-top:6px;">
                        <div style="background:{p_color};width:{progress}%;height:6px;border-radius:4px;"></div>
                    </div>
                    <div style="font-size:0.69rem;color:#5a6278;margin-top:4px;">{len(team_logs)} entries</div>
                </div>
                """, unsafe_allow_html=True)

            # Activity Logbook
            st.markdown('<div style="font-size:0.65rem;font-weight:700;color:#5a6278;text-transform:uppercase;letter-spacing:0.1em;margin:0.8rem 0 0.4rem;">📖 Activity Logbook</div>', unsafe_allow_html=True)
            if not team_logs:
                st.markdown('<div style="color:#5a6278;font-size:0.83rem;padding:0.4rem;">No activity logged yet.</div>', unsafe_allow_html=True)
            else:
                lc1, lc2 = st.columns(2)
                for i, log in enumerate(reversed(team_logs[-10:])):
                    cat  = log.get("category","general")
                    safe = log["content"].replace("<","&lt;").replace(">","&gt;")
                    card = f"""
                    <div class="log-entry">
                        <div class="log-dot" style="background:{dot_color(cat)};width:8px;height:8px;border-radius:50%;margin-top:5px;flex-shrink:0;"></div>
                        <div>
                            <div style="font-size:0.82rem;color:#e8eaf0;">{safe}</div>
                            <div style="font-size:0.68rem;color:#5a6278;margin-top:2px;">
                                <span class="badge badge-{cat}">{cat}</span>
                                {log['author']} · {log['timestamp']}
                            </div>
                        </div>
                    </div>
                    """
                    (lc1 if i % 2 == 0 else lc2).markdown(card, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════

if not is_logged_in():
    render_login()
    st.stop()

render_sidebar()

page = st.session_state.get("current_page", "🏠 Dashboard")

if page == "🏠 Dashboard":
    render_dashboard()
elif page == "👥 Team":
    render_team_page()
elif page == "💬 AI Chat":
    render_chat_page()
elif page == "🕰 Timeline":
    render_timeline_page()
elif page == "🎓 Teacher View":
    if is_teacher():
        render_teacher_page()
    else:
        st.error("🔒 Access denied. Teachers only.")
