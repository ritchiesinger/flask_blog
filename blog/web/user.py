"""WEB-роуты профиля пользователя."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from blog.constants import (
    PROFILE_TAB_POSTS,
    PROFILE_TABS,
    ROLE_BADGE_CLASSES,
    ROLE_DISPLAY_NAMES,
    ROLE_TARGET_OPTIONS,
    Roles,
    role_includes,
)
from blog.pagination import page_from_args, tab_from_args
from blog.services import user_service
from blog.services.base_errors import NotFoundError
from blog.web.errors import web_errors

bp = Blueprint("user", __name__)


@bp.get("/user/<username>")
@web_errors
def profile(username: str):
    """Профиль пользователя: аватар, логин, роль и лента активной вкладки.

    Вкладка — параметр tab (posts/comments, мусор → posts), страница ленты —
    page. Санитизация обоих — через pagination.py. Рендерится только активная
    лента: неактивная не запрашивается вовсе. Неизвестный логин — NotFoundError
    → фирменная 404-страница.

    Контролы смены роли видит только SuperAdministrator и только на чужом
    профиле пользователя с поверхностной ролью (USER/ADMIN); на своём профиле
    контролов нет — смена собственной роли запрещена (→ ARC-0041).
    """
    tab = tab_from_args(allowed=PROFILE_TABS, default=PROFILE_TAB_POSTS)
    profile_user, pagination = user_service.get_profile(username=username, tab=tab, page=page_from_args())
    can_change_role = (
        current_user.is_authenticated
        and role_includes(current_user.role, Roles.SUPERADMIN)
        and profile_user.id != current_user.id
        and profile_user.role in ROLE_TARGET_OPTIONS
    )
    return render_template(
        "blog/profile.html",
        profile_user=profile_user,
        tab=tab,
        pagination=pagination,
        can_change_role=can_change_role,
        available_roles=ROLE_TARGET_OPTIONS.get(profile_user.role, ()),
        role_titles=ROLE_DISPLAY_NAMES,
        role_badges=ROLE_BADGE_CLASSES,
    )


@bp.post("/user/<username>/role")
@login_required
@web_errors
def change_role(username: str):
    """Меняет роль пользователя профиля; только SuperAdministrator.

    Гость — редирект на логин (login_required); не-супер под сессией — 404
    (скрытое действие, как в админке: не подсказывать существование).
    Проверки поверхности (USER/ADMIN), запрета самоизменения и валидации
    роли — в user_service.change_role: единая логика для API и WEB.

    Args:
        username: логин пользователя, чья роль меняется.

    Returns:
        Редирект на профиль с флеш-сообщением о результате.
    """
    if not role_includes(current_user.role, Roles.SUPERADMIN):
        raise NotFoundError("Страница не найдена.")
    target = user_service.get_user_by_username(username)
    new_role = request.form.get("role", "")
    user_service.change_role(target.id, new_role, actor=current_user)
    flash(f"Роль пользователя {username} изменена на {ROLE_DISPLAY_NAMES.get(new_role, new_role)}.", "success")
    return redirect(url_for("user.profile", username=username))
