"""Роуты API аутентификации: выдача JWT-токена и регистрация."""

from dataclasses import dataclass
from typing import Any

from flask import Blueprint, request
from flask_jwt_extended import create_access_token

from blog.api.errors import api_errors
from blog.services import auth_service

bp = Blueprint("api_auth", __name__)


@dataclass
class Endpoints:
    """Пути API-эндпоинтов аутентификации."""

    GET_TOKEN: str = "/api/token"
    REGISTER: str = "/api/register"


@bp.post(Endpoints.GET_TOKEN)
def token() -> tuple[dict[str, Any], int] | dict[str, str]:
    """Выдаёт JWT-токен в обмен на логин и пароль.

    Принимает JSON или обычную форму:
        {"username": "admin", "password": "123456"}

    Returns:
        (Токен доступа, 200) в виде {"access_token": "..."}.
        (Описание ошибки, 401), если учётные данные неверны.
    """
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    user = auth_service.authenticate(username, password)
    if user is None:
        return {"error": "Неверный логин или пароль."}, 401
    return {"access_token": create_access_token(identity=str(user.id))}


@bp.post(Endpoints.REGISTER)
@api_errors
def register() -> tuple[dict[str, Any], int]:
    """Регистрирует нового пользователя.

    Принимает JSON или обычную форму с полями username и password.
    Пароль хэшируется в auth_service.register_user.

    Returns:
        (Данные созданного пользователя, 201) в виде
        {"user": {"id": ..., "username": ...}}.
    """
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    user = auth_service.register_user(username, password)
    return {"user": {"id": user.id, "username": user.username}}, 201
