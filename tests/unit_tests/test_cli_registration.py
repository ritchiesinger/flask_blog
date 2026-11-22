"""Проверка регистрация CLI-команд в фабрике приложения."""
from json import dumps

from click import Command
from flask import Flask
from glamor import attach, attachment_type, epic, feature, severity, severity_level, step, story, title

from blog import cli
from tests.tools.asserters.base_asserters import assert_condition


@epic("UNIT")
@feature("Фабрика приложения")
@story("Регистрация CLI команд")
@severity(severity_level.BLOCKER)
@title("Каждая команда blog/cli.py зарегистрирована в app.cli фабрики")
def test_all_cli_commands_registered_in_factory(setup_app: Flask):
    """Проверяется что все команды CLI код для которых есть в проекте зарегистрированы в приложении Flask."""
    with step("Получение списка имеющихся команд"):
        expected = {obj.name for obj in vars(cli).values() if isinstance(obj, Command)}
        attach(body=dumps(list(expected), indent=2), name="Имеющиеся команды", attachment_type=attachment_type.JSON)
    with step("Получение зарегистрированных команд"):
        registered = set(setup_app.cli.commands)
        attach(
            body=dumps(list(registered), indent=2),
            name="Зарегистрированные команды",
            attachment_type=attachment_type.JSON
        )
        missing = expected - registered
        assert_condition(
            condition=not missing,
            allure_step_name="Все имеющиеся команды зарегистрированы в приложении",
            error_text=f"Команды не зарегистрированы в фабрике: {sorted(missing)}"
        )
