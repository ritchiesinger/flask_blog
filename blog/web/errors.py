"""Обработка ошибок для web-роутов."""

from functools import wraps

from flask import abort

from blog.services.base_errors import ForbiddenError, NotFoundError, ServiceError


def web_errors(view):
    """Конвертирует доменные ошибки в HTTP-ответы для web-роутов.

    Перехватывает исключения сервисного слоя и превращает их в abort():
    NotFoundError -> 404, ForbiddenError -> 403, прочие ServiceError —
    со своим status_code.

    Ошибки форм обрабатываются в самих роутах через flash, поэтому
    BadRequestError сюда не попадает. Остальные исключения не ловим
    сознательно: баги должны дойти до пользователя как 500.

    Args:
        view: Декорируемая view-функция.

    Returns:
        Обёрнутая функция с тем же контрактом вызова.
    """
    @wraps(view)
    def wrapper(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except NotFoundError:
            abort(404)
        except ForbiddenError:
            abort(403)
        except ServiceError as e:
            abort(e.status_code)
    return wrapper
