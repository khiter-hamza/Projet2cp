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
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = (os.getenv("MAIL_PASSWORD") or "").replace(" ", "")
MAIL_FROM = os.getenv("MAIL_FROM") or MAIL_USERNAME
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USE_TLS = (os.getenv("MAIL_USE_TLS", "false").strip().lower() in {"1", "true", "yes", "on"})
