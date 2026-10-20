import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
for _folder in ["core", "market", "scrapers", "models", "pipelines"]:
    _folder_path = str(REPO_ROOT / _folder)
    if _folder_path not in sys.path:
        sys.path.insert(0, _folder_path)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

KALSHI_API_BASE_URL = os.getenv("KALSHI_API_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2")
RT_POLL_INTERVAL_SECONDS = int(os.getenv("RT_POLL_INTERVAL_SECONDS", "60"))
DEFAULT_EDGE_THRESHOLD = float(os.getenv("DEFAULT_EDGE_THRESHOLD", "0.12"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
