"""Тесты обработки необработанных исключений: страница ошибки 500."""

from flask import Flask
from glamor import epic, feature, severity, severity_level, step, story, title

from tests.tools.asserters.base_asserters import assert_condition, assert_equal


@epic("WEB")
@feature("Обработка ошибок сервера")
@story("Необработанное исключение")
class TestServerError500:
    """Проверки обработчика необработанных исключений (500)."""

    @title("Необработанное исключение отдаёт страницу 500")
    @severity(severity_level.CRITICAL)
    def test_unhandled_exception_returns_500(self, setup_app: Flask):
        """Необработанное исключение в роуте приводит к странице 500.

        Ожидание: ответ 500, в теле — страница из errors/500.html.
        Нюанс теста: в TESTING-режиме Flask пробрасывает исключения мимо
        errorhandler(500), поэтому PROPAGATE_EXCEPTIONS гасится явно —
        поведение приводится к продовому.
        """
        @setup_app.route("/boom")
        def boom():
            raise RuntimeError("искусственная ошибка для теста")

        setup_app.config["PROPAGATE_EXCEPTIONS"] = False

        with step("Оператор. WEB. Запрос к роуту с необработанным исключением"):
            client = setup_app.test_client()
            response = client.get("/boom")
            assert_equal(expect=500, actual=response.status_code, name="HTTP status")

        with step("Проверка тела ответа: страница ошибки 500"):
            assert_condition(
                condition=b"500" in response.data,
                allure_step_name="В теле ответа страница ошибки 500",
                error_text="В теле ответа нет страницы errors/500.html!",
            )
