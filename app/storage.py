"""Simple filesystem-backed storage for coachings and patient models.

No database - each record is one JSON metadata file on disk. Coaching uploads
additionally get their raw HTML saved alongside. This is intentionally simple:
the whole point is a small internal portal, not a multi-user system with
concurrent writers.
"""
from __future__ import annotations

import json
import shutil
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


def _delete_rgroups_files(coaching_id: str) -> None:
    """Derived rgroups-pipeline CSVs (see app/rgroups_tool.py) go stale once
    the bundle they were built from is gone."""
    for suffix in ("rgroups_table.csv", "rgroups_requests.csv", "rgroups_generated.csv"):
        (Config.COACHING_FILES_DIR / f"{coaching_id}.{suffix}").unlink(missing_ok=True)


def delete_coaching(coaching_id: str) -> bool:
    meta = get_coaching(coaching_id)
    if meta is None:
        return False
    file_path = Config.COACHING_FILES_DIR / meta["stored_filename"]
    file_path.unlink(missing_ok=True)
    if meta.get("bundle"):
        (Config.COACHING_FILES_DIR / meta["bundle"]["stored_filename"]).unlink(missing_ok=True)
    if meta.get("participant_import"):  # pre-chats legacy attachment, if never migrated
        pi = meta["participant_import"]
        (Config.COACHING_FILES_DIR / pi["raw_stored_filename"]).unlink(missing_ok=True)
        (Config.COACHING_FILES_DIR / pi["data_stored_filename"]).unlink(missing_ok=True)
    chats_dir = Config.COACHING_FILES_DIR / f"{coaching_id}.chats"
    if chats_dir.exists():
        shutil.rmtree(chats_dir)
    _delete_rgroups_files(coaching_id)
    (Config.COACHINGS_DIR / f"{coaching_id}.json").unlink(missing_ok=True)
    return True


def coaching_file_path(coaching_id: str) -> Path | None:
    meta = get_coaching(coaching_id)
    if meta is None:
        return None
    return Config.COACHING_FILES_DIR / meta["stored_filename"]


# ---------------------------------------------------------------------------
# Coaching bundle (coaching.json — the Stage-3 machine-readable export that
# unlocks the faithful chat engine). Attached to an existing coaching; the
# upload flow itself stays HTML-only.
# ---------------------------------------------------------------------------

class BundleError(ValueError):
    """Raised when an attached file isn't a usable coaching.json."""


def _bundle_summary(data: dict) -> dict:
    rules = data.get("rules") or {}
    sr = rules.get("sendingRules")
    val = data.get("validation") or {}
    return {
        "microDialogs": len(data.get("microDialogs") or []),
        "nodes": len(data.get("nodes") or []),
        "ruleTreeNodes": len(rules.get("ruleTree") or []),
        "sendingRules": len(sr) if sr is not None else None,
        "hasRules": bool(rules.get("ruleTree")),
        "scrapedAt": (data.get("coaching") or {}).get("scrapedAt"),
        "coherenceOk": val.get("ok"),
        "coherenceWarnings": val.get("warnings") or [],
    }


