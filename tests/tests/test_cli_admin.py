"""Тесты CLI-команд управления администраторами: create-admin и make-admin."""

from flask import Flask
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.cli import create_admin, make_admin
from blog.constants import Roles
from blog.extensions import db
from blog.models import User
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_equal
from tests.tools.cli_tools import invoke_cli


@epic("CLI")
@feature("Управление администраторами")
@story("Создание администратора")
class TestCreateAdmin:
    """Проверки CLI-команды create-admin."""

    @title("Команда create-admin создаёт пользователя с ролью админ")
    @severity(severity_level.BLOCKER)
    def test_creates_admin(self, setup_app: Flask):
        """create-admin создаёт пользователя с ролью ADMIN и паролем из аргументов.

        Ожидание: exit_code 0, в выводе подтверждение «создан»; в БД —
        пользователь с role == Roles.ADMIN и паролем, проходящим check_password.
        """
        with step("Оператор. CLI. Создание администратора командой create-admin"):
            result = invoke_cli(setup_app, create_admin, ["new_admin", "S3cret"], hidden=(1,))
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="создан" in result.output,
                allure_step_name="В выводе есть подтверждение создания",
                error_text="В выводе команды нет подтверждения создания!",
            )

        with step("ORM. Проверка созданного администратора в БД"):
            with setup_app.app_context():
                user = db.session.execute(db.select(User).filter_by(username="new_admin")).scalars().first()
            assert_condition(
                condition=user is not None,
                allure_step_name="Пользователь new_admin найден в БД",
                error_text="Пользователь new_admin не найден в БД!",
            )
            assert_equal(expect=Roles.ADMIN, actual=user.role, name="user.role")
            assert_condition(
                condition=user.check_password("S3cret"),
                allure_step_name="Пароль созданного пользователя совпадает",
                error_text="Пароль пользователя не совпадает с переданным команде!",
            )

    @title("Повторный create-admin на существующем пользователе не перезаписывает его")
    @severity(severity_level.CRITICAL)
    def test_existing_user_is_not_overwritten(self, setup_app: Flask, setup_test_user: UserObject):
        """create-admin на существующем пользователе отказывает без изменения его данных.

        Ожидание: exit_code 0 и вывод «уже существует»; роль и пароль
        существующего пользователя не изменены. Отказ — сообщением, не падением.
        """
        existing = setup_test_user
        with step("Оператор. CLI. Повторное создание администратора с именем существующего пользователя"):
            result = invoke_cli(
                setup_app,
                create_admin,
                [existing.db_model.username, "irrelevant"],
                hidden=(1,)
            )
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="уже существует" in result.output,
                allure_step_name="В выводе сообщение о существующем пользователе",
                error_text="В выводе команды нет сообщения «уже существует»!",
            )

        with step("ORM. Проверка неизменности существующего пользователя"):
            with setup_app.app_context():
                user = db.session.get(User, existing.db_model.id)
            assert_equal(expect=Roles.USER, actual=user.role, name="user.role")
            assert_condition(
                condition=not user.check_password("irrelevant"),
                allure_step_name="Пароль существующего пользователя не изменён",
                error_text="Пароль существующего пользователя перезаписан!",
            )


@epic("CLI")
@feature("Управление администраторами")
@story("Назначение администратора")
class TestMakeAdmin:
    """Проверки CLI-команды make-admin."""

    @title("make-admin назначает роль админ существующему пользователю")
    @severity(severity_level.BLOCKER)
    def test_promotes_existing_user(self, setup_app: Flask, setup_test_user: UserObject):
        """make-admin переводит существующего пользователя в ADMIN.

        Ожидание: exit_code 0, в выводе подтверждение; в БД роль пользователя —
        ADMIN, пароль не изменён (команда его не трогает).
        """
        existing = setup_test_user
        with step("Оператор. CLI. Назначение администратора командой make-admin"):
            result = invoke_cli(setup_app, make_admin, [existing.db_model.username])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="теперь администратор" in result.output,
                allure_step_name="В выводе есть подтверждение назначения",
                error_text="В выводе команды нет подтверждения назначения!",
            )

        with step("ORM. Проверка роли и пароля пользователя в БД"):
            with setup_app.app_context():
                user = db.session.get(User, existing.db_model.id)
            assert_equal(expect=Roles.ADMIN, actual=user.role, name="user.role")
            assert_condition(
                condition=user.check_password(existing.password),
                allure_step_name="Пароль пользователя не изменён",
                error_text="Пароль пользователя изменился после make-admin!",
            )

    @title("make-admin на несуществующем пользователе сообщает об отсутствии и ничего не создаёт")
    @severity(severity_level.CRITICAL)
    def test_user_not_found(self, setup_app: Flask):
        """make-admin с несуществующим именем завершается сообщением, без создания.

        Ожидание: exit_code 0 (отказ — сообщением, не падением), в выводе
        «не найден»; пользователь в БД не создан.
        """
        with step("Оператор. CLI. Попытка назначения администратора несуществующему пользователю"):
            result = invoke_cli(setup_app, make_admin, ["ghost"])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="не найден" in result.output,
                allure_step_name="В выводе сообщение об отсутствии пользователя",
                error_text="В выводе команды нет сообщения «не найден»!",
            )

        with step("ORM. Проверка, что пользователь не создан"):
            with setup_app.app_context():
                user = db.session.execute(db.select(User).filter_by(username="ghost")).scalars().first()
            assert_condition(
                condition=user is None,
                allure_step_name="Пользователь ghost не создан",
                error_text="Пользователь ghost появился в БД после make-admin!",
            )

    @title("Повторный make-admin на уже-админе идемпотентен")
    @severity(severity_level.MINOR)
    def test_repeated_promotion_is_idempotent(self, setup_app: Flask, setup_test_user: UserObject):
        """make-admin на пользователе с ролью ADMIN завершается штатно, без побочных эффектов.

        Ожидание: exit_code 0, вывод тот же, что при первом назначении;
        роль остаётся ADMIN, пароль не тронут. Контракт: команда не различает
        «стал админом» и «уже был админом» — повтор безопасен.
        """
        admin = setup_test_user
        with step("ORM. Предусловие. Пользователь уже с ролью ADMIN"):
            with setup_app.app_context():
                user = db.session.get(User, admin.db_model.id)
                user.role = Roles.ADMIN
                db.session.commit()

        with step("Оператор. CLI. Повторное назначение администратора командой make-admin"):
            result = invoke_cli(setup_app, make_admin, [admin.db_model.username])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="теперь администратор" in result.output,
                allure_step_name="В выводе то же подтверждение назначения",
                error_text="Вывод при повторном назначении отличается от первого!",
            )

        with step("ORM. Проверка неизменности пользователя"):
            with setup_app.app_context():
                user = db.session.get(User, admin.db_model.id)
            assert_equal(expect=Roles.ADMIN, actual=user.role, name="user.role")
            assert_condition(
                condition=user.check_password(admin.password),
                allure_step_name="Пароль пользователя не изменён",
                error_text="Пароль пользователя изменился после повторного make-admin!",
            )