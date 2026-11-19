"""Тесты API комментариев: список, создание, редактирование, удаление и контроль доступа."""
from typing import Any

from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_equal, assert_status_code
from tests.tools.clients.api import Api


@epic("API")
@feature("Комментарии")
@story("Контроль доступа")
class TestAccessControl:
    """Проверки того, что операции с комментариями требуют валидный токен."""

    @title("Получение ошибки при создании комментария без токена")
    @severity(severity_level.CRITICAL)
    def test_create_requires_token(self, setup_app_client: FlaskClient, setup_test_user_post: dict[str, Any]):
        """Создание комментария без токена отклоняется защитой эндпоинта.

        Ожидание: 401 — личность не установлена, токена нет вовсе.
        """
        api = Api(setup_app_client)
        with step("API. Попытка создания комментария без токена"):
            response = api.comments.create(post_id=setup_test_user_post["id"], body="Текст")
            assert_status_code(expect=401, response=response)

    @title("Получение ошибки при редактировании комментария без токена")
    @severity(severity_level.CRITICAL)
    def test_update_requires_token(self, setup_app_client: FlaskClient, setup_test_user_post_comment: dict[str, Any]):
        """PATCH без токена отклоняется: 401."""
        comment, api = setup_test_user_post_comment, Api(setup_app_client)
        with step("API. Попытка редактирования комментария без токена"):
            response = api.comments.update(comment_id=comment["id"], body="Новое тело")
            assert_status_code(expect=401, response=response)

    @title("Получение ошибки при удалении комментария без токена")
    @severity(severity_level.CRITICAL)
    def test_delete_requires_token(self, setup_app_client: FlaskClient, setup_test_user_post_comment: dict[str, Any]):
        """DELETE без токена отклоняется: 401."""
        comment, api = setup_test_user_post_comment, Api(setup_app_client)
        with step("API. Попытка удаления комментария без токена"):
            response = api.comments.delete(comment_id=comment["id"])
            assert_status_code(expect=401, response=response)


@epic("API")
@feature("Комментарии")
@story("Создание комментария")
class TestCreate:
    """Проверки создания комментария."""

    @title("Успешное создание комментария")
    @severity(severity_level.BLOCKER)
    def test_create_success(self, setup_test_user: UserObject, setup_test_user_post: dict[str, Any]):
        """Создание возвращает 201 с телом и автором.

        Ожидание: в теле — отправленный текст и ``author.id`` автора комментария.
        """
        user, post, expected_body = setup_test_user, setup_test_user_post, "Первый комментарий"
        with step("Пользователь. API. Создание комментария"):
            response = user.api.create_comment(post_id=post["id"], body=expected_body)
            assert_status_code(expect=201, response=response)
            data = response.get_json()
            assert_equal(expect=expected_body, actual=data["body"], name="Тело комментария")
            assert_equal(expect=user.db_model.id, actual=data["author"]["id"], name="Автор комментария")

    @title("Получение ошибки при создании комментария с пустым телом")
    @severity(severity_level.CRITICAL)
    def test_create_empty_body(self, setup_test_user: UserObject, setup_test_user_post: dict[str, Any]):
        """Тело из одних пробелов отклоняется валидацией сервиса: 400."""
        post, user = setup_test_user_post, setup_test_user
        with step("Пользователь. API. Попытка создания комментария с пустым телом"):
            response = user.api.create_comment(post_id=post["id"], body="   ")
            assert_status_code(expect=400, response=response)

    @title("Получение ошибки при создании комментария к несуществующему посту")
    @severity(severity_level.CRITICAL)
    def test_create_unknown_post(self, setup_test_user: UserObject):
        """Комментарий к несуществующему посту даёт 404."""
        user = setup_test_user
        with step("Пользователь. API. Попытка создания комментария к несуществующему посту"):
            response = user.api.create_comment(post_id=10 ** 9, body="Текст")
            assert_status_code(expect=404, response=response)


