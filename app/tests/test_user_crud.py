"""Тесты про пользовательские методы по работе с профилем."""

# pylint: disable=duplicate-code  # Да, тесты пишутся шаблонно

from allure import epic, feature, story, title

from app.helpers import HTTPCodes, ErrorTexts, ErrorCodes
from app.tests.steps import steps_users, steps_common
from app.tests.steps.steps_common import Check


@epic("API")
@feature("Профиль пользователя")
@story("Работа со своим профилем")
@title("Успешное получение данных о своём профиле (Basic Auth)")
def test_success_get_self_user_profile_via_basic_auth(client, precondition_test_user):
    """Успешное получение данных своего профиля (Basic Auth)."""
    response = steps_users.self_get_user_profile(
        http_client=client,
        basic_auth_header=precondition_test_user.basic_auth_header
    )
    steps_common.verifier(
        "Проверки данных из ответа",
        [
            Check("status_code", HTTPCodes.SUCCESS, response.status_code),
            Check("error_code", ErrorCodes.SUCCESS, response.json["error_code"]),
            Check("error_text", None, response.json["error_text"]),
            Check("login", precondition_test_user.login, response.json["data"]["login"]),
            Check("email", precondition_test_user.email, response.json["data"]["email"]),
            Check("id", precondition_test_user.user_id, response.json["data"]["id"])
        ]
    )


@epic("API")
@feature("Профиль пользователя")
@story("Работа со своим профилем")
@title("Нельзя отредактировать свой профиль без каких либо параметров для изменения (Basic Auth)")
def test_fail_edit_profile_no_args_via_basic_auth(client, precondition_test_user):
    """Ошибка редактирования профиля без каких либо параметров для изменения (Basic Auth)."""
    response = steps_users.self_edit_user_profile(
        http_client=client,
        basic_auth_header=precondition_test_user.basic_auth_header
    )
    steps_common.verifier(
        "Проверки данных из ответа",
        [
            Check("status_code", HTTPCodes.BAD_REQUEST, response.status_code),
            Check("error_code", ErrorCodes.REQUIRED_ARG_MISSING, response.json["error_code"]),
            Check("error_text", ErrorTexts.REQUIRED_ARG_MISSING, response.json["error_text"])
        ]
    )


@epic("API")
@feature("Профиль пользователя")
@story("Работа со своим профилем")
@title("Нельзя изменить login своего профиля на уже существующий в системе (Basic Auth)")
def test_fail_edit_profile_login_already_exist_via_basic_auth(client, precondition_test_user):
    """Нельзя изменить логин профиля на тот, который уже зарегистрирован в системе (Basic Auth)."""
    response = steps_users.self_edit_user_profile(
        http_client=client,
        body={"login": precondition_test_user.login},
        basic_auth_header=precondition_test_user.basic_auth_header
    )
    steps_common.verifier(
        "Проверки данных из ответа",
        [
            Check("status_code", HTTPCodes.BAD_REQUEST, response.status_code),
            Check("error_code", ErrorCodes.LOGIN_ALREADY_EXIST, response.json["error_code"]),
            Check("error_text", ErrorTexts.LOGIN_ALREADY_EXIST, response.json["error_text"])
        ]
    )


@epic("API")
@feature("Профиль пользователя")
@story("Работа со своим профилем")
@title("Нельзя изменить email своего профиля на уже существующий в системе (Basic Auth)")
def test_fail_edit_profile_email_already_exist_via_basic_auth(client, precondition_test_user):
    """Нельзя изменить email профиля на тот, который уже зарегистрирован в системе (Basic Auth)."""
    response = steps_users.self_edit_user_profile(
        http_client=client,
        body={"email": precondition_test_user.email},
        basic_auth_header=precondition_test_user.basic_auth_header
    )
    steps_common.verifier(
        "Проверки данных из ответа",
        [
            Check("status_code", HTTPCodes.BAD_REQUEST, response.status_code),
            Check("error_code", ErrorCodes.EMAIL_ALREADY_EXIST, response.json["error_code"]),
            Check("error_text", ErrorTexts.EMAIL_ALREADY_EXIST, response.json["error_text"])
        ]
    )
