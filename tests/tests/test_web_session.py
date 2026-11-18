"""Тесты загрузки пользователя из сессии: работа колбэка Flask-Login."""

from flask import Flask
from glamor import epic, feature, severity, severity_level, step, story, title

from tests.tools.asserters.base_asserters import assert_condition, assert_equal
from tests.tools.clients.web_client import WebClient


@epic("WEB")
@feature("Загрузка пользователя из сессии")
@story("Колбэк Flask-Login")
class TestSessionUserLoading:
    """Проверки, что пользователь под сессией загружается колбэком load_user."""

    @title("После логина запрос отдаёт данные пользователя из сессии")
    @severity(severity_level.CRITICAL)
    def test_index_shows_authenticated_user(self, setup_app: Flask, setup_test_user):
        """Логин через форму, затем запрос к главной: колбэк load_user срабатывает честно.

        Ожидание: логин → 302 (редирект не следует — канон двухшагового редиректа); запрос к главной под сессией → 200,
        в теле имя пользователя и ссылка «Выход». Нюанс: Flask-Login вызывает load_user из blog/loaders.py при
        обращении к current_user — базовый шаблон читает его на каждом запросе, поэтому колбэк гарантированно
        отрабатывает (строка return в loaders.py).
        """
        username = setup_test_user.db_model.username

        client = WebClient(setup_app.test_client())

        with step("Оператор. WEB. Логин фикстурного пользователя через форму"):
            response = client.auth.login(username, setup_test_user.password)
            assert_equal(expect=302, actual=response.status_code, name="HTTP status")

        with step("Оператор. WEB. Запрос к главной под сессией"):
            response = client.posts.index()
            assert_equal(expect=200, actual=response.status_code, name="HTTP status")

        with step("Проверка: пользователь загружен из сессии, а не просто сидит cookie"):
            assert_condition(
                condition=username.encode() in response.data,
                allure_step_name="Имя пользователя в теле главной страницы",
                error_text="Имени пользователя нет на главной: load_user вернул None или не сработал!",
            )
            assert_condition(
                condition=b'data-action="logout"' in response.data,
                allure_step_name="Ссылка «Выход» в навигации (current_user.is_authenticated)",
                error_text="Навигация показывает гостя: пользователь не загружен из сессии!",
            )