@epic("API")
@feature("Комментарии")
@story("Получение списка комментариев")
class TestList:
    """Проверки публичного списка комментариев."""

    @title("Публичное получение списка комментариев, новые сверху")
    @severity(severity_level.BLOCKER)
    def test_list_newest_first(
            self,
            setup_app_client: FlaskClient,
            setup_test_user_post: dict[str, Any],
            setup_test_user_post_comment: dict[str, Any],
            setup_foreign_comment: dict[str, Any],
    ):
        """Список отдаётся без токена в конверте; первый — созданный последним."""
        api = Api(setup_app_client)
        comment_2, post = setup_foreign_comment, setup_test_user_post
        with step("API. Получение списка комментариев"):
            response = api.comments.list_for_post(post_id=post["id"])
            assert_status_code(expect=200, response=response)
            data = response.get_json()
            assert_equal(expect=2, actual=data["total"], name="Количество комментариев")
            assert_equal(expect=comment_2["id"], actual=data["comments"][0]["id"], name="ID первого в списке")

    @title("Получение ошибки при запросе комментариев несуществующего поста")
    @severity(severity_level.CRITICAL)
    def test_list_unknown_post(self, setup_app_client: FlaskClient):
        """Список для несуществующего поста даёт 404, а не пустой 200."""
        api = Api(setup_app_client)
        with step("API. Попытка получения комментариев несуществующего поста"):
            response = api.comments.list_for_post(post_id=10 ** 9)
            assert_status_code(expect=404, response=response)


@epic("API")
@feature("Комментарии")
@story("Редактирование комментария")
class TestUpdate:
    """Проверки редактирования: права, частичное обновление, валидация."""

    @title("Успешное редактирование своего комментария")
    @severity(severity_level.BLOCKER)
    def test_update_own(self, setup_test_user: UserObject, setup_test_user_post_comment: dict[str, Any]):
        """Автор обновляет текст: 200, новое тело в ответе."""
        comment, user, expected_body = setup_test_user_post_comment, setup_test_user, "Обновлённый текст"
        with step("Пользователь. API. Редактирование своего комментария"):
            response = user.api.edit_comment(comment_id=comment["id"], new_body=expected_body)
            assert_status_code(expect=200, response=response)
            assert_equal(expect=expected_body, actual=response.get_json()["body"], name="Новый текст комментария")

    @title("Получение ошибки при редактировании чужого комментария")
    @severity(severity_level.CRITICAL)
    def test_update_foreign(self, setup_test_user_2: UserObject, setup_test_user_post_comment: dict[str, Any]):
        """Чужой пользователь редактировать не может: 403."""
        user, comment = setup_test_user_2, setup_test_user_post_comment
        with step("Пользователь 2. API. Попытка редактирования чужого комментария"):
            response = user.api.edit_comment(comment_id=comment["id"], new_body="Взлом")
            assert_status_code(expect=403, response=response)

    @title("Частичное обновление: запрос без ключа body не меняет текст")
    @severity(severity_level.CRITICAL)
    def test_update_without_body_key(self, setup_test_user: UserObject, setup_test_user_post_comment: dict[str, Any]):
        """PATCH без ключа 'body' оставляет текст как был: 200."""
        user, comment = setup_test_user, setup_test_user_post_comment
        with step("Пользователь. API. PATCH без ключа body"):
            response = user.api.edit_comment(comment_id=comment["id"])
            assert_status_code(expect=200, response=response)
            assert_equal(expect=comment["body"], actual=response.get_json()["body"], name="Текст комментария")

    @title("Получение ошибки при редактировании с пустым телом")
    @severity(severity_level.CRITICAL)
    def test_update_empty_body(self, setup_test_user: UserObject, setup_test_user_post_comment: dict[str, Any]):
        """Явно пустое тело отклоняется: 400."""
        user, comment = setup_test_user, setup_test_user_post_comment
        with step("Пользователь. API. PATCH с пустым телом"):
            response = user.api.edit_comment(comment_id=comment["id"], new_body="   ")
            assert_status_code(expect=400, response=response)

    @title("Получение ошибки при редактировании несуществующего комментария")
    @severity(severity_level.CRITICAL)
    def test_update_unknown_comment(self, setup_test_user: UserObject):
        """Несуществующий комментарий даёт 404."""
        user = setup_test_user
        with step("Пользователь. API. PATCH несуществующего комментария"):
            response = user.api.edit_comment(comment_id=10 ** 9, new_body="Текст")
            assert_status_code(expect=404, response=response)