def save_coaching_bundle(coaching_id: str, file_bytes: bytes) -> dict:
    """Validate and attach a coaching.json to an existing coaching. Returns
    the updated coaching meta. Raises BundleError on a bad file."""
    meta = get_coaching(coaching_id)
    if meta is None:
        raise BundleError("coaching not found")
    try:
        data = json.loads(file_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise BundleError(f"not valid JSON: {e}") from None
    if not isinstance(data, dict):
        raise BundleError("expected a JSON object")
    missing = [k for k in ("microDialogs", "nodes") if not isinstance(data.get(k), list)]
    if missing:
        raise BundleError(
            f"not a coaching.json — missing list field(s): {', '.join(missing)}. "
            "Produce one with tools/coaching-bundle-export/export_coaching.sh.")

    stored = f"{coaching_id}.bundle.json"
    with open(Config.COACHING_FILES_DIR / stored, "wb") as f:
        f.write(file_bytes)

    meta["bundle"] = {
        "stored_filename": stored,
        "uploaded_at": _now_iso(),
        "size_bytes": len(file_bytes),
        "summary": _bundle_summary(data),
    }
    _write_json(Config.COACHINGS_DIR / f"{coaching_id}.json", meta)
    return meta


def delete_coaching_bundle(coaching_id: str) -> bool:
    meta = get_coaching(coaching_id)
    if meta is None or not meta.get("bundle"):
        return False
    (Config.COACHING_FILES_DIR / meta["bundle"]["stored_filename"]).unlink(missing_ok=True)
    meta.pop("bundle", None)
    _write_json(Config.COACHINGS_DIR / f"{coaching_id}.json", meta)
    _delete_rgroups_files(coaching_id)
    return True


def coaching_bundle_path(coaching_id: str) -> Path | None:
    meta = get_coaching(coaching_id)
    if meta is None or not meta.get("bundle"):
        return None
    p = Config.COACHING_FILES_DIR / meta["bundle"]["stored_filename"]
    return p if p.exists() else None


# ---------------------------------------------------------------------------
# Chats — every conversation explored in the Chat tab, persisted server-side
# so it survives a page reload and is listed in a sidebar: either a freshly
# simulated "live" run, or one seeded from a real participant's .pmcp export
# ("imported", via app.participant_import). A coaching can hold any number of
# each. Each chat's full {clock, vars, open_dialog, pending, transcript}
# state (app.coaching_sim.Simulator) lives in its own file under
# "<coaching_id>.chats/"; only a small summary is kept in the coaching's own
# meta file, for cheap sidebar listing.
# ---------------------------------------------------------------------------

def _chats_dir(coaching_id: str) -> Path:
    d = Config.COACHING_FILES_DIR / f"{coaching_id}.chats"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_chat_state(coaching_id: str, chat_id: str, state: dict) -> None:
    _write_json(_chats_dir(coaching_id) / f"{chat_id}.json", state)


def _read_chat_state(coaching_id: str, chat_id: str) -> dict | None:
    path = _chats_dir(coaching_id) / f"{chat_id}.json"
    if not path.exists():
        return None
    return _read_json(path)


def _migrate_legacy_participant_import(coaching_id: str, meta: dict) -> dict:
    """One-time upgrade path: before chats existed, a coaching could hold at
    most one attached participant_import. Turn it into a regular imported
    chat the first time this coaching's chats are touched post-redesign."""
    pi = meta.get("participant_import")
    if not pi:
        return meta
    from app.coaching_sim import Simulator

    data_path = Config.COACHING_FILES_DIR / pi["data_stored_filename"]
    raw_path = Config.COACHING_FILES_DIR / pi["raw_stored_filename"]
    if data_path.exists():
        import_data = _read_json(data_path)
        state = Simulator(model=None).initial_state_from_import(import_data)
        label = (import_data["participant"].get("nickname")
                 or import_data["participant"].get("systemUniqueId") or "participant")
        chat_id = uuid.uuid4().hex
        now = pi.get("uploaded_at") or _now_iso()
        summary = {
            "id": chat_id, "name": f"{label} (imported)", "kind": "imported",
            "created_at": now, "updated_at": now,
            "participant_summary": pi.get("summary"),
        }
        _write_chat_state(coaching_id, chat_id, state)
        if raw_path.exists():
            raw_path.rename(_chats_dir(coaching_id) / f"{chat_id}.pmcp")
        meta.setdefault("chats", []).append(summary)
    data_path.unlink(missing_ok=True)
    raw_path.unlink(missing_ok=True)
    meta.pop("participant_import", None)
    _write_json(Config.COACHINGS_DIR / f"{coaching_id}.json", meta)
    return meta


def list_chats(coaching_id: str) -> list[dict]:
    meta = get_coaching(coaching_id)
    if meta is None:
        return []
    meta = _migrate_legacy_participant_import(coaching_id, meta)
    return sorted(meta.get("chats", []), key=lambda c: c.get("updated_at", ""), reverse=True)


def get_chat(coaching_id: str, chat_id: str) -> dict | None:
    """A chat's summary plus its full state, for loading into the Chat tab
    when selected from the sidebar."""
    meta = get_coaching(coaching_id)
    if meta is None:
        return None
    meta = _migrate_legacy_participant_import(coaching_id, meta)
    summary = next((c for c in meta.get("chats", []) if c["id"] == chat_id), None)
    if summary is None:
        return None
    state = _read_chat_state(coaching_id, chat_id)
    if state is None:
        return None
    return {**summary, "state": state}


def create_chat(coaching_id: str, name: str, kind: str, state: dict,
                 participant_summary: dict | None = None) -> dict:
    meta = get_coaching(coaching_id)
    if meta is None:
        raise ValueError("coaching not found")
    chat_id = uuid.uuid4().hex
    now = _now_iso()
    summary = {
        "id": chat_id, "name": name, "kind": kind,
        "created_at": now, "updated_at": now,
        "participant_summary": participant_summary,
    }
    _write_chat_state(coaching_id, chat_id, state)
    meta.setdefault("chats", []).append(summary)
    _write_json(Config.COACHINGS_DIR / f"{coaching_id}.json", meta)
    return {**summary, "state": state}


def update_chat_state(coaching_id: str, chat_id: str, state: dict) -> bool:
    meta = get_coaching(coaching_id)
    if meta is None:
        return False
    summary = next((c for c in meta.get("chats", []) if c["id"] == chat_id), None)
    if summary is None:
        return False
    summary["updated_at"] = _now_iso()
    _write_chat_state(coaching_id, chat_id, state)
    _write_json(Config.COACHINGS_DIR / f"{coaching_id}.json", meta)
    return True


def rename_chat(coaching_id: str, chat_id: str, name: str) -> bool:
    meta = get_coaching(coaching_id)
    if meta is None:
        return False
    summary = next((c for c in meta.get("chats", []) if c["id"] == chat_id), None)
    if summary is None:
        return False
    summary["name"] = name
    _write_json(Config.COACHINGS_DIR / f"{coaching_id}.json", meta)
    return True


def delete_chat(coaching_id: str, chat_id: str) -> bool:
    meta = get_coaching(coaching_id)
    if meta is None:
        return False
    chats = meta.get("chats", [])
    remaining = [c for c in chats if c["id"] != chat_id]
    if len(remaining) == len(chats):
        return False
    meta["chats"] = remaining
    _write_json(Config.COACHINGS_DIR / f"{coaching_id}.json", meta)
    (_chats_dir(coaching_id) / f"{chat_id}.json").unlink(missing_ok=True)
    (_chats_dir(coaching_id) / f"{chat_id}.pmcp").unlink(missing_ok=True)
    return True


def create_imported_chat(coaching_id: str, filename: str, file_bytes: bytes) -> dict:
    """Parse a .pmcp export and add it as a new imported chat. Raises
    participant_import.ParticipantImportError on a bad file."""
    from app.coaching_sim import Simulator
    from app.participant_import import parse_pmcp

    if get_coaching(coaching_id) is None:
        raise ValueError("coaching not found")
    data = parse_pmcp(file_bytes)  # raises ParticipantImportError on bad input
    state = Simulator(model=None).initial_state_from_import(data)
    label = data["participant"].get("nickname") or data["participant"].get("systemUniqueId") or "participant"
    summary = {
        "nickname": data["participant"].get("nickname"),
        "systemUniqueId": data["participant"].get("systemUniqueId"),
        "variables": len(data["variables"]),
        "timelineEvents": len(data["timeline"]),
        "cascadesCompleted": data["dialog_status"].get("cascadesCompleted"),
        "warnings": data["warnings"],
    }
    chat = create_chat(coaching_id, name=f"{label} (imported)", kind="imported",
                        state=state, participant_summary=summary)
    with open(_chats_dir(coaching_id) / f"{chat['id']}.pmcp", "wb") as f:
        f.write(file_bytes)
    return chat


def reseed_imported_chat(coaching_id: str, chat_id: str) -> dict | None:
    """Re-parse an imported chat's original .pmcp and rebuild its seeded
    state from scratch — what "reset" means for an imported chat, since a
    plain blank reset would otherwise discard the only link back to the
    real participant it came from."""
    from app.coaching_sim import Simulator
    from app.participant_import import parse_pmcp

    raw_path = _chats_dir(coaching_id) / f"{chat_id}.pmcp"
    if not raw_path.exists():
        return None
    data = parse_pmcp(raw_path.read_bytes())
    return Simulator(model=None).initial_state_from_import(data)


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
