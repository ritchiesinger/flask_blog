"""Корневой conftest: слушатель PRAGMA foreign_keys и подключение плагинов с фикстурами."""

import sqlite3

from sqlalchemy import event
from sqlalchemy.engine import Engine


@event.listens_for(Engine, "connect")
def _enable_sqlite_fk(dbapi_connection, connection_record):
    """Включает контроль внешних ключей в SQLite — по умолчанию он выключен."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")


pytest_plugins = [
    "preconditions.app_preconditions",
    "preconditions.users_preconditions",
    "preconditions.posts_preconditions",
    "preconditions.comments_preconditions",
]
