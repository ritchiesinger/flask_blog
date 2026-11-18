"""Тесты CLI-команды init-db: инициализация базы данных."""

from flask import Flask
from glamor import epic, feature, severity, severity_level, step, story, title
from sqlalchemy import inspect

from blog.extensions import db
from tests.tools.asserters.base_asserters import assert_condition, assert_equal
from tests.tools.cli_tools import invoke_cli


@epic("CLI")
@feature("Обслуживание базы данных")
@story("Инициализация базы")
class TestInitDb:
    """Проверки CLI-команды init-db."""

    @title("init-db создаёт все таблицы и подтверждает инициализацию")
    @severity(severity_level.BLOCKER)
    def test_init_db_creates_tables(self, setup_app: Flask):
        """init-db создаёт все таблицы БД и печатает подтверждение.

        Ожидание: exit_code 0, в выводе «База инициализирована.»,
        в БД присутствуют таблицы user и post.
        """
        command = setup_app.cli.commands["init-db"]

        with step("Оператор. CLI. Инициализация базы командой init-db"):
            result = invoke_cli(setup_app, command, [])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="База инициализирована." in result.output,
                allure_step_name="В выводе подтверждение инициализации",
                error_text="В выводе команды нет подтверждения инициализации!",
            )

        with step("ORM. Проверка созданных таблиц"):
            with setup_app.app_context():
                tables = set(inspect(db.engine).get_table_names())
            assert_condition(
                condition={"user", "post"} <= tables,
                allure_step_name="Таблицы user и post созданы",
                error_text="После init-db в БД нет таблиц user и post!",
            )
