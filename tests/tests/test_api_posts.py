"""Тесты API постов: создание, редактирование, удаление и защита чужих постов."""

from typing import Any

from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_equal, assert_status_code
from tests.tools.asserters.soft_asserters import SoftAssert
from tests.tools.clients.api import Api


@epic("API")
@feature("Посты")
@story("Контроль доступа")
class TestAccessControl:
    """Проверки того, что создание поста требует валидный токен."""

    @title("Получение ошибки при создании поста без токена")
    @severity(severity_level.CRITICAL)
    def test_create_requires_token(self, setup_app_client: FlaskClient):
        """Создание поста без токена отклоняется защитой эндпоинта.

        Ожидание: 401 — личность не установлена, токена нет вовсе.
        """
        api = Api(setup_app_client)
        with step("API. Попытка создания поста без токена"):
            response = api.posts.create(title="x", body="y")
            assert_status_code(expect=401, response=response)

    @title("Получение ошибки при создании поста с некорректным токеном")
    @severity(severity_level.CRITICAL)
    def test_invalid_token(self, setup_app_client: FlaskClient):
        """Токен в неверном формате отклоняется парсером JWT.

        Ожидание: 422 — токен передан, но разобрать его нельзя. Код отличен от 401:
        это не отсутствие личности, а нечитаемое предъявленное доказательство.
        """
        api = Api(setup_app_client)
        with step("API. Попытка создания поста с некорректным токеном"):
            response = api.posts.create(title="x", body="y", token="garbage.token.here")
            assert_status_code(expect=422, response=response)


@epic("API")
@feature("Посты")
@story("Создание поста")
class TestCreate:
    """Проверки создания поста: успех и ошибка валидации."""

    @title("Успешное создание поста пользователем с ролью user")
    @severity(severity_level.BLOCKER)
    def test_create_success(self, setup_test_user: UserObject):
        """Создание поста возвращает 201 и данные поста с автором.

        Ожидание: в теле — заголовок, совпадающий с отправленным, и
        ``author.id``, совпадающий с id пользователя из фикстуры.
        """
        user = setup_test_user
        user.refresh_api_token()
        with step("Пользователь. API. Создание поста"):
            response = user.api.create_post(title="Мой пост", body="Тестовое тело")
            assert_status_code(expect=201, response=response)
            data = response.get_json()
            assert_condition(
                condition=data["title"] == "Мой пост",
                allure_step_name="В ответе возвращен отправленный заголовок",
                error_text="Заголовок в ответе не совпадает с отправленным!",
            )
            assert_condition(
                condition=data["author"]["id"] == user.db_model.id,
                allure_step_name="В ответе указан автор — текущий пользователь",
                error_text="Автор поста в ответе не совпадает с текущим пользователем!",
            )

    @title("Получение ошибки при создании поста с пустым заголовком")
    @severity(severity_level.CRITICAL)
    def test_create_without_title(self, setup_test_user: UserObject):
        """Пустой заголовок отклоняется валидацией сервиса (BadRequestError).

        Ожидание: 400 и поле error в JSON.
        """
        user = setup_test_user
        user.refresh_api_token()
        with step("Пользователь. API. Попытка создания поста с пустым заголовком"):
            response = user.api.create_post(title="", body="Тестовое тело")
            assert_status_code(expect=400, response=response)
            assert_condition(
                condition="error" in response.get_json(),
                allure_step_name="В ответе присутствует поле error",
                error_text="Поле error отсутствует в JSON ответа!",
            )


