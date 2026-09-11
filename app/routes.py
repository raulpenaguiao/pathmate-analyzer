import json

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from app import rgroups_tool, storage
from app.auth import login_required
from app.coaching_model import load_model
from app.coaching_sim import Simulator
from app.coaching_stats import extract_rules_tree
from app.participant_import import ParticipantImportError

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def dashboard():
    coachings = storage.list_coachings()
    patient_models = storage.list_patient_models()
    return render_template(
        "dashboard.html",
        coaching_count=len(coachings),
        patient_model_count=len(patient_models),
        recent_coachings=coachings[:5],
        recent_patient_models=patient_models[:5],
    )


# ---------------------------------------------------------------------------
# Coachings
# ---------------------------------------------------------------------------

@bp.route("/coachings")
@login_required
def coachings_list():
    tag_filter = request.args.get("tag", "").strip()
    coachings = storage.list_coachings()
    if tag_filter:
        coachings = [c for c in coachings if c.get("tag", "") == tag_filter]
    all_tags = sorted({c.get("tag", "") for c in storage.list_coachings() if c.get("tag")})
    return render_template(
        "coachings.html", coachings=coachings, all_tags=all_tags, tag_filter=tag_filter
    )


@bp.route("/coachings/upload", methods=["POST"])
@login_required
def coaching_upload():
    name = request.form.get("name", "").strip()
    tag = request.form.get("tag", "").strip()
    upload = request.files.get("file")

    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("main.coachings_list"))

    if not upload or not upload.filename:
        flash("A coaching HTML file is required.", "error")
        return redirect(url_for("main.coachings_list"))

    if not upload.filename.lower().endswith(".html"):
        flash("Only .html coaching exports are accepted.", "error")
        return redirect(url_for("main.coachings_list"))

    file_bytes = upload.read()
    meta = storage.save_coaching(name=name, tag=tag, filename=upload.filename, file_bytes=file_bytes)
    flash(f'Coaching "{name}" uploaded.', "success")

    bundle_upload = request.files.get("bundle")
    if bundle_upload and bundle_upload.filename:
        if not bundle_upload.filename.lower().endswith(".json"):
            flash("coaching.json not attached: expected a .json file.", "error")
        else:
            try:
                bundle_meta = storage.save_coaching_bundle(meta["id"], bundle_upload.read())
                s = bundle_meta["bundle"]["summary"]
                flash(f"coaching.json attached — {s['microDialogs']} dialogs, "
                      f"{s['nodes']} nodes, {s['ruleTreeNodes']} rule-tree nodes.",
                      "success")
            except storage.BundleError as e:
                flash(f"coaching.json not attached: {e}", "error")

    return redirect(url_for("main.coachings_list"))


@bp.route("/coachings/<coaching_id>/view")
@login_required
def coaching_view(coaching_id):
    meta = storage.get_coaching(coaching_id)
    if meta is None:
        abort(404)
    return render_template(
        "coaching_view.html", coaching=meta, model=load_model(coaching_id)
    )


@bp.route("/coachings/<coaching_id>/tab/micro-dialogs")
@login_required
def coaching_micro_dialogs(coaching_id):
    meta = storage.get_coaching(coaching_id)
    model = load_model(coaching_id)
    if meta is None or model is None:
        abort(404)
    return render_template(
        "_tab_micro_dialogs.html", coaching=meta, model=model
    )


@bp.route("/coachings/<coaching_id>/chats")
@login_required
def coaching_chats_list(coaching_id):
    """Sidebar contents: every persisted chat (live or imported) for this
    coaching, most recently updated first."""
    if storage.get_coaching(coaching_id) is None:
        abort(404)
    return jsonify(chats=storage.list_chats(coaching_id))


@bp.route("/coachings/<coaching_id>/chats/new", methods=["POST"])
@login_required
def coaching_chat_new(coaching_id):
    model = load_model(coaching_id)
    if model is None:
        abort(404)
    name = f"Chat {len(storage.list_chats(coaching_id)) + 1}"
    chat = storage.create_chat(coaching_id, name=name, kind="live", state=Simulator(model).initial_state())
    return jsonify(chat=chat)


