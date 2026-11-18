"""Предусловия связанные с Flask app."""

from collections.abc import Generator
from json import dumps
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from flask import Flask
from flask.testing import FlaskClient
from glamor import attach, attachment_type, step, title
from pytest import fixture

from blog import create_app
from blog.extensions import db
from tests.tools.clients.custom_flask_client import AllureClient


@fixture
@title.setup("Flask. Подготовлен тестовый экземпляр приложения с in-memory БД")
@title.teardown("Flask. Завершение сессии БД и её удаление")
def setup_app(setup_tmp_dir: Path) -> Generator[Flask, Any]:
    """Чистое приложение с in-memory базой на каждый тест.

    Контекст приложения закрывается до yield: каждый запрос теста
    получает свежий контекст (и свежий g) — как в реальном сервере.
    UPLOAD_FOLDER — временная папка теста, изолированная от рабочей.
    """
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "UPLOAD_FOLDER": str(setup_tmp_dir / "uploads"),
        "MAX_CONTENT_LENGTH": 5 * 1024 * 1024,
    }
    attach(body=dumps(test_config, indent=2), name="Конфиг приложения", attachment_type=attachment_type.JSON)
    app = create_app(test_config=test_config)
    with app.app_context():
        with step("Создание БД"):
            db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@fixture
@title("Подготовлен Flask-клиент для взаимодействия с Flask-приложением")
def setup_app_client(setup_app: Flask) -> FlaskClient:
    """Клиент для отправки запросов."""
    setup_app.test_client_class = AllureClient
    return setup_app.test_client()


@fixture
@title.setup("Подготовлена временная папка приложения")
@title.teardown("Удаление временной папки приложения")
def setup_tmp_dir() -> Generator[Path]:
    """Изолированная временная директория под нужды теста."""
    with TemporaryDirectory() as tmp:
        yield Path(tmp)