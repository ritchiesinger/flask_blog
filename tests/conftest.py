"""Корневой conftest: слушатель PRAGMA foreign_keys и подключение плагинов с фикстурами."""

from sqlite3 import Connection

from sqlalchemy import event
from sqlalchemy.engine import Engine


@event.listens_for(Engine, "connect")
def _enable_sqlite_fk(dbapi_connection, connection_record):
    """Включает контроль внешних ключей в SQLite — по умолчанию он выключен."""
    if isinstance(dbapi_connection, Connection):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")


pytest_plugins = [
    "tests.preconditions.app_preconditions",
    "tests.preconditions.users_preconditions",
    "tests.preconditions.posts_preconditions",
    "tests.preconditions.comments_preconditions",
]
