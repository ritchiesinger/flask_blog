"""WEB-тесты комментариев: просмотр, создание, редактирование, удаление."""

from typing import Any

from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_status_code
from tests.tools.clients.web_client import WebClient

FLASH_EMPTY = "Текст комментария не может быть пустым."
FLASH_SUCCESS = "Комментарий добавлен!"
NAV_MARK = "Постраничная навигация"


@epic("WEB")
@feature("Комментарии")
@story("Просмотр поста")
class TestView:
    """Проверки отображения комментариев на странице поста."""

    @title("Гость видит комментарии и призыв войти, но не видит формы")
    @severity(severity_level.CRITICAL)
    def test_guest_view(
            self,
            setup_app_client: FlaskClient,
            setup_test_user_post: dict[str, Any],
            setup_test_user_post_comment: dict[str, Any],
    ):
        """Публичная страница показывает список, без формы и кнопок правки."""
        comment, post, web = setup_test_user_post_comment, setup_test_user_post, WebClient(setup_app_client)
        with step("WEB. Открытие страницы поста гостем"):
            response = web.comments.view_post(post_id=post["id"])
            assert_status_code(expect=200, response=response)
            page = response.get_data(as_text=True)
            assert_condition(
                condition=comment["body"] in page,
                allure_step_name="Текст комментария отображается гостю",
                error_text="Комментарий не найден на публичной странице поста!",
            )
            assert_condition(
                condition="Войдите" in page,
                allure_step_name="Гостю показан призыв войти",
                error_text="Нет приглашения войти для гостя вместо формы комментария!",
            )
            assert_condition(
                condition="Ваш комментарий" not in page,
                allure_step_name="Форма комментария не отображается гостю",
                error_text="Форма комментария отображается!",
            )

    @title("Авторизованный пользователь видит форму комментария")
    @severity(severity_level.CRITICAL)
    def test_user_view(self, setup_test_user: UserObject, setup_test_user_post: dict[str, Any]):
        """После логина на странице есть форма отправки."""
        user, post = setup_test_user, setup_test_user_post
        with step("Пользователь. WEB. Авторизация"):
            response = user.web.auth.login(username=user.db_model.username, password=user.password)
            assert_status_code(expect=302, response=response)
        with step("Пользователь. WEB. Открытие страницы поста"):
            response = user.web.comments.view_post(post_id=post["id"])
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="Написать комментарий..." in response.get_data(as_text=True),
                allure_step_name="Форма комментария отображается",
                error_text="Форма комментария не видна авторизованному пользователю!",
            )

    @title("Комментарий отображается с автором и без markdown-разметки")
    @severity(severity_level.CRITICAL)
    def test_comment_plain_text(self, setup_test_user: UserObject, setup_test_user_post: dict[str, Any]):
        """Markdown-синтаксис в комментарии остаётся видимым текстом, а не превращается в разметку."""
        user, post, body = setup_test_user, setup_test_user_post, "**Жирный** markdown"
        with step("Пользователь. WEB. Авторизация"):
            response = user.web.auth.login(username=user.db_model.username, password=user.password)
            assert_status_code(expect=302, response=response)
        with step("Пользователь. WEB. Создание комментария с markdown-синтаксисом"):
            assert_status_code(expect=302, response=user.web.comments.create_comment(post_id=post["id"], body=body))
        with step("Пользователь. WEB. Проверка страницы поста"):
            page = user.web.comments.view_post(post_id=post["id"]).get_data(as_text=True)
            assert_condition(
                condition=body in page,
                allure_step_name="Синтаксис markdown виден как текст",
                error_text="Комментарий отрендерен markdown-ом — должно быть экранирование!",
            )