@bp.route("/coachings/<coaching_id>/chats/<chat_id>")
@login_required
def coaching_chat_get(coaching_id, chat_id):
    chat = storage.get_chat(coaching_id, chat_id)
    if chat is None:
        abort(404)
    model = load_model(coaching_id)
    return jsonify(
        chat=chat,
        dialogs=[{"i": d.i, "name": d.name} for d in model.micro_dialogs] if model else [],
        groups=[{"i": g.i, "name": g.name} for g in model.message_groups] if model else [],
        languages=model.languages if model else ["en-GB"],
    )


@bp.route("/coachings/<coaching_id>/chats/<chat_id>/step", methods=["POST"])
@login_required
def coaching_chat_step(coaching_id, chat_id):
    model = load_model(coaching_id)
    if model is None:
        abort(404)
    existing = storage.get_chat(coaching_id, chat_id)
    if existing is None:
        abort(404)
    payload = request.get_json(silent=True) or {}
    action = payload.get("action") or {}

    if action.get("type") == "reset" and existing.get("kind") == "imported":
        # "reset" on an imported chat means replay the real participant
        # again from scratch, not wipe it to a blank live simulation.
        state = storage.reseed_imported_chat(coaching_id, chat_id) or existing["state"]
    else:
        sim = Simulator(model, lang=payload.get("lang"))
        state = existing["state"]
        try:
            state = sim.step(state, action)
        except Exception as exc:  # keep a bad rule from 500-ing the whole run
            state.setdefault("transcript", []).append(
                {"kind": "system", "text": f"Simulation error: {exc}", "t": ""}
            )
    storage.update_chat_state(coaching_id, chat_id, state)
    return jsonify(state=state)


@bp.route("/coachings/<coaching_id>/chats/<chat_id>/rename", methods=["POST"])
@login_required
def coaching_chat_rename(coaching_id, chat_id):
    name = (request.get_json(silent=True) or {}).get("name", "").strip()
    if not name or not storage.rename_chat(coaching_id, chat_id, name):
        return jsonify(ok=False), 400
    return jsonify(ok=True)


@bp.route("/coachings/<coaching_id>/chats/<chat_id>/delete", methods=["POST"])
@login_required
def coaching_chat_delete(coaching_id, chat_id):
    return jsonify(ok=storage.delete_chat(coaching_id, chat_id))


@bp.route("/coachings/<coaching_id>/raw")
@login_required
def coaching_raw(coaching_id):
    file_path = storage.coaching_file_path(coaching_id)
    if file_path is None or not file_path.exists():
        abort(404)
    return send_file(file_path, mimetype="text/html")


@bp.route("/coachings/<coaching_id>/rules-tree")
@login_required
def coaching_rules_tree(coaching_id):
    file_path = storage.coaching_file_path(coaching_id)
    if file_path is None or not file_path.exists():
        abort(404)
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    tree = extract_rules_tree(file_bytes)
    return render_template("rules_tree_fragment.html", tree=tree)


@bp.route("/coachings/<coaching_id>/download")
@login_required
def coaching_download(coaching_id):
    meta = storage.get_coaching(coaching_id)
    file_path = storage.coaching_file_path(coaching_id)
    if meta is None or file_path is None or not file_path.exists():
        abort(404)
    return send_file(
        file_path,
        as_attachment=True,
        download_name=meta.get("original_filename", "coaching.html"),
    )


@bp.route("/coachings/<coaching_id>/delete", methods=["POST"])
@login_required
def coaching_delete(coaching_id):
    if storage.delete_coaching(coaching_id):
        flash("Coaching deleted.", "success")
    else:
        flash("Coaching not found.", "error")
    return redirect(url_for("main.coachings_list"))


