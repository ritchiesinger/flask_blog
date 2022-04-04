"""Тесты про административные методы по работе с пользователями."""

from allure import feature, story, title, link, epic

from app.helpers import HTTPCodes, ErrorTexts, ErrorCodes
from app.tests.steps import steps_common, steps_users
from app.tests.steps.steps_common import Check

# pylint: disable=duplicate-code  # Да, тесты пишутся шаблонно

DOC_LINK = "https://github.com/ritchiesinger/flask_blog/wiki/Методы-администратора"


@epic("API")
@feature("Административные методы по работе с пользователями")
@story("Получение данных пользователей (Basic Auth)")
@link(DOC_LINK, name="Административные методы по работе с пользователями")
@title("Успешное получение данных пользователя администратором")
def test_success_admin_get_user_profile_via_basic_auth(
    client,
    precondition_test_admin,
    precondition_test_user
):
    """Успешное получение данных пользователя администратором."""
    response = steps_users.admin_get_user_data(
        http_client=client,
        user_id=precondition_test_user.user_id,
        basic_auth_header=precondition_test_admin.basic_auth_header,
        step_name=f"Получение данных пользователя {precondition_test_user.login}"
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
@feature("Административные методы по работе с пользователями")
@story("Поиск пользователей (Basic Auth)")
@link(DOC_LINK, name="Административные методы по работе с пользователями")
@title("Успешный поиск пользователей без параметров")
def test_success_admin_search_users_via_basic_auth_no_params(client, precondition_test_admin):
    """Успешный поиск пользователей без параметров."""
    response = steps_users.admin_search_users(
        http_client=client,
        basic_auth_header=precondition_test_admin.basic_auth_header
    )
    steps_common.verifier(
        "Проверки данных из ответа",
        [
            Check("status_code", HTTPCodes.SUCCESS, response.status_code),
            Check("error_code", ErrorCodes.SUCCESS, response.json["error_code"]),
            Check("error_text", None, response.json["error_text"]),
            Check("Номер возвращаемой страницы", 1, response.json["data"]["page"]),
            Check("Элементов на страницу (настройка)", 10, response.json["data"]["per_page"]),
            Check("Найден хотя бы один пользователь", True, len(response.json["data"]["users"]) > 0)
        ]
    )


@epic("API")
@feature("Административные методы по работе с пользователями")
@story("Получение данных пользователей (Basic Auth)")
@link(DOC_LINK, name="Административные методы по работе с пользователями")
@title("Нельзя получить данные пользователя без указания ID")
def test_fail_admin_get_user_profile_via_basic_auth_no_id(client, precondition_test_admin):
    """Нельзя получить информацию о пользователе не передав идентификатор."""
    response = steps_users.admin_get_user_data(
        http_client=client,
        user_id=None,
        basic_auth_header=precondition_test_admin.basic_auth_header
    )
    steps_common.verifier(
        "Проверки кодов ответа и сообщения",
        [
            Check("status_code", HTTPCodes.BAD_REQUEST, response.status_code),
            Check("error_code", ErrorCodes.REQUIRED_ARGS_MISSING, response.json["error_code"]),
            Check("error_text", ErrorTexts.REQUIRED_ARGS_MISSING, response.json["error_text"])
        ]
    )


@epic("API")
@feature("Административные методы по работе с пользователями")
@story("Получение данных пользователей (Basic Auth)")
@link(DOC_LINK, name="Административные методы по работе с пользователями")
@title("Нельзя получить данные несуществующего пользователя")
def test_fail_admin_get_user_profile_via_basic_auth_not_found(client, precondition_test_admin):
    """Нельзя получить данные несуществующего пользователя."""
    response = steps_users.admin_get_user_data(
        http_client=client,
        user_id=0,
        basic_auth_header=precondition_test_admin.basic_auth_header
    )
    steps_common.verifier(
        "Проверки кодов ответа и сообщения",
        [
            Check("status_code", HTTPCodes.NOT_FOUND, response.status_code),
            Check("error_code", ErrorCodes.USER_NOT_FOUND, response.json["error_code"]),
            Check("error_text", ErrorTexts.USER_NOT_FOUND, response.json["error_text"])
        ]
    )


@epic("API")
@feature("Административные методы по работе с пользователями")
@story("Изменение данных пользователей (Basic Auth)")
@link(DOC_LINK, name="Административные методы по работе с пользователями")
@title("Успешное изменение email пользователя")
def test_success_admin_edit_user_email_via_basic_auth(client, precondition_test_admin):
    """Успешное изменение email пользователя администратором."""
    email_1 = "ritchie1@mail.ru"
    email_2 = "changed_ritchie1@mail.ru"
    response = steps_users.admin_get_user_data(
        http_client=client,
        user_id=3,
        basic_auth_header=precondition_test_admin.basic_auth_header,
        step_name="Получение данных пользователя для определения текущего email"
    )
    curent_email = response.json["data"]["email"]
    new_email = email_1 if curent_email == email_2 else email_2
    response = steps_users.admin_edit_user(
        http_client=client,
        user_id=3,
        body={"email": new_email},
        basic_auth_header=precondition_test_admin.basic_auth_header,
        step_name=f"Изменение email у пользователя {response.json['data']['login']}"
    )
    steps_common.verifier(
        "Проверки результатов изменения",
        [
            Check("status_code", HTTPCodes.SUCCESS, response.status_code),
            Check("error_code", ErrorCodes.SUCCESS, response.json["error_code"]),
            Check("error_text", None, response.json["error_text"]),
            Check("email", new_email, response.json["data"]["email"])
        ]
    )


@epic("API")
@feature("Административные методы по работе с пользователями")
@story("Изменение данных пользователей (Basic Auth)")
@link(DOC_LINK, name="Административные методы по работе с пользователями")
@title("Успешное изменение login пользователя")
def test_success_admin_edit_login_email_via_basic_auth(client, precondition_test_admin):
    """Успешное изменение login пользователя администратором."""
    login_1 = "ritchie22311"
    login_2 = "changed_ritchie22311"
    response = steps_users.admin_get_user_data(
        http_client=client,
        user_id=3,
        basic_auth_header=precondition_test_admin.basic_auth_header,
        step_name="Получение данных пользователя для определения текущего login"
    )
    current_login = response.json["data"]["login"]
    new_login = login_1 if current_login == login_2 else login_2
    response = steps_users.admin_edit_user(
        http_client=client,
        user_id=3,
        body={"login": new_login},
        basic_auth_header=precondition_test_admin.basic_auth_header,
        step_name=f"Изменение login у пользователя {current_login}"
    )
    steps_common.verifier(
        "Проверки результатов изменения",
        [
            Check("status_code", HTTPCodes.SUCCESS, response.status_code),
            Check("error_code", ErrorCodes.SUCCESS, response.json["error_code"]),
            Check("error_text", None, response.json["error_text"]),
            Check("login", new_login, response.json["data"]["login"])
        ]
    )


@epic("API")
@feature("Административные методы по работе с пользователями")
@story("Изменение данных пользователей (Basic Auth)")
@link(DOC_LINK, name="Административные методы по работе с пользователями")
@title("Успешное изменение login и email пользователя")
def test_success_admin_edit_login_and_email_via_basic_auth(client, precondition_test_admin):
    """Успешное изменение login и email пользователя администратором."""
    login_1 = "ritchie22311"
    login_2 = "changed_ritchie22311"
    email_1 = "ritchie1@mail.ru"
    email_2 = "changed_ritchie1@mail.ru"
    response = steps_users.admin_get_user_data(
        http_client=client,
        user_id=3,
        basic_auth_header=precondition_test_admin.basic_auth_header,
        step_name="Получение данных пользователя для определения текущего login и email"
    )
    curent_email = response.json["data"]["email"]
    current_login = response.json["data"]["login"]
    new_login = login_1 if current_login == login_2 else login_2
    new_email = email_1 if curent_email == email_2 else email_2
    response = steps_users.admin_edit_user(
        http_client=client,
        user_id=3,
        body={"login": new_login, "email": new_email},
        basic_auth_header=precondition_test_admin.basic_auth_header,
        step_name=f"Изменение login и email пользователя {current_login}"
    )
    steps_common.verifier(
        "Проверки результатов изменения",
        [
            Check("status_code", HTTPCodes.SUCCESS, response.status_code),
            Check("error_code", ErrorCodes.SUCCESS, response.json["error_code"]),
            Check("error_text", None, response.json["error_text"]),
            Check("email", new_email, response.json["data"]["email"]),
            Check("login", new_login, response.json["data"]["login"])
        ]
    )


@epic("API")
@feature("Административные методы по работе с пользователями")
@story("Изменение данных пользователей (Basic Auth)")
@link(DOC_LINK, name="Административные методы по работе с пользователями")
@title("Нельзя изменить login пользователю на уже существующий в системе")
def test_fail_admin_edit_user_via_basic_auth_login_already_exist(client, precondition_test_admin):
    """Нельзя изменить login пользователя если такой login уже есть в системе."""
    login_1 = "ritchie22311"
    login_2 = "changed_ritchie22311"
    response = steps_users.admin_get_user_data(
        http_client=client,
        user_id=3,
        basic_auth_header=precondition_test_admin.basic_auth_header,
        step_name="Получение данных пользователя для определения текущего login"
    )
    current_login = response.json["data"]["login"]
    new_login = login_2 if current_login == login_2 else login_1
    response = steps_users.admin_edit_user(
        http_client=client,
        user_id=3,
        body={"login": new_login},
        basic_auth_header=precondition_test_admin.basic_auth_header,
        step_name=f"Изменение login и email пользователя {current_login}"
    )
    steps_common.verifier(
        "Проверки результатов изменения",
        [
            Check("status_code", HTTPCodes.BAD_REQUEST, response.status_code),
            Check("error_code", ErrorCodes.LOGIN_ALREADY_EXIST, response.json["error_code"]),
            Check("error_text", ErrorTexts.LOGIN_ALREADY_EXIST, response.json["error_text"])
        ]
    )


@epic("API")
@feature("Административные методы по работе с пользователями")
@story("Изменение данных пользователей (Basic Auth)")
@link(DOC_LINK, name="Административные методы по работе с пользователями")
@title("Нельзя изменить email пользователю на уже существующий в системе")
def test_fail_admin_edit_user_via_basic_auth_email_already_exist(client, precondition_test_admin):
    """Нельзя изменить email пользователя если такой email уже есть в системе."""
    email_1 = "ritchie1@mail.ru"
    email_2 = "changed_ritchie1@mail.ru"
    response = steps_users.admin_get_user_data(
        http_client=client,
        user_id=3,
        basic_auth_header=precondition_test_admin.basic_auth_header,
        step_name="Получение данных пользователя для определения текущего login"
    )
    curent_email = response.json["data"]["email"]
    new_email = email_2 if curent_email == email_2 else email_1
    response = steps_users.admin_edit_user(
        http_client=client,
        user_id=3,
        body={"email": new_email},
        basic_auth_header=precondition_test_admin.basic_auth_header,
        step_name="Изменение email пользователя"
    )
    steps_common.verifier(
        "Проверки результатов изменения",
        [
            Check("status_code", HTTPCodes.BAD_REQUEST, response.status_code),
            Check("error_code", ErrorCodes.EMAIL_ALREADY_EXIST, response.json["error_code"]),
            Check("error_text", ErrorTexts.EMAIL_ALREADY_EXIST, response.json["error_text"])
        ]
    )


@epic("API")
@feature("Административные методы по работе с пользователями")
@story("Удаление пользователей (Basic Auth)")
@link(DOC_LINK, name="Административные методы по работе с пользователями")
@title("Успешное удаление пользователя")
def test_success_admin_delete_user(client, precondition_test_admin, faker):
    """Успешное удаление свежезарегистрированного пользователя."""
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
        "Проверки результатов создания",
        [
            Check("status_code", HTTPCodes.SUCCESS, response.status_code),
            Check("error_code", ErrorCodes.SUCCESS, response.json["error_code"]),
            Check("error_text", None, response.json["error_text"])
        ]
    )
    new_user_id = response.json["data"]["id"]
    response = steps_users.admin_delete_user(
        http_client=client,
        user_id=new_user_id,
        basic_auth_header=precondition_test_admin.basic_auth_header
    )
    steps_common.verifier(
        "Проверки результатов удаления",
        [
            Check("status_code", HTTPCodes.SUCCESS, response.status_code),
            Check("error_code", ErrorCodes.SUCCESS, response.json["error_code"]),
            Check("error_text", None, response.json["error_text"])
        ]
    )


