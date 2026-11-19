"""Роуты API для администрирования пользователей."""

from typing import Any

from flask import Blueprint, request
from flask_jwt_extended import get_current_user

from blog.api.decorators import role_required
from blog.api.errors import api_errors
from blog.constants import USERS_PER_PAGE, Roles
from blog.pagination import page_from_args, per_page_from_args
from blog.services import admin_service, user_service
from blog.services.base_errors import BadRequestError

bp = Blueprint("api_admin", __name__)


@bp.get("/api/users")
@api_errors
@role_required(Roles.ADMIN)
def list_users() -> dict[str, Any]:
    """Возвращает страницу пользователей в конверте с пагинацией.

    Доступно только администраторам (SUPERADMIN проходит по иерархии,
    → ARC-0041).

    Query-параметры: page (по умолчанию 1), per_page (по умолчанию
    USERS_PER_PAGE, срезается до MAX_PER_PAGE).

    Returns:
        Конверт: users — представления пользователей страницы, page, pages,
        total, per_page.
    """
    pagination = admin_service.list_users(
        page=page_from_args(),
        per_page=per_page_from_args(USERS_PER_PAGE),
    )
    return {
        "users": [{"id": u.id, "username": u.username, "role": u.role} for u in pagination.items],
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
        "per_page": pagination.per_page,
    }


@bp.patch("/api/users/<int:user_id>")
@api_errors
@role_required(Roles.SUPERADMIN)
def change_user_role(user_id: int) -> dict[str, Any]:
    """Меняет роль пользователя. Доступно только SuperAdministrator.

    Поверхность смены роли — только USER <-> ADMIN: SUPERADMIN через
    интерфейсы не выдаётся и не снимается (роль уникальна, → ARC-0041).
    Свою роль супер-админ поменять не может.

    Тело запроса: {"role": "user" | "admin"}.

    Args:
        user_id: Идентификатор пользователя.

    Returns:
        Представление пользователя с новой ролью.

    Raises:
        BadRequestError: Ключ role отсутствует или роль вне поверхности.
        ForbiddenError: Актёр меняет собственную роль (не-супер отсечён
            декоратором).
        NotFoundError: Пользователь не существует.
    """
    payload = request.get_json(silent=True) or {}
    if "role" not in payload:
        raise BadRequestError("Отсутствует ключ 'role'.")
    user = user_service.change_role(user_id, payload["role"], actor=get_current_user())
    return {"id": user.id, "username": user.username, "role": user.role}


@bp.delete("/api/users/<int:user_id>")
@api_errors
@role_required(Roles.ADMIN)
def delete_user(user_id: int) -> tuple[str, int]:
    """Удаляет пользователя с указанным идентификатором.

    Доступно только администраторам; передаёт удаляющему как actor,
    чтобы сервис мог запретить самоудаление (если такая проверка есть).

    Args:
        user_id: Идентификатор пользователя.

    Returns:
        Пустое тело со статусом 204.
    """
    admin_service.delete_user(user_id, actor=get_current_user())
    return "", 204