@epic("API")
@feature("Комментарии")
@story("Удаление комментария")
class TestDelete:
    """Проверки удаления: права и эффект."""

    @title("Успешное удаление своего комментария")
    @severity(severity_level.BLOCKER)
    def test_delete_own(
            self,
            setup_test_user: UserObject,
            setup_test_user_post: dict[str, Any],
            setup_test_user_post_comment: dict[str, Any],
    ):
        """Автор удаляет комментарий: 204, список пустеет."""
        comment, post = setup_test_user_post_comment, setup_test_user_post
        user = setup_test_user
        with step("Пользователь. API. Удаление своего комментария"):
            response = user.api.delete_comment(comment_id=comment["id"])
            assert_status_code(expect=204, response=response)
        with step("Пользователь. API. Проверка пустого списка"):
            response = user.api.get_comments_list(post_id=post["id"])
            assert_status_code(expect=200, response=response)
            data = response.get_json()
            assert_equal(expect=0, actual=data["total"], name="Количество комментариев после удаления")

    @title("Получение ошибки при удалении чужого комментария")
    @severity(severity_level.CRITICAL)
    def test_delete_foreign(self, setup_test_user_2: UserObject, setup_test_user_post_comment: dict[str, Any]):
        """Чужой пользователь удалять не может: 403."""
        user, comment = setup_test_user_2, setup_test_user_post_comment
        with step("Пользователь 2. API. Попытка удаления чужого комментария"):
            response = user.api.delete_comment(comment_id=comment["id"])
            assert_status_code(expect=403, response=response)

    @title("Получение ошибки при удалении несуществующего комментария")
    @severity(severity_level.CRITICAL)
    def test_delete_unknown_comment(self, setup_test_user: UserObject):
        """Несуществующий комментарий даёт 404."""
        user = setup_test_user
        with step("Пользователь. API. DELETE несуществующего комментария"):
            response = user.api.delete_comment(comment_id=10 ** 9)
            assert_status_code(expect=404, response=response)


