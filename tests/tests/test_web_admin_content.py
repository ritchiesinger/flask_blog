"""Ревизия роли администратора: удаление чужого контента и запрет чужого редактирования.

Единая модель прав (blog/services/permissions.py): автор — любое действие со своим; администратор —
удаление чужого, одинаково в WEB и API; редактирование чужого остаётся авторским. Отказы обычного
пользователя на чужом контенте покрыты прежними модулями (test_api_comments, test_api_posts,
test_web_blog, test_web_comments) — здесь админские ветки.

Ожидания: удаление админом — тот же контракт, что у автора (WEB — 302 на пост/главную; API — 204);
редактирование чужого админом — 403, роль не расширяет Action.UPDATE. Проверки удаления на двух
уровнях — ответ интерфейса и состояние БД (канон TestAdminDeleteUser::test_admin_deletes_regular_user).
"""

from flask import Flask
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.extensions import db
from blog.models import Comment, Post
from tests.constants.web_endpoints import WebEndpoints
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_redirect, assert_status_code


@epic("WEB")
class TestWebAdminDeleteForeign:
    """Администратор удаляет чужие сущности через WEB-интерфейс."""

    @feature("Возможности администратора", "Ревизия роли")
    @story("Удаление чужого комментария")
    @severity(severity_level.BLOCKER)
    @title("Администратор удаляет чужой комментарий — редирект на пост, комментария больше нет")
    def test_admin_deletes_foreign_comment(self, setup_admin_user: UserObject, setup_foreign_comment: dict):
        """Успех: сервис разрешает админу удаление чужого (Action.DELETE), как если бы он был автором."""
        admin, comment = setup_admin_user, setup_foreign_comment
        with step("Администратор. WEB. Авторизация"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Администратор. WEB. Удаление чужого комментария"):
            response = admin.web.comments.delete_comment(comment_id=comment["id"])
            assert_redirect(
                expect=WebEndpoints.POSTS.VIEW.format(post_id=comment["post_id"]),
                response=response,
            )
        with step("Администратор. WEB. Проверка исчезновения комментария"):
            response = admin.web.posts.view(post_id=comment["post_id"])
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=comment["body"][:40] not in response.get_data(as_text=True),
                allure_step_name="Комментария больше нет на странице поста",
                error_text="Удалённый админом комментарий остался в разметке страницы поста",
            )

    @feature("Возможности администратора", "Ревизия роли")
    @story("Удаление чужого поста")
    @severity(severity_level.BLOCKER)
    @title("Администратор удаляет чужой пост — пост становится недоступным")
    def test_admin_deletes_foreign_post(
            self, setup_app: Flask, setup_admin_user: UserObject, setup_test_user_post: dict,
    ):
        """Удаление чужого поста админом — основной сценарий ревизии роли; проверка двух уровней."""
        admin, post_id = setup_admin_user, setup_test_user_post["id"]
        with step("Администратор. WEB. Авторизация"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Администратор. WEB. Удаление чужого поста"):
            response = admin.web.posts.delete(post_id=post_id)
            assert_redirect(expect=WebEndpoints.POSTS.INDEX, response=response)
        with step("Администратор. WEB. Проверка недоступности поста"):
            assert_status_code(expect=404, response=admin.web.posts.view(post_id=post_id))
        with setup_app.app_context(), step("DB. Удалённый пост отсутствует в БД"):
            assert_condition(
                condition=db.session.get(Post, post_id) is None,
                allure_step_name="Поста нет на уровне хранилища",
                error_text="Пост, удалённый админом, остался в БД",
            )


@epic("WEB")
class TestWebAdminNoEdit:
    """Редактирование чужого админу не открывается и напрямую."""

    @feature("Возможности администратора", "Ревизия роли")
    @story("Редактирование чужого поста")
    @severity(severity_level.CRITICAL)
    @title("Форма редактирования чужого поста для администратора — 403")
    def test_admin_cannot_open_foreign_post_form(self, setup_admin_user: UserObject, setup_test_user_post: dict):
        """ensure_allowed с Action.UPDATE не делает исключений для роли админа."""
        admin, post = setup_admin_user, setup_test_user_post
        with step("Администратор. WEB. Авторизация"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Администратор. WEB. Запрос формы редактирования чужого поста"):
            response = admin.web.posts.update_form(post_id=post["id"])
            assert_status_code(expect=403, response=response)

    @feature("Возможности администратора", "Ревизия роли")
    @story("Редактирование чужого комментария")
    @severity(severity_level.CRITICAL)
    @title("Форма редактирования чужого комментария для администратора — 403")
    def test_admin_cannot_open_foreign_comment_form(self, setup_admin_user: UserObject, setup_foreign_comment: dict):
        """Зеркально постам: чужой комментарий админ не редактирует."""
        admin, comment = setup_admin_user, setup_foreign_comment
        with step("Администратор. WEB. Авторизация"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Администратор. WEB. Запрос формы редактирования чужого комментария"):
            response = admin.web.comments.update_comment_form(comment_id=comment["id"])
            assert_status_code(expect=403, response=response)


@epic("API")
class TestApiAdminDeleteForeign:
    """Администратор удаляет чужие сущности через API."""

    @feature("Возможности администратора", "Ревизия роли")
    @story("Удаление чужого комментария")
    @severity(severity_level.BLOCKER)
    @title("Администратор удаляет чужой комментарий через API — 204 и отсутствие в БД")
    def test_admin_deletes_foreign_comment(
            self, setup_app: Flask, setup_admin_user: UserObject, setup_foreign_comment: dict,
    ):
        """Контракт удаления тот же, что у автора: 204 (канон test_delete_own в test_api_comments)."""
        admin, comment_id = setup_admin_user, setup_foreign_comment["id"]
        with step("Администратор. API. Удаление чужого комментария"):
            response = admin.api.delete_comment(comment_id=comment_id)
            assert_status_code(expect=204, response=response)
        with setup_app.app_context(), step("DB. Удалённый комментарий отсутствует в БД"):
            assert_condition(
                condition=db.session.get(Comment, comment_id) is None,
                allure_step_name="Комментария нет на уровне хранилища",
                error_text="Комментарий, удалённый админом, остался в БД",
            )

    @feature("Возможности администратора", "Ревизия роли")
    @story("Удаление чужого поста")
    @severity(severity_level.BLOCKER)
    @title("Администратор удаляет чужой пост через API — 204 и отсутствие в БД")
    def test_admin_deletes_foreign_post(
            self, setup_app: Flask, setup_admin_user: UserObject, setup_test_user_post: dict,
    ):
        """Зеркально комментариям: чужой пост удаляется админом с тем же контрактом."""
        admin, post_id = setup_admin_user, setup_test_user_post["id"]
        with step("Администратор. API. Удаление чужого поста"):
            response = admin.api.delete_post(post_id=post_id)
            assert_status_code(expect=204, response=response)
        with setup_app.app_context(), step("DB. Удалённый пост отсутствует в БД"):
            assert_condition(
                condition=db.session.get(Post, post_id) is None,
                allure_step_name="Поста нет на уровне хранилища",
                error_text="Пост, удалённый админом, остался в БД",
            )


@epic("API")
class TestApiAdminNoEdit:
    """Редактирование чужого админу закрыто и в API."""

    @feature("Возможности администратора", "Ревизия роли")
    @story("Редактирование чужого комментария")
    @severity(severity_level.CRITICAL)
    @title("PATCH чужого комментария от администратора — 403")
    def test_admin_cannot_update_foreign_comment(self, setup_admin_user: UserObject, setup_foreign_comment: dict):
        """Роль админа не расширяет Action.UPDATE — правка остаётся авторской."""
        admin, comment = setup_admin_user, setup_foreign_comment
        with step("Администратор. API. Попытка правки чужого комментария"):
            response = admin.api.edit_comment(comment_id=comment["id"], new_body="Админ переписал чужое")
            assert_status_code(expect=403, response=response)

    @feature("Возможности администратора", "Ревизия роли")
    @story("Редактирование чужого поста")
    @severity(severity_level.CRITICAL)
    @title("PATCH чужого поста от администратора — 403")
    def test_admin_cannot_update_foreign_post(self, setup_admin_user: UserObject, setup_test_user_post: dict):
        """Зеркально комментариям: чужой пост админ не редактирует."""
        admin, post = setup_admin_user, setup_test_user_post
        with step("Администратор. API. Попытка правки чужого поста"):
            response = admin.api.edit_post(post_id=post["id"], new_title="Админ переписал", new_body="чужой пост")
            assert_status_code(expect=403, response=response)
