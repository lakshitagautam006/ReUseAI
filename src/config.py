"""Configuration module for ReUseAI.
Loads environment variables and exposes unified settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Groq Vision AI Credentials & Settings
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

try:
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

GROQ_API_KEY = GROQ_API_KEY.strip()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()
APP_ENV = os.getenv("APP_ENV", "development").strip()

# Legacy alias (optional fallback)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Image Processing & API Constraints (Phase 3 Preprocessing Standards)
MAX_IMAGE_DIMENSION = 1024   # Max dimension constraint (preserves aspect ratio; downscales only >1024px)
MAX_FILE_SIZE_MB = 10        # Maximum upload size in Streamlit
SUPPORTED_IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]

# API Network & Retry Constraints
API_REQUEST_TIMEOUT_MS = 35000  # 35s request timeout
MAX_API_RETRIES = 2             # 1 initial attempt + 1 retry max


def is_api_configured() -> bool:
    """Check if a valid Groq API key is configured."""
    return bool(GROQ_API_KEY and not GROQ_API_KEY.startswith("your_"))
