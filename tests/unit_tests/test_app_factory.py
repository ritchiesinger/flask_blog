"""Юнит-тесты фабрики приложения: сборка без тестового конфига."""

from flask import Flask
from glamor import epic, feature, severity, severity_level, step, story, title

from blog import create_app
from tests.tools.asserters.base_asserters import assert_condition, assert_equal


@epic("UNIT")
@feature("Фабрика приложения")
@story("Создание приложения")
class TestCreateApp:
    """Контракт фабрики create_app."""

    @severity(severity_level.BLOCKER)
    @title("create_app() без test_config строит полноценное приложение")
    def test_create_app_without_test_config(self):
        """create_app() без test_config строит полноценное приложение.

        Ожидание: возвращается Flask-приложение; конфигурация взята из blog.config.Config (ветка test_config is None —
        ранее недостижимая: все тесты передавали test_config); CLI-команды зарегистрированы. Фикстуры и клиент не
        нужны — сборка приложения не требует БД.
        """
        with step("Создание приложения"):
            app = create_app()
            assert_condition(
                condition=isinstance(app, Flask) is True,
                allure_step_name="Созданный экземпляр приложения имеет тип Flask",
                error_text="Неожиданный тип у созданного экземпляра приложения!"
            )
            assert_equal(expect="blog", actual=app.name, name="Имя приложения")
            assert_condition(
                condition="init-db" in app.cli.commands,
                allure_step_name="init-db найдена среди зарегистрированных CLI команд",
                error_text="init-db не найдена среди зарегистрированных CLI команд",
            )
            assert_condition(
                condition="create-admin" in app.cli.commands,
                allure_step_name="create-admin найдена среди зарегистрированных CLI команд",
                error_text="create-admin не найдена среди зарегистрированных CLI команд",
            )
            assert_condition(
                condition="make-admin" in app.cli.commands,
                allure_step_name="make-admin найдена среди зарегистрированных CLI команд",
                error_text="make-admin не найдена среди зарегистрированных CLI команд",
            )
