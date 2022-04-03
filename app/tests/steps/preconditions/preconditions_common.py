"""Общие базовые предусловия."""

# pylint: disable=redefined-outer-name  # pylint не любит цепочки фикстур

from allure import title
from pytest import fixture

from app import create_app
from config import TestingConfig


@title("Подготовка приложения с тестовой конфигурацией")
@fixture()
def test_app():
    """Готовим приложение с тестовой конфигурацией."""
    app = create_app(TestingConfig)
    # other setup can go here
    yield app
    # clean up / reset resources here


@title("Подготовка HTTP клиента для запросов")
@fixture()
def client(test_app):
    """Готовим клиент для запросов."""
    return test_app.test_client()


@title("Подготовка CLI с тестовой конфигурацией")
@fixture()
def runner(test_app):
    """Готовим CLI для использования в тестах."""
    return test_app.test_cli_runner()
