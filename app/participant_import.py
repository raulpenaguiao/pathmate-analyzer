"""Parses a ``.pmcp`` export - a zip of raw PMCP/Mongo persistence dumps for
one participant - into a compact, portal-friendly snapshot: a current
``$variable`` state plus a chronological timeline of everything actually
observable, for seeding the Chat tab's simulator with a real participant's
history instead of a blank one.

A ``.pmcp`` file holds one flat member per Mongo document, named
``M <ClassName> <ObjectId>`` (no extension). Each member JSON-encodes an
envelope whose own ``content`` field is *itself* JSON, encoded as a string:

    {"clazz": "ParticipantVariableWithValue", "objectId": "...",
     "content": "{\\"name\\":\\"$foo\\",\\"value\\":\\"bar\\",...}", ...}

Only four classes have shown up in samples so far: ``Participant`` (root
record), ``DialogStatus`` (monitoring progress + dialog-cascade bookkeeping),
``DialogOption`` (device binding - push tokens + a chat auth secret, always
skipped, never stored), and ``ParticipantVariableWithValue`` (one row per
``$``-prefixed variable, current value + a ``formerVariableValues`` history
capped at 1000 entries).

Known limitation, confirmed against two real exports: ``DialogStatus``'s
``microDialogCascade`` field (the *currently in-flight* dialog, if any) has
been empty in every sample seen - so there is no confirmed schema for it, and
no way yet to resolve a cascade to the actual message text a participant saw.
The observable timeline is therefore built from variable changes and
cascade-*completion* markers (``safeCascades``) only - real, orderable events,
but without the message content that produced them.
"""
from __future__ import annotations

import io
import json
import zipfile


class ParticipantImportError(ValueError):
    """Raised when a .pmcp file isn't a usable single-participant export."""


# Variables PMCP recomputes every processing cycle rather than in response to
# anything the participant actually did - per-tick system noise, not events
# worth surfacing in a navigable timeline. Still included in the variable
# snapshot used to seed the simulator, just not in `timeline`.
NOISY_VARS = {
    "$today", "$mergedAt", "$hasNewData", "$environmentalDataOutdated",
    "$triggerSensorDataUpdate", "$timeDecimal", "$claidLastSensorDataMinute",
    "$dummyVar", "$systemDayOfMonth", "$systemMonth", "$systemYear",
    "$systemDayOfWeek", "$systemHour", "$systemMinute",
}

NO_MESSAGE_TEXT_WARNING = (
    "message text is not recoverable from this export - $variable changes and "
    "cascade-completion markers are the only observable events; there is no "
    "record of which dialog/message produced them."
)


def _parse_envelope(raw: bytes) -> dict:
    envelope = json.loads(raw.decode("utf-8"))
    content_raw = envelope.get("content")
    content = json.loads(content_raw) if isinstance(content_raw, str) else (content_raw or {})
    return {"clazz": envelope.get("clazz"), "content": content}


def parse_pmcp(file_bytes: bytes) -> dict:
    """Parse a .pmcp zip into a single participant's snapshot.

    Returns ``{participant, dialog_status, device_bindings_count, variables,
    timeline, warnings}``. Raises ``ParticipantImportError`` on a bad file, no
    ``Participant`` document, or more than one (multi-participant .pmcp files
    aren't supported - one import seeds one simulator run).
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(file_bytes))
    except zipfile.BadZipFile as e:
        raise ParticipantImportError(f"not a valid .pmcp zip: {e}") from None

    by_clazz: dict[str, list[dict]] = {}
    for info in zf.infolist():
        if info.is_dir():
            continue
        name = info.filename.rsplit("/", 1)[-1]
        parts = name.split(" ")
        if len(parts) < 3 or parts[0] != "M":
            continue  # not one of our documents (junk/metadata entries)
        try:
            doc = _parse_envelope(zf.read(info))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if doc["clazz"]:
            by_clazz.setdefault(doc["clazz"], []).append(doc["content"])

    participants = by_clazz.get("Participant") or []
    if not participants:
        raise ParticipantImportError("no Participant document found in this .pmcp")
    if len(participants) > 1:
        raise ParticipantImportError(
            f"{len(participants)} Participant documents found - this importer "
            "handles exactly one participant per .pmcp file")
    p = participants[0]
    participant_id = p.get("_id")

    dialog_statuses = [
        d for d in by_clazz.get("DialogStatus", []) if d.get("participant") == participant_id
    ]
    dialog_status = dialog_statuses[0] if dialog_statuses else None

    device_bindings_count = len(
        [d for d in by_clazz.get("DialogOption", []) if d.get("participant") == participant_id]
    )

    variables: dict[str, str] = {}
    timeline: list[dict] = []
    for v in by_clazz.get("ParticipantVariableWithValue", []):
        if v.get("participant") != participant_id:
            continue
        name = v.get("name")
        if not name:
            continue
        variables[name] = v.get("value")
        if name in NOISY_VARS:
            continue
        history = list(v.get("formerVariableValues") or [])
        history.append({"timestamp": v.get("timestamp"), "value": v.get("value")})
        if len({h.get("value") for h in history}) <= 1:
            continue  # re-written every cycle but never actually changes - no signal
        seen = set()
        for h in history:
            ts = h.get("timestamp")
            if not ts:
                continue
            marker = (ts, h.get("value"))
            if marker in seen:
                continue
            seen.add(marker)
            timeline.append({"timestamp": ts, "kind": "var_change", "name": name, "value": h.get("value")})

    warnings: list[str] = []
    if dialog_status is not None:
        if dialog_status.get("microDialogCascade"):
            warnings.append(
                "microDialogCascade was non-empty at export time - a dialog was "
                "literally mid-flight, but its schema is unconfirmed (no sample "
                "seen yet), so it is not resolved or seeded into the simulator.")
        for cascade_id in dialog_status.get("safeCascades") or []:
            ts_str = cascade_id.split("-", 1)[0]
            try:
                ts = int(ts_str)
            except ValueError:
                continue
            timeline.append({"timestamp": ts, "kind": "cascade_complete", "cascade_id": cascade_id})
    else:
        warnings.append("no DialogStatus document found for this participant")

    timeline.sort(key=lambda e: e["timestamp"])
    warnings.append(NO_MESSAGE_TEXT_WARNING)

    return {
        "participant": {
            "id": participant_id,
            "systemUniqueId": p.get("systemUniqueId"),
            "nickname": p.get("nickname"),
            "intervention": p.get("intervention"),
            "language": p.get("language"),
            "createdTimestamp": p.get("createdTimestamp"),
            "lastLoginTimestamp": p.get("lastLoginTimestamp"),
            "lastLogoutTimestamp": p.get("lastLogoutTimestamp"),
        },
        "dialog_status": {
            "monitoringDaysParticipated": (dialog_status or {}).get("monitoringDaysParticipated"),
            "screeningSurveyPerformed": (dialog_status or {}).get("screeningSurveyPerformed"),
            "hasOpenMessagesToBeSent": (dialog_status or {}).get("hasOpenMessagesToBeSent"),
            "cascadesCompleted": len((dialog_status or {}).get("safeCascades") or []),
        },
        "device_bindings_count": device_bindings_count,
        "variables": variables,
        "timeline": timeline,
        "warnings": warnings,
    }
