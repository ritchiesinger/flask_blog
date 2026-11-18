"""Декоратор проверки роли пользователя для API-роутов."""

from collections.abc import Callable
from functools import wraps

from flask_jwt_extended import get_current_user, verify_jwt_in_request

from blog.services.base_errors import ForbiddenError


def role_required[**P, R](*roles: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Ограничивает доступ к роуту пользователями с одной из заданных ролей.

    Требует действующий JWT-токен: сначала проверяется токен, затем роль
    текущего пользователя. Если пользователь не найден (например, удалён,
    а токен ещё жив) или его роль не входит в заданные — выбрасывается
    ForbiddenError (403 через api_errors).

    Args:
        roles: Допустимые роли, например Roles.ADMIN.

    Returns:
        Декоратор для функции-роута с теми же аргументами и типом возврата.

    Example:
        @bp.delete("/posts/<int:post_id>")
        @api_errors
        @jwt_required()
        @role_required(Roles.ADMIN)
        def delete_post(post_id: int): ...
    """

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            verify_jwt_in_request()
            user = get_current_user()

            # Если пользователь не найден (например, удалён, а токен ещё жив) — 403
            if user is None or user.role not in roles:
                raise ForbiddenError("Недостаточно прав для выполнения операции")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