@bp.route("/coachings/<coaching_id>/bundle", methods=["POST"])
@login_required
def coaching_bundle_upload(coaching_id):
    """Attach a coaching.json (the Stage-3 export) to this coaching — unlocks
    the faithful chat engine. The main upload flow stays HTML-only."""
    if storage.get_coaching(coaching_id) is None:
        abort(404)
    upload = request.files.get("bundle")
    if not upload or not upload.filename:
        flash("Choose a coaching.json file.", "error")
    elif not upload.filename.lower().endswith(".json"):
        flash("Expected a .json file (from export_coaching.sh).", "error")
    else:
        try:
            meta = storage.save_coaching_bundle(coaching_id, upload.read())
            s = meta["bundle"]["summary"]
            flash(f"coaching.json attached — {s['microDialogs']} dialogs, "
                  f"{s['nodes']} nodes, {s['ruleTreeNodes']} rule-tree nodes.",
                  "success")
        except storage.BundleError as e:
            flash(f"Not attached: {e}", "error")
    return redirect(url_for("main.coaching_view", coaching_id=coaching_id) + "#stats")


@bp.route("/coachings/<coaching_id>/participant-import", methods=["POST"])
@login_required
def coaching_participant_import_upload(coaching_id):
    """Parse a .pmcp participant export and add it as a new imported chat —
    listed in the Chat tab sidebar alongside any live/simulated chats,
    seeded with that participant's real variable state and reconstructed
    event history, immediately explorable and continuable."""
    if storage.get_coaching(coaching_id) is None:
        abort(404)
    upload = request.files.get("participant_import")
    if not upload or not upload.filename:
        flash("Choose a .pmcp file.", "error")
    elif not upload.filename.lower().endswith(".pmcp"):
        flash("Expected a .pmcp file (a zipped participant export).", "error")
    else:
        try:
            chat = storage.create_imported_chat(coaching_id, upload.filename, upload.read())
            s = chat["participant_summary"]
            flash(f'Imported "{chat["name"]}" as a new chat — {s["variables"]} variables, '
                  f'{s["timelineEvents"]} timeline events, {s["cascadesCompleted"]} cascades completed.',
                  "success")
        except ParticipantImportError as e:
            flash(f"Not imported: {e}", "error")
    return redirect(url_for("main.coaching_view", coaching_id=coaching_id) + "#chat")


@bp.route("/coachings/<coaching_id>/bundle/delete", methods=["POST"])
@login_required
def coaching_bundle_delete(coaching_id):
    if storage.delete_coaching_bundle(coaching_id):
        flash("coaching.json detached.", "success")
    else:
        flash("No coaching.json was attached.", "error")
    return redirect(url_for("main.coaching_view", coaching_id=coaching_id) + "#stats")


# ---------------------------------------------------------------------------
# Randomisation groups (r_) pipeline, steps 1-3 -- only when a coaching.json
# is attached. Step 4 (Playwright write-back) needs a browser and stays CLI:
# tools/rgroups-table/rgroup_apply.py
# ---------------------------------------------------------------------------

def _require_bundle(coaching_id):
    meta = storage.get_coaching(coaching_id)
    if meta is None:
        abort(404)
    bundle_path = storage.coaching_bundle_path(coaching_id)
    if bundle_path is None:
        abort(404)
    return meta, bundle_path


@bp.route("/coachings/<coaching_id>/tab/rgroups")
@login_required
def coaching_rgroups_tab(coaching_id):
    meta, _ = _require_bundle(coaching_id)
    previews = {kind: rgroups_tool.preview(coaching_id, kind)
                for kind in ("table", "requests", "generated")}
    return render_template("_tab_rgroups.html", coaching=meta, previews=previews)


@bp.route("/coachings/<coaching_id>/rgroups/report", methods=["POST"])
@login_required
def rgroups_report(coaching_id):
    _, bundle_path = _require_bundle(coaching_id)
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        summary = rgroups_tool.run_report(coaching_id, bundle)
        return jsonify(ok=True, **summary)
    except Exception as e:  # noqa: BLE001
        return jsonify(ok=False, error=str(e)), 400


