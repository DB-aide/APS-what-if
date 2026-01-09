# config.py
# Android paths do NOT belong in config.py!

from pathlib import Path

# ===============================
# Project directories
# ===============================

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Assumes config.py is located inside the project.
    """
    return Path(__file__).resolve().parent


def ensure_directories() -> dict:
    """
    Ensures all required directories exist.
    Works on Linux, Windows, macOS.
    Returns paths as Path objects.
    """

    project_root = get_project_root()

    paths = {
        "PROJECT_ROOT": project_root,
        "WORKING_DIR": project_root / "your_working_directory",
        "AAPS_LOGS_DIR": project_root / "aapsLogs",
    }

    for name, path in paths.items():
        try:
            path.mkdir(parents=True, exist_ok=True)
            # print(f"[OK] Directory exists: {path}")
        except Exception as e:
            print(f"[ERROR] Cannot create {name}: {path} → {e}")

    return paths

# ===============================
# Initialize on import
# ===============================

PATHS = ensure_directories()

# Convenient shortcuts
PROJECT_ROOT = PATHS["PROJECT_ROOT"]
DEFAULT_WDIR = PATHS["WORKING_DIR"]
AAPS_LOGS_DIR = PATHS["AAPS_LOGS_DIR"]
VARYHOME = DEFAULT_WDIR

# Alias voor oudere code
WORKING_DIR = DEFAULT_WDIR

# Default file patterns
DEFAULT_AAPS_ZIP_PATTERN = AAPS_LOGS_DIR / "*.zip"

# encoding safe. No more PYTHONUTF8 hacks needed!
DEFAULT_ENCODING = "utf-8"