@epic("API")
@feature("Административные методы по работе с пользователями")
@story("Удаление пользователей (Basic Auth)")
@link(DOC_LINK, name="Административные методы по работе с пользователями")
@title("Нельзя удалить несуществующего пользователя")
def test_fail_admin_delete_user_not_found(client, precondition_test_admin):
    """Нельзя удалить несуществующего пользователя."""
    response = steps_users.admin_delete_user(
        http_client=client,
        user_id=0,
        basic_auth_header=precondition_test_admin.basic_auth_header
    )
    steps_common.verifier(
        "Проверки результатов удаления",
        [
            Check("status_code", HTTPCodes.NOT_FOUND, response.status_code),
            Check("error_code", ErrorCodes.USER_NOT_FOUND, response.json["error_code"]),
            Check("error_text", ErrorTexts.USER_NOT_FOUND, response.json["error_text"])
        ]
    )


@epic("API")
@feature("Административные методы по работе с пользователями")
@story("Удаление пользователей (Basic Auth)")
@link(DOC_LINK, name="Административные методы по работе с пользователями")
@title("Администратор не может удалить сам себя")
def test_fail_admin_self_delete(client, precondition_test_admin):
    """Нельзя удалить администратором самого себя."""
    response = steps_users.admin_delete_user(
        http_client=client,
        user_id=precondition_test_admin.user_id,
        basic_auth_header=precondition_test_admin.basic_auth_header
    )
    steps_common.verifier(
        "Проверки результатов удаления",
        [
            Check("status_code", HTTPCodes.BAD_REQUEST, response.status_code),
            Check(
                "error_code",
                ErrorCodes.ADMIN_SELF_DELETE_NOT_ALLOWED,
                response.json["error_code"]
            ),
            Check(
                "error_text",
                ErrorTexts.ADMIN_SELF_DELETE_NOT_ALLOWED,
                response.json["error_text"]
            )
        ]
    )
