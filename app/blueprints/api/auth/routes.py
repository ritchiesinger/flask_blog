"""Маршруты и функции связанные с аутентификацией в API."""

from typing import Tuple, Union

from flask import g, session

from app.helpers import Response
from app.models import User
from . import bp as auth_bp, basic_auth, token_auth


@auth_bp.route('/token')
@basic_auth.login_required
def get_auth_token() -> Tuple[Response, int]:
    """Получение bearer токена."""
    return Response(data={"user_roles": g.user.to_dict()["roles"]}).get()


@basic_auth.verify_password
def verify_password(login: str, password: str) -> Union[User, bool]:
    """Проверка пароля.

    :param login: логин;
    :param password: пароль.
    :return: модель текущего пользователя или False.
    """
    user = User.query.filter_by(login=login).first()
    if not user or not user.verify_password(password):
        return False
    session["user_roles"] = user.to_dict()["roles"]
    g.user = user
    return user


@token_auth.verify_token
def verify_token(token: str) -> Union[User, bool]:
    """Проверка токена.

    :param token: токен.
    :return: модель текущего пользователя или False.
    """
    user = User.verify_token(token)
    if not user:
        return False
    session["user_roles"] = user.to_dict()["roles"]
    g.user = user
    return user


@basic_auth.get_user_roles
def get_user_roles(_):
    """Получение ролей пользователя для разграничения доступа в рамках ролевой модели."""
    return g.user.to_dict()["roles"]
