"""Роуты API по работе с постами."""

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from blog.constants import POSTS_PER_PAGE
from blog.pagination import page_from_args, per_page_from_args
from blog.services import post_service
from blog.services.base_errors import BadRequestError

from .errors import api_errors

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.get("/posts")
def list_posts() -> dict:
    """Возвращает страницу постов в конверте с пагинацией.

    Query-параметры: page (по умолчанию 1), per_page (по умолчанию
    POSTS_PER_PAGE, срезается до MAX_PER_PAGE).

    Returns:
        Конверт: posts — представления постов страницы, page, pages,
        total, per_page.
    """
    pagination = post_service.list_posts(page=page_from_args(), per_page=per_page_from_args(POSTS_PER_PAGE))
    return {
        "posts": [post.to_dict() for post in pagination.items],
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
        "per_page": pagination.per_page,
    }


@bp.post("/posts")
@api_errors
@jwt_required()
def create_post() -> tuple[dict, int]:
    """Создаёт пост от имени текущего пользователя.

    Требует JWT-токен. Тело поста может быть пустым, заголовок — нет.

    Returns:
        (Представление созданного поста, 201).
    """
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()

    if not title:
        raise BadRequestError("Title is required.")

    post = post_service.create_post(
        title,
        body,
        author_id=int(get_jwt_identity()),  # вместо current_user.id
    )
    return post.to_dict(), 201


@bp.patch("/posts/<int:post_id>")
@api_errors
@jwt_required()
def update_post(post_id: int) -> dict:
    """Обновляет пост с указанным идентификатором.

    Требует JWT-токен; редактировать может только автор поста.
    Несуществующий пост даёт 404, чужой — 403 (через api_errors).

    Args:
        post_id: Идентификатор поста.

    Returns:
        Обновлённое представление поста.
    """
    data = request.get_json(silent=True) or {}
    post = post_service.get_post(post_id, check_author=int(get_jwt_identity()))
    post = post_service.update_post(
        post,
        data.get("title", post.title),
        data.get("body", post.body),
    )
    return post.to_dict()


@bp.delete("/posts/<int:post_id>")
@api_errors
@jwt_required()
def delete_post(post_id: int) -> tuple[str, int]:
    """Удаляет пост с указанным идентификатором.

    Требует JWT-токен; удалять может только автор поста.

    Args:
        post_id: Идентификатор поста.

    Returns:
        Пустое тело со статусом 204.
    """
    post = post_service.get_post(post_id, check_author=int(get_jwt_identity()))
    post_service.delete_post(post)
    return "", 204
