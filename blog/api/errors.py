"""Декоратор для обработки ошибок сервисного слоя в API-роутах."""

from collections.abc import Callable
from functools import wraps

from flask import jsonify

from blog.services.base_errors import BadRequestError, ForbiddenError, NotFoundError, ServiceError


def api_errors[**P, R](view: Callable[P, R]) -> Callable[P, R]:
    """Перехватывает исключения сервисного слоя и возвращает их как JSON-ответы.

    Преобразует ServiceError и его наследников в JSON с полем "error"
    и соответствующим статусом: NotFoundError -> 404, ForbiddenError -> 403,
    BadRequestError -> 400, остальные — по status_code исключения.
    Необработанные исключения пробрасываются дальше и дают 500.

    Args:
        view: Функция-роут, возвращающая JSON-ответ.

    Returns:
        Обёрнутая функция с теми же аргументами и типом возврата.
    """

    @wraps(view)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return view(*args, **kwargs)
        except NotFoundError as e:
            return jsonify({"error": str(e)}), 404
        except ForbiddenError as e:
            return jsonify({"error": str(e)}), 403
        except BadRequestError as e:
            return jsonify({"error": str(e)}), 400
        except ServiceError as e:
            return jsonify({"error": str(e)}), e.status_code
        # Остальные — 500 по умолчанию

    return wrapper
