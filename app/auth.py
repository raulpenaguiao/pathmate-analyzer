from functools import wraps

from flask import Blueprint, redirect, render_template, request, session, url_for

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
        if not session.get("logged_in"):
            return redirect(url_for("auth.login", next=request.path))
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
        elif username == Config.APP_USERNAME and password == Config.APP_PASSWORD:
            session.clear()
            session["logged_in"] = True
            session["username"] = username
            next_url = _safe_next_url(request.args.get("next")) or url_for("main.dashboard")
            return redirect(next_url)
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
