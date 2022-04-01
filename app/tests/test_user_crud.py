"""Тесты про пользовательские методы по работе с профилем."""

from app.helpers import HTTPCodes, ErrorTexts, ErrorCodes


def test_success_get_self_user_profile(client, user_basic_auth_header):
    """Успешное получение данных своего профиля."""
    expected_email = "Filiberto_Jacobson22@gmail.com"
    headers = {}
    headers.update(user_basic_auth_header)
    response = client.get("/api/user", headers=headers)
    details = f"{response.json.get('error_text')}"
    assert response.status_code == HTTPCodes.SUCCESS, details
    assert response.json["error_code"] == ErrorCodes.SUCCESS
    assert response.json["error_text"] is None
    assert response.json["data"]["email"] == expected_email
    assert response.json["data"]["login"] == "Ernestine47"


def test_fail_edit_profile_no_args(client, user_basic_auth_header):
    """Ошибка редактирования профиля без передачи каких либо параметров для изменения."""
    headers = {}
    headers.update(user_basic_auth_header)
    response = client.patch("/api/user", headers=headers, json={})
    details = f"{response.json.get('error_text')}"
    assert response.status_code == HTTPCodes.BAD_REQUEST, details
    assert response.json["error_code"] == ErrorCodes.REQUIRED_ARG_MISSING
    assert response.json["error_text"] == ErrorTexts.REQUIRED_ARG_MISSING


def test_fail_edit_profile_login_already_exist(client, user_basic_auth_header):
    """Нельзя изменить логин профиля на тот, который уже зарегистрирован в системе."""
    headers = {}
    headers.update(user_basic_auth_header)
    response = client.patch(f"/api/user", headers=headers, json={"login": "ritchie_singer"})
    assert response.status_code == HTTPCodes.BAD_REQUEST, response.json
    assert response.json["error_code"] == ErrorCodes.LOGIN_ALREADY_EXIST
    assert response.json["error_text"] == ErrorTexts.LOGIN_ALREADY_EXIST


def test_fail_edit_profile_email_already_exist(client, user_basic_auth_header):
    """Нельзя изменить email профиля на тот, который уже зарегистрирован в системе."""
    headers = {}
    headers.update(user_basic_auth_header)
    response = client.patch(f"/api/user", headers=headers, json={"email": "ritchie1222@mail.ru"})
    assert response.status_code == HTTPCodes.BAD_REQUEST, response.json
    assert response.json["error_code"] == ErrorCodes.EMAIL_ALREADY_EXIST
    assert response.json["error_text"] == ErrorTexts.EMAIL_ALREADY_EXIST
