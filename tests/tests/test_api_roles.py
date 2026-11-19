"""API-тесты смены роли пользователя: PATCH /api/users/<id>.

Поверхность смены роли — только USER <-> ADMIN, действие доступно только
SuperAdministrator (→ ARC-0041). SUPERADMIN через интерфейсы не выдаётся
и не снимается: роль уникальна, её единственный канал — CLI. Порядок
проверок сервиса даёт карту ответов: 401 (без токена) → 403 (не супер или
своя роль) → 400 (ключ отсутствует или роль вне поверхности) → 404
(пользователя нет) → 200 (успех; повтор той же роли идемпотентен).
"""

from flask import Flask
from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.constants import Roles
from blog.extensions import db
from blog.models import User
from tests.objects.user import UserObject
from tests.preconditions.users_preconditions import create_user
from tests.tools.asserters.base_asserters import assert_condition, assert_equal, assert_status_code
from tests.tools.asserters.soft_asserters import SoftAssert
from tests.tools.clients.api import Api

SUPERADMIN_PASSWORD = "password123"


def make_superadmin(app: Flask, app_client: FlaskClient, username: str = "super_boss") -> UserObject:
    """Создаёт супер-админа напрямую через модель: роль не выдаётся интерфейсами.

    Args:
        app: тестовое приложение (app_context для записи в БД).
        app_client: клиент для UserObject.
        username: логин супер-админа.

    Returns:
        UserObject супер-админа.
    """
    return create_user(
        app=app, app_client=app_client, username=username,
        password=SUPERADMIN_PASSWORD, role=Roles.SUPERADMIN,
    )


def make_admin(app: Flask, app_client: FlaskClient, username: str) -> UserObject:
    """Создаёт администратора напрямую через модель.

    Args:
        app: тестовое приложение.
        app_client: клиент для UserObject.
        username: логин администратора.

    Returns:
        UserObject администратора.
    """
    return create_user(
        app=app, app_client=app_client, username=username,
        password="password123", role=Roles.ADMIN,
    )


