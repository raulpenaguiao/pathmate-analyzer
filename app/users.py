"""Portal accounts beyond the .env login.

The .env user (APP_USERNAME / APP_PASSWORD) is the admin: it always works,
can't be deleted here, and its password lives in the deployment secrets.
Every other account is a row in DATA_DIR/users.json, which the deploy's
rsync leaves alone (data/ is excluded), so accounts survive redeploys.
Passwords are stored only as Werkzeug hashes.
"""
from __future__ import annotations

import hmac
import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

from app.config import Config

USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{2,40}$")
MIN_PASSWORD_LEN = 10
ROLES = ("user", "admin")
_DUMMY_HASH = generate_password_hash(secrets.token_urlsafe(16))


class UserError(ValueError):
    """A request the caller should show back to the admin as-is."""


def _users_path() -> Path:
    return Config.DATA_DIR / "users.json"


def _load() -> dict:
    p = _users_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _save(users: dict) -> None:
    p = _users_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(users, indent=2, sort_keys=True), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(p)


def is_env_admin(username: str) -> bool:
    return bool(Config.APP_USERNAME) and username == Config.APP_USERNAME


def check_env_admin(username: str, password: str) -> bool:
    if not Config.APP_USERNAME or not Config.APP_PASSWORD:
        return False
    return (hmac.compare_digest(username.encode(), Config.APP_USERNAME.encode())
            and hmac.compare_digest(password.encode(), Config.APP_PASSWORD.encode()))


def authenticate(username: str, password: str) -> dict | None:
    """{"username", "is_admin"} for valid credentials, else None."""
    if check_env_admin(username, password):
        return {"username": username, "is_admin": True}
    if is_env_admin(username):
        return None  # the .env name never falls through to users.json
    rec = _load().get(username)
    # hash-check even unknown names, so response time doesn't reveal which exist
    ok = check_password_hash(rec["password_hash"] if rec else _DUMMY_HASH, password)
    if rec and ok:
        return {"username": username, "is_admin": rec.get("role") == "admin"}
    return None


def exists(username: str) -> bool:
    return is_env_admin(username) or username in _load()


def is_admin(username: str) -> bool:
    if is_env_admin(username):
        return True
    rec = _load().get(username)
    return bool(rec) and rec.get("role") == "admin"


def list_users() -> list[dict]:
    """Public fields only, never the hash."""
    return [
        {"username": name, "role": rec.get("role", "user"),
         "created_at": rec.get("created_at", ""), "created_by": rec.get("created_by", "")}
        for name, rec in sorted(_load().items())
    ]


def generate_password() -> str:
    return secrets.token_urlsafe(12)


def _check_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LEN:
        raise UserError(f"Passwords need at least {MIN_PASSWORD_LEN} characters.")


def create_user(username: str, password: str, role: str, created_by: str) -> None:
    username = username.strip()
    if not USERNAME_RE.match(username):
        raise UserError("Usernames are 2-40 characters: letters, digits, '.', '_' or '-'.")
    if role not in ROLES:
        raise UserError("Unknown role.")
    _check_password(password)
    users = _load()
    if is_env_admin(username) or username in users:
        raise UserError(f"The username '{username}' is already taken.")
    users[username] = {
        "password_hash": generate_password_hash(password),
        "role": role,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "created_by": created_by,
    }
    _save(users)


def set_password(username: str, password: str) -> None:
    if is_env_admin(username):
        raise UserError("The admin's password is set in the deployment secrets, not here.")
    _check_password(password)
    users = _load()
    if username not in users:
        raise UserError("No such user.")
    users[username]["password_hash"] = generate_password_hash(password)
    _save(users)


def delete_user(username: str) -> None:
    if is_env_admin(username):
        raise UserError("The .env admin can't be deleted.")
    users = _load()
    if users.pop(username, None) is None:
        raise UserError("No such user.")
    _save(users)
