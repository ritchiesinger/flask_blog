"""Тесты защиты web-логина от open redirect (параметр next)."""

from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from tests.constants.web_endpoints import WebEndpoints
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_redirect, assert_status_code


@epic("WEB")
@feature("Аутентификация")
@story("Защита от open redirect")
class TestLoginRedirect:
    """Параметр next при успешном логине ведёт только на внутренние пути."""

    @title("Внешний next при логине ведёт на главную, а не на внешний сайт")
    @severity(severity_level.CRITICAL)
    def test_external_next_leads_to_index(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """Внешний URL в next не уводит наружу — редирект на главную.

        Ожидание: 302 и Location в точности равен главной — проверка именно
        «повёл на главную», а не просто «не уловит наружу»: редирект на
        страницу ошибки или обратно на логин тоже не соответствует названию.
        """
        user = setup_test_user
        with step("Пользователь. WEB. Логин с внешним next"):
            response = setup_app_client.post(
                f"{WebEndpoints.AUTH.LOGIN}?next=https://evil.site",
                data={
                    "username": user.db_model.username,
                    "password": user.password,
                },
            )
            assert_redirect(expect="/", response=response)

    @title("Протокол-относительный next при логине ведёт на главную")
    @severity(severity_level.CRITICAL)
    def test_protocol_relative_next_leads_to_index(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """Протокол-относительный next=//evil.site тоже отвергается.

        Ожидание: 302 и в Location нет внешнего сайта. Форма ``//host``
        обходит наивную проверку «начинается с /» — отдельный тест оправдан.
        """
        user = setup_test_user
        with step("Пользователь. WEB. Логин с протокол-относительным next"):
            response = setup_app_client.post(
                f"{WebEndpoints.AUTH.LOGIN}?next=//evil.site",
                data={
                    "username": user.db_model.username,
                    "password": user.password,
                },
            )
            assert_status_code(expect=302, response=response)
            assert_condition(
                condition="evil.site" not in response.headers["Location"],
                allure_step_name="В Location нет внешнего сайта",
                error_text="Редирект уводит на внешний сайт!",
            )

    @title("Внутренний относительный next при логине сохраняется")
    @severity(severity_level.CRITICAL)
    def test_internal_next_is_honored(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """Внутренний относительный next работает как ожидается.

        Ожидание: 302 и Location в точности равен пути из next — защита
        не должна отбрасывать и легитимные внутренние пути.
        """
        user = setup_test_user
        with step("Пользователь. WEB. Логин с внутренним next"):
            response = setup_app_client.post(
                f"{WebEndpoints.AUTH.LOGIN}?next=/posts",
                data={"username": user.db_model.username, "password": user.password},
            )
            assert_redirect(expect="/posts", response=response)

    @title("next без ведущего слеша при логине ведёт на главную")
    @severity(severity_level.CRITICAL)
    def test_next_without_leading_slash_leads_to_index(
            self,
            setup_app_client: FlaskClient,
            setup_test_user: UserObject,
    ):
        """next="evil.com/path" без схемы отсекается проверкой ведущего слеша.

        Ожидание: 302, Location в точности равен главной — next отброшен,
        а не приведён к безопасному виду.
        """
        user = setup_test_user
        with step("Пользователь. WEB. Логин с next без ведущего слеша"):
            response = setup_app_client.post(
                f"{WebEndpoints.AUTH.LOGIN}?next=evil.com/path",
                data={"username": user.db_model.username, "password": user.password},
            )
            assert_redirect(expect="/", response=response)
