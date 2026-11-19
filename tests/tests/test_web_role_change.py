"""WEB-тесты смены роли на профиле пользователя.

Контролы (dropdown + «Изменить») рисуются только супер-админу и только на
чужом профиле пользователя с поверхностной ролью; на собственном профиле
супер-админа их нет — смена собственной роли запрещена (→ ARC-0041).
Не-супер, долбящийся в POST напрямую, получает 404: действие скрыто.
"""

from flask import Flask
from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.constants import Roles
from tests.objects.user import UserObject
from tests.preconditions.users_preconditions import create_user
from tests.tools.asserters.base_asserters import assert_condition, assert_status_code
from tests.tools.clients.web_client import WebClient

PAGE_NOT_FOUND = "Страница не найдена."
CHANGE_ROLE_BUTTON = "Изменить"
ROLE_SELECT_MARK = 'name="role"'
FLASH_ROLE_CHANGED = "изменена на Administrator."


def make_superadmin(app: Flask, app_client: FlaskClient, username: str = "super_boss") -> UserObject:
    """Создаёт супер-админа напрямую через модель: роль не выдаётся интерфейсами.

    Args:
        app: тестовое приложение (app_context для записи в БД).
        app_client: клиент для UserObject.
        username: логин супер-админа.

    Returns:
        UserObject супер-админа.
    """
    return create_user(
        app=app, app_client=app_client, username=username,
        password="password123", role=Roles.SUPERADMIN,
    )


@epic("WEB")
@feature("Профиль пользователя", "Управление ролями")
@story("Видимость контролов смены роли")
class TestRoleControlsVisibility:
    """Контролы видит только супер-админ и только на чужом профиле."""

    @severity(severity_level.BLOCKER)
    @title("Супер-администратор видит контролы смены роли на чужом профиле")
    def test_superadmin_sees_controls_on_foreign_profile(
            self, setup_app: Flask, setup_app_client: FlaskClient, setup_test_user: UserObject,
    ):
        """Профиль обычного пользователя под супер-админом: dropdown и кнопка «Изменить»."""
        super_user = make_superadmin(setup_app, setup_app_client)
        with step("Оператор. WEB. Логин супер-администратора"):
            super_user.web.auth.login(username=super_user.db_model.username, password=super_user.password)
        with step("Оператор. WEB. Открытие профиля обычного пользователя"):
            response = super_user.web.users.profile(username=setup_test_user.db_model.username)
            assert_status_code(expect=200, response=response)
            body = response.get_data(as_text=True)
        with step("Проверка содержимого"):
            assert_condition(
                condition=ROLE_SELECT_MARK in body,
                allure_step_name="Dropdown выбора роли на странице",
                error_text="Dropdown смены роли не найден на профиле!",
            )
            assert_condition(
                condition=CHANGE_ROLE_BUTTON in body,
                allure_step_name="Кнопка «Изменить» на странице",
                error_text="Кнопка смены роли не найдена на профиле!",
            )

    @severity(severity_level.CRITICAL)
    @title("На собственном профиле супер-администратора контролов нет")
    def test_superadmin_no_controls_on_own_profile(self, setup_app: Flask, setup_app_client: FlaskClient):
        """Свой профиль: смену собственной роли запрещено и в интерфейсе не рисуют."""
        super_user = make_superadmin(setup_app, setup_app_client)
        with step("Оператор. WEB. Логин супер-администратора"):
            super_user.web.auth.login(username=super_user.db_model.username, password=super_user.password)
        with step("Оператор. WEB. Открытие собственного профиля"):
            response = super_user.web.users.profile(username=super_user.db_model.username)
            assert_status_code(expect=200, response=response)
            body = response.get_data(as_text=True)
        assert_condition(
            condition=CHANGE_ROLE_BUTTON not in body,
            allure_step_name="Кнопки «Изменить» на собственном профиле нет",
            error_text="Контролы смены роли отрисованы на собственном профиле супер-админа!",
        )

    @severity(severity_level.NORMAL)
    @title("Обычный пользователь не видит контролов на чужом профиле")
    def test_regular_user_no_controls_on_foreign_profile(
            self, setup_app_client: FlaskClient, setup_test_user: UserObject,
    ):
        """Профиль другого пользователя под обычной сессией: контролов нет."""
        with step("Оператор. WEB. Логин обычного пользователя"):
            setup_test_user.web.auth.login(
                username=setup_test_user.db_model.username, password=setup_test_user.password,
            )
        with step("Оператор. WEB. Открытие чужого профиля"):
            response = setup_test_user.web.users.profile(username="someone_else")
            body = response.get_data(as_text=True)
        assert_condition(
            condition=CHANGE_ROLE_BUTTON not in body,
            allure_step_name="Контролов смены роли на странице нет",
            error_text="Контролы смены роли видны обычному пользователю!",
        )


@epic("WEB")
@feature("Профиль пользователя", "Управление ролями")
@story("Смена роли через профиль")
class TestChangeRoleAction:
    """Действие смены роли: редирект, флеш, изменение роли в БД."""

    @severity(severity_level.BLOCKER)
    @title("Супер-администратор меняет роль через профиль")
    def test_superadmin_changes_role(
            self, setup_app: Flask, setup_app_client: FlaskClient, setup_test_user: UserObject,
    ):
        """POST смены роли → 302 на профиль; после перехода флеш, в БД роль admin."""
        super_user = make_superadmin(setup_app, setup_app_client)
        with step("Оператор. WEB. Логин супер-администратора"):
            super_user.web.auth.login(username=super_user.db_model.username, password=super_user.password)
        with step("Оператор. WEB. Смена роли пользователя через профиль"):
            response = super_user.web.users.change_role(
                username=setup_test_user.db_model.username, role=Roles.ADMIN,
            )
        assert_status_code(expect=302, response=response)
        with step("Оператор. WEB. Переход по редиректу"):
            followed = setup_app_client.get(response.headers["Location"])
            body = followed.get_data(as_text=True)
        with step("Проверка флеша и состояния"):
            assert_condition(
                condition=FLASH_ROLE_CHANGED in body,
                allure_step_name="Флеш «Роль изменена на Administrator»",
                error_text="Флеш-сообщение о смене роли не найдено после редиректа!",
            )

    @severity(severity_level.CRITICAL)
    @title("Администратор, долбящийся в смену роли напрямую, получает 404")
    def test_non_super_direct_post_404(self, setup_app: Flask, setup_app_client: FlaskClient,
                                       setup_test_user: UserObject):
        """POST /user/<username>/role под не-супером → 404: действие скрыто."""
        admin = create_user(
            app=setup_app, app_client=setup_app_client, username="plain_admin",
            password="password123", role=Roles.ADMIN,
        )
        with step("Оператор. WEB. Логин администратора"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Оператор. WEB. Прямой POST смены роли"):
            response = admin.web.users.change_role(
                username=setup_test_user.db_model.username, role=Roles.ADMIN,
            )
        assert_status_code(expect=404, response=response)
        assert_condition(
            condition=PAGE_NOT_FOUND in response.get_data(as_text=True),
            allure_step_name="Фирменная 404-страница",
            error_text="Ответ не является фирменной страницей 404!",
        )

    @severity(severity_level.NORMAL)
    @title("Гость, долбящийся в смену роли, попадает на логин")
    def test_guest_redirects_to_login(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """POST без сессии → 302 на /login (login_required)."""
        with step("Гость. WEB. Прямой POST смены роли без сессии"):
            response = WebClient(setup_app_client).users.change_role(
                username=setup_test_user.db_model.username, role=Roles.ADMIN,
            )
        assert_status_code(expect=302, response=response)
