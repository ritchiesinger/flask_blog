"""WEB-тесты человекочитаемых названий ролей: единый язык UI (→ ARC-0043)."""

from flask import Flask
from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.constants import Roles
from tests.objects.user import UserObject
from tests.preconditions.users_preconditions import create_user
from tests.tools.asserters.base_asserters import assert_condition, assert_status_code
from tests.tools.clients.web_client import WebClient

BADGE_USER = ">User</span>"
BADGE_ADMIN = ">Administrator</span>"
OPTION_ADMIN_VALUE = 'value="admin"'
OPTION_ADMIN_TEXT = ">Administrator</option>"


@epic("WEB")
@feature("Профиль пользователя", "Управление ролями")
@story("Отображение ролей")
class TestRoleDisplay:
    """Бейджи и подписи dropdown говорят на языке флеша: Administrator, User."""

    @title("Бейдж роли на профиле показывает человекочитаемое название")
    @severity(severity_level.MINOR)
    def test_profile_badge_display_name(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """Гость на публичном профиле видит бейдж «User», а не машинное значение.

        Ожидание: 200; в разметке есть >User</span> и нет >user</span>.
        """
        user = setup_test_user
        with step("Гость. WEB. Открытие профиля пользователя"):
            response = WebClient(app_client=setup_app_client).users.profile(username=user.db_model.username)
            assert_status_code(expect=200, response=response)
            body = response.get_data(as_text=True)
        with step("Проверка содержимого"):
            assert_condition(
                condition=BADGE_USER in body,
                allure_step_name="Бейдж роли человекочитаемый",
                error_text="Бейдж профиля не содержит «User»!",
            )

    @title("Dropdown смены роли показывает «Administrator» при машинном value")
    @severity(severity_level.MINOR)
    def test_dropdown_option_display_name(
            self, setup_app: Flask, setup_app_client: FlaskClient, setup_test_user: UserObject,
    ):
        """Супер-админ на чужом профиле: подпись опции человекочитаемая, value машинный.

        Ожидание: 200; в разметке value="admin" (контракт POST не менялся) и
        текст опции «Administrator».
        """
        super_user = create_user(
            app=setup_app, app_client=setup_app_client,
            username="display_super", password="password123", role=Roles.SUPERADMIN,
        )
        with step("Оператор. WEB. Логин супер-администратора"):
            super_user.web.auth.login(username=super_user.db_model.username, password=super_user.password)
        with step("Оператор. WEB. Открытие профиля обычного пользователя"):
            response = super_user.web.users.profile(username=setup_test_user.db_model.username)
            assert_status_code(expect=200, response=response)
            body = response.get_data(as_text=True)
        with step("Проверка содержимого"):
            assert_condition(
                condition=OPTION_ADMIN_VALUE in body,
                allure_step_name="value опции остаётся машинным",
                error_text="Опция dropdown потеряла машинное value!",
            )
            assert_condition(
                condition=OPTION_ADMIN_TEXT in body,
                allure_step_name="Подпись опции человекочитаемая",
                error_text="Опция dropdown не показывает «Administrator»!",
            )

    @title("Бейдж роли в списке пользователей админки человекочитаемый")
    @severity(severity_level.MINOR)
    def test_admin_list_badge_display_name(self, setup_admin_user: UserObject):
        """Админ в списке пользователей видит свой бейдж как «Administrator»."""
        admin = setup_admin_user
        with step("Администратор. WEB. Авторизация"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Администратор. WEB. Открытие списка пользователей"):
            response = admin.web.admin.users()
            assert_status_code(expect=200, response=response)
            body = response.get_data(as_text=True)
        with step("Проверка содержимого"):
            assert_condition(
                condition=BADGE_ADMIN in body,
                allure_step_name="Бейдж роли в админке человекочитаемый",
                error_text="Бейдж админки не содержит «Administrator»!",
            )