@epic("WEB")
@feature("Комментарии")
@story("Создание комментария")
class TestCreate:
    """Проверки создания комментария через web-форму."""

    @title("Гость при попытке создать комментарий перенаправляется на логин")
    @severity(severity_level.CRITICAL)
    def test_guest_redirect(self, setup_app_client: FlaskClient, setup_test_user_post: dict[str, Any]):
        """POST без сессии перехватывает login_required: 302."""
        post, web = setup_test_user_post, WebClient(setup_app_client)
        with step("WEB. Попытка создания комментария"):
            response = web.comments.create_comment(post_id=post["id"], body="Текст")
            assert_status_code(expect=302, response=response)

    @title("Пустой комментарий отклоняется с flash-сообщением")
    @severity(severity_level.CRITICAL)
    def test_empty_body_flash(self, setup_test_user: UserObject, setup_test_user_post: dict[str, Any]):
        """Тело из одних пробелов: 200, flash с ошибкой, без редиректа."""
        user, post = setup_test_user, setup_test_user_post
        with step("Пользователь. WEB. Авторизация"):
            response = user.web.auth.login(username=user.db_model.username, password=user.password)
            assert_status_code(expect=302, response=response)
        with step("Пользователь. WEB. Отправка пустого комментария"):
            response = user.web.comments.create_comment(post_id=post["id"], body="   ")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=FLASH_EMPTY in response.get_data(as_text=True),
                allure_step_name="Flash-сообщение об ошибке показано",
                error_text="Пустой комментарий прошёл без сообщения об ошибке!",
            )

    @title("Успешное создание: редирект на страницу поста и комментарий в списке")
    @severity(severity_level.BLOCKER)
    def test_create_success(self, setup_test_user: UserObject, setup_test_user_post: dict[str, Any]):
        """Создание даёт 302 и flash успеха; комментарий виден на странице."""
        user, post = setup_test_user, setup_test_user_post
        with step("Пользователь. WEB. Авторизация"):
            response = user.web.auth.login(username=user.db_model.username, password=user.password)
            assert_status_code(expect=302, response=response)
        with step("Пользователь. WEB. Создание комментария"):
            response = user.web.comments.create_comment(post_id=post["id"], body="Мой первый комментарий")
            assert_status_code(expect=302, response=response)
        with step("Пользователь. WEB. Открытие страницы поста"):
            page = user.web.comments.view_post(post_id=post["id"]).get_data(as_text=True)
            assert_condition(
                condition="Мой первый комментарий" in page and FLASH_SUCCESS in page,
                allure_step_name="Комментарий и flash успеха отображаются",
                error_text="Комментарий не появился на странице поста!",
            )


