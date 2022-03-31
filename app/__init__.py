"""Инициализация приложения."""

from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS

from config import DevelopmentConfig

migrate = Migrate()
cors = CORS()


def create_app(config_class=DevelopmentConfig):
    """Фабрика приложения Flask."""

    # pylint: disable=import-outside-toplevel  # Особенность Flask

    app = Flask(__name__)
    app.config.from_object(config_class)

    from app.models import db
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    from app.blueprints.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app
