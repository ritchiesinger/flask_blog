"""Роуты API по работе с комментариями."""

from flask import Blueprint, request
from flask_jwt_extended import current_user, get_jwt_identity, jwt_required

from blog.constants import COMMENTS_PER_PAGE
from blog.pagination import page_from_args, per_page_from_args
from blog.services import comment_service
from blog.services.permissions import Action, ensure_allowed

from .errors import api_errors

bp = Blueprint("api_comments", __name__, url_prefix="/api")


@bp.get("/posts/<int:post_id>/comments")
@api_errors
def list_comments(post_id: int) -> dict:
    """Возвращает комментарии поста в конверте (публичный эндпоинт).

    Конверт как у /api/posts: comments, page, pages, total, per_page.
    Санитизация page/per_page — через pagination.py. Несуществующий пост — 404.

    Args:
        post_id: Идентификатор поста.

    Returns:
        Конверт с представлениями комментариев и метаданными пагинации.
    """
    pagination = comment_service.list_for_post(
        post_id=post_id,
        page=page_from_args(),
        per_page=per_page_from_args(COMMENTS_PER_PAGE),
    )
    return {
        "comments": [comment.to_dict() for comment in pagination.items],
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
        "per_page": pagination.per_page,
    }


@bp.post("/posts/<int:post_id>/comments")
@api_errors
@jwt_required()
def create_comment(post_id: int) -> tuple[dict, int]:
    """Создаёт комментарий к посту от имени текущего пользователя.

    Требует JWT-токен. Пустое (или из одних пробелов) тело даёт 400 —
    валидация в сервисе.

    Args:
        post_id: Идентификатор поста.

    Returns:
        (Представление созданного комментария, 201).
    """
    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    comment = comment_service.create_comment(
        post_id=post_id,
        author_id=int(get_jwt_identity()),
        body=body,
    )
    return comment.to_dict(), 201


@bp.patch("/comments/<int:comment_id>")
@api_errors
@jwt_required()
def update_comment(comment_id: int) -> dict:
    """Обновляет комментарий с указанным идентификатором.

    Требует JWT-токен; редактировать может только автор комментария.
    Несуществующий комментарий даёт 404, чужой — 403 (через api_errors).

    Args:
        comment_id: Идентификатор комментария.

    Returns:
        Обновлённое представление комментария.
    """
    data = request.get_json(silent=True) or {}
    comment = comment_service.get_comment(comment_id)
    ensure_allowed(comment.author_id, actor=current_user, action=Action.UPDATE, subject="комментария")
    comment = comment_service.update_comment(comment, data.get("body", comment.body))
    return comment.to_dict()


@bp.delete("/comments/<int:comment_id>")
@api_errors
@jwt_required()
def delete_comment(comment_id: int) -> tuple[str, int]:
    """Удаляет комментарий с указанным идентификатором.

    Требует JWT-токен; удалять может только автор комментария.

    Args:
        comment_id: Идентификатор комментария.

    Returns:
        Пустое тело со статусом 204.
    """
    comment = comment_service.get_comment(comment_id)
    ensure_allowed(comment.author_id, actor=current_user, action=Action.DELETE, subject="комментария")
    comment_service.delete_comment(comment)
    return "", 204
