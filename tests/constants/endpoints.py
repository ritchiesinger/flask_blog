"""Константы эндпоинтов API приложения."""

from dataclasses import dataclass


@dataclass
class Auth:
    """Эндпоинты аутентификации."""

    TOKEN: str = "/api/token"
    REGISTER: str = "/api/register"

@dataclass
class Posts:
    """Эндпоинты постов."""

    POSTS: str = "/api/posts"
    POST: str = "/api/posts/{}"
    POST_COMMENTS: str = "/api/posts/{post_id}/comments"
    COMMENT: str = "/api/comments/{comment_id}"

@dataclass
class Users:
    """Эндпоинты пользователей."""

    USERS: str = "/api/users"
    USER: str = "/api/users/{}"

@dataclass
class APIEndpoints:
    """Корневой реестр эндпоинтов API."""

    AUTH = Auth
    POSTS = Posts
    USERS = Users