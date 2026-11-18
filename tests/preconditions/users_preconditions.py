"""Предусловия, связанные с пользователями."""

from json import dumps

from faker import Faker
from flask import Flask
from flask.testing import FlaskClient
from glamor import attach, attachment_type, step, title
from pytest import fixture

from blog.constants import Roles
from blog.extensions import db
from blog.models import User
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_redirect

fake = Faker()


def create_user(
    app: Flask,
    app_client: FlaskClient,
    username: str,
    password: str,
    role: str = Roles.USER,
) -> UserObject:
    """Создаёт пользователя напрямую через модель и возвращает его обёртку.

    Args:
        app: тестовое приложение, нужен его app_context для записи в БД.
        app_client: клиент, который попадёт в UserObject.
        username: логин создаваемого пользователя.
        password: пароль (в UserObject хранится открытым текстом).
        role: роль пользователя, по умолчанию Roles.USER.

    Returns:
        UserObject: обёртка над созданным пользователем для дальнейших шагов.
    """
    with step("ORM. Создание пользователя"):
        with app.app_context():
            user = User(username=username, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)  # материализуем все скаляры после expire_on_commit
            attach(
                body=dumps(user.to_dict(), indent=2),
                name="Атрибуты созданного пользователя",
                attachment_type=attachment_type.JSON,
            )
            db.session.expunge(user)  # db_model живёт в тестах детачнутым: скаляры читаемы, связи — нет
            return UserObject(client=app_client, db_model=user, password=password)


@fixture
@title("Создан Пользователь 1")
def setup_test_user(setup_app: Flask, setup_app_client: FlaskClient) -> UserObject:
    """Обычный пользователь, созданный напрямую через модель."""
    username, password = fake.user_name(), "password123"
    return create_user(app=setup_app, app_client=setup_app_client, username=username, password=password)


@fixture
@title("Создан Пользователь 2")
def setup_test_user_2(setup_app: Flask, setup_app_client: FlaskClient) -> UserObject:
    """Обычный пользователь, созданный напрямую через модель."""
    username, password = fake.user_name(), "password123"
    return create_user(app=setup_app, app_client=setup_app_client, username=username, password=password)


@fixture
@title("Создан Администратор 1")
def setup_admin_user(setup_app: Flask, setup_app_client: FlaskClient) -> UserObject:
    """Администратор, созданный напрямую через модель."""
    username, password = fake.user_name(), "password123"
    return create_user(
        app=setup_app,
        app_client=setup_app_client,
        username=username,
        password=password,
        role=Roles.ADMIN,
    )


@fixture
@title("Пользователь. WEB. Авторизован")
def setup_logged_in_user(setup_test_user: UserObject) -> UserObject:
    """Открывает WEB-сессию пользователя через форму логина."""
    user = setup_test_user
    with step("Пользователь. WEB. Вход в систему"):
        response = user.web.auth.login(username=user.db_model.username, password=user.password)
        assert_redirect(expect="/", response=response)
    return user
