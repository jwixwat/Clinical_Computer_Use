"""
Central configuration for the supervised computer-use harness.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[3]
TRACE_DIR = ROOT / "traces"
SCREENSHOT_DIR = ROOT / "screenshots"
LOG_DIR = ROOT / "logs"

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_SAFETY_IDENTIFIER = os.getenv("OPENAI_SAFETY_IDENTIFIER", "clinical_computer_use")
PROMPT_BUNDLE_VERSION = os.getenv("PROMPT_BUNDLE_VERSION", "n1.v2")
POLICY_BUNDLE_VERSION = os.getenv("POLICY_BUNDLE_VERSION", "myle.v1")
TOOL_SURFACE_VERSION = os.getenv("TOOL_SURFACE_VERSION", "ui-candidate.v1")
ARTIFACT_POLICY_VERSION = os.getenv("ARTIFACT_POLICY_VERSION", "phi.v1")
ARTIFACT_RETENTION_DAYS = int(os.getenv("ARTIFACT_RETENTION_DAYS", "14"))
MYLE_USERNAME = os.getenv("MYLE_USERNAME", "")
MYLE_PASSWORD = os.getenv("MYLE_PASSWORD", "")

CHROME_PATH = os.getenv(
    "CHROME_PATH",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
)
CHROME_PROFILE_DIR = os.getenv(
    "CHROME_PROFILE_DIR",
    str(ROOT / ".chrome_profile"),
)
DEBUG_URL = os.getenv("DEBUG_URL", "http://127.0.0.1:9222")
EMR_BASE_URL = os.getenv("EMR_BASE_URL", "https://chmg.medfarsolutions.com/html5")
EMR_URL_PATTERN = os.getenv("EMR_URL_PATTERN", "chmg.medfarsolutions.com/html5")
MYLE_LOGIN_USERNAME_SELECTOR = os.getenv("MYLE_LOGIN_USERNAME_SELECTOR", "input[data-cy='login-username']")
MYLE_LOGIN_PASSWORD_SELECTOR = os.getenv("MYLE_LOGIN_PASSWORD_SELECTOR", "input[data-cy='login-password']")
MYLE_LOGIN_BUTTON_SELECTOR = os.getenv("MYLE_LOGIN_BUTTON_SELECTOR", "button[data-cy='login-button']")

ALLOWED_DOMAINS = tuple(
    domain.strip()
    for domain in os.getenv("ALLOWED_DOMAINS", "chmg.medfarsolutions.com").split(",")
    if domain.strip()
)

MAX_AGENT_STEPS = int(os.getenv("MAX_AGENT_STEPS", "75"))
MAX_RUN_MINUTES = int(os.getenv("MAX_RUN_MINUTES", "20"))

AUTONOMY_MAX_CONSECUTIVE_T0 = int(os.getenv("AUTONOMY_MAX_CONSECUTIVE_T0", "4"))
AUTONOMY_MAX_CONSECUTIVE_T1 = int(os.getenv("AUTONOMY_MAX_CONSECUTIVE_T1", "1"))
AUTONOMY_MAX_SAME_SURFACE_NO_PROGRESS = int(os.getenv("AUTONOMY_MAX_SAME_SURFACE_NO_PROGRESS", "3"))
CHECKPOINT_MAX_ROLLING_PER_6_STEPS = int(os.getenv("CHECKPOINT_MAX_ROLLING_PER_6_STEPS", "2"))
