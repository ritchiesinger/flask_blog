"""WEB-админка: доступ к роутам по ролям и удаление пользователей.

Ролевая модель WEB (решение 2026-11-13): гость — редирект на логин; не-админ — 404 (страница «не существует»);
админ — 200. Удаление самого себя — 403 от сервиса, как в API.
"""

from flask import Flask
from flask.testing import FlaskClient
from glamor import epic, feature, step, story, title

from blog.models.user import User
from tests.constants.web_endpoints import WebEndpoints
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_equal, assert_status_code
from tests.tools.clients.web_client import WebClient

MENU_ITEM = "Административная панель"
FLASH_USER_DELETED = "Пользователь удалён."
PAGE_NOT_FOUND = "Страница не найдена."


@epic("WEB")
@feature("Административная панель")
class TestAccessControl:
    """Гости и пользователи без роли администратора к WEB-слою администратора не допущены."""

    @story("Просмотр списка пользователей")
    @title("WEB-роут на получение списка пользователей для гостя ведёт на страницу авторизации")
    def test_guest_redirect_to_login(self, setup_app_client: FlaskClient):
        """Без сессии GET списка возвращает 302 на логин."""
        with step("WEB. Запрос списка пользователей без сессии"):
            response = WebClient(setup_app_client).admin.users()
            assert_status_code(expect=302,response=response)
            assert_condition(
                condition=response.headers["Location"].startswith(WebEndpoints.AUTH.LOGIN),
                allure_step_name="Редирект ведёт на страницу логина",
                error_text=f"Ожидался редирект на логин, получено: {str(response.headers.get('Location'))}",
            )

    @story("Просмотр списка пользователей")
    @title("WEB-роут на получение списка пользователей для не-администратора не существует (404)")
    def test_list_hidden_for_regular_user(self, setup_test_user: UserObject):
        """Не-админ под сессией получает 404: админ-поверхность неотличима от несуществующей."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Запрос списка пользователей"):
            response = setup_test_user.web.admin.users()
            assert_status_code(expect=404, response=response)

    @story("Удаление пользователя")
    @title("WEB-роут на удаление пользователя для не-администратора не существует (404)")
    def test_delete_hidden_for_regular_user(self, setup_test_user: UserObject, setup_test_user_2: UserObject):
        """POST удаления от не-админа — 404, даже с корректным id цели."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Попытка удаления пользователя"):
            response = setup_test_user.web.admin.delete_user(user_id=setup_test_user_2.db_model.id)
            assert_status_code(expect=404, response=response)


