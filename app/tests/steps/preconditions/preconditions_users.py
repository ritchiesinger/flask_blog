"""Предусловия связанные с пользователями."""

from allure import title
from pytest import fixture

from app.helpers import UserData

TEST_USER_CREDS = (7, "Jettie_Price11", "qwerty", "Carmine_Mills12@gmail.com")
TEST_ADMIN_CREDS = (2, "ritchie_singer", "qwerty", "ritchie1222@mail.ru")


@title("Получение тестового пользователя")
@fixture()
def precondition_test_user() -> UserData:
    """Существующий в системе тестовый пользователь без прав администратора."""
    return UserData(*TEST_USER_CREDS)


@title("Получение тестового администратора")
@fixture()
def precondition_test_admin() -> UserData:
    """Заголовок Authorization для тестового администратора."""
    return UserData(*TEST_ADMIN_CREDS)
