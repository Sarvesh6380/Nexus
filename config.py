"""
config.py — Environment variables & global constants for Nexus.
"""

import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
HINDSIGHT_API_URL = os.getenv("HINDSIGHT_API_URL", "http://localhost:8888")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "")
HINDSIGHT_BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "nexus-project")
GROQ_MODEL = "llama-3.3-70b-versatile"

VALID_CATEGORIES  = ["decision", "task", "role", "blocker", "general"]
VALID_CATS_SET    = set(VALID_CATEGORIES)
