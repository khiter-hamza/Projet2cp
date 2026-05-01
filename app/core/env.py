import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env once from common locations.
ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_CANDIDATES = [
    ROOT_DIR / ".env",
    ROOT_DIR / "backend" / ".env",
]

for env_path in ENV_CANDIDATES:
    if env_path.exists():
        load_dotenv(env_path, override=False)
        break


# Example exports (similar to JS env module pattern)


# Mail configuration exports
