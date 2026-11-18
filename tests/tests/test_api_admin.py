"""API-тесты административной части: ролевая модель и управление пользователями.

Проверяют доступ к эндпоинтам администратора (список и удаление пользователей) с трёх уровней доступа:
неавторизованный запрос, запрос обычного пользователя, запрос администратора. Запросы отправляются через объектные
обёртки (``Api`` или методы ``UserObject``) — сырых обращений к клиенту и URL в тестах нет.

Ожидаемая логика ответов, на которую опираются тесты:
- без Bearer-токена — 401: сервер не может установить личность запросившего;
- под обычным пользователем — 403: личность установлена, роли не хватает;
- под администратором — успешный код и ожидаемое изменение данных.

Структуру отчёта задают декораторы glamor: epic/feature/story группируют тесты, ``title`` даёт человекочитаемое имя.
Докстринги при этом живут в IDE и отвечают на вопрос «почему ожидание именно такое» — их не видно в отчёте, и это
нормально. Проверки — через ``assert_status_code``/``assert_condition``; где нужно увидеть
все несоответствия за один прогон, используется ``SoftAssert``.
"""
from flask import Flask
from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.extensions import db
from blog.models import User
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_equal, assert_status_code
from tests.tools.asserters.soft_asserters import SoftAssert
from tests.tools.clients.api import Api


