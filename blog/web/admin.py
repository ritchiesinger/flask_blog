"""WEB-роуты административной панели.

Доступ (решение 2026-11-13): гость — редирект на логин (login_required);
не-админ под сессией — 404 (страница «не существует», не раскрываем её
наличие); админ — 200. Самоудаление — ForbiddenError от сервиса (403),
как в API: админ знает, что страница есть, и заслуживает честного ответа.
"""

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from blog.constants import ROLE_BADGE_CLASSES, ROLE_DISPLAY_NAMES, USERS_PER_PAGE
from blog.pagination import page_from_args
from blog.services import admin_service
from blog.services.base_errors import NotFoundError
from blog.web.errors import web_errors

bp = Blueprint("admin", __name__)


@bp.get("/admin/users")
@login_required
@web_errors
def users():
    """Список пользователей с пагинацией (только для администраторов).

    Роль каждого пользователя — цветной бейдж с человекочитаемым названием
    (→ ARC-0043); иерархия видна прямо в таблице (→ ARC-0041).
    """
    if not current_user.is_admin:
        raise NotFoundError("Страница не найдена.")
    pagination = admin_service.list_users(page=page_from_args(), per_page=USERS_PER_PAGE)
    return render_template(
        "admin/users.html",
        users=pagination.items,
        pagination=pagination,
        role_badges=ROLE_BADGE_CLASSES,
        role_titles=ROLE_DISPLAY_NAMES,
    )


@bp.post("/admin/users/<int:user_id>/delete")
@login_required
@web_errors
def delete_user(user_id: int):
    """Удаление пользователя; для не-админа страница не существует (404).

    Args:
        user_id: идентификатор удаляемого пользователя.

    Returns:
        Редирект на список пользователей.
    """
    if not current_user.is_admin:
        raise NotFoundError("Страница не найдена.")
    admin_service.delete_user(user_id, actor=current_user)
    flash("Пользователь удалён.", "success")
    return redirect(url_for("admin.users"))
