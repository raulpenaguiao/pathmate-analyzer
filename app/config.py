import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    APP_USERNAME = os.environ.get("APP_USERNAME", "")
    APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
    SECRET_KEY = os.environ.get("APP_SECRET_KEY", "")

    # More than one account now (app/users.py) and no CSRF tokens: Lax keeps
    # the session cookie off cross-site POSTs. Secure is opt-in, since local
    # runs are plain http; set SESSION_COOKIE_SECURE=1 behind HTTPS.
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "") == "1"

    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data")).resolve()
    COACHINGS_DIR = DATA_DIR / "coachings"
    COACHING_FILES_DIR = COACHINGS_DIR / "files"
    PATIENT_MODELS_DIR = DATA_DIR / "patient_models"

    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB, coaching exports can be large

    @classmethod
    def ensure_dirs(cls):
        cls.COACHING_FILES_DIR.mkdir(parents=True, exist_ok=True)
        cls.PATIENT_MODELS_DIR.mkdir(parents=True, exist_ok=True)
