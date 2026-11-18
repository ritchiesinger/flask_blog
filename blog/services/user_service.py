"""Бизнес-логика профиля пользователя."""

from flask_sqlalchemy.pagination import Pagination
from sqlalchemy.orm import joinedload

from blog.constants import POSTS_PER_PAGE
from blog.extensions import db
from blog.models.comment import Comment
from blog.models.post import Post
from blog.models.user import User

from .base_errors import NotFoundError


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


def get_profile(
    username: str, page: int = 1, comment_page: int = 1, per_page: int = POSTS_PER_PAGE
) -> tuple[User, Pagination, Pagination]:
    """Собирает профиль: пользователь плюс две пагинированные ленты.

    Ленты независимы: посты листаются параметром page, комментарии —
    comment_page. Санитизация параметров — на WEB-слое через pagination.py.

    Args:
        username: Логин пользователя профиля.
        page: Страница ленты постов.
        comment_page: Страница ленты комментариев.
        per_page: Размер страницы обеих лент; по умолчанию POSTS_PER_PAGE.

    Returns:
        Кортеж: пользователь, страница его постов, страница его комментариев.

    Raises:
        NotFoundError: Пользователь не существует.
    """
    user = get_user_by_username(username)
    posts = list_user_posts(user.id, page=page, per_page=per_page)
    comments = list_user_comments(user.id, page=comment_page, per_page=per_page)
    return user, posts, comments