@epic("API")
class TestAdminAccessControl:
    """Проверки ролевой модели доступа к административным эндпоинтам.

    Каждый эндпоинт проверяется на запреты с двух уровней: без авторизации (401) и под обычным пользователем (403).
    Позитивные сценарии — в смежных классах.
    """

    @feature("Возможности администратора", "Ролевая модель")
    @story("Получение списка пользователей")
    @severity(severity_level.NORMAL)
    @title("Нельзя получить список пользователей без авторизации")
    def test_list_users_requires_token(self, setup_app_client: FlaskClient):
        """Список пользователей без авторизации недоступен: 401 и поле 'error'.

        Ожидание 401, а не 403: без Bearer-токена сервер не может установить личность запросившего, поэтому ответ
        говорит об отсутствии аутентификации, а не о нехватке прав.
        """
        with step("API. Попытка получения списка пользователей без авторизации"):
            api = Api(setup_app_client)
            response = api.users.list()
            SoftAssert(
                assert_status_code(expect=401, response=response, soft_assert=True),
                assert_condition(
                    condition="error" in response.get_json(),
                    allure_step_name="В ответе есть поле 'error'",
                    error_text="В ответе нет поля 'error'",
                    soft_assert=True
                ),
            )

    @feature("Возможности администратора", "Ролевая модель")
    @story("Удаление пользователей")
    @severity(severity_level.NORMAL)
    @title("Нельзя удалить пользователя без авторизации")
    def test_delete_user_requires_token(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """Удаление пользователя без авторизации отклоняется: 401 и поле 'error'.

        Ожидание аналогично ``test_list_users_requires_token``: аутентификация проверяется раньше любых проверок прав
        и существования цели.
        """
        with step("API. Попытка удаления пользователя без авторизации"):
            api = Api(setup_app_client)
            user_id = setup_test_user.db_model.id
            response = api.users.delete(user_id=user_id)
            SoftAssert(
                assert_status_code(expect=401, response=response, soft_assert=True),
                assert_condition(
                    condition="error" in response.get_json(),
                    allure_step_name="В ответе есть поле 'error'",
                    error_text="В ответе нет поля 'error'",
                    soft_assert=True
                ),
            )

    @feature("Возможности администратора", "Ролевая модель")
    @story("Получение списка пользователей")
    @title("Пользователь без роли администратора не может получать список пользователей")
    @severity(severity_level.CRITICAL)
    def test_regular_user_cannot_list_users(self, setup_test_user: UserObject):
        """Обычный пользователь получает 403 при запросе списка пользователей.

        Отличие от 401: пользователь аутентифицирован (``refresh_api_token``), но его роли недостаточно — в ответе
        поле 'error', а не данные.
        """
        user = setup_test_user
        user.refresh_api_token()
        with step("Пользователь. API. Попытка получения списка пользователей"):
            response = user.api.list_users()
            SoftAssert(
                assert_status_code(expect=403, response=response, soft_assert=True),
                assert_condition(
                    condition="error" in response.get_json(),
                    allure_step_name="В ответе есть поле 'error'",
                    error_text="В ответе нет поля 'error'",
                    soft_assert=True
                ),
            )

    @feature("Возможности администратора", "Ролевая модель")
    @story("Удаление пользователей")
    @severity(severity_level.CRITICAL)
    @title("Пользователь без роли администратора не может удалять пользователей")
    def test_regular_user_cannot_delete_users(self, setup_test_user: UserObject, setup_test_user_2: UserObject):
        """Обычный пользователь получает 403 при удалении другого пользователя.

        Цель — чужая учётная запись: проверяется запрет на административное действие, а не на работу с собственной
        учётной записью.
        """
        user, victim_id = setup_test_user, setup_test_user_2.db_model.id
        user.refresh_api_token()
        with step("Пользователь. API. Попытка удаления пользователя"):
            response = user.api.delete_user(user_id=victim_id)
            SoftAssert(
                assert_status_code(expect=403, response=response, soft_assert=True),
                assert_condition(
                    condition="error" in response.get_json(),
                    allure_step_name="В ответе есть поле 'error'",
                    error_text="В ответе нет поля 'error'",
                    soft_assert=True
                ),
            )

    @feature("Возможности администратора", "Ролевая модель")
    @story("Удаление пользователей")
    @severity(severity_level.NORMAL)
    @title("Валидация роли при удалении пользователя срабатывает первее остальных ограничений")
    def test_regular_user_cannot_delete_self_even_as_target(self, setup_test_user: UserObject):
        """Обычный пользователь удаляет самого себя — и получает 403, а не другие коды.

        Ожидание фиксирует приоритет ограничений: сначала проверяется роль (403), и лишь затем правило «нельзя удалить
        самого себя» и существование цели. Поэтому ответ совпадает с удалением чужого пользователя — это и есть
        признак того, что ролевая проверка первая.
        """
        user = setup_test_user
        user.refresh_api_token()
        with step("Пользователь. API. Попытка удаления пользователя"):
            response = user.api.delete_user(user_id=user.db_model.id)
            SoftAssert(
                assert_status_code(expect=403, response=response, soft_assert=True),
                assert_condition(
                    condition="error" in response.get_json(),
                    allure_step_name="В ответе есть поле 'error'",
                    error_text="В ответе нет поля 'error'",
                    soft_assert=True
                ),
            )


@epic("API")
class TestAdminListUsers:
    """Проверки успешного получения списка пользователей администратором."""

    @feature("Возможности администратора")
    @story("Получение списка пользователей")
    @severity(severity_level.BLOCKER)
    @title("Администратор может получить список всех пользователей")
    def test_admin_sees_all_users(self, setup_admin_user: UserObject, setup_test_user: UserObject):
        """Администратор получает конверт со списком пользователей, каждая запись несёт роль.

        Ожидания: код 200; в конверте есть список 'users' и метаданные пагинации; в списке
        присутствуют и администратор, и обычный пользователь; у каждой записи есть поле
        'role'. Проверки soft — чтобы за один прогон увидеть все расхождения, а не только
        первое.
        """
        admin = setup_admin_user
        admin.refresh_api_token()
        with step("Администратор. API. Получение списка пользователей"):
            response = admin.api.list_users()
            assert_status_code(expect=200, response=response)
            data = response.get_json()
            users = data["users"]
            usernames = {entry["username"] for entry in users}
            SoftAssert(
                assert_condition(
                    condition=admin.db_model.username in usernames,
                    allure_step_name="Администратор 1 найден в полученном списке",
                    error_text="Администратор 1 не найден в полученном списке!",
                    soft_assert=True
                ),
                assert_condition(
                    condition=setup_test_user.db_model.username in usernames,
                    allure_step_name="Пользователь 1 найден в полученном списке",
                    error_text="Пользователь 1 не найден в полученном списке!",
                    soft_assert=True
                ),
                assert_condition(
                    condition=all("role" in entry for entry in users),
                    allure_step_name="Каждый пользователь в списке несёт роль",
                    error_text="Найдены пользователи без роли!",
                    soft_assert=True
                ),
                assert_condition(
                    condition=all(key in data for key in ("page", "pages", "total", "per_page")),
                    allure_step_name="Конверт несёт метаданные пагинации",
                    error_text="В конверте нет метаданных пагинации!",
                    soft_assert=True
                ),
            )


@epic("API")
@feature("Возможности администратора")
class TestAdminDeleteUser:
    """Проверки удаления пользователей администратором: успех, запреты и граничные случаи."""

    @story("Удаление пользователей")
    @severity(severity_level.BLOCKER)
    @title("Администратор может удалить обычного пользователя (с ролью user)")
    def test_admin_deletes_regular_user(
            self,
            setup_app: Flask,
            setup_admin_user: UserObject,
            setup_test_user: UserObject
    ):
        """Администратор удаляет обычного пользователя: 204, запись исчезает из БД.

        Проверка двух уровней: код ответа и прямое обращение к БД (``db.session.get`` в контексте приложения) —
        пользователь должен быть удалён на уровне хранилища, а не только скрыт от API.
        """
        admin, victim_id = setup_admin_user, setup_test_user.db_model.id
        admin.refresh_api_token()
        with step("Администратор. API. Удаление пользователя"):
            response = admin.api.delete_user(user_id=victim_id)
            assert_status_code(expect=204, response=response)
            with setup_app.app_context():
                assert_condition(
                    condition=db.session.get(User, victim_id) is None,
                    allure_step_name="DB. Удалённый пользователь отсутствует в БД",
                    error_text="DB. Удалённый пользователь найден в БД!"
                )

    @story("Удаление пользователей")
    @severity(severity_level.CRITICAL)
    @title("Администратор не может удалить самого себя")
    def test_admin_cannot_delete_self(self, setup_admin_user: UserObject):
        """Администратор не может удалить собственную учётную запись: 403 и поле 'error'.

        Запрет на самоудаление дополняет ролевую модель: при достаточной роли цель «сам себе» всё равно отклоняется.
        """
        admin = setup_admin_user
        admin.refresh_api_token()
        with step("Администратор. API. Попытка удаления самого себя"):
            response = admin.api.delete_user(user_id=admin.db_model.id)
            SoftAssert(
                assert_status_code(expect=403, response=response, soft_assert=True),
                assert_condition(
                    condition="error" in response.get_json(),
                    allure_step_name="В ответе есть поле 'error'",
                    error_text="В ответе нет поля 'error'",
                    soft_assert=True
                ),
            )

    @story("Удаление пользователей")
    @severity(severity_level.NORMAL)
    @title("Корректный код (404) при попытке удалить несуществующего пользователя")
    def test_delete_unknown_user_returns_404(self, setup_admin_user: UserObject):
        """Удаление несуществующего пользователя возвращает 404 и поле 'error'.

        Ожидание показывает, что «цель не найдена» различима от успешного удаления и от запрета доступа — три разных
        исхода с разными кодами.
        """
        admin = setup_admin_user
        admin.refresh_api_token()
        with step("Администратор. API. Попытка удалить несуществующего пользователя"):
            response = admin.api.delete_user(user_id=99999)
            SoftAssert(
                assert_status_code(expect=404, response=response, soft_assert=True),
                assert_condition(
                    condition="error" in response.get_json(),
                    allure_step_name="В ответе есть поле 'error'",
                    error_text="В ответе нет поля 'error'",
                    soft_assert=True
                ),
            )

    @story("Удаление пользователей")
    @severity(severity_level.CRITICAL)
    @title("У удалённого пользователя отзывается токен")
    def test_deleted_user_token_is_revoked(self, setup_admin_user: UserObject, setup_test_user: UserObject):
        """После удаления пользователя его прежний API-токен перестаёт работать (401).

        Сценарий из трёх действий: токен жертвы фиксируется до удаления, администратор удаляет пользователя, затем
        жертва обращается к API со старым токеном. Ожидание 401 подтверждает, что удаление отзывает существующие
        токены, а не только блокирует вход по паролю.
        """
        admin, victim = setup_admin_user, setup_test_user
        with step("Пользователь. API. Получение токена"):
            victim_id = victim.db_model.id
            victim.refresh_api_token()
        with step("Администратор. API. Получение токена"):
            admin.refresh_api_token()
        with step("Администратор. API. Удаление пользователя"):
            response = admin.api.delete_user(user_id=victim_id)
            assert_status_code(expect=204, response=response)
        with step("Удалённый Пользователь. API. Попытка получения списка пользователей"):
            response = victim.api.list_users()
            assert_status_code(expect=401, response=response)


@epic("API")
@feature("Возможности администратора", "Ролевая модель")
@story("Пагинация списка пользователей")
class TestAdminListUsersPagination:
    """Пагинация GET /api/users: конверт, санитизация параметров, границы."""

    @title("9 пользователей делятся на страницу из 5 и страницу из 4")
    @severity(severity_level.CRITICAL)
    def test_list_pagination_splits_users(self, setup_app_client: FlaskClient, setup_admin_user: UserObject):
        """Конверт отдаёт пользователей страницы и метаданные пагинации.

        Ожидание: пользователи упорядочены по возрастанию id — старейшие первыми,
        противоположно постам. Эталон порядка берётся полной выборкой, поэтому
        тест не зависит от состава фикстур: на стр. 1 — пять минимальных id,
        на стр. 2 — следующие четыре.
        """
        admin = setup_admin_user
        admin.refresh_api_token()
        api = Api(setup_app_client)
        with step("Администратор. API. Регистрация семи пользователей 01..07"):
            for number in range(1, 8):
                response = api.auth.register(username=f"user_{number:02d}", password="пароль-тест")
                assert_status_code(expect=201, response=response)

        with step("Администратор. API. Полная выборка как эталон порядка"):
            data = admin.api.list_users(per_page=50).get_json()
            all_ids = [entry["id"] for entry in data["users"]]
            assert_condition(
                condition=all_ids == sorted(all_ids),
                allure_step_name="Полная выборка упорядочена по возрастанию id",
                error_text="Полная выборка не упорядочена по возрастанию id!",
            )

        with step("Администратор. API. Открытие первой страницы"):
            data = admin.api.list_users(page=1, per_page=5).get_json()
            assert_condition(
                condition=[entry["id"] for entry in data["users"]] == all_ids[:5],
                allure_step_name="На первой странице пять минимальных id по возрастанию",
                error_text="Первая страница не содержит пять минимальных id в порядке возрастания!",
            )
            SoftAssert(
                assert_equal(expect=len(all_ids), actual=data["total"], name="Всего пользователей", soft_assert=True),
                assert_equal(expect=2, actual=data["pages"], name="Всего страниц", soft_assert=True),
                assert_equal(expect=5, actual=data["per_page"], name="Размер страницы", soft_assert=True),
                assert_equal(expect=1, actual=data["page"], name="Номер страницы", soft_assert=True),
            )
        with step("Администратор. API. Открытие второй страницы"):
            data = admin.api.list_users(page=2, per_page=5).get_json()
            assert_condition(
                condition=[entry["id"] for entry in data["users"]] == all_ids[5:10],
                allure_step_name="На второй странице следующие четыре id по возрастанию",
                error_text="Вторая страница не содержит следующие четыре id по возрастанию!",
            )

    @title("Мусорные page и per_page дают первую страницу с дефолтным размером")
    @severity(severity_level.MINOR)
    def test_users_params_sanitization(self, setup_app_client: FlaskClient, setup_admin_user: UserObject):
        """?page=0/-5/abc → страница 1; ?per_page=0/abc → дефолт 20; ?per_page=100 → срез до 50."""
        admin = setup_admin_user
        admin.refresh_api_token()
        with step("Администратор. API. Некорректные page и per_page"):
            for bad_page, bad_per_page in ((0, 0), (-5, None), (None, 0)):
                data = admin.api.list_users(page=bad_page, per_page=bad_per_page).get_json()
                assert_condition(
                    condition=data["page"] == 1 and data["per_page"] == 20,
                    allure_step_name=f"page={bad_page}, per_page={bad_per_page} санитизированы",
                    error_text=f"Санитизация сломалась: page={bad_page}, per_page={bad_per_page}!",
                )
        with step("Администратор. API. Мусорные значения"):
            data = admin.api.list_users(page="abc").get_json()
            assert_condition(
                condition=data["page"] == 1,
                allure_step_name="page=abc даёт первую страницу",
                error_text="page=abc сломал список пользователей!",
            )
            data = admin.api.list_users(per_page="abc").get_json()
            assert_condition(
                condition=data["per_page"] == 20,
                allure_step_name="per_page=abc даёт дефолт 20",
                error_text="per_page=abc сломал список пользователей!",
            )
        with step("Администратор. API. per_page больше лимита срезается до MAX_PER_PAGE"):
            data = admin.api.list_users(per_page=100).get_json()
            assert_condition(
                condition=data["per_page"] == 50,
                allure_step_name="per_page=100 отдаёт 50",
                error_text="per_page=100 не срезался до лимита!",
            )

    @title("Страница за пределами total отдаёт 200 и пустой users")
    @severity(severity_level.MINOR)
    def test_users_page_beyond_total(self, setup_app_client: FlaskClient, setup_admin_user: UserObject):
        """?page=999 → 200, пустой users, честные total/pages — сверка с эталоном полной выборки."""
        admin = setup_admin_user
        admin.refresh_api_token()
        with step("Администратор. API. Полная выборка как эталон метаданных"):
            full = admin.api.list_users().get_json()
        with step("Администратор. API. Открытие страницы 999"):
            response = admin.api.list_users(page=999)
            assert_status_code(expect=200, response=response)
            data = response.get_json()
            SoftAssert(
                assert_equal(expect=[], actual=data["users"], name="Пользователи страницы", soft_assert=True),
                assert_equal(expect=full["total"], actual=data["total"], name="Всего пользователей", soft_assert=True),
                assert_equal(expect=full["pages"], actual=data["pages"], name="Всего страниц", soft_assert=True),
            )