@epic("WEB")
@feature("Административная панель")
@story("Управление пользователями")
class TestAdminUsers:
    """Администратор видит список и удаляет пользователей."""

    @title("Администратор видит список пользователей")
    def test_admin_sees_users(self, setup_admin_user: UserObject, setup_test_user: UserObject):
        """Под админом список открывается: 200, созданный пользователь и кнопки на месте."""
        admin, user = setup_admin_user, setup_test_user
        with step("Администратор. WEB. Авторизация"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Администратор. WEB. Открытие списка пользователей"):
            response = admin.web.admin.users()
            assert_status_code(expect=200, response=response)
            body = response.get_data(as_text=True)
            assert_condition(
                condition=user.db_model.username in body,
                allure_step_name="Список содержит созданного пользователя",
                error_text=f"Пользователь {user.db_model.username} не найден в списке",
            )
            assert_condition(
                condition="/admin/users/" in body and "/delete" in body,
                allure_step_name="Формы удаления на месте",
                error_text="Форма удаления не отрендерена",
            )

    @title("Администратор удаляет обычного пользователя")
    def test_admin_deletes_regular_user(
            self,
            setup_app: Flask,
            setup_admin_user: UserObject,
            setup_test_user: UserObject,
    ):
        """Удаление: 302 на список, флеш, пользователь исчезает из БД."""
        admin, user = setup_admin_user, setup_test_user
        with step("Администратор. WEB. Авторизация"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Администратор. WEB. Список до удаления (положительный контроль)"):
            response = admin.web.admin.users()
            assert_condition(
                condition=user.db_model.username in response.get_data(as_text=True),
                allure_step_name=f"Пользователь '{user.db_model.username}' присутствует до удаления",
                error_text=f"Пользователь '{user.db_model.username}' не найден до удаления",
            )
        with step("Администратор. WEB. Удаление пользователя"):
            response = admin.web.admin.delete_user(user_id=user.db_model.id)
            assert_status_code(expect=302, response=response)
            assert_equal(
                expect=WebEndpoints.ADMIN.USERS,
                actual=response.headers["Location"],
                name="Заголовок Location",
            )
        with step("Администратор. WEB. Флеш об успехе"):
            response = admin.web.admin.users()
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=FLASH_USER_DELETED in response.get_data(as_text=True),
                allure_step_name="Флеш об успехе",
                error_text="Флеш-сообщение не найдено",
            )
        with step("ORM. Проверка исчезновения пользователя"):
            with setup_app.app_context():
                gone = User.query.filter_by(username=user.db_model.username).one_or_none()
                assert_condition(
                    condition=gone is None,
                    allure_step_name="Пользователь удалён из БД",
                    error_text="Пользователь остался в БД",
                )

    @title("Администратор не может удалить сам себя (403)")
    def test_admin_cannot_delete_self(self, setup_admin_user: UserObject):
        """Админ не может удалить сам себя: ForbiddenError от сервиса — 403, как в API."""
        admin = setup_admin_user
        with step("Администратор. WEB. Авторизация"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Администратор. WEB. Попытка удаления самого себя"):
            response = admin.web.admin.delete_user(user_id=admin.db_model.id)
            assert_status_code(expect=403, response=response)

    @title("Удаление несуществующего пользователя: 404")
    def test_delete_unknown_user(self, setup_admin_user: UserObject):
        """Несуществующий id — NotFoundError: 404."""
        admin = setup_admin_user
        with step("Администратор. WEB. Авторизация"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Администратор. WEB. Удаление несуществующего пользователя"):
            response = admin.web.admin.delete_user(user_id=99999)
            assert_status_code(expect=404, response=response)


@epic("WEB")
@feature("Административная панель")
@story("Навигация")
class TestAdminMenu:
    """Пункт «Административная панель» — только для админов; у остальных меню пустое сознательно."""

    @title("Пункт меню виден только администратору")
    def test_menu_item_visibility(
            self,
            setup_app_client: FlaskClient,
            setup_admin_user: UserObject,
            setup_test_user: UserObject,
    ):
        """Пункт присутствует у админа, отсутствует у обычного пользователя и гостя."""
        admin, user = setup_admin_user, setup_test_user
        with step("Администратор. WEB. Авторизация"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Администратор. WEB. Главная страница"):
            response = admin.web.posts.index()
            assert_condition(
                condition=MENU_ITEM in response.get_data(as_text=True),
                allure_step_name=f"Пункт '{MENU_ITEM}' меню виден админу",
                error_text=f"Пункт меню '{MENU_ITEM}' не найден на странице админа",
            )
        with step("Администратор. WEB. Выход из системы"):
            response = admin.web.auth.logout()
            assert_status_code(expect=302, response=response)
            assert_equal(expect="/", actual=response.headers["Location"], name="Заголовок Location")
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Главная страница"):
            response = user.web.posts.index()
            assert_condition(
                condition=MENU_ITEM not in response.get_data(as_text=True),
                allure_step_name=f"Пункт меню '{MENU_ITEM}' скрыт у обычного пользователя",
                error_text=f"Пункт меню '{MENU_ITEM}' виден не-админу",
            )
        with step("WEB. Главная страница без сессии"):
            response = WebClient(setup_app_client).posts.index()
            assert_condition(
                condition=MENU_ITEM not in response.get_data(as_text=True),
                allure_step_name=f"Пункт меню '{MENU_ITEM}' скрыт у гостя",
                error_text=f"Пункт меню '{MENU_ITEM}' виден гостю",
            )


@epic("WEB")
@feature("Административная панель")
@story("Обработка ошибок")
class TestNotFoundPage:
    """Фирменная 404-страница: 404 стал основной ошибкой для не-админов."""

    @title("Несуществующий URL рендерит фирменную 404")
    def test_unknown_url_renders_custom_404(self, setup_app_client: FlaskClient):
        """Гость на левом URL получает нашу страницу 404, а не голую заглушку."""
        with step("WEB. Запрос несуществующего URL"):
            response = setup_app_client.get("/no-such-page-abc")
            assert_status_code(expect=404, response=response)
            body = response.get_data(as_text=True)
            assert_condition(
                condition="404" in body,
                allure_step_name="Статус на странице",
                error_text="Страница без упоминания 404"
            )
            assert_condition(
                condition=PAGE_NOT_FOUND in body,
                allure_step_name="Осмысленный текст",
                error_text="Текст 404-страницы не найден"
            )
