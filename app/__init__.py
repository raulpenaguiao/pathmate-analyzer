from flask import Flask

from app.config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.ensure_dirs()

    if not Config.SECRET_KEY:
        raise RuntimeError(
            "APP_SECRET_KEY is not set. Copy .env.example to .env and fill it in."
        )

    from app.auth import bp as auth_bp
    from app.routes import bp as main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app
