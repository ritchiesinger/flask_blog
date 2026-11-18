"""Юнит-тесты обёртки web_errors: конвертация доменных ошибок в HTTP.

Обёртка проверяется напрямую, без приложения и клиента: ``abort()`` поднимает исключение werkzeug и вне app-контекста,
поэтому достаточно перехватить его.
"""

import pytest
from glamor import epic, feature, severity, severity_level, story, title
from werkzeug.exceptions import HTTPException

from blog.services.base_errors import ConflictError
from blog.web.errors import web_errors


@epic("UNIT")
@feature("Обертки ошибок")
@story("WebErrors")
@severity(severity_level.NORMAL)
class TestWebErrors:
    """Контракт обёртки: маппинг ServiceError и пропуск посторонних исключений."""

    @title("ServiceError конвертируется в abort со статусом самого исключения")
    def test_service_error_converted_to_its_status_code(self):
        """ServiceError конвертируется в abort со статусом самого исключения.

        Ожидание: HTTPException с кодом 409 — берётся из e.status_code, а не подставляется константой. Fallback-ветка
        через роуты недостижима, поэтому проверяется только юнитом.
        """

        @web_errors
        def view():
            raise ConflictError("дубль имени")

        with pytest.raises(HTTPException) as exc_info:
            view()
        assert exc_info.value.code == 409

    @title("Постороннее исключение проходит как есть")
    def test_foreign_exception_not_caught(self):
        """Постороннее исключение обёртка не ловит — долетает как есть.

        Ожидание: ValueError поднимается наружу в исходном виде. Сознательный контракт обёртки: баги должны дойти до
        пользователя как 500.
        """

        @web_errors
        def view():
            raise ValueError("баг")

        with pytest.raises(ValueError):
            view()
