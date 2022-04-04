"""Шаги про работу с пользователями."""

from json import dumps
from typing import Dict, Optional

from allure import attach, attachment_type, step
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from app.helpers import generate_url_params_from_dict


def user_registration(
    http_client: FlaskClient,
    login: Optional[str] = None,
    password: Optional[str] = None,
    email: Optional[str] = None,
    step_name: str = "Регистрация нового пользователя"
) -> TestResponse:
    """Регистрация нового пользователя.

    :param http_client: http клиент для запросов;
    :param login: логин пользователя;
    :param password: пароль пользователя;
    :param email: адрес электронной почты пользователя;
    :param step_name: возможность указать произвольное имя шага для отчёта.
    :return: ответ сервиса.
    """
    with step(step_name):
        body = {"login": login, "password": password, "email": email}
        request_url = "/api/registration"
        attach_req_str = (
            f"POST {request_url}\n\n"
            f"Body:\n{dumps(body, ensure_ascii=False, indent=2)}"
        )
        attach(attach_req_str, "HTTP запрос")
        response = http_client.post("/api/registration", json=body)
        attach(
            dumps(response.json, ensure_ascii=False, indent=2),
            f"HTTP ответ {response.status_code}",
            attachment_type=attachment_type.JSON
        )
        return response


def admin_get_user_data(
    http_client: FlaskClient,
    user_id: Optional[int] = None,
    basic_auth_header: Optional[Dict[str, str]] = None,
    bearer_token_header: Optional[Dict[str, str]] = None,
    step_name: str = "Получение данных пользователя администратором (api/admin/users/)"
) -> TestResponse:
    """Получение данных пользователя администратором (api/admin/users/).

    :param http_client: http клиент для запросов;
    :param user_id: идентификатор пользователя;
    :param basic_auth_header: заголовок Authorization с basic auth;
    :param bearer_token_header: заголовок Authorization с bearer token;
    :param step_name: возможность указать произвольное имя шага для отчёта.
    :return: ответ сервиса.
    """
    with step(step_name):
        headers = {}
        basic_auth_header = basic_auth_header or {}
        bearer_token_header = bearer_token_header or {}
        user_id = user_id if user_id is not None else ""
        if basic_auth_header:
            headers.update(basic_auth_header)
        elif bearer_token_header:
            headers.update(bearer_token_header)
        request_url = "/api/admin/users/" + str(user_id)
        attach_req_str = (
            f"GET {request_url}\n\n"
            f"Headers:\n{dumps(headers, ensure_ascii=False, indent=2)}\n\n"
        )
        attach(attach_req_str, "HTTP запрос")
        response = http_client.get("/api/admin/users/" + str(user_id), headers=headers)
        attach(
            dumps(response.json, ensure_ascii=False, indent=2),
            f"HTTP ответ {response.status_code}",
            attachment_type=attachment_type.JSON
        )
        return response


def admin_search_users(
    http_client: FlaskClient,
    search_filter: Dict[str, str] = None,
    basic_auth_header: Optional[Dict[str, str]] = None,
    bearer_token_header: Optional[Dict[str, str]] = None,
    step_name: str = "Поиск пользователей администратором (api/admin/users/search)"
) -> TestResponse:
    """Поиск пользователей администратором (api/admin/users/search).

    :param http_client: http клиент для запросов;
    :param search_filter: параметры фильтра для поискового запроса;
    :param basic_auth_header: заголовок Authorization с basic auth;
    :param bearer_token_header: заголовок Authorization с bearer token;
    :param step_name: возможность указать произвольное имя шага для отчёта.
    :return: ответ сервиса.
    """
    with step(step_name):
        headers = {}
        basic_auth_header = basic_auth_header or {}
        bearer_token_header = bearer_token_header or {}
        if basic_auth_header:
            headers.update(basic_auth_header)
        elif bearer_token_header:
            headers.update(bearer_token_header)
        request_url = "/api/admin/users/search" + generate_url_params_from_dict(search_filter)
        attach_req_str = (
            f"GET {request_url}\n\n"
            f"Headers:\n{dumps(headers, ensure_ascii=False, indent=2)}\n\n"
        )
        attach(attach_req_str, "HTTP запрос")
        response = http_client.get(request_url, headers=headers)
        attach(
            dumps(response.json, ensure_ascii=False, indent=2),
            f"HTTP ответ {response.status_code}",
            attachment_type=attachment_type.JSON
        )
        return response


def admin_edit_user(  # pylint: disable=too-many-arguments  #  Здесь столько надо
    http_client: FlaskClient,
    user_id: Optional[int] = None,
    body: Dict[str, str] = None,
    basic_auth_header: Optional[Dict[str, str]] = None,
    bearer_token_header: Optional[Dict[str, str]] = None,
    step_name: str = "Изменение данных пользователя администратором (api/admin/users/)"
) -> TestResponse:
    """Изменение данных пользователя администратором (api/admin/users/).

    :param http_client: http клиент для запросов;
    :param user_id: идентификатор пользователя;
    :param body: параметры пользовательского профиля к изменению;
    :param basic_auth_header: заголовок Authorization с basic auth;
    :param bearer_token_header: заголовок Authorization с bearer token;
    :param step_name: возможность указать произвольное имя шага для отчёта.
    :return: ответ сервиса.
    """
    with step(step_name):
        headers = {}
        basic_auth_header = basic_auth_header or {}
        bearer_token_header = bearer_token_header or {}
        body = body if body is not None else {}
        user_id = user_id if user_id is not None else ""
        if basic_auth_header:
            headers.update(basic_auth_header)
        elif bearer_token_header:
            headers.update(bearer_token_header)
        request_url = "/api/admin/users/" + str(user_id)
        attach_req_str = (
            f"PATCH {request_url}\n\n"
            f"Headers:\n{dumps(headers, ensure_ascii=False, indent=2)}\n\n"
            f"Body:\n{body}"
        )
        attach(attach_req_str, "HTTP запрос")
        response = http_client.patch("/api/admin/users/" + str(user_id), headers=headers, json=body)
        attach(
            dumps(response.json, ensure_ascii=False, indent=2),
            f"HTTP ответ {response.status_code}",
            attachment_type=attachment_type.JSON
        )
        return response


