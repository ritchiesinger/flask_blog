"""Тесты WEB-роутов админки: ролевой доступ, удаление пользователей, пагинация списка.

Ролевая модель WEB (решение 2026-11-13): гость — редирект на логин; не-админ — 404 (страница «не существует»);
админ — 200. Удаление самого себя — 403 от сервиса, как в API. Пагинация списка — трио по эталону
TestIndexPagination (→ ARC-0061).
"""

from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.models.user import User
from tests.constants.web_endpoints import WebEndpoints
from tests.objects.user import UserObject
from tests.preconditions.users_preconditions import create_user
from tests.tools.asserters.base_asserters import assert_condition, assert_redirect, assert_status_code
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
            assert_status_code(expect=302, response=response)
            assert_condition(
                condition=response.headers.get("Location", "").startswith(WebEndpoints.AUTH.LOGIN),
                allure_step_name="Редирект ведёт на страницу логина",
                error_text=f"Ожидался редирект на логин, получено: {str(response.headers.get('Location'))}",
            )

    @story("Просмотр списка пользователей")
    @title("WEB-роут на получение списка пользователей для не-администратора не существует (404)")
    def test_list_hidden_for_regular_user(self, setup_logged_in_user: UserObject):
        """Не-админ под сессией получает 404: админ-поверхность неотличима от несуществующей."""
        user = setup_logged_in_user
        with step("Пользователь. WEB. Запрос списка пользователей"):
            response = user.web.admin.users()
            assert_status_code(expect=404, response=response)

    @story("Удаление пользователя")
    @title("WEB-роут на удаление пользователя для не-администратора не существует (404)")
    def test_delete_hidden_for_regular_user(self, setup_logged_in_user: UserObject, setup_test_user_2: UserObject):
        """POST удаления от не-админа — 404, даже с корректным id цели."""
        user = setup_logged_in_user
        with step("Пользователь. WEB. Попытка удаления пользователя"):
            response = user.web.admin.delete_user(user_id=setup_test_user_2.db_model.id)
            assert_status_code(expect=404, response=response)


@epic("WEB")
@feature("Административная панель")
@story("Управление пользователями")
class TestAdminUsers:
    """Администратор видит список и удаляет пользователей."""

    @title("Администратор видит список пользователей")
    def test_admin_sees_users(self, setup_logged_in_admin: UserObject, setup_test_user: UserObject):
        """Под админом список открывается: 200, созданный пользователь и кнопки на месте."""
        admin, user = setup_logged_in_admin, setup_test_user
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
            setup_logged_in_admin: UserObject,
            setup_test_user: UserObject,
    ):
        """Удаление: 302 на список, флеш, пользователь исчезает из БД."""
        admin, user = setup_logged_in_admin, setup_test_user
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
        with step("Администратор. WEB. Флеш об успехе"):
            response = admin.web.admin.users()
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=FLASH_USER_DELETED in response.get_data(as_text=True),
                allure_step_name="Флеш об успехе",
                error_text="Флеш-сообщение не найдено",
            )
        with step("ORM. Проверка исчезновения пользователя"):
            with admin.client.application.app_context():
                gone = User.query.filter_by(username=user.db_model.username).one_or_none()
                assert_condition(
                    condition=gone is None,
                    allure_step_name="Пользователь удалён из БД",
                    error_text="Пользователь остался в БД",
                )

    @title("Администратор не может удалить сам себя (403)")
    def test_admin_cannot_delete_self(self, setup_logged_in_admin: UserObject):
        """Админ не может удалить сам себя: ForbiddenError от сервиса — 403, как в API."""
        admin = setup_logged_in_admin
        with step("Администратор. WEB. Попытка удаления самого себя"):
            response = admin.web.admin.delete_user(user_id=admin.db_model.id)
            assert_status_code(expect=403, response=response)

    @title("Удаление несуществующего пользователя: 404")
    def test_delete_unknown_user(self, setup_logged_in_admin: UserObject):
        """Несуществующий id — NotFoundError: 404."""
        admin = setup_logged_in_admin
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
            setup_logged_in_admin: UserObject,
            setup_test_user: UserObject,
            setup_app_client: FlaskClient,
    ):
        """Пункт присутствует у админа, отсутствует у обычного пользователя и гостя.

        Одна авторизованная фикстура на тест (→ ARC-0061): смена личности — явными шагами.
        """
        admin, user = setup_logged_in_admin, setup_test_user
        with step("Администратор. WEB. Главная страница"):
            response = admin.web.posts.index()
            assert_condition(
                condition=MENU_ITEM in response.get_data(as_text=True),
                allure_step_name=f"Пункт '{MENU_ITEM}' меню виден админу",
                error_text=f"Пункт меню '{MENU_ITEM}' не найден на странице админа",
            )
        with step("Администратор. WEB. Выход из системы"):
            response = admin.web.auth.logout()
            assert_redirect(expect="/", response=response)
        with step("Пользователь. WEB. Вход в систему"):
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


