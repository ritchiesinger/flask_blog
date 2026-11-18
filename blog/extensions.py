"""Экземпляры расширений Flask.

Расширения создаются здесь без привязки к приложению, а инициализируются
в фабрике приложения (init_app) — это позволяет избежать циклических
импортов между моделями, роутами и app.

Naming convention для SQLAlchemy задаёт имена ограничений в БД,
чтобы миграции Alembic не пересоздавали их при переименовании.
"""

from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
# Создаём экземпляры расширений (без привязки к приложению)
db = SQLAlchemy(metadata=MetaData(naming_convention=convention))
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()

# Настройки, специфичные для расширений
login_manager.login_view = "auth.login"  # куда редиректить при входе
login_manager.session_protection = "strong"  # защита сессии
