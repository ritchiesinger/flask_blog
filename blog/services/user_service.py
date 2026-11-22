"""Бизнес-логика профиля пользователя."""

from collections.abc import Callable

from flask_sqlalchemy.pagination import Pagination
from sqlalchemy.orm import joinedload

from blog.constants import (
    DISPLAY_NAME_MAX_LENGTH,
    POSTS_PER_PAGE,
    PROFILE_TAB_COMMENTS,
    PROFILE_TAB_POSTS,
    Roles,
    role_includes,
)
from blog.extensions import db
from blog.models.comment import Comment
from blog.models.post import Post
from blog.models.user import User
from blog.services import avatar_service

from .base_errors import BadRequestError, ConflictError, ForbiddenError, NotFoundError


def get_user_by_username(username: str) -> User:
    """Возвращает пользователя по логину.

    Args:
        username: Логин пользователя.

    Returns:
        Модель пользователя.

    Raises:
        NotFoundError: Пользователь не существует.
    """
    user = db.session.scalars(db.select(User).filter_by(username=username)).one_or_none()
    if user is None:
        raise NotFoundError(f"User '{username}' doesn't exist.")
    return user


def get_user_by_id(user_id: int) -> User:
    """Возвращает пользователя по идентификатору.

    Args:
        user_id: Идентификатор пользователя.

    Returns:
        Модель пользователя.

    Raises:
        NotFoundError: Пользователь не существует.
    """
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError(f"User #{user_id} doesn't exist.")
    return user


def change_role(user_id: int, new_role: str, *, actor: User) -> User:
    """Меняет роль пользователя. Доступно только SuperAdministrator.

    Поверхность смены роли — только USER <-> ADMIN: SUPERADMIN не выдаётся и не снимается
    через интерфейсы (роль уникальна, единственный её канал — CLI, → ARC-0041). Свою роль
    супер-админ поменять не может.

    Args:
        user_id: Идентификатор пользователя, чья роль меняется.
        new_role: Новая роль (Roles.USER или Roles.ADMIN).
        actor: Действующий пользователь; смена роли — полномочие SUPERADMIN.

    Returns:
        Обновлённая модель пользователя.

    Raises:
        ForbiddenError: Актёр не супер-админ или меняет собственную роль.
        BadRequestError: Новая роль вне разрешённой поверхности (USER/ADMIN).
        NotFoundError: Пользователь не существует.
    """
    if not role_includes(actor.role, Roles.SUPERADMIN):
        raise ForbiddenError("Смену ролей выполняет только SuperAdministrator")
    if actor.id == user_id:
        raise ForbiddenError("Свою роль менять нельзя")
    if new_role not in _CHANGEABLE_ROLES:
        raise BadRequestError(f"Роль '{new_role}' недоступна для назначения")
    user = get_user_by_id(user_id)
    user.role = new_role
    db.session.commit()
    return user


_CHANGEABLE_ROLES = frozenset((Roles.USER, Roles.ADMIN))


def promote_to_superadmin(username: str) -> User:
    """Выдаёт роль SUPERADMIN пользователю. Единственный канал выдачи супер-роли (CLI).

    Роль уникальна по построению: персональный блог принадлежит одному хозяину.
    Сценарий смены хозяина — через CLI: удалить старого супер-админа, выдать роль новому.

    Args:
        username: Логин пользователя.

    Returns:
        Обновлённая модель пользователя.

    Raises:
        NotFoundError: Пользователь не существует.
        ConflictError: SuperAdministrator уже существует.
    """
    existing = db.session.scalar(db.select(User).filter_by(role=Roles.SUPERADMIN))
    if existing is not None:
        raise ConflictError(f"SuperAdministrator already exists: '{existing.username}'.")
    user = get_user_by_username(username)
    user.role = Roles.SUPERADMIN
    db.session.commit()
    return user


def delete_user(user_id: int) -> None:
    """Удаляет пользователя без проверки прав (CLI — читерский слой).

    Посты и комментарии уходят каскадом на уровне БД; аватарные файлы удаляются
    сразу после commit (→ ARC-0051) — аватары не имеют строк в БД, чистить их
    командой не из чего. Постовые картинки остаются до чистки clean-uploads.

    Args:
        user_id: Идентификатор пользователя.

    Raises:
        NotFoundError: Пользователь не существует.
    """
    user = get_user_by_id(user_id)
    avatar_name = user.avatar_filename
    db.session.delete(user)
    db.session.commit()
    if avatar_name:
        avatar_service.delete_avatar_files(avatar_name)  # после commit: сбой файлов не теряет БД-состояние


