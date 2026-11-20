"""Тесты WEB-шпаргалки Markdown: присутствие на формах поста, отсутствие в публичных местах."""

from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_status_code
from tests.tools.clients.web_client import WebClient

CHEATSHEET_ANCHOR = 'id="md-cheatsheet"'
CHEATSHEET_TRIGGER = 'data-bs-target="#md-cheatsheet"'


@epic("WEB")
@feature("Посты")
@story("Шпаргалка Markdown")
class TestCheatsheetPresence:
    """Шпаргалка свернута у редактора и присутствует только на формах поста."""

    @title("Шпаргалка есть на форме создания поста")
    @severity(severity_level.MINOR)
    def test_cheatsheet_on_create_form(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """Авторизованный пользователь видит шпаргалку на форме создания.

        Ожидание: 200; в разметке есть якорь #md-cheatsheet и триггер с
        data-bs-target на него. Проверка структурная, не по видимому тексту
        кнопки (→ ARC-0039).
        """
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Открытие формы создания поста"):
            response = user.web.posts.create_form()
            assert_status_code(expect=200, response=response)
            page = response.get_data(as_text=True)
            assert_condition(
                condition=CHEATSHEET_ANCHOR in page,
                allure_step_name="Якорь шпаргалки есть на форме создания",
                error_text="Блок #md-cheatsheet не найден на форме создания поста!",
            )
            assert_condition(
                condition=CHEATSHEET_TRIGGER in page,
                allure_step_name="Триггер шпаргалки есть на форме создания",
                error_text="Кнопка-триггер шпаргалки не найдена на форме создания поста!",
            )

    @title("Шпаргалка есть на форме редактирования своего поста")
    @severity(severity_level.MINOR)
    def test_cheatsheet_on_update_form(
            self,
            setup_app_client: FlaskClient,
            setup_test_user: UserObject,
            setup_test_user_post: dict,
    ):
        """Автор своего поста видит шпаргалку и на форме редактирования.

        Ожидание: 200; в разметке есть якорь #md-cheatsheet и триггер на него.
        Пост создаётся тем же пользователем, что и логинится — предусловия
        разделяют одну фикстуру.
        """
        user, post = setup_test_user, setup_test_user_post
        with step("Пользователь. WEB. Авторизация автора поста"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Открытие формы редактирования поста"):
            response = user.web.posts.update_form(post_id=post["id"])
            assert_status_code(expect=200, response=response)
            page = response.get_data(as_text=True)
            assert_condition(
                condition=CHEATSHEET_ANCHOR in page,
                allure_step_name="Якорь шпаргалки есть на форме редактирования",
                error_text="Блок #md-cheatsheet не найден на форме редактирования поста!",
            )
            assert_condition(
                condition=CHEATSHEET_TRIGGER in page,
                allure_step_name="Триггер шпаргалки есть на форме редактирования",
                error_text="Кнопка-триггер шпаргалки не найдена на форме редактирования поста!",
            )


@epic("WEB")
@feature("Посты")
@story("Шпаргалка Markdown")
class TestCheatsheetAbsence:
    """В публичных местах шпаргалки быть не должно."""

    @title("Шпаргалки нет в ленте и на странице поста")
    @severity(severity_level.MINOR)
    def test_no_cheatsheet_on_public_pages(self, setup_app_client: FlaskClient, setup_test_user_post: dict):
        """Гость не встречает разметку шпаргалки вне форм поста.

        Ожидание: 200 на ленте и на странице поста; якоря #md-cheatsheet и
        триггера в разметке нет (структурная проверка отсутствия, → ARC-0039).
        """
        post = setup_test_user_post
        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. Открытие главной страницы"):
            response = guest.posts.index()
            assert_status_code(expect=200, response=response)
            page = response.get_data(as_text=True)
            assert_condition(
                condition=CHEATSHEET_ANCHOR not in page,
                allure_step_name="Якоря шпаргалки нет в ленте",
                error_text="Шпаргалка неожиданно оказалась в ленте!",
            )
        with step("Гость. WEB. Открытие страницы поста"):
            response = guest.posts.view(post_id=post["id"])
            assert_status_code(expect=200, response=response)
            page = response.get_data(as_text=True)
            assert_condition(
                condition=CHEATSHEET_ANCHOR not in page,
                allure_step_name="Якоря шпаргалки нет на странице поста",
                error_text="Шпаргалка неожиданно оказалась на странице поста!",
            )
