"""Административные операции над пользователями."""

from flask_sqlalchemy.pagination import Pagination

from blog.constants import USERS_PER_PAGE
from blog.extensions import db
from blog.models import User
from blog.services.base_errors import ForbiddenError, NotFoundError


def list_users(page: int = 1, per_page: int = USERS_PER_PAGE) -> Pagination:
    """Возвращает страницу пользователей по возрастанию id.

    Args:
        page: Номер страницы, начиная с 1; по умолчанию — первая.
        per_page: Размер страницы; по умолчанию USERS_PER_PAGE.

    Returns:
        Объект Pagination: items — пользователи страницы, total, pages,
        has_prev/has_next.
    """
    stmt = db.select(User).order_by(User.id)
    return db.paginate(stmt, page=page, per_page=per_page, error_out=False)


def delete_user(user_id: int, actor: User) -> None:
    """Удаляет пользователя по идентификатору.

    Args:
        user_id: Идентификатор удаляемого пользователя.
        actor: Пользователь, выполняющий операцию; должен быть
            администратором.

    Raises:
        NotFoundError: Пользователь не найден.
        ForbiddenError: Актор не администратор или пытается
            удалить самого себя.
    """
    if not actor.is_admin:
        raise ForbiddenError("Требуются права администратора.")

    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError("Пользователь не найден.")
    if user.id == actor.id:
        raise ForbiddenError("Нельзя удалить самого себя.")

    db.session.delete(user)
    db.session.commit()
