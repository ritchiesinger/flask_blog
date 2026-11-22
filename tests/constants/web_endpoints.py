"""Константы эндпоинтов web-интерфейса."""

from dataclasses import dataclass


@dataclass
class Auth:
    """WEB-эндпоинты аутентификации."""

    LOGIN: str = "/login"
    LOGOUT: str = "/logout"
    REGISTER: str = "/register"


@dataclass
class User:
    """WEB-эндпоинты профиля пользователя (аватар и имя — → ARC-0051)."""

    PROFILE: str = "/user/{username}"
    CHANGE_ROLE: str = "/user/{username}/role"
    DISPLAY_NAME: str = "/user/{username}/display_name"
    AVATAR: str = "/user/{username}/avatar"
    AVATAR_RESET: str = "/user/{username}/avatar/reset"


@dataclass
class Posts:
    """WEB-эндпоинты постов."""

    INDEX: str = "/"
    CREATE: str = "/create"
    VIEW: str = "/{post_id}"
    UPDATE: str = "/{post_id}/update"
    DELETE: str = "/{post_id}/delete"


@dataclass
class Comments:
    """WEB-эндпоинты комментариев."""

    CREATE: str = "/{post_id}/comments"
    UPDATE: str = "/comments/{comment_id}/update"
    DELETE: str = "/comments/{comment_id}/delete"


@dataclass
class Admin:
    """WEB-эндпоинты административной панели."""

    USERS: str = "/admin/users"
    DELETE_USER: str = "/admin/users/{user_id}/delete"


@dataclass
class Uploads:
    """WEB-эндпоинты загрузок."""
    UPLOAD = "/uploads"


@dataclass
class WebEndpoints:
    """Корневой реестр WEB-эндпоинтов."""

    AUTH = Auth
    POSTS = Posts
    COMMENTS = Comments
    ADMIN = Admin
    UPLOADS = Uploads
    USER = User
