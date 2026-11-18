"""WEB-тесты комментариев: просмотр, создание, редактирование, удаление."""

from typing import Any

from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_status_code
from tests.tools.clients.web_client import WebClient

FLASH_EMPTY = "Текст комментария не может быть пустым."
FLASH_SUCCESS = "Комментарий добавлен!"


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