@epic("WEB")
@feature("Административная панель")
@story("Пагинация списка пользователей")
class TestAdminUsersPagination:
    """Пагинация WEB-админки: разбиение по страницам, санитизация номера страницы.

    Эталон — TestIndexPagination (→ ARC-0061). Отличие от эталона: admin_service.list_users
    пагинирует по id возрастанию (→ ARC-0032), поэтому на первой странице — admin и user01..user19,
    на второй — user20. Страницы запрашиваются фасадом admin.web.admin.users(query_string=...) —
    cookie админ-сессии едины на клиенте фикстуры; ORM-посев идёт через публичный admin.client
    (→ ARC-0061).
    """

    @title("21 пользователь делится на страницу из 20 и страницу из 1")
    @severity(severity_level.CRITICAL)
    def test_admin_users_pagination_splits_list(self, setup_logged_in_admin: UserObject):
        """Список делится по USERS_PER_PAGE: admin и user01..user19 на первой, user20 на второй.

        Ожидание: на стр. 1 — user01 и user19 (user20 нет), на стр. 2 — user20 (user01 нет).
        """
        admin = setup_logged_in_admin
        with step("ORM. Создание 20 пользователей user01..user20"):
            for number in range(1, 21):
                create_user(
                    app=admin.client.application,
                    app_client=admin.client,
                    username=f"user{number:02d}",
                    password="password123",
                )
        with step("Администратор. WEB. Открытие первой страницы"):
            first = admin.web.admin.users(query_string={"page": 1})
            assert_status_code(expect=200, response=first)
        with step("Проверка: на первой странице admin и первые 19, user20 нет"):
            page_text = first.get_data(as_text=True)
            assert_condition(
                condition="user01" in page_text and "user19" in page_text,
                allure_step_name="На первой странице начало списка",
                error_text="Первые пользователи не найдены на первой странице!",
            )
            assert_condition(
                condition="user20" not in page_text,
                allure_step_name="Последний пользователь на второй странице",
                error_text="user20 попал на первую страницу!",
            )
        with step("Администратор. WEB. Открытие второй страницы"):
            second = admin.web.admin.users(query_string={"page": 2})
            assert_status_code(expect=200, response=second)
            page_text = second.get_data(as_text=True)
            assert_condition(
                condition="user20" in page_text,
                allure_step_name="На второй странице последний пользователь",
                error_text="user20 не найден на второй странице!",
            )
            assert_condition(
                condition="user01" not in page_text,
                allure_step_name="Начало списка не дублируется на второй странице",
                error_text="user01 продублировался на второй странице!",
            )

    @title("Мусор и некорректный page дают первую страницу без ошибок")
    @severity(severity_level.MINOR)
    def test_admin_users_page_sanitization(self, setup_logged_in_admin: UserObject):
        """?page=0, -5, abc → 200 и первая страница (fallback без исключений)."""
        admin = setup_logged_in_admin
        with step("ORM. Создание пользователя user01 для контроля"):
            create_user(
                app=admin.client.application,
                app_client=admin.client,
                username="user01", password="password123",
            )
        with step("Администратор. WEB. ?page=0 и ?page=-5"):
            for bad_page in (0, -5):
                response = admin.web.admin.users(query_string={"page": bad_page})
                assert_status_code(expect=200, response=response)
                assert_condition(
                    condition="user01" in response.get_data(as_text=True),
                    allure_step_name=f"page={bad_page} даёт первую страницу",
                    error_text=f"page={bad_page} сломал список пользователей!",
                )
        with step("Администратор. WEB. ?page=abc"):
            response = admin.web.admin.users(query_string={"page": "abc"})
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="user01" in response.get_data(as_text=True),
                allure_step_name="page=abc даёт первую страницу",
                error_text="page=abc сломал список пользователей!",
            )

    @title("Страница за пределами total отдаёт 200 и пустой список")
    @severity(severity_level.MINOR)
    def test_admin_users_page_beyond_total(self, setup_logged_in_admin: UserObject):
        """?page=999 → 200, пустой список (error_out=False)."""
        admin = setup_logged_in_admin
        with step("ORM. Создание пользователя user01 для контроля"):
            create_user(
                app=admin.client.application,
                app_client=admin.client,
                username="user01",
                password="password123"
            )
        with step("Администратор. WEB. Открытие страницы 999"):
            response = admin.web.admin.users(query_string={"page": 999})
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="user01" not in response.get_data(as_text=True),
                allure_step_name="Список за пределами total пуст",
                error_text="За пределами total список не пуст!",
            )
