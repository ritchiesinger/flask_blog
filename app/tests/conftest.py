"""Настройки и фикстуры pytest."""

# pylint: disable=redefined-outer-name  # PyLint'у не нравятся зависимые фикстуры PyTest

from base64 import b64encode
from typing import Dict

from pytest import fixture
from app import create_app
from config import TestingConfig


def get_basic_auth_header(login: str, password: str) -> Dict[str, str]:
    """Получение заголовка авторизации Basic Auth."""
    basic_auth = b64encode(bytes(f"{login}:{password}", encoding="UTF-8")).decode("utf-8")
    return {"Authorization": f"Basic {basic_auth}"}


@fixture()
def test_app():
    """Готовим приложение с тестовой конфигурацией."""
    app = create_app(TestingConfig)
    # other setup can go here
    yield app
    # clean up / reset resources here


@fixture()
def client(test_app):
    """Готовим клиент для запросов."""
    return test_app.test_client()


@fixture()
def runner(test_app):
    """Готовим CLI для использования в тестах."""
    return test_app.test_cli_runner()


@fixture()
def user_basic_auth_header():
    """Заголовок Authorization для тестового пользователя."""
    return get_basic_auth_header("Ernestine47", "qwerty")


@fixture()
def admin_basic_auth_header():
    """Заголовок Authorization для тестового администратора."""
    return get_basic_auth_header("ritchie_singer", "qwerty")
