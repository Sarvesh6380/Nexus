"""
config.py — Environment variables & global constants for Nexus.
Reads from st.secrets (Streamlit Cloud) first, then .env, then defaults.
"""
import os
from dotenv import load_dotenv

load_dotenv()

def _get(key: str, default: str = "") -> str:
    """Try st.secrets first (Streamlit Cloud), then os.environ, then default."""
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return val
    except Exception:
        pass
    return os.getenv(key, default)

GROQ_API_KEY      = _get("GROQ_API_KEY")
HINDSIGHT_API_URL = _get("HINDSIGHT_API_URL", "http://localhost:8888")
HINDSIGHT_API_KEY = _get("HINDSIGHT_API_KEY")
HINDSIGHT_BANK_ID = _get("HINDSIGHT_BANK_ID", "nexus-project")
SUPABASE_URL      = _get("SUPABASE_URL")
SUPABASE_KEY      = _get("SUPABASE_KEY")
GROQ_MODEL        = "llama-3.3-70b-versatile"

VALID_CATEGORIES  = ["decision", "task", "role", "blocker", "general"]
VALID_CATS_SET    = set(VALID_CATEGORIES)
