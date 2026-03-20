"""
utils/hindsight_helper.py — All Hindsight retain/recall helpers for Nexus.
Package: pip install hindsight-client
"""

import datetime
import streamlit as st
from config import HINDSIGHT_API_URL, HINDSIGHT_BANK_ID


@st.cache_resource
def get_hindsight_client():
    """Instantiate and cache a Hindsight client."""
    try:
        from hindsight_client import Hindsight
        return Hindsight(base_url=HINDSIGHT_API_URL)
    except Exception as e:
        st.error(f"Hindsight init error: {e}")
        return None


def hs_retain(content: str, metadata: dict) -> object | None:
    """
    Save a memory to Hindsight.
    Encodes category + author into content string for searchability.
    """
    hs = get_hindsight_client()
    if hs is None:
        return None
    try:
        ts       = metadata.get("timestamp", datetime.datetime.utcnow().isoformat())
        category = metadata.get("category", "general")
        author   = metadata.get("author",   "Team")
        enriched = f"[{category.upper()}] (by {author}) {content}"
        return hs.retain(
            bank_id   = HINDSIGHT_BANK_ID,
            content   = enriched,
            context   = category,
            timestamp = ts,
        )
    except Exception as e:
        st.warning(f"Hindsight retain error: {e}")
        return None


def hs_recall(query: str, top_k: int = 5) -> list:
    """Retrieve semantically relevant memories for a query."""
    hs = get_hindsight_client()
    if hs is None:
        return []
    try:
        resp = hs.recall(bank_id=HINDSIGHT_BANK_ID, query=query)
        raw  = getattr(resp, "results", resp) or []
        memories = []
        for r in raw[:top_k]:
            if isinstance(r, dict):
                text, ts = r.get("text", ""), r.get("timestamp", "")
            else:
                text, ts = getattr(r, "text", str(r)), getattr(r, "timestamp", "")
            memories.append({"content": text, "timestamp": ts})
        return memories
    except Exception as e:
        st.warning(f"Hindsight recall error: {e}")
        return []


def hs_recent(top_k: int = 5) -> list:
    """Fetch recent memories for the Truth Timeline."""
    return hs_recall(
        "project decision task role update assignment deadline",
        top_k=top_k,
    )


def parse_memory_meta(mem: dict) -> dict:
    """
    Unpack category, author, timestamp from enriched memory string.
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
