from flask import Flask

from app.config import Config
from app.deploy_info import read_deploy_info
from app.proxy import ReverseProxied


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.ensure_dirs()

    if not Config.SECRET_KEY:
        raise RuntimeError(
            "APP_SECRET_KEY is not set. Copy .env.example to .env and fill it in."
        )

    app.wsgi_app = ReverseProxied(app.wsgi_app)

    from app.auth import bp as auth_bp
    from app.routes import bp as main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.context_processor
    def inject_deploy_info():
        return {"deploy_info": read_deploy_info()}

    return app
