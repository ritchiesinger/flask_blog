"""Тесты CLI-команд управления ролями: make-superadmin и delete-user."""

from flask import Flask
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.cli import delete_user, make_superadmin
from blog.constants import Roles
from blog.extensions import db
from blog.models import User
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_equal
from tests.tools.cli_tools import invoke_cli


@epic("CLI")
@feature("Управление ролями", "Управление пользователями")
@story("Выдача роли SuperAdministrator")
class TestMakeSuperadmin:
    """Проверки CLI-команды make-superadmin."""

    @title("make-superadmin выдаёт пользователю роль SUPERADMIN")
    @severity(severity_level.BLOCKER)
    def test_grants_superadmin(self, setup_app: Flask, setup_test_user: UserObject):
        """Команда выдаёт супер-роль существующему пользователю.

        Ожидание: exit_code 0, в выводе подтверждение «SuperAdministrator»;
        в БД роль пользователя — Roles.SUPERADMIN.
        """
        target = setup_test_user
        with step("Оператор. CLI. Выдача супер-роли командой make-superadmin"):
            result = invoke_cli(setup_app, make_superadmin, [target.db_model.username])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="SuperAdministrator" in result.output,
                allure_step_name="В выводе есть подтверждение выдачи роли",
                error_text="В выводе команды нет подтверждения выдачи супер-роли!",
            )

        with step("ORM. Проверка роли пользователя в БД"):
            with setup_app.app_context():
                user = db.session.execute(
                    db.select(User).filter_by(username=target.db_model.username),
                ).scalars().first()
            assert_equal(expect=Roles.SUPERADMIN, actual=user.role, name="user.role")

    @title("Повторный make-superadmin при существующем супер-админе отказывает")
    @severity(severity_level.CRITICAL)
    def test_refuses_when_superadmin_exists(
            self,
            setup_app: Flask,
            setup_test_user: UserObject,
            setup_test_user_2: UserObject,
    ):
        """Команда отказывает, если супер-админ уже существует; существующий не затрагивается.

        Ожидание: первый вызов выдаёт роль первому; второй — отказ с именем
        существующего супер-админа; роль второго не изменена, роль первого
        осталась SUPERADMIN. Роль уникальна по построению (→ ARC-0041).
        """
        first, second = setup_test_user, setup_test_user_2
        with step("Оператор. CLI. Первичное назначение супер-админа"):
            grant = invoke_cli(setup_app, make_superadmin, [first.db_model.username])
            assert_equal(expect=0, actual=grant.exit_code, name="Exit code первого вызова")

        with step("Оператор. CLI. Повторная попытка назначения второму пользователю"):
            result = invoke_cli(setup_app, make_superadmin, [second.db_model.username])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="already exists" in result.output,
                allure_step_name="В выводе есть отказ: супер-админ уже существует",
                error_text="В выводе команды нет отказа о существующем супер-админе!",
            )
            assert_condition(
                condition=first.db_model.username in result.output,
                allure_step_name="В отказе назван логин существующего супер-админа",
                error_text="В отказе не назван логин существующего супер-админа!",
            )

        with step("ORM. Проверка ролей обоих пользователей в БД"):
            with setup_app.app_context():
                first_role = db.session.execute(
                    db.select(User).filter_by(username=first.db_model.username),
                ).scalars().first().role
                second_role = db.session.execute(
                    db.select(User).filter_by(username=second.db_model.username),
                ).scalars().first().role
            assert_equal(expect=Roles.SUPERADMIN, actual=first_role, name="Роль первого пользователя")
            assert_equal(expect=Roles.USER, actual=second_role, name="Роль второго пользователя")

    @title("make-superadmin на несуществующем пользователе сообщает об отсутствии")
    @severity(severity_level.MINOR)
    def test_user_not_found(self, setup_app: Flask):
        """Команда на неизвестном логине отказывает сообщением, не падением.

        Ожидание: exit_code 0 и вывод «не найден».
        """
        with step("Оператор. CLI. Попытка выдачи роли несуществующему пользователю"):
            result = invoke_cli(setup_app, make_superadmin, ["ghost_user"])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="не найден" in result.output,
                allure_step_name="В выводе есть сообщение об отсутствии пользователя",
                error_text="В выводе команды нет сообщения об отсутствии пользователя!",
            )


@story("Удаление пользователя")
class TestDeleteUser:
    """Проверки CLI-команды delete-user."""

    @title("delete-user удаляет пользователя из БД")
    @severity(severity_level.BLOCKER)
    def test_deletes_user(self, setup_app: Flask, setup_test_user: UserObject):
        """Команда удаляет пользователя; после удаления его в БД нет.

        Ожидание: exit_code 0, вывод «удалён»; повторная выборка по логину — None.
        Посты и комментарии уходят каскадом БД (покрыто test_api_admin_cascade).
        """
        target = setup_test_user
        with step("Оператор. CLI. Удаление пользователя командой delete-user"):
            result = invoke_cli(setup_app, delete_user, [target.db_model.username])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="удалён" in result.output,
                allure_step_name="В выводе есть подтверждение удаления",
                error_text="В выводе команды нет подтверждения удаления!",
            )

        with step("ORM. Пользователя в БД больше нет"):
            with setup_app.app_context():
                user = db.session.execute(
                    db.select(User).filter_by(username=target.db_model.username),
                ).scalars().first()
            assert_condition(
                condition=user is None,
                allure_step_name="Пользователь отсутствует в БД",
                error_text="Пользователь после удаления остался в БД!",
            )

    @title("delete-user на несуществующем пользователе сообщает об отсутствии")
    @severity(severity_level.MINOR)
    def test_user_not_found(self, setup_app: Flask):
        """Команда на неизвестном логине отказывает сообщением, не падением.

        Ожидание: exit_code 0 и вывод «не найден».
        """
        with step("Оператор. CLI. Попытка удаления несуществующего пользователя"):
            result = invoke_cli(setup_app, delete_user, ["ghost_user"])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="не найден" in result.output,
                allure_step_name="В выводе есть сообщение об отсутствии пользователя",
                error_text="В выводе команды нет сообщения об отсутствии пользователя!",
            )
