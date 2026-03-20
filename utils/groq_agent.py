"""
utils/groq_agent.py — Groq LLM client, conflict detection, and chat agent.
"""

import json
import streamlit as st
from config import GROQ_API_KEY, GROQ_MODEL
from utils.hindsight_helper import hs_recall


# ── Cached client ──────────────────────────────────────────────

@st.cache_resource
def get_groq_client():
    """Instantiate and cache a Groq client."""
    try:
        from groq import Groq
        return Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"Groq init error: {e}")
        return None


# ── Conflict Detection ─────────────────────────────────────────

_CONFLICT_SYSTEM = """
You are a conflict-detection engine for a project management tool.
Given a NEW entry and a list of EXISTING memories, decide if the new entry
contradicts any existing decision (e.g. changes a deadline, re-assigns a role,
reverses a technology choice).

Reply with ONLY valid JSON — no markdown fences, no preamble:
{
  "conflict": true | false,
  "conflicting_memory": "<exact content of conflicting memory, or empty string>",
  "conflicting_date": "<ISO timestamp of conflicting memory, or empty string>",
  "reason": "<one-sentence explanation, or empty string>"
}
"""

def detect_conflict(new_entry: str, memories: list) -> dict:
    """
    Ask Groq to compare new_entry against existing memories.

    Args:
        new_entry : The new event/decision text.
        memories  : List of existing memory dicts from Hindsight.

    Returns:
        Dict with keys: conflict (bool), conflicting_memory,
                        conflicting_date, reason.
    """
    groq = get_groq_client()
    if groq is None or not memories:
        return {"conflict": False}

    memory_text = "\n".join(
        f"- [{m.get('timestamp', '?')}] {m.get('content', '')}"
        for m in memories[:10]
    )
    user_msg = f"NEW ENTRY:\n{new_entry}\n\nEXISTING MEMORIES:\n{memory_text}"

    try:
        resp = groq.chat.completions.create(
            model       = GROQ_MODEL,
            messages    = [
                {"role": "system", "content": _CONFLICT_SYSTEM},
                {"role": "user",   "content": user_msg},
            ],
            temperature = 0.1,
            max_tokens  = 300,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.lower().startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        st.warning(f"Conflict detection error: {e}")
        return {"conflict": False}


# ── Chat Agent ─────────────────────────────────────────────────

_CHAT_SYSTEM = """
You are Nexus, an intelligent AI project manager embedded in a team's
collaboration tool. You have access to the team's persistent memory.

CONTEXT FROM MEMORY:
{context}

Rules:
1. Answer questions using the retrieved memory context above when relevant.
2. If memory is empty, say so honestly and offer to help anyway.
3. Be concise, structured, and professional.
4. When citing a decision, always mention who made it and when (if known).
5. Never invent facts not present in the memory context.
"""

def chat_with_nexus(user_question: str, history: list) -> str:
    """
    Retrieves relevant Hindsight memories, injects them as context,
    then asks Groq to answer the user's question.

    Args:
        user_question : The user's chat input.
        history       : List of prior {role, content} turns.

    Returns:
        Assistant reply string.
    """
    groq = get_groq_client()
    if groq is None:
        return "Groq client unavailable. Check your GROQ_API_KEY."

    memories = hs_recall(user_question, top_k=5)
    context  = (
        "\n".join(
            f"[{m.get('timestamp','?')}] {m.get('content','')}"
            for m in memories
        )
        if memories else "No relevant memories found."
    )

    groq_messages = [
        {"role": "system", "content": _CHAT_SYSTEM.format(context=context)}
    ]
    for turn in history[-10:]:
        groq_messages.append({"role": turn["role"], "content": turn["content"]})
    groq_messages.append({"role": "user", "content": user_question})

    try:
        resp = groq.chat.completions.create(
            model       = GROQ_MODEL,
            messages    = groq_messages,
            temperature = 0.5,
            max_tokens  = 800,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Groq error: {e}"