def admin_delete_user(
    http_client: FlaskClient,
    user_id: Optional[int] = None,
    basic_auth_header: Optional[Dict[str, str]] = None,
    bearer_token_header: Optional[Dict[str, str]] = None,
    step_name: str = "Удаление пользователя администратором (api/admin/users/)"
) -> TestResponse:
    """Удаление пользователя администратором (api/admin/users/).

    :param http_client: http клиент для запросов;
    :param user_id: идентификатор пользователя;
    :param basic_auth_header: заголовок Authorization с basic auth;
    :param bearer_token_header: заголовок Authorization с bearer token;
    :param step_name: возможность указать произвольное имя шага для отчёта.
    :return: ответ сервиса.
    """
    with step(step_name):
        headers = {}
        basic_auth_header = basic_auth_header or {}
        bearer_token_header = bearer_token_header or {}
        user_id = user_id if user_id is not None else ""
        if basic_auth_header:
            headers.update(basic_auth_header)
        elif bearer_token_header:
            headers.update(bearer_token_header)
        request_url = "/api/admin/users/" + str(user_id)
        attach_req_str = (
            f"DELETE {request_url}\n\n"
            f"Headers:\n{dumps(headers, ensure_ascii=False, indent=2)}\n\n"
        )
        attach(attach_req_str, "HTTP запрос")
        response = http_client.delete("/api/admin/users/" + str(user_id), headers=headers)
        attach(
            dumps(response.json, ensure_ascii=False, indent=2),
            f"HTTP ответ {response.status_code}",
            attachment_type=attachment_type.JSON
        )
        return response


def self_get_user_profile(
    http_client: FlaskClient,
    basic_auth_header: Optional[Dict[str, str]] = None,
    bearer_token_header: Optional[Dict[str, str]] = None,
    step_name: str = "Получение данных своего профиля (api/user)"
) -> TestResponse:
    """Получение данных своего профиля (api/user).

    :param http_client: http клиент для запросов;
    :param basic_auth_header: заголовок Authorization с basic auth;
    :param bearer_token_header: заголовок Authorization с bearer token;
    :param step_name: возможность указать произвольное имя шага для отчёта.
    :return: ответ сервиса.
    """
    with step(step_name):
        headers = {}
        basic_auth_header = basic_auth_header or {}
        bearer_token_header = bearer_token_header or {}
        if basic_auth_header:
            headers.update(basic_auth_header)
        elif bearer_token_header:
            headers.update(bearer_token_header)
        request_url = "/api/user"
        attach_req_str = (
            f"GET {request_url}\n\n"
            f"Headers:\n{dumps(headers, ensure_ascii=False, indent=2)}\n\n"
        )
        attach(attach_req_str, "HTTP запрос")
        response = http_client.get(request_url, headers=headers)
        attach(
            dumps(response.json, ensure_ascii=False, indent=2),
            f"HTTP ответ {response.status_code}",
            attachment_type=attachment_type.JSON
        )
        return response


def self_edit_user_profile(
    http_client: FlaskClient,
    body: Dict[str, str] = None,
    basic_auth_header: Optional[Dict[str, str]] = None,
    bearer_token_header: Optional[Dict[str, str]] = None,
    step_name: str = "Изменение данных своего профиля (api/user)"
) -> TestResponse:
    """Изменение данных своего профиля (api/user).

    :param http_client: http клиент для запросов;
    :param body: параметры пользовательского профиля к изменению;
    :param basic_auth_header: заголовок Authorization с basic auth;
    :param bearer_token_header: заголовок Authorization с bearer token;
    :param step_name: возможность указать произвольное имя шага для отчёта.
    :return: ответ сервиса.
    """
    with step(step_name):
        headers = {}
        basic_auth_header = basic_auth_header or {}
        bearer_token_header = bearer_token_header or {}
        body = body if body is not None else {}
        if basic_auth_header:
            headers.update(basic_auth_header)
        elif bearer_token_header:
            headers.update(bearer_token_header)
        attach_req_str = (
            "PATCH /api/user\n\n"
            f"Headers:\n{dumps(headers, ensure_ascii=False, indent=2)}\n\n"
            f"Body:\n{body}"
        )
        attach(attach_req_str, "HTTP запрос")
        response = http_client.patch("/api/user", headers=headers, json=body)
        attach(
            dumps(response.json, ensure_ascii=False, indent=2),
            f"HTTP ответ {response.status_code}",
            attachment_type=attachment_type.JSON
        )
        return response
