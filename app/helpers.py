"""Вспомогательные инструменты и константы."""

from base64 import b64encode
from dataclasses import dataclass
from typing import Dict, Tuple

from flask import g, jsonify, wrappers


class UserData:
    """Данные пользователя."""

    def __init__(
        self,
        user_id: int = None,
        login: str = None,
        password: str = None,
        email: str = None
    ):
        self.user_id = user_id
        self.login = login
        self.password = password
        self.email = email
        self.basic_auth_header = get_basic_auth_header(login, password)

    def set_user_id(self, user_id: int):
        """Определение идентификатора пользователя."""
        self.user_id = user_id

    def set_login(self, login: str):
        """Определение логина."""
        self.login = login

    def set_password(self, password: str):
        """Определение логина."""
        self.password = password

    def set_email(self, email: str):
        """Определение логина."""
        self.email = email

    def set_basic_auth_header(self):
        """Генерация заголовка с Basic Auth для HTTP-запросов."""
        self.basic_auth_header = get_basic_auth_header(self.login, self.password)


@dataclass
class HTTPCodes:
    """HTTP коды ответов сервера."""
    SUCCESS = 200
    BAD_REQUEST = 400
    NOT_FOUND = 404


@dataclass
class ErrorCodes:
    """Бизнес-коды ошибок."""
    SUCCESS = 0
    LOGIN_ALREADY_EXIST = 1
    EMAIL_ALREADY_EXIST = 2
    REQUIRED_ARGS_MISSING = 3
    REQUIRED_ARG_MISSING = 4
    USER_NOT_FOUND = 5
    ADMIN_SELF_DELETE_NOT_ALLOWED = 6
    ROLE_ALREADY_EXIST = 7
    ROLE_NOT_FOUND = 8
    ROLE_ALREADY_ASSIGN = 9
    ROLE_ASSINGMENT_NOT_FOUND = 10


@dataclass
class ErrorTexts:
    """Возможные тексты ошибок."""
    LOGIN_ALREADY_EXIST = "Пользователь с таким login уже зарегистрирован!"
    EMAIL_ALREADY_EXIST = "Пользователь с таким email уже зарегистрирован!"
    REQUIRED_ARGS_MISSING = "Отсутствуют обязательные аргументы!"
    REQUIRED_ARG_MISSING = "Отсутствуют аргументы (должен быть хотя бы один)!"
    USER_NOT_FOUND = "Пользователь с таким id не найден!"
    ADMIN_SELF_DELETE_NOT_ALLOWED = "Этой командой удалить самого себя нельзя!"
    ROLE_ALREADY_EXIST = "Роль с таким именем (name) уже существует!"
    ROLE_NOT_FOUND = "Роль с таким id не найдена!"
    ROLE_ALREADY_ASSIGN = "Эта роль уже назначена пользователю!"
    ROLE_ASSINGMENT_NOT_FOUND = "Роль не найдена у пользователя!"


class Response:  # pylint: disable=too-few-public-methods  # Здесь больше не нужно
    """Возвращаемый ответ."""

    def __init__(  # pylint: disable=too-many-arguments  # Нужно больше 5 аргументов
        self,
        status_code=HTTPCodes.SUCCESS,
        error_code=ErrorCodes.SUCCESS,
        error_text=None,
        data=None,
        token=None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.error_text = error_text
        self.data = data
        self.token = token

    def get(self) -> Tuple[wrappers.Response, int]:
        """Генерация ответа на основе данных сформированного объекта."""
        if g.get("user"):
            self.token = g.user.generate_token()
        response_body = {
            "error_code": self.error_code,
            "error_text": self.error_text,
            "data": self.data
        }
        if self.token:
            response_body["token"] = self.token
        return jsonify(response_body), self.status_code


@dataclass
class Errors:
    """Преднастроенные константы возможных ответов API сервиса."""

    EMPTY_SUCCESS = Response()
    LOGIN_ALREADY_EXIST = Response(
        status_code=HTTPCodes.BAD_REQUEST,
        error_code=ErrorCodes.LOGIN_ALREADY_EXIST,
        error_text=ErrorTexts.LOGIN_ALREADY_EXIST
    )
    EMAIL_ALREADY_EXIST = Response(
        status_code=HTTPCodes.BAD_REQUEST,
        error_code=ErrorCodes.EMAIL_ALREADY_EXIST,
        error_text=ErrorTexts.EMAIL_ALREADY_EXIST
    )
    REQUIRED_ARGS_MISSING = Response(
        status_code=HTTPCodes.BAD_REQUEST,
        error_code=ErrorCodes.REQUIRED_ARGS_MISSING,
        error_text=ErrorTexts.REQUIRED_ARGS_MISSING
    )
    REQUIRED_ARG_MISSING = Response(
        status_code=HTTPCodes.BAD_REQUEST,
        error_code=ErrorCodes.REQUIRED_ARG_MISSING,
        error_text=ErrorTexts.REQUIRED_ARG_MISSING
    )
    USER_NOT_FOUND = Response(
        status_code=HTTPCodes.NOT_FOUND,
        error_code=ErrorCodes.USER_NOT_FOUND,
        error_text=ErrorTexts.USER_NOT_FOUND
    )
    ADMIN_SELF_DELETE_NOT_ALLOWED = Response(
        status_code=HTTPCodes.BAD_REQUEST,
        error_code=ErrorCodes.ADMIN_SELF_DELETE_NOT_ALLOWED,
        error_text=ErrorTexts.ADMIN_SELF_DELETE_NOT_ALLOWED
    )
    ROLE_ALREADY_EXIST = Response(
        status_code=HTTPCodes.BAD_REQUEST,
        error_code=ErrorCodes.ROLE_ALREADY_EXIST,
        error_text=ErrorTexts.ROLE_ALREADY_EXIST
    )
    ROLE_NOT_FOUND = Response(
        status_code=HTTPCodes.NOT_FOUND,
        error_code=ErrorCodes.ROLE_NOT_FOUND,
        error_text=ErrorTexts.ROLE_NOT_FOUND
    )
    ROLE_ALREADY_ASSIGN = Response(
        status_code=HTTPCodes.BAD_REQUEST,
        error_code=ErrorCodes.ROLE_ALREADY_ASSIGN,
        error_text=ErrorTexts.ROLE_ALREADY_ASSIGN
    )
    ROLE_ASSINGMENT_NOT_FOUND = Response(
        status_code=HTTPCodes.NOT_FOUND,
        error_code=ErrorCodes.ROLE_ASSINGMENT_NOT_FOUND,
        error_text=ErrorTexts.ROLE_ASSINGMENT_NOT_FOUND
    )


def get_basic_auth_header(login: str, password: str) -> Dict[str, str]:
    """Получение заголовка авторизации Basic Auth."""
    basic_auth = b64encode(bytes(f"{login}:{password}", encoding="UTF-8")).decode("utf-8")
    return {"Authorization": f"Basic {basic_auth}"}