@bp.route("/coachings/<coaching_id>/rgroups/prepare", methods=["POST"])
@login_required
def rgroups_prepare(coaching_id):
    _require_bundle(coaching_id)
    try:
        summary = rgroups_tool.run_prepare(coaching_id)
        return jsonify(ok=True, **summary)
    except Exception as e:  # noqa: BLE001
        return jsonify(ok=False, error=str(e)), 400


@bp.route("/coachings/<coaching_id>/rgroups/expand/start", methods=["POST"])
@login_required
def rgroups_expand_start(coaching_id):
    _require_bundle(coaching_id)
    api_key = (request.form.get("api_key") or "").strip()
    provider = (request.form.get("provider") or "claude").strip()
    limit_raw = (request.form.get("limit") or "").strip()
    if not api_key:
        return jsonify(ok=False, error="An API key is required."), 400
    if provider not in ("claude", "chatgpt"):
        return jsonify(ok=False, error="Unknown provider."), 400
    try:
        limit = int(limit_raw)
        if limit < 1:
            raise ValueError
    except ValueError:
        return jsonify(ok=False, error="Limit must be a positive integer."), 400
    try:
        job_id = rgroups_tool.start_expand_job(coaching_id, provider, limit, api_key)
        return jsonify(ok=True, jobId=job_id)
    except (FileNotFoundError, ValueError) as e:
        return jsonify(ok=False, error=str(e)), 400


@bp.route("/coachings/<coaching_id>/rgroups/expand/status/<job_id>")
@login_required
def rgroups_expand_status(coaching_id, job_id):
    job = rgroups_tool.job_status(job_id)
    if job is None or job.get("coachingId") != coaching_id:
        return jsonify(ok=False, error="Unknown job."), 404
    return jsonify(ok=True, **job)


@bp.route("/coachings/<coaching_id>/rgroups/download/<kind>")
@login_required
def rgroups_download(coaching_id, kind):
    _require_bundle(coaching_id)
    paths = {
        "table": rgroups_tool.table_path(coaching_id),
        "requests": rgroups_tool.requests_path(coaching_id),
        "generated": rgroups_tool.generated_path(coaching_id),
    }
    path = paths.get(kind)
    if path is None or not path.exists():
        abort(404)
    return send_file(path, as_attachment=True, download_name=f"rgroups_{kind}.csv")


# ---------------------------------------------------------------------------
# Patient models
# ---------------------------------------------------------------------------

@bp.route("/patient-models")
@login_required
def patient_models_list():
    models = storage.list_patient_models()
    return render_template("patient_models.html", models=models)


@bp.route("/patient-models/new")
@login_required
def patient_model_new():
    return render_template("patient_model_form.html", model=None)


@bp.route("/patient-models", methods=["POST"])
@login_required
def patient_model_create():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("main.patient_model_new"))

    storage.save_patient_model(request.form.to_dict())
    flash(f'Patient model "{name}" created.', "success")
    return redirect(url_for("main.patient_models_list"))


@bp.route("/patient-models/<model_id>/edit")
@login_required
def patient_model_edit(model_id):
    model = storage.get_patient_model(model_id)
    if model is None:
        abort(404)
    return render_template("patient_model_form.html", model=model)


@bp.route("/patient-models/<model_id>", methods=["POST"])
@login_required
def patient_model_update(model_id):
    existing = storage.get_patient_model(model_id)
    if existing is None:
        abort(404)

    name = request.form.get("name", "").strip()
    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("main.patient_model_edit", model_id=model_id))

    data = request.form.to_dict()
    data["created_at"] = existing.get("created_at")
    storage.save_patient_model(data, model_id=model_id)
    flash(f'Patient model "{name}" updated.', "success")
    return redirect(url_for("main.patient_models_list"))


@bp.route("/patient-models/<model_id>/delete", methods=["POST"])
@login_required
def patient_model_delete(model_id):
    if storage.delete_patient_model(model_id):
        flash("Patient model deleted.", "success")
    else:
        flash("Patient model not found.", "error")
    return redirect(url_for("main.patient_models_list"))
