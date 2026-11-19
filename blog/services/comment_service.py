"""Бизнес-логика работы с комментариями."""

from flask_sqlalchemy.pagination import Pagination

from blog.constants import COMMENTS_PER_PAGE
from blog.extensions import db
from blog.models.comment import Comment
from blog.models.post import Post

from .base_errors import BadRequestError, NotFoundError


def list_for_post(post_id: int, page: int = 1, per_page: int = COMMENTS_PER_PAGE) -> Pagination:
    """Возвращает пагинированные комментарии поста, новые первыми.

    Args:
        post_id: Идентификатор поста.
        page: Номер страницы; за пределами total — пустая страница (error_out=False).
        per_page: Размер страницы.

    Returns:
        Страница комментариев.

    Raises:
        NotFoundError: Пост не существует.
    """
    if db.session.get(Post, post_id) is None:
        raise NotFoundError(f"Post id {post_id} doesn't exist.")
    stmt = (
        db.select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created.desc(), Comment.id.desc())
    )
    return db.paginate(stmt, page=page, per_page=per_page, error_out=False)


def get_comment(comment_id: int) -> Comment:
    """Возвращает комментарий по идентификатору.

    Args:
        comment_id: Идентификатор комментария.

    Returns:
        Модель комментария.

    Raises:
        NotFoundError: Комментарий не существует.
    """
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        raise NotFoundError(f"Comment id {comment_id} doesn't exist.")
    return comment


def create_comment(post_id: int, author_id: int, body: str) -> Comment:
    """Создаёт комментарий и сохраняет его в базу.

    Args:
        post_id: Идентификатор поста.
        author_id: Идентификатор автора комментария.
        body: Текст комментария.

    Returns:
        Модель созданного комментария.

    Raises:
        NotFoundError: Пост не существует.
        BadRequestError: Текст комментария пуст.
    """
    if db.session.get(Post, post_id) is None:
        raise NotFoundError(f"Post id {post_id} doesn't exist.")
    if not body.strip():
        raise BadRequestError("Текст комментария не может быть пустым!")
    comment = Comment(body=body.strip(), post_id=post_id, author_id=author_id)
    db.session.add(comment)
    db.session.commit()
    return comment


def update_comment(comment: Comment, body: str) -> Comment:
    """Обновляет текст комментария.

    Args:
        comment: Модель комментария.
        body: Новый текст.

    Returns:
        Обновлённая модель комментария.

    Raises:
        BadRequestError: Текст комментария пуст.
    """
    if not body.strip():
        raise BadRequestError("Текст комментария не может быть пустым!")
    comment.body = body.strip()
    db.session.commit()
    return comment


def delete_comment(comment: Comment) -> None:
    """Удаляет комментарий.

    Args:
        comment: Модель комментария.
    """
    db.session.delete(comment)
    db.session.commit()