@epic("WEB")
@feature("Комментарии")
@story("Редактирование комментария")
class TestUpdate:
    """Проверки редактирования: форма, валидация, права."""

    @title("Автор видит форму редактирования со своим текстом")
    @severity(severity_level.BLOCKER)
    def test_update_form(self, setup_test_user: UserObject, setup_test_user_post_comment: dict[str, Any]):
        """GET формы даёт 200 и текущий текст комментария."""
        user, comment = setup_test_user, setup_test_user_post_comment
        with step("Пользователь. WEB. Авторизация"):
            response = user.web.auth.login(username=user.db_model.username, password=user.password)
            assert_status_code(expect=302, response=response)
        with step("Пользователь. WEB. Открытие формы редактирования"):
            response = user.web.comments.update_comment_form(comment_id=comment["id"])
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=comment["body"] in response.get_data(as_text=True),
                allure_step_name="Текущий текст в форме",
                error_text="Текст комментария не найден в форме редактирования!",
            )

    @title("Пустое тело при редактировании отклоняется с flash-сообщением")
    @severity(severity_level.CRITICAL)
    def test_update_empty_flash(self, setup_test_user: UserObject, setup_test_user_post_comment: dict[str, Any]):
        """Отправка пустой формы редактирования: 200 с flash, редиректа нет."""
        user, comment = setup_test_user, setup_test_user_post_comment
        with step("Пользователь. WEB. Авторизация"):
            response = user.web.auth.login(username=user.db_model.username, password=user.password)
            assert_status_code(expect=302, response=response)
        with step("Пользователь. WEB. Отправка пустой формы редактирования"):
            response = user.web.comments.update_comment(comment_id=comment["id"], body="")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=FLASH_EMPTY in response.get_data(as_text=True),
                allure_step_name="Flash-сообщение об ошибке показано",
                error_text="Пустое обновление прошло без ошибки!",
            )

    @title("Успешное редактирование возвращает на страницу поста с новым текстом")
    @severity(severity_level.BLOCKER)
    def test_update_success(
            self,
            setup_test_user: UserObject,
            setup_test_user_post: dict[str, Any],
            setup_test_user_post_comment: dict[str, Any],
    ):
        """POST с новым телом: 302, на странице новый текст."""
        user, comment, post = setup_test_user, setup_test_user_post_comment, setup_test_user_post
        with step("Пользователь. WEB. Авторизация"):
            response = user.web.auth.login(username=user.db_model.username, password=user.password)
            assert_status_code(expect=302, response=response)
        with step("Пользователь. WEB. Редактирование комментария"):
            response = user.web.comments.update_comment(comment_id=comment["id"], body="Обновлённое тело")
            assert_status_code(expect=302, response=response)
        with step("Пользователь. WEB. Проверка страницы поста"):
            page = user.web.comments.view_post(post_id=post["id"]).get_data(as_text=True)
            assert_condition(
                condition="Обновлённое тело" in page,
                allure_step_name="Новый текст отображается",
                error_text="Обновлённый текст не появился на странице!",
            )

    @title("Чужой комментарий нельзя отредактировать: 403")
    @severity(severity_level.CRITICAL)
    def test_update_foreign(self, setup_test_user_2: UserObject, setup_test_user_post_comment: dict[str, Any]):
        """Второй пользователь получает 403 и на GET формы, и на POST."""
        user2, comment = setup_test_user_2, setup_test_user_post_comment
        with step("Пользователь 2. WEB. Авторизация"):
            response = user2.web.auth.login(username=user2.db_model.username, password=user2.password)
            assert_status_code(expect=302, response=response)
        with step("Пользователь 2. WEB. GET формы чужого комментария"):
            assert_status_code(expect=403, response=user2.web.comments.update_comment_form(comment_id=comment["id"]))
        with step("Пользователь 2. WEB. POST формы чужого комментария"):
            response = user2.web.comments.update_comment(comment_id=comment["id"], body="Взлом")
            assert_status_code(expect=403, response=response)

    @title("Редактирование несуществующего комментария даёт 404")
    @severity(severity_level.CRITICAL)
    def test_update_unknown(self, setup_test_user: UserObject):
        """Несуществующий комментарий: 404."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            response = user.web.auth.login(username=user.db_model.username, password=user.password)
            assert_status_code(expect=302, response=response)
        with step("Пользователь. WEB. GET формы несуществующего комментария"):
            assert_status_code(expect=404, response=user.web.comments.update_comment_form(comment_id=10 ** 9))
        with step("Пользователь. WEB. POST несуществующего комментария"):
            assert_status_code(expect=404, response=user.web.comments.update_comment(comment_id=10 ** 9, body="Текст"))


@epic("WEB")
@feature("Комментарии")
@story("Удаление комментария")
class TestDelete:
    """Проверки удаления: успех, права, 404."""

    @title("Автор удаляет свой комментарий")
    @severity(severity_level.BLOCKER)
    def test_delete_own(
            self,
            setup_test_user: UserObject,
            setup_test_user_post: dict[str, Any],
            setup_test_user_post_comment: dict[str, Any],
    ):
        """Удаление: 302, комментарий исчез со страницы."""
        user, comment, post = setup_test_user, setup_test_user_post_comment, setup_test_user_post
        with step("Пользователь. WEB. Авторизация"):
            response = user.web.auth.login(username=user.db_model.username, password=user.password)
            assert_status_code(expect=302, response=response)
        with step("Пользователь. WEB. Удаление комментария"):
            response = user.web.comments.delete_comment(comment_id=comment["id"])
            assert_status_code(expect=302, response=response)
        with step("Пользователь. WEB. Проверка страницы поста"):
            page = user.web.comments.view_post(post_id=post["id"]).get_data(as_text=True)
            assert_condition(
                condition=comment["body"] not in page,
                allure_step_name="Комментарий исчез со страницы",
                error_text="Удалённый комментарий всё ещё отображается!",
            )

    @title("Чужой комментарий нельзя удалить: 403")
    @severity(severity_level.CRITICAL)
    def test_delete_foreign(self, setup_test_user_2: UserObject, setup_test_user_post_comment: dict[str, Any]):
        """Второй пользователь получает 403."""
        user2, comment = setup_test_user_2, setup_test_user_post_comment
        with step("Пользователь 2. WEB. Авторизация"):
            response = user2.web.auth.login(username=user2.db_model.username, password=user2.password)
            assert_status_code(expect=302, response=response)
        with step("Пользователь 2. WEB. Удаление чужого комментария"):
            assert_status_code(expect=403, response=user2.web.comments.delete_comment(comment_id=comment["id"]))

    @title("Удаление несуществующего комментария даёт 404")
    @severity(severity_level.CRITICAL)
    def test_delete_unknown(self, setup_test_user: UserObject):
        """Несуществующий комментарий: 404."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            response = user.web.auth.login(username=user.db_model.username, password=user.password)
            assert_status_code(expect=302, response=response)
        with step("Пользователь. WEB. Удаление несуществующего комментария"):
            assert_status_code(expect=404, response=user.web.comments.delete_comment(comment_id=10 ** 9))


