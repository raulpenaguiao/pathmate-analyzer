from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from app import users
from app.config import Config

bp = Blueprint("auth", __name__)


def _safe_next_url(candidate):
    # Only allow same-site relative paths ("/foo") - reject absolute URLs and
    # protocol-relative ones ("//evil.com") to avoid an open-redirect via ?next=.
    if candidate and candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        # a deleted account's session stops working on its next request
        if session.get("logged_in") and not users.exists(session.get("username", "")):
            session.clear()
        if not session.get("logged_in"):
            # request.script_root carries the mount prefix (e.g. /pathmate-analyzer)
            # when behind the reverse proxy - request.path alone would drop it.
            next_url = request.script_root + request.path
            return redirect(url_for("auth.login", next=next_url))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        # re-read the role: a demoted/deleted admin loses access at once
        if not users.is_admin(session.get("username", "")):
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("main.dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if not Config.APP_USERNAME or not Config.APP_PASSWORD:
            error = "Server is missing APP_USERNAME/APP_PASSWORD configuration."
        else:
            who = users.authenticate(username, password)
            if who:
                session.clear()
                session["logged_in"] = True
                session["username"] = who["username"]
                session["is_admin"] = who["is_admin"]
                next_url = _safe_next_url(request.args.get("next")) or url_for("main.dashboard")
                return redirect(next_url)
            error = "Invalid username or password."

    return render_template("login.html", error=error)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    username = session["username"]
    env_admin = users.is_env_admin(username)
    if request.method == "POST" and not env_admin:
        current = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        if not users.authenticate(username, current):
            flash("Your current password is wrong.", "error")
        elif new != request.form.get("new_password_again", ""):
            flash("The two new passwords don't match.", "error")
        else:
            try:
                users.set_password(username, new)
                flash("Password changed.", "success")
                return redirect(url_for("auth.account"))
            except users.UserError as e:
                flash(str(e), "error")
    return render_template("account.html", env_admin=env_admin,
                           min_len=users.MIN_PASSWORD_LEN)


@bp.route("/users", methods=["GET", "POST"])
@admin_required
def users_admin():
    # The one-time password is rendered straight into this response (no
    # redirect/flash), so it never sits in the signed-but-readable session cookie.
    created = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "") or users.generate_password()
        role = request.form.get("role", "user")
        try:
            users.create_user(username, password, role, created_by=session["username"])
            created = {"username": username, "password": password, "role": role}
        except users.UserError as e:
            flash(str(e), "error")
    return render_template("users.html", accounts=users.list_users(), created=created,
                           admin_name=Config.APP_USERNAME, min_len=users.MIN_PASSWORD_LEN)


@bp.route("/users/<username>/reset", methods=["POST"])
@admin_required
def users_reset(username):
    password = users.generate_password()
    try:
        users.set_password(username, password)
    except users.UserError as e:
        flash(str(e), "error")
        return redirect(url_for("auth.users_admin"))
    return render_template("users.html", accounts=users.list_users(),
                           created={"username": username, "password": password, "reset": True},
                           admin_name=Config.APP_USERNAME, min_len=users.MIN_PASSWORD_LEN)


@bp.route("/users/<username>/delete", methods=["POST"])
@admin_required
def users_delete(username):
    if username == session.get("username"):
        flash("You can't delete the account you're logged in with.", "error")
    else:
        try:
            users.delete_user(username)
            flash(f"Deleted '{username}'.", "success")
        except users.UserError as e:
            flash(str(e), "error")
    return redirect(url_for("auth.users_admin"))