@epic("API")
@feature("Комментарии")
@story("Пагинация списка")
class TestListPagination:
    """Пагинация публичного списка комментариев: разбивка, санитизация, выход за пределы."""

    @title("Одиннадцать комментариев делятся на две страницы, новые сверху")
    @severity(severity_level.CRITICAL)
    def test_list_pagination_splits_comments(
            self, setup_test_user: UserObject, setup_test_user_post: dict[str, Any],
    ):
        """Страница 1 — десять новейших, страница 2 — старейший; конверт согласован."""
        user, post = setup_test_user, setup_test_user_post
        markers = []
        with step("Пользователь. API. Создание одиннадцати комментариев с маркерами"):
            for i in range(1, 12):
                marker = f"token-{i}"
                markers.append(marker)
                response = user.api.create_comment(post_id=post["id"], body=f"{marker} текст")
                assert_status_code(expect=201, response=response)
        with step("API. Первая страница комментариев"):
            page1 = user.api.get_comments_list(post_id=post["id"], page=1)
            assert_status_code(expect=200, response=page1)
            data1 = page1.get_json()
        with step("API. Вторая страница комментариев"):
            page2 = user.api.get_comments_list(post_id=post["id"], page=2)
            assert_status_code(expect=200, response=page2)
            data2 = page2.get_json()
        with step("Проверка конверта и разбивки"):
            assert_equal(expect=11, actual=data1["total"], name="Всего комментариев")
            assert_equal(expect=2, actual=data1["pages"], name="Всего страниц")
            assert_equal(expect=10, actual=data1["per_page"], name="Размер страницы")
            assert_equal(expect=1, actual=data1["page"], name="Номер первой страницы")
            assert_equal(
                expect=10, actual=len(data1["comments"]), name="Количество на первой странице",
            )
            assert_equal(expect=2, actual=data2["page"], name="Номер второй страницы")
            assert_equal(expect=1, actual=len(data2["comments"]), name="Количество на второй странице")
            first_page_tokens = {c["body"].split(" ")[0] for c in data1["comments"]}
            assert_equal(
                expect={f"token-{i}" for i in range(2, 12)},
                actual=first_page_tokens,
                name="Первая страница — десять новейших",
            )
            assert_equal(
                expect="token-1",
                actual=data2["comments"][0]["body"].split(" ")[0],
                name="Вторая страница — старейший",
            )

    @title("Санитизация page и per_page: мусор и границы дают каноничные значения")
    @severity(severity_level.CRITICAL)
    def test_list_params_sanitization(self, setup_test_user: UserObject, setup_test_user_post: dict[str, Any]):
        """page=abc/-3 → 1; per_page=garbage/-3 → 10; per_page=100 → 50 (MAX_PER_PAGE)."""
        user, post = setup_test_user, setup_test_user_post
        with step("Пользователь. API. Создание трёх комментариев"):
            for i in range(3):
                response = user.api.create_comment(post_id=post["id"], body=f"comment-{i}")
                assert_status_code(expect=201, response=response)
        with step("API. Мусорный page"):
            garbage_page = user.api.get_comments_list(post_id=post["id"], page="abc")
        with step("API. Отрицательный page"):
            negative_page = user.api.get_comments_list(post_id=post["id"], page=-3)
        with step("API. Мусорный per_page"):
            garbage_per_page = user.api.get_comments_list(post_id=post["id"], per_page="garbage")
        with step("API. Отрицательный per_page"):
            negative_per_page = user.api.get_comments_list(post_id=post["id"], per_page=-3)
        with step("API. per_page выше потолка"):
            oversized = user.api.get_comments_list(post_id=post["id"], per_page=100)
        with step("Проверка санитизации"):
            for name, response in (
                    ("мусорный page", garbage_page), ("отрицательный page", negative_page),
                    ("мусорный per_page", garbage_per_page), ("отрицательный per_page", negative_per_page),
            ):
                assert_status_code(expect=200, response=response)
                data = response.get_json()
                assert_equal(expect=1, actual=data["page"], name=f"{name}: страница сброшена в 1")
                assert_equal(expect=10, actual=data["per_page"], name=f"{name}: размер страницы каноничный")
                assert_equal(expect=3, actual=data["total"], name=f"{name}: все комментарии на месте")
        with step("Проверка потолка per_page"):
            data = oversized.get_json()
            assert_equal(expect=50, actual=data["per_page"], name="per_page выше потолка обрезан до MAX_PER_PAGE")
            assert_equal(expect=1, actual=data["page"], name="Страница при потолке не искажена")

    @title("Страница за пределами total — пустой список без ошибки")
    @severity(severity_level.CRITICAL)
    def test_list_page_beyond_total(self, setup_test_user: UserObject, setup_test_user_post: dict[str, Any]):
        """page=5 при одной странице: 200, пустой список, метаданные согласованы."""
        user, post = setup_test_user, setup_test_user_post
        with step("Пользователь. API. Создание комментария"):
            response = user.api.create_comment(post_id=post["id"], body="Единственный")
            assert_status_code(expect=201, response=response)
        with step("API. Страница за пределами total"):
            response = user.api.get_comments_list(post_id=post["id"], page=5)
            assert_status_code(expect=200, response=response)
            data = response.get_json()
        with step("Проверка пустой страницы"):
            assert_equal(expect=[], actual=data["comments"], name="Список пуст")
            assert_equal(expect=1, actual=data["total"], name="Total не искажён")
            assert_equal(expect=1, actual=data["pages"], name="Pages не искажён")
