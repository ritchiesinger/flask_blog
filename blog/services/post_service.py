"""Бизнес-логика работы с постами."""

from flask_sqlalchemy.pagination import Pagination

from blog.constants import POSTS_PER_PAGE
from blog.extensions import db
from blog.models.post import Post

from .base_errors import ForbiddenError, NotFoundError


def list_posts(page: int = 1, per_page: int = POSTS_PER_PAGE) -> Pagination:
    """Возвращает страницу постов, новые первыми.

    Args:
        page: Номер страницы, начиная с 1; по умолчанию — первая.
        per_page: Размер страницы; по умолчанию POSTS_PER_PAGE.

    Returns:
        Объект Pagination: items — посты страницы, total, pages,
        has_prev/has_next.
    """
    stmt = db.select(Post).order_by(Post.created.desc(), Post.id.desc())
    return db.paginate(stmt, page=page, per_page=per_page, error_out=False)


def get_post(post_id: int, *, check_author: int | None = None) -> Post:
    """Возвращает пост по идентификатору.

    Args:
        post_id: Идентификатор поста.
        check_author: Идентификатор текущего пользователя; если задан
            и не совпадает с автором поста, бросает ForbiddenError.

    Returns:
        Модель поста.

    Raises:
        NotFoundError: Пост не существует.
        ForbiddenError: Пост принадлежит другому пользователю.
    """
    post = db.session.get(Post, post_id)
    if post is None:
        raise NotFoundError(f"Post id {post_id} doesn't exist.")
    if check_author is not None and post.author_id != check_author:
        raise ForbiddenError("Вы не являетесь автором этого поста!")
    return post


def create_post(title: str, body: str, author_id: int) -> Post:
    """Создаёт пост и сохраняет его в базу.

    Args:
        title: Заголовок поста.
        body: Тело поста.
        author_id: Идентификатор автора поста.

    Returns:
        Модель созданного поста.
    """
    post = Post(title=title, body=body, author_id=author_id)
    db.session.add(post)
    db.session.commit()
    return post


def update_post(post: Post, title: str, body: str) -> Post:
    """Обновляет заголовок и тело поста.

    Args:
        post: Модель поста.
        title: Новый заголовок.
        body: Новое тело.

    Returns:
        Обновлённая модель поста.
    """
    post.title = title
    post.body = body
    db.session.commit()
    return post


def delete_post(post: Post) -> None:
    """Удаляет пост.

    Args:
        post: Модель поста.
    """
    db.session.delete(post)
    db.session.commit()