@epic("WEB")
@feature("Комментарии")
@story("Пагинация комментариев поста")
class TestCommentsPagination:
    """?page листает комментарии поста: разбивка, санитизация, выход за пределы."""

    @title("Одиннадцать комментариев делятся на две страницы, новые сверху")
    @severity(severity_level.CRITICAL)
    def test_pagination_splits_comments(self, setup_test_user, setup_test_user_post):
        """Страница 1 — десять новейших, страница 2 — старейший; навигация на обеих."""
        user, post = setup_test_user, setup_test_user_post
        markers = []
        with step("Пользователь. API. Создание одиннадцати комментариев с маркерами"):
            for i in range(1, 12):
                marker = f"token-{i}"
                markers.append(marker)
                response = user.api.create_comment(post_id=post["id"], body=f"{marker} текст")
                assert_status_code(expect=201, response=response)
        with step("Пользователь. WEB. Первая страница комментариев"):
            page1 = user.web.comments.view_post(post_id=post["id"], page=1)
            assert_status_code(expect=200, response=page1)
            body1 = page1.get_data(as_text=True)
        with step("Пользователь. WEB. Вторая страница комментариев"):
            page2 = user.web.comments.view_post(post_id=post["id"], page=2)
            assert_status_code(expect=200, response=page2)
            body2 = page2.get_data(as_text=True)
        with step("Проверка разбивки"):
            assert_condition(
                condition=NAV_MARK in body1 and NAV_MARK in body2,
                allure_step_name="Навигация отрисована на обеих страницах",
                error_text="Блок 'Постраничная навигация' не найден на одной из страниц",
            )
            assert_condition(
                condition=all(m in body1 for m in markers[1:]),
                allure_step_name="Первая страница — десять новейших",
                error_text="Первая страница не содержит ровно десять новейших комментариев",
            )
            assert_condition(
                condition=markers[0] in body2 and not any(m in body2 for m in markers[1:]),
                allure_step_name="Вторая страница — только старейший",
                error_text="Вторая страница комментариев не соответствует ожиданию",
            )

    def test_comments_page_sanitization(
            self, setup_test_user, setup_test_user_post, setup_test_user_post_comment,
    ):
        """page=abc и page=-3 не роняют страницу поста: 200, комментарий на месте."""
        user, post, comment = setup_test_user, setup_test_user_post, setup_test_user_post_comment
        with step("Пользователь. WEB. Страница поста с мусорным page"):
            garbage = user.web.comments.view_post(post_id=post["id"], page="abc")
            negative = user.web.comments.view_post(post_id=post["id"], page="-3")
            assert_status_code(expect=200, response=garbage)
            assert_status_code(expect=200, response=negative)
        with step("Проверка содержимого"):
            for response in (garbage, negative):
                assert_condition(
                    condition=comment["body"] in response.get_data(as_text=True),
                    allure_step_name="Первая страница комментариев показана",
                    error_text="Мусорный page не вернул первую страницу",
                )

    @title("Страница за пределами total — пустой список без ошибки")
    @severity(severity_level.CRITICAL)
    def test_comments_page_beyond_total(self, setup_test_user, setup_test_user_post, setup_test_user_post_comment):
        """page=5 при одной странице комментариев: 200, пустое состояние, комментария нет."""
        user, post, comment = setup_test_user, setup_test_user_post, setup_test_user_post_comment
        with step("Пользователь. WEB. Страница поста за пределами total"):
            response = user.web.comments.view_post(post_id=post["id"], page=5)
            assert_status_code(expect=200, response=response)
            page = response.get_data(as_text=True)
        with step("Проверка пустой страницы"):
            assert_condition(
                condition="Комментариев пока нет." in page and comment["body"] not in page,
                allure_step_name="За пределами total — пустой список",
                error_text="Страница за пределами total не отработала как пустая",
            )