@epic("API")
@feature("Посты")
@story("Редактирование и удаление поста")
class TestUpdateDelete:
    """Проверки редактирования и удаления собственного поста."""

    @title("Успешное редактирование собственного поста")
    @severity(severity_level.BLOCKER)
    def test_update_own_post(self, setup_test_user: UserObject):
        """Редактирование собственного поста возвращает 200 с новым заголовком.

        Ожидание: 200 и в теле — заголовок, совпадающий с отправленным при
        редактировании.
        """
        user = setup_test_user
        user.refresh_api_token()
        with step("Пользователь. API. Создание поста"):
            response = user.api.create_post(title="Начальный заголовок", body="Какое-то тело поста")
            assert_status_code(expect=201, response=response)
            post_id = response.get_json()["id"]

        with step("Пользователь. API. Редактирование собственного поста"):
            response = user.api.edit_post(post_id=post_id, new_title="Обновлённый заголовок")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=response.get_json()["title"] == "Обновлённый заголовок",
                allure_step_name="В ответе возвращен новый заголовок",
                error_text="Заголовок в ответе не совпадает с новым!",
            )

    @title("Успешное удаление собственного поста")
    @severity(severity_level.BLOCKER)
    def test_delete_own_post(self, setup_test_user: UserObject):
        """Удаление собственного поста возвращает 204 и пост исчезает из списка.

        Ожидание: 204 без тела; после удаления список постов пользователя пуст.
        Перед удалением — положительный контроль: пост присутствует в списке,
        иначе пустота после удаления не отличает «удалил» от «не создавал».
        """
        user = setup_test_user
        user.refresh_api_token()
        with step("Пользователь. API. Создание поста"):
            response = user.api.create_post()
            assert_status_code(expect=201, response=response)
            post_id = response.get_json()["id"]
            posts = user.api.get_posts_list().get_json()["posts"]
            assert_condition(
                condition=post_id in [post["id"] for post in posts],
                allure_step_name="Созданный пост присутствует в списке постов",
                error_text="Созданный пост не найден в списке постов!",
            )

        with step("Пользователь. API. Удаление собственного поста"):
            response = user.api.delete_post(post_id=post_id)
            assert_status_code(expect=204, response=response)
            assert_condition(
                condition=user.api.get_posts_list().get_json()["posts"] == [],
                allure_step_name="Список постов пуст после удаления",
                error_text="Список постов не пуст после удаления!",
            )


@epic("API")
@feature("Посты")
@story("Защита чужого поста")
class TestForeignPostProtection:
    """Проверки защиты чужих постов: редактировать и удалять их нельзя."""

    @title("Получение ошибки при редактировании чужого поста")
    @severity(severity_level.CRITICAL)
    def test_cannot_patch_foreign_post(self, setup_test_user_2: UserObject, setup_test_user_post: dict[str, Any]):
        """Редактирование чужого поста отклоняется (ForbiddenError).

        Ожидание: 403 — личность установлена, но действия на чужой пост
        у пользователя нет прав.
        """
        user_2 = setup_test_user_2
        user_1_post_id = setup_test_user_post["id"]
        user_2.refresh_api_token()
        with step("Пользователь 2. API. Попытка редактирования чужого поста"):
            response = user_2.api.edit_post(post_id=user_1_post_id, new_title="Новый заголовок")
            assert_status_code(expect=403, response=response)

    @title("Получение ошибки при удалении чужого поста")
    @severity(severity_level.CRITICAL)
    def test_cannot_delete_foreign_post(self, setup_test_user_2: UserObject, setup_test_user_post: dict[str, Any]):
        """Удаление чужого поста отклоняется (ForbiddenError), пост остаётся в списке.

        Ожидание: 403; после попытки чужой пост по-прежнему присутствует
        в списке постов — проверка по id, а не по количеству.
        """
        user_2, user_1_post_id = setup_test_user_2, setup_test_user_post["id"]
        user_2.refresh_api_token()
        with step("Пользователь 2. API. Попытка удаления чужого поста"):
            response = user_2.api.delete_post(post_id=user_1_post_id)
            assert_status_code(expect=403, response=response)
        with step("Пользователь 2. API. Получение списка постов"):
            posts = user_2.api.get_posts_list().get_json()["posts"]
            assert_condition(
                condition=user_1_post_id in [post["id"] for post in posts],
                allure_step_name="Чужой пост остался в списке постов",
                error_text="Чужой пост исчез из списка постов!",
            )


