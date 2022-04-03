"""Тесты про регистрацию нового пользователя."""

from allure import epic, feature, story, title

from app.helpers import HTTPCodes, ErrorTexts, ErrorCodes
from app.tests.steps import steps_users, steps_common
from app.tests.steps.steps_common import Check


@epic("API")
@feature("Профиль пользователя")
@story("Регистрация нового пользователя")
@title("Успешная регистрация нового пользователя")
def test_success_user_registration(client, faker):
    """Успешная регистрация нового пользователя."""
    faker.random.seed()
    login = faker.user_name()
    email = faker.email()
    response = steps_users.user_registration(
        http_client=client,
        login=login,
        password="qwerty",
        email=email
    )
    steps_common.verifier(
        "Проверки данных из ответа",
        [
            Check("status_code", HTTPCodes.SUCCESS, response.status_code),
            Check("error_code", ErrorCodes.SUCCESS, response.json["error_code"]),
            Check("error_text", None, response.json["error_text"])
        ]
    )


@epic("API")
@feature("Профиль пользователя")
@story("Регистрация нового пользователя")
@title("Нельзя зарегистрировать нового пользователя без указания login")
def test_failed_user_registration_without_login(client, faker):
    """Нельзя зарегистрировать пользователя без логина."""
    faker.random.seed()
    email = faker.email()
    response = steps_users.user_registration(
        http_client=client,
        login=None,
        password="qwerty",
        email=email
    )
    steps_common.verifier(
        "Проверки данных из ответа",
        [
            Check("status_code", HTTPCodes.BAD_REQUEST, response.status_code),
            Check("error_code", ErrorCodes.REQUIRED_ARGS_MISSING, response.json["error_code"]),
            Check("error_text", ErrorTexts.REQUIRED_ARGS_MISSING, response.json["error_text"])
        ]
    )


@epic("API")
@feature("Профиль пользователя")
@story("Регистрация нового пользователя")
@title("Нельзя зарегистрировать нового пользователя без указания email")
def test_failed_user_registration_without_email(client, faker):
    """Нельзя зарегистрировать пользователя без email."""
    faker.random.seed()
    login = faker.user_name()
    response = steps_users.user_registration(
        http_client=client,
        login=login,
        password="qwerty",
        email=None
    )
    steps_common.verifier(
        "Проверки данных из ответа",
        [
            Check("status_code", HTTPCodes.BAD_REQUEST, response.status_code),
            Check("error_code", ErrorCodes.REQUIRED_ARGS_MISSING, response.json["error_code"]),
            Check("error_text", ErrorTexts.REQUIRED_ARGS_MISSING, response.json["error_text"])
        ]
    )


@epic("API")
@feature("Профиль пользователя")
@story("Регистрация нового пользователя")
@title("Нельзя зарегистрировать нового пользователя без указания password")
def test_failed_user_registration_without_password(client, faker):
    """Нельзя зарегистрировать пользователя без пароля."""
    faker.random.seed()
    login = faker.user_name()
    email = faker.email()
    response = steps_users.user_registration(
        http_client=client,
        login=login,
        password=None,
        email=email
    )
    steps_common.verifier(
        "Проверки данных из ответа",
        [
            Check("status_code", HTTPCodes.BAD_REQUEST, response.status_code),
            Check("error_code", ErrorCodes.REQUIRED_ARGS_MISSING, response.json["error_code"]),
            Check("error_text", ErrorTexts.REQUIRED_ARGS_MISSING, response.json["error_text"])
        ]
    )


@epic("API")
@feature("Профиль пользователя")
@story("Регистрация нового пользователя")
@title("Нельзя зарегистрировать пользователя с login который уже существует в системе")
def test_failed_user_registration_login_already_exist(client, faker, precondition_test_user):
    """Нельзя зарегистрировать пользователя с логином который уже существует в системе."""
    faker.random.seed()
    email = faker.email()
    response = steps_users.user_registration(
        http_client=client,
        login=precondition_test_user.login,
        password="qwerty",
        email=email
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
@story("Регистрация нового пользователя")
@title("Нельзя зарегистрировать пользователя с email который уже существует в системе")
def test_failed_user_registration_email_already_exist(client, faker, precondition_test_user):
    """Нельзя зарегистрировать пользователя с email который уже существует в системе."""
    faker.random.seed()
    response = steps_users.user_registration(
        http_client=client,
        login=faker.user_name(),
        password="qwerty",
        email=precondition_test_user.email
    )
    steps_common.verifier(
        "Проверки данных из ответа",
        [
            Check("status_code", HTTPCodes.BAD_REQUEST, response.status_code),
            Check("error_code", ErrorCodes.EMAIL_ALREADY_EXIST, response.json["error_code"]),
            Check("error_text", ErrorTexts.EMAIL_ALREADY_EXIST, response.json["error_text"])
        ]
    )
