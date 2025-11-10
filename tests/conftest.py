"""
Pytest configuration for RIH Assistant (Phase 6 baseline)
- Ensures project root is on sys.path
- Optionally loads .env if present
- Sets safe defaults so new Phase 6 pieces won't break Phase 5
"""

import os
import sys
import pathlib
import logging

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Optional: load .env if python-dotenv is installed (no hard dependency)
try:
    from dotenv import load_dotenv  # type: ignore

    env_path = ROOT / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except Exception:
    # Safe to ignore if not available
    pass

# Defaults: Phase 5 behavior, Phase 6 features off
os.environ.setdefault("STRANDS_ENABLED", "false")
os.environ.setdefault("RIH_PLANNER", "RULE")
os.environ.setdefault("PYTHONHASHSEED", "0")

# Keep test logs calm
logging.basicConfig(level=logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
