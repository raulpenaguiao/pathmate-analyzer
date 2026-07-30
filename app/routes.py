from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from app import storage
from app.auth import login_required
from app.coaching_stats import extract_rules_tree

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
    storage.save_coaching(name=name, tag=tag, filename=upload.filename, file_bytes=file_bytes)
    flash(f'Coaching "{name}" uploaded.', "success")
    return redirect(url_for("main.coachings_list"))


@bp.route("/coachings/<coaching_id>/view")
@login_required
def coaching_view(coaching_id):
    meta = storage.get_coaching(coaching_id)
    if meta is None:
        abort(404)
    return render_template("coaching_view.html", coaching=meta)


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