@epic("API")
@feature("Посты")
@story("Пагинация списка")
class TestListPagination:
    """Пагинация GET /api/posts: конверт, санитизация параметров, границы."""

    @title("7 постов делятся на страницу из 5 и страницу из 2 в конверте")
    @severity(severity_level.CRITICAL)
    def test_list_pagination_splits_feed(self, setup_test_user: UserObject):
        """Конверт отдаёт посты страницы и метаданные пагинации.

        Ожидание: на стр. 1 — 5 постов (07..03), на стр. 2 — 2 поста (02, 01);
        total=7, pages=2, per_page=5.
        """
        user = setup_test_user
        user.refresh_api_token()
        with step("Пользователь. API. Создание 7 постов с нумерацией 01..07"):
            for number in range(1, 8):
                response = user.api.create_post(title=f"Пост {number:02d}", body=f"Тело поста {number:02d}")
                assert_status_code(expect=201, response=response)

        with step("Пользователь. API. Открытие первой страницы"):
            data = user.api.get_posts_list(page=1).get_json()
            assert_condition(
                condition=[post["title"] for post in data["posts"]] == [
                    f"Пост {number:02d}" for number in range(7, 2, -1)
                ],
                allure_step_name="На первой странице пять новейших постов в порядке убывания",
                error_text="Первая страница содержит не пять новейших постов или в неверном порядке!",
            )
            SoftAssert(
                assert_equal(expect=7, actual=data["total"], name="Всего постов", soft_assert=True),
                assert_equal(expect=2, actual=data["pages"], name="Всего страниц", soft_assert=True),
                assert_equal(expect=5, actual=data["per_page"], name="Размер страницы", soft_assert=True),
                assert_equal(expect=1, actual=data["page"], name="Номер страницы", soft_assert=True),
            )
        with step("Пользователь. API. Открытие второй страницы"):
            data = user.api.get_posts_list(page=2).get_json()
            assert_condition(
                condition=[post["title"] for post in data["posts"]] == ["Пост 02", "Пост 01"],
                allure_step_name="На второй странице два старейших поста в порядке убывания",
                error_text="Вторая страница не содержит ровно посты 02 и 01 в порядке убывания!",
            )

    @title("Мусорные page и per_page дают первую страницу с дефолтным размером")
    @severity(severity_level.MINOR)
    def test_list_params_sanitization(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """?page=0/-5/abc → страница 1; ?per_page=0/abc → дефолт 5; ?per_page=100 → срез до 50."""
        user = setup_test_user
        user.refresh_api_token()
        with step("Пользователь. API. Создание поста"):
            response = user.api.create_post(title="Пост для санитизации", body="Тело")
            assert_status_code(expect=201, response=response)

        api = Api(setup_app_client)
        with step("Пользователь. API. Некорректные page и per_page"):
            for bad_page, bad_per_page in ((0, 0), (-5, None), (None, 0)):
                data = api.posts.list(page=bad_page, per_page=bad_per_page).get_json()
                assert_condition(
                    condition=data["page"] == 1 and data["per_page"] == 5,
                    allure_step_name=f"page={bad_page}, per_page={bad_per_page} санитизированы",
                    error_text=f"Санитизация сломалась: page={bad_page}, per_page={bad_per_page}!",
                )
        with step("Пользователь. API. Мусорные значения через сырой клиент"):
            data = api.posts.list(page="abc").get_json()
            assert_condition(
                condition=data["page"] == 1,
                allure_step_name="page=abc даёт первую страницу",
                error_text="page=abc сломал список!",
            )
            data = api.posts.list(per_page="abc").get_json()
            assert_condition(
                condition=data["per_page"] == 5,
                allure_step_name="per_page=abc даёт дефолт",
                error_text="per_page=abc сломал список!",
            )
        with step("Пользователь. API. per_page больше лимита срезается до MAX_PER_PAGE"):
            data = api.posts.list(per_page=100).get_json()
            assert_condition(
                condition=data["per_page"] == 50,
                allure_step_name="per_page=100 отдаёт 50",
                error_text="per_page=100 не срезался до лимита!",
            )

    @title("Страница за пределами total отдаёт 200 и пустой posts")
    @severity(severity_level.MINOR)
    def test_list_page_beyond_total(self, setup_test_user: UserObject):
        """?page=999 → 200, пустой posts, честные total/pages."""
        user = setup_test_user
        user.refresh_api_token()
        with step("Пользователь. API. Создание поста"):
            response = user.api.create_post(title="Пост для границ", body="Тело")
            assert_status_code(expect=201, response=response)
        with step("Пользователь. API. Открытие страницы 999"):
            response = user.api.get_posts_list(page=999)
            assert_status_code(expect=200, response=response)
            data = response.get_json()
            SoftAssert(
                assert_equal(expect=[], actual=data["posts"], name="Посты страницы", soft_assert=True),
                assert_equal(expect=1, actual=data["total"], name="Всего постов", soft_assert=True),
                assert_equal(expect=1, actual=data["pages"], name="Всего страниц", soft_assert=True),
            )
