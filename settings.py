import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

KALSHI_API_BASE_URL = os.getenv("KALSHI_API_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2")
RT_POLL_INTERVAL_SECONDS = int(os.getenv("RT_POLL_INTERVAL_SECONDS", "60"))
DEFAULT_EDGE_THRESHOLD = float(os.getenv("DEFAULT_EDGE_THRESHOLD", "0.12"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
