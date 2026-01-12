"""
update by author: Dries Bakker (NL) With the help of ChatGTP
File name: config.py

Version: 1.0.0 12-01-2026 Now works well for Windows, Linux, Mac, and Android.

"""

from pathlib import Path
import os

# ==================================================
# Project root
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent

# ==================================================
# Working directory (output from emulator)
# ==================================================
# This used to be often hardcoded → now os-proof
DEFAULT_ROOT = os.getcwd()
DEFAULT_WDIR = PROJECT_ROOT / "your_working_directory"

# ==================================================
# AAPS log directories
# ==================================================

# Standard Linux/PC logs
AAPS_LOGS_DIR = PROJECT_ROOT / "aapsLogs"

# Android (NOT used automatically,
# only available if the code explicitly requests it)
ANDROID_AAPS_LOG_DIRS = [
    Path("/storage/emulated/0/Documents/aapsLogs"),  # Android 11+
]

# ==================================================
# Ensure directories exist (safe)
# ==================================================

for d in (
    DEFAULT_WDIR,
    AAPS_LOGS_DIR,
):
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[config] Cannot create directory {d}: {e}")

# ==================================================
# File patterns
# ==================================================

DEFAULT_AAPS_ZIP_PATTERN = AAPS_LOGS_DIR / "*.zip"

# ==================================================
# Encoding safe. No more PYTHONUTF8 hacks needed!
# ==================================================

DEFAULT_ENCODING = "utf-8"

# ==================================================
# Compatibility aliases (IMPORTANT)
# ==================================================
# Some old code expects this name
VARYHOME = DEFAULT_WDIR

# ===============================
# Platform behavior
# ===============================

# When True:
#   - emulator_batch.py will try Android paths
# When False (default):
#   - always use AAPS_LOGS_DIR for input
ENABLE_ANDROID_DETECTION = False
