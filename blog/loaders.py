"""Колбэки загрузки пользователя: для Flask-Login и flask-jwt-extended.

Функции вызываются фреймворками автоматически — импортировать модуль нужно, чтобы колбэки были зарегистрированы.
"""

from blog.extensions import db, jwt, login_manager
from blog.models.user import User


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """Загружает пользователя по идентификатору из сессии (Flask-Login).

    Args:
        user_id: Идентификатор пользователя из сессии.

    Returns:
        Пользователь или None, если не найден или id некорректен.
    """
    return db.session.get(User, int(user_id))


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_payload) -> User | None:
    """Загружает пользователя по данным JWT-токена (flask-jwt-extended).

    Args:
        _jwt_header: Заголовок токена (не используется).
        jwt_payload: Полезная нагрузка токена; id пользователя в ключе "sub".

    Returns:
        Пользователь или None, если не найден или id некорректен.
    """
    return db.session.get(User, int(jwt_payload["sub"]))
