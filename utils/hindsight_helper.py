"""
utils/hindsight_helper.py — All Hindsight retain/recall helpers for Nexus.
"""

import datetime
import streamlit as st
from config import HINDSIGHT_API_URL, HINDSIGHT_BANK_ID


# ── Cached client ──────────────────────────────────────────────

@st.cache_resource
def get_hindsight_client():
    """
    Try to connect to Hindsight. Returns None silently if not available.
    Install: pip install hindsight-client
    """
    try:
        from hindsight_client import Hindsight
        return Hindsight(base_url=HINDSIGHT_API_URL)
    except ImportError:
        return None   # package not installed — silent, app works without it
    except Exception:
        return None   # backend not running — silent


# ── Core Operations ────────────────────────────────────────────

def hs_retain(content: str, metadata: dict) -> object | None:
    """
    Save a memory to Hindsight.
    Encodes category + author directly into content string so
    they remain searchable and recoverable after recall().
    """
    hs = get_hindsight_client()
    if hs is None:
        return None
    try:
        ts       = metadata.get("timestamp", datetime.datetime.utcnow().isoformat())
        category = metadata.get("category", "general")
        author   = metadata.get("author",   "Team")
        enriched = f"[{category.upper()}] (by {author}) {content}"
        result   = hs.retain(
            bank_id   = HINDSIGHT_BANK_ID,
            content   = enriched,
            context   = category,
            timestamp = ts,
        )
        return result
    except Exception as e:
        return None  # Hindsight unavailable
        return None


def hs_recall(query: str, top_k: int = 5) -> list:
    """
    Retrieve semantically relevant memories for a query.
    Returns list of dicts: [{"content": str, "timestamp": str}, ...]
    """
    hs = get_hindsight_client()
    if hs is None:
        return []
    try:
        resp = hs.recall(
            bank_id = HINDSIGHT_BANK_ID,
            query   = query,
        )
        raw      = getattr(resp, "results", resp) or []
        memories = []
        for r in raw[:top_k]:
            if isinstance(r, dict):
                text = r.get("text", "")
                ts   = r.get("timestamp", "")
            else:
                text = getattr(r, "text", str(r))
                ts   = getattr(r, "timestamp", "")
            memories.append({"content": text, "timestamp": ts})
        return memories
    except Exception as e:
        return []   # Hindsight unavailable
        return []


def hs_recent(top_k: int = 5) -> list:
    """
    Fetch recent memories for the Truth Timeline.
    """
    return hs_recall(
        "project decision task role update assignment deadline",
        top_k=top_k,
    )


def parse_memory_meta(mem: dict) -> dict:
    """
    Extract category, author, timestamp from enriched memory string.
    Format: [CATEGORY] (by AUTHOR) <original text>
    """
    content  = mem.get("content", "")
    category = "general"
    author   = "Unknown"
    ts_raw   = mem.get("timestamp", "")

    if content.startswith("[") and "]" in content:
        try:
            tag_end  = content.index("]")
            category = content[1:tag_end].lower()
            rest     = content[tag_end + 1:].strip()
            if rest.startswith("(by ") and ")" in rest:
                auth_end = rest.index(")")
                author   = rest[4:auth_end]
                content  = rest[auth_end + 1:].strip()
            else:
                content = rest
        except Exception:
            pass

    try:
        ts = datetime.datetime.fromisoformat(ts_raw).strftime("%b %d %Y · %H:%M UTC")
    except Exception:
        ts = ts_raw or "—"

    return {"content": content, "category": category, "author": author, "ts": ts}
