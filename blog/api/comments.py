"""Роуты API по работе с комментариями."""

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from blog.services import comment_service

from .errors import api_errors

bp = Blueprint("api_comments", __name__, url_prefix="/api")


@bp.get("/posts/<int:post_id>/comments")
@api_errors
def list_comments(post_id: int) -> list[dict]:
    """Возвращает комментарии поста (публичный эндпоинт).

    Несуществующий пост даёт 404 (через api_errors).

    Args:
        post_id: Идентификатор поста.

    Returns:
        JSON-массив представлений комментариев.
    """
    comments = comment_service.list_for_post(post_id)
    return [comment.to_dict() for comment in comments]


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
    comment = comment_service.get_comment(comment_id, check_author=int(get_jwt_identity()))
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
    comment = comment_service.get_comment(comment_id, check_author=int(get_jwt_identity()))
    comment_service.delete_comment(comment)
    return "", 204