def change_display_name(username: str, new_name: str | None, *, actor: User) -> User:
    """Меняет отображаемое имя пользователя. Доступно только владельцу.

    Имя необязательное и неуникальное (→ ARC-0051): пустое значение после strip —
    сброс (display_name обнуляется, интерфейс показывает логин). Лимит длины —
    DISPLAY_NAME_MAX_LENGTH. Гвард «только владелец» здесь defense-in-depth:
    WEB-роут прячет действие 404 раньше (как в смене роли, → ARC-0041).

    Args:
        username: Логин пользователя, чьё имя меняется.
        new_name: Новое отображаемое имя; None или пустое — сброс на логин.
        actor: Действующий пользователь; менять имя может только владелец.

    Returns:
        Обновлённая модель пользователя.

    Raises:
        ForbiddenError: Актёр не владелец профиля.
        BadRequestError: Имя длиннее DISPLAY_NAME_MAX_LENGTH.
        NotFoundError: Пользователь не существует.
    """
    if actor.username != username:
        raise ForbiddenError("Отображаемое имя меняет только владелец профиля")
    user = get_user_by_username(username)
    cleaned = (new_name or "").strip()
    if not cleaned:
        user.display_name = None
    elif len(cleaned) > DISPLAY_NAME_MAX_LENGTH:
        raise BadRequestError(
            f"Отображаемое имя не может быть длиннее {DISPLAY_NAME_MAX_LENGTH} символов"
        )
    else:
        user.display_name = cleaned
    db.session.commit()
    return user


def list_user_posts(user_id: int, page: int = 1, per_page: int = POSTS_PER_PAGE) -> Pagination:
    """Возвращает страницу постов пользователя, новые первыми.

    Args:
        user_id: Идентификатор автора.
        page: Номер страницы, начиная с 1.
        per_page: Размер страницы; по умолчанию POSTS_PER_PAGE.

    Returns:
        Объект Pagination: items — посты страницы, total, pages,
        has_prev/has_next.
    """
    stmt = db.select(Post).filter_by(author_id=user_id).order_by(Post.created.desc(), Post.id.desc())
    return db.paginate(stmt, page=page, per_page=per_page, error_out=False)


def list_user_comments(user_id: int, page: int = 1, per_page: int = POSTS_PER_PAGE) -> Pagination:
    """Возвращает страницу комментариев пользователя, новые первыми.

    Комментарий загружается вместе с постом-родителем (joinedload): шаблону
    профиля нужны заголовок и адрес поста, без eager-загрузки получается N+1.

    Args:
        user_id: Идентификатор автора.
        page: Номер страницы, начиная с 1.
        per_page: Размер страницы; по умолчанию POSTS_PER_PAGE.

    Returns:
        Объект Pagination: items — комментарии страницы, total, pages,
        has_prev/has_next.
    """
    stmt = (
        db.select(Comment)
        .options(joinedload(Comment.post))
        .filter_by(author_id=user_id)
        .order_by(Comment.created.desc(), Comment.id.desc())
    )
    return db.paginate(stmt, page=page, per_page=per_page, error_out=False)


def get_profile(username: str, tab: str = PROFILE_TAB_POSTS, page: int = 1) -> tuple[User, Pagination]:
    """Собирает профиль: пользователь плюс одна пагинированная лента — активная вкладка.

    Неактивные разделы не запрашиваются: одна лента на показ, а не две.

    Args:
        username: Логин пользователя профиля.
        tab: Активная вкладка (значение из PROFILE_TABS); по умолчанию посты.
        page: Страница активной ленты.

    Returns:
        Кортеж: пользователь, страница активной ленты.

    Raises:
        NotFoundError: Пользователь не существует.
    """
    user = get_user_by_username(username)
    return user, _FEEDS[tab](user.id, page=page)


_FEEDS: dict[str, Callable[..., Pagination]] = {
    PROFILE_TAB_POSTS: list_user_posts,
    PROFILE_TAB_COMMENTS: list_user_comments,
}
