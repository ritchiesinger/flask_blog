"""Тесты про регистрацию нового пользователя."""

from app.helpers import HTTPCodes, ErrorTexts, ErrorCodes


def test_success_user_registration(client, faker):
    """Успешная регистрация нового пользователя."""
    faker.random.seed()
    login = faker.user_name()
    email = faker.email()
    body = {"login": login, "password": "qwerty", "email": email}
    response = client.post("/api/registration", json=body)
    details = f"{response.json.get('error_text')}. Данные запроса: {body}"
    assert response.status_code == HTTPCodes.SUCCESS, details
    assert response.json.get("error_code") == ErrorCodes.SUCCESS
    assert response.json.get("error_text") is None


def test_failed_user_registration_without_login(client, faker):
    """Нельзя зарегистрировать пользователя без логина."""
    faker.random.seed()
    email = faker.email()
    response = client.post("/api/registration", json={"password": "qwerty", "email": email})
    error_text = f"status_code = {response.status_code}. {response.json['error_text']}"
    assert response.status_code == HTTPCodes.BAD_REQUEST, error_text
    assert response.json.get("error_code") == ErrorCodes.REQUIRED_ARGS_MISSING
    assert response.json.get("error_text") == ErrorTexts.REQUIRED_ARGS_MISSING


def test_failed_user_registration_without_email(client, faker):
    """Нельзя зарегистрировать пользователя без email."""
    faker.random.seed()
    login = faker.user_name()
    response = client.post("/api/registration", json={"login": login, "password": "qwerty"})
    assert response.status_code == HTTPCodes.BAD_REQUEST
    assert response.json.get("error_code") == ErrorCodes.REQUIRED_ARGS_MISSING
    assert response.json.get("error_text") == ErrorTexts.REQUIRED_ARGS_MISSING


def test_failed_user_registration_without_password(client, faker):
    """Нельзя зарегистрировать пользователя без пароля."""
    faker.random.seed()
    login = faker.user_name()
    email = faker.email()
    response = client.post("/api/registration", json={"login": login, "email": email})
    assert response.status_code == HTTPCodes.BAD_REQUEST
    assert response.json.get("error_code") == ErrorCodes.REQUIRED_ARGS_MISSING
    assert response.json.get("error_text") == ErrorTexts.REQUIRED_ARGS_MISSING


def test_failed_user_registration_login_already_exist(client, faker):
    """Нельзя зарегистрировать пользователя с логином который уже существует в системе."""
    faker.random.seed()
    login = "ritchie_singer"
    email = faker.email()
    response = client.post(
        "/api/registration",
        json={"login": login, "email": email, "password": "qwerty"}
    )
    assert response.status_code == HTTPCodes.BAD_REQUEST
    assert response.json.get("error_code") == ErrorCodes.LOGIN_ALREADY_EXIST
    assert response.json.get("error_text") == ErrorTexts.LOGIN_ALREADY_EXIST


def test_failed_user_registration_email_already_exist(client, faker):
    """Нельзя зарегистрировать пользователя с email который уже существует в системе."""
    faker.random.seed()
    login = faker.user_name()
    email = "ritchie1222@mail.ru"
    response = client.post(
        "/api/registration",
        json={"login": login, "email": email, "password": "qwerty"}
    )
    assert response.status_code == HTTPCodes.BAD_REQUEST
    assert response.json.get("error_code") == ErrorCodes.EMAIL_ALREADY_EXIST
    assert response.json.get("error_text") == ErrorTexts.EMAIL_ALREADY_EXIST