@epic("API")
class TestChangeRoleAccessControl:
    """Запреты смены роли: гость, обычный пользователь, админ, самоизменение."""

    @feature("Управление ролями", "Ролевая модель")
    @story("Доступ к смене роли")
    @severity(severity_level.NORMAL)
    @title("Нельзя сменить роль без авторизации")
    def test_change_role_requires_token(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """PATCH без Bearer-токена → 401: личность запросившего не установлена."""
        with step("API. Попытка смены роли без токена"):
            api = Api(setup_app_client)
            response = api.users.change_role(user_id=setup_test_user.db_model.id, role=Roles.ADMIN)
        SoftAssert(
            assert_status_code(expect=401, response=response, soft_assert=True),
            assert_condition(
                condition="error" in response.get_json(),
                allure_step_name="В теле ответа есть поле 'error'",
                error_text="В ответе нет поля 'error'!",
                soft_assert=True,
            ),
        )

    @feature("Управление ролями", "Ролевая модель")
    @story("Доступ к смене роли")
    @severity(severity_level.CRITICAL)
    @title("Обычный пользователь не может менять роли")
    def test_regular_user_forbidden(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """PATCH под обычным пользователем → 403: роли не хватает."""
        with step("API. Смена роли от имени обычного пользователя"):
            response = setup_test_user.api.change_user_role(
                user_id=setup_test_user.db_model.id + 1, new_role=Roles.ADMIN,
            )
        assert_status_code(expect=403, response=response)

    @feature("Управление ролями", "Ролевая модель")
    @story("Доступ к смене роли")
    @severity(severity_level.CRITICAL)
    @title("Администратор не является супер-администратором: смена роли ему недоступна")
    def test_admin_forbidden(self, setup_app: Flask, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """PATCH под админом (не супер) → 403: ADMIN не наследует SUPERADMIN."""
        admin = make_admin(setup_app, setup_app_client, "plain_admin")
        with step("API. Смена роли от имени администратора"):
            response = admin.api.change_user_role(
                user_id=setup_test_user.db_model.id, new_role=Roles.ADMIN,
            )
        assert_status_code(expect=403, response=response)

    @feature("Управление ролями", "Ролевая модель")
    @story("Доступ к смене роли")
    @severity(severity_level.CRITICAL)
    @title("Супер-администратор не может изменить собственную роль")
    def test_superadmin_cannot_change_own_role(self, setup_app: Flask, setup_app_client: FlaskClient):
        """Свой профиль → 403, даже с валидной ролью в теле (→ ARC-0041)."""
        super_user = make_superadmin(setup_app, setup_app_client)
        with step("API. Попытка смены собственной роли супер-админом"):
            response = super_user.api.change_user_role(
                user_id=super_user.db_model.id, new_role=Roles.ADMIN,
            )
        assert_status_code(expect=403, response=response)


@epic("API")
@feature("Управление ролями", "Поверхность смены роли")
@story("Валидация новой роли")
class TestChangeRoleSurface:
    """SUPERADMIN не выдаётся через интерфейсы; ключ role обязателен."""

    @severity(severity_level.CRITICAL)
    @title("Роль SUPERADMIN не выдаётся через API")
    def test_superadmin_role_not_assignable(self, setup_app: Flask, setup_app_client: FlaskClient,
                                            setup_test_user: UserObject):
        """role=superadmin → 400: действие не существует на этом слое."""
        super_user = make_superadmin(setup_app, setup_app_client)
        with step("API. Попытка выдать SUPERADMIN через PATCH"):
            response = super_user.api.change_user_role(
                user_id=setup_test_user.db_model.id, new_role=Roles.SUPERADMIN,
            )
        assert_status_code(expect=400, response=response)

    @severity(severity_level.NORMAL)
    @title("Неизвестная роль отклоняется")
    def test_unknown_role_rejected(self, setup_app: Flask, setup_app_client: FlaskClient,
                                   setup_test_user: UserObject):
        """role=moderator → 400: вне поверхности USER/ADMIN."""
        super_user = make_superadmin(setup_app, setup_app_client)
        with step("API. Попытка выдать несуществующую роль"):
            response = super_user.api.change_user_role(
                user_id=setup_test_user.db_model.id, new_role="moderator",
            )
        assert_status_code(expect=400, response=response)

    @severity(severity_level.NORMAL)
    @title("Запрос без ключа role отклоняется")
    def test_missing_role_key_rejected(self, setup_app: Flask, setup_app_client: FlaskClient,
                                       setup_test_user: UserObject):
        """PATCH без ключа 'role' → 400 (клиент собирает такое тело ролью None)."""
        super_user = make_superadmin(setup_app, setup_app_client)
        with step("API. PATCH без ключа 'role' в теле"):
            api = Api(setup_app_client)
            response = api.users.change_role(
                user_id=setup_test_user.db_model.id, role=None, token=super_user.api_token,
            )
        assert_status_code(expect=400, response=response)


@epic("API")
@feature("Управление ролями", "Возможности супер-администратора")
@story("Успешная смена роли")
class TestChangeRoleBySuperadmin:
    """Позитивные сценарии и карта 404/200."""

    @severity(severity_level.BLOCKER)
    @title("Супер-администратор повышает пользователя до администратора")
    def test_promote_user_to_admin(self, setup_app: Flask, setup_app_client: FlaskClient,
                                   setup_test_user: UserObject):
        """PATCH role=admin → 200, роль в теле и в БД — admin."""
        super_user = make_superadmin(setup_app, setup_app_client)
        with step("API. Смена роли USER -> ADMIN"):
            response = super_user.api.change_user_role(
                user_id=setup_test_user.db_model.id, new_role=Roles.ADMIN,
            )
        with step("Проверка ответа"):
            data = response.get_json()
            SoftAssert(
                assert_status_code(expect=200, response=response, soft_assert=True),
                assert_equal(expect=Roles.ADMIN, actual=data.get("role"), name="role в теле ответа", soft_assert=True),
                assert_equal(
                    expect=setup_test_user.db_model.username,
                    actual=data.get("username"),
                    name="username в теле ответа",
                    soft_assert=True,
                ),
            )
        with step("ORM. Роль пользователя в БД"):
            with setup_app.app_context():
                user = db.session.execute(
                    db.select(User).filter_by(username=setup_test_user.db_model.username),
                ).scalars().first()
            assert_equal(expect=Roles.ADMIN, actual=user.role, name="user.role в БД")

    @severity(severity_level.BLOCKER)
    @title("Супер-администратор снимает роль администратора")
    def test_demote_admin_to_user(self, setup_app: Flask, setup_app_client: FlaskClient):
        """PATCH role=user у админа → 200, роль в БД — user."""
        admin = make_admin(setup_app, setup_app_client, "demoted_admin")
        super_user = make_superadmin(setup_app, setup_app_client)
        with step("API. Смена роли ADMIN -> USER"):
            response = super_user.api.change_user_role(
                user_id=admin.db_model.id, new_role=Roles.USER,
            )
        assert_status_code(expect=200, response=response)
        with step("ORM. Роль пользователя в БД"):
            with setup_app.app_context():
                user = db.session.execute(db.select(User).filter_by(username="demoted_admin")).scalars().first()
            assert_equal(expect=Roles.USER, actual=user.role, name="user.role в БД")

    @severity(severity_level.NORMAL)
    @title("Повторная смена роли на то же значение идемпотентна")
    def test_repeated_change_idempotent(self, setup_app: Flask, setup_app_client: FlaskClient,
                                        setup_test_user: UserObject):
        """Двойной PATCH role=admin → оба 200, роль не меняется повторно."""
        super_user = make_superadmin(setup_app, setup_app_client)
        with step("API. Первая смена роли"):
            first = super_user.api.change_user_role(
                user_id=setup_test_user.db_model.id, new_role=Roles.ADMIN,
            )
        with step("API. Повтор той же смены"):
            second = super_user.api.change_user_role(
                user_id=setup_test_user.db_model.id, new_role=Roles.ADMIN,
            )
        SoftAssert(
            assert_status_code(expect=200, response=first, soft_assert=True),
            assert_status_code(expect=200, response=second, soft_assert=True),
            assert_equal(
                expect=Roles.ADMIN,
                actual=second.get_json().get("role"),
                name="role после повтора",
                soft_assert=True,
            ),
        )

    @severity(severity_level.NORMAL)
    @title("Смена роли несуществующего пользователя — 404")
    def test_unknown_user_404(self, setup_app: Flask, setup_app_client: FlaskClient):
        """PATCH на чужом id → 404."""
        super_user = make_superadmin(setup_app, setup_app_client)
        with step("API. PATCH на несуществующем пользователе"):
            response = super_user.api.change_user_role(user_id=999_999, new_role=Roles.ADMIN)
        assert_status_code(expect=404, response=response)


@epic("API")
@feature("Управление ролями", "Иерархия ролей")
@story("SUPERADMIN наследует полномочия администратора")
class TestSuperadminHierarchyAccess:
    """Существующие админ-эндпоинты открыты супер-админу по иерархии (→ ARC-0041)."""

    @severity(severity_level.CRITICAL)
    @title("Супер-администратор видит список пользователей")
    def test_superadmin_can_list_users(self, setup_app: Flask, setup_app_client: FlaskClient):
        """GET /api/users под супер-админом → 200."""
        super_user = make_superadmin(setup_app, setup_app_client)
        with step("API. Список пользователей от имени супер-админа"):
            api = Api(setup_app_client)
            response = api.users.list(token=super_user.api_token)
        assert_status_code(expect=200, response=response)

    @severity(severity_level.CRITICAL)
    @title("Супер-администратор может удалить пользователя")
    def test_superadmin_can_delete_user(self, setup_app: Flask, setup_app_client: FlaskClient,
                                        setup_test_user: UserObject):
        """DELETE /api/users/<id> под супер-админом → 204, пользователь удалён."""
        super_user = make_superadmin(setup_app, setup_app_client)
        with step("API. Удаление пользователя от имени супер-админа"):
            api = Api(setup_app_client)
            response = api.users.delete(user_id=setup_test_user.db_model.id, token=super_user.api_token)
        assert_status_code(expect=204, response=response)
