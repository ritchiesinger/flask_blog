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
from blog.services import avatar_service, user_service
from blog.services.base_errors import BadRequestError, NotFoundError
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

    Args:
        username: логин пользователя профиля.

    Returns:
        Страница профиля.
    """
    tab = tab_from_args(allowed=PROFILE_TABS, default=PROFILE_TAB_POSTS)
    profile_user, pagination = user_service.get_profile(username=username, tab=tab, page=page_from_args())
    can_change_role = (
        current_user.is_authenticated
        and role_includes(current_user.role, Roles.SUPERADMIN)
        and profile_user.id != current_user.id
        and profile_user.role in ROLE_TARGET_OPTIONS
    )
    is_owner = current_user.is_authenticated and current_user.id == profile_user.id
    return render_template(
        "blog/profile.html",
        profile_user=profile_user,
        tab=tab,
        pagination=pagination,
        can_change_role=can_change_role,
        is_owner=is_owner,
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


@bp.post("/user/<username>/display_name")
@login_required
@web_errors
def change_display_name(username: str):
    """Меняет отображаемое имя; только владелец профиля (→ ARC-0051).

    Гость — редирект на логин; не-владелец под сессией — 404 (скрытое
    действие). Валидация (strip, лимит, пустое → сброс) — в сервисе.

    Args:
        username: логин владельца профиля.

    Returns:
        Редирект на профиль с флеш-сообщением о результате.
    """
    if current_user.username != username:
        raise NotFoundError("Страница не найдена.")
    user = user_service.change_display_name(username, request.form.get("display_name"), actor=current_user)
    flash(f"Отображаемое имя обновлено: {user.shown_name}.", "success")
    return redirect(url_for("user.profile", username=username))


@bp.post("/user/<username>/avatar")
@login_required
@web_errors
def upload_avatar(username: str):
    """Загружает аватар; только владелец профиля (→ ARC-0051).

    Гость — редирект на логин; не-владелец под сессией — 404 (скрытое
    действие, как смена роли). Проверка владельца дублируется гвардом
    сервиса (defense-in-depth). Кроп делает виджет в браузере — на сервер
    приходит уже квадрат; сервис дорежет и пережмёт до двух размеров.

    Args:
        username: логин владельца профиля.

    Returns:
        Редирект на профиль с флеш-сообщением о результате.

    Raises:
        BadRequestError: файл не передан или не прошёл валидацию сервиса.
    """
    if current_user.username != username:
        raise NotFoundError("Страница не найдена.")
    file = request.files.get("file")
    if file is None or not file.filename:
        raise BadRequestError("Файл не передан.")
    avatar_service.save_avatar(current_user, file, file.filename, actor=current_user)
    flash("Аватар обновлён.", "success")
    return redirect(url_for("user.profile", username=username))


@bp.post("/user/<username>/avatar/reset")
@login_required
@web_errors
def reset_user_avatar(username: str):
    """Сбрасывает аватар: возврат к автогенерации; только владелец.

    Args:
        username: логин владельца профиля.

    Returns:
        Редирект на профиль с флеш-сообщением о результате.
    """
    if current_user.username != username:
        raise NotFoundError("Страница не найдена.")
    avatar_service.reset_avatar(current_user, actor=current_user)
    flash("Аватар сброшен.", "success")
    return redirect(url_for("user.profile", username=username))
