"""Simple filesystem-backed storage for coachings and patient models.

No database - each record is one JSON metadata file on disk. Coaching uploads
additionally get their raw HTML saved alongside. This is intentionally simple:
the whole point is a small internal portal, not a multi-user system with
concurrent writers.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.coaching_stats import compute_stats
from app.config import Config


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: dict):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Coachings
# ---------------------------------------------------------------------------

def list_coachings():
    records = []
    for meta_path in Config.COACHINGS_DIR.glob("*.json"):
        records.append(_read_json(meta_path))
    records.sort(key=lambda r: r.get("uploaded_at", ""), reverse=True)
    return records


def get_coaching(coaching_id: str):
    meta_path = Config.COACHINGS_DIR / f"{coaching_id}.json"
    if not meta_path.exists():
        return None
    return _read_json(meta_path)


def save_coaching(name: str, tag: str, filename: str, file_bytes: bytes):
    coaching_id = uuid.uuid4().hex
    stored_filename = f"{coaching_id}.html"
    file_path = Config.COACHING_FILES_DIR / stored_filename
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    try:
        stats = compute_stats(file_bytes)
    except Exception:
        # A malformed/unexpected export shouldn't block the upload - just
        # store it without stats rather than losing the file.
        stats = {}

    meta = {
        "id": coaching_id,
        "name": name,
        "tag": tag,
        "original_filename": filename,
        "stored_filename": stored_filename,
        "size_bytes": len(file_bytes),
        "uploaded_at": _now_iso(),
        "stats": stats,
    }
    _write_json(Config.COACHINGS_DIR / f"{coaching_id}.json", meta)
    return meta


def delete_coaching(coaching_id: str) -> bool:
    meta = get_coaching(coaching_id)
    if meta is None:
        return False
    file_path = Config.COACHING_FILES_DIR / meta["stored_filename"]
    file_path.unlink(missing_ok=True)
    (Config.COACHINGS_DIR / f"{coaching_id}.json").unlink(missing_ok=True)
    return True


def coaching_file_path(coaching_id: str) -> Path | None:
    meta = get_coaching(coaching_id)
    if meta is None:
        return None
    return Config.COACHING_FILES_DIR / meta["stored_filename"]


# ---------------------------------------------------------------------------
# Patient models
# ---------------------------------------------------------------------------

PATIENT_MODEL_FIELDS = [
    "name",
    "archetype_tag",
    "notification_response_minutes",
    "phone_time_minutes_per_day",
    "sleep_start",
    "sleep_end",
    "adherence_spirometry_pct",
    "adherence_medication_pct",
    "adherence_acq_pct",
    "adherence_education_pct",
    "completion_after_engagement_pct",
    "reschedule_acceptance_pct",
    "notes",
]


def list_patient_models():
    records = []
    for meta_path in Config.PATIENT_MODELS_DIR.glob("*.json"):
        records.append(_read_json(meta_path))
    records.sort(key=lambda r: r.get("name", "").lower())
    return records


def get_patient_model(model_id: str):
    meta_path = Config.PATIENT_MODELS_DIR / f"{model_id}.json"
    if not meta_path.exists():
        return None
    return _read_json(meta_path)


def save_patient_model(data: dict, model_id: str | None = None):
    is_new = model_id is None
    if is_new:
        model_id = uuid.uuid4().hex

    record = {field: data.get(field, "") for field in PATIENT_MODEL_FIELDS}
    record["id"] = model_id
    record["created_at"] = data.get("created_at") or _now_iso()
    record["updated_at"] = _now_iso()

    _write_json(Config.PATIENT_MODELS_DIR / f"{model_id}.json", record)
    return record


def delete_patient_model(model_id: str) -> bool:
    meta_path = Config.PATIENT_MODELS_DIR / f"{model_id}.json"
    if not meta_path.exists():
        return False
    meta_path.unlink()
    return True
