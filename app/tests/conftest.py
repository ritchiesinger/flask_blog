"""Настройки и фикстуры pytest."""

# pylint: disable=redefined-outer-name  # PyLint'у не нравятся зависимые фикстуры PyTest

from pytest import fixture
from app import create_app
from config import TestingConfig


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
