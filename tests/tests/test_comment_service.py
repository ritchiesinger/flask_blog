"""Тесты сервисного слоя комментариев."""

from flask import Flask
from glamor import epic, feature, severity, severity_level, step, story, title
from pytest import raises

from blog.models import Comment, Post
from blog.services import comment_service
from blog.services.base_errors import BadRequestError, NotFoundError
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_equal


@epic("Сервис")
@feature("Комментарии")
@story("Создание комментария")
class TestCreateComment:
    """Создание комментария."""

    @title("Успешное создание комментария с нормализацией тела")
    @severity(severity_level.BLOCKER)
    def test_create_success(
            self,
            setup_app: Flask,
            setup_test_user: UserObject,
            setup_test_user_post_via_service: Post,
    ):
        """Создание сохраняет комментарий; тело нормализуется strip-ом."""
        user, post = setup_test_user, setup_test_user_post_via_service
        with setup_app.app_context(), step("Пользователь. SERVICE. Создание комментария"):
            comment = comment_service.create_comment(
                post_id=post.id,
                author_id=user.db_model.id,
                body="  Текст комментария  ",
            )
            assert_equal(expect="Текст комментария", actual=comment.body, name="body")
            assert_equal(expect=post.id, actual=comment.post_id, name="post_id")
            assert_equal(expect=user.db_model.id, actual=comment.author_id, name="author_id")

    @title("Ошибка при создании комментария к несуществующему посту")
    @severity(severity_level.CRITICAL)
    def test_create_unknown_post(self, setup_app: Flask, setup_test_user: UserObject):
        """Несуществующий пост даёт NotFoundError."""
        user = setup_test_user
        with setup_app.app_context(), raises(NotFoundError), step("Пользователь. SERVICE. Добавление комментария"):
            comment_service.create_comment(post_id=10 ** 9, author_id=user.db_model.id, body="Текст")

    @title("Ошибка при создании комментария с пустым телом")
    @severity(severity_level.CRITICAL)
    def test_create_empty_body(
            self,
            setup_app: Flask,
            setup_test_user: UserObject,
            setup_test_user_post_via_service: Post,
    ):
        """Тело из одних пробелов даёт BadRequestError."""
        user, post = setup_test_user, setup_test_user_post_via_service
        with setup_app.app_context(), raises(BadRequestError), step("Пользователь. SERVICE. Добавление комментария"):
            comment_service.create_comment(post_id=post.id, author_id=user.db_model.id, body="   ")


@epic("Сервис")
@feature("Комментарии")
@story("Получение комментариев")
class TestListAndGet:
    """Получение комментариев."""

    @title("Список комментариев поста, новые сверху")
    @severity(severity_level.BLOCKER)
    def test_list_newest_first(
            self,
            setup_app: Flask,
            setup_test_user: UserObject,
            setup_test_user_post_via_service: Post,
            setup_test_user_comment_via_service: Comment,
    ):
        """Оба комментария в списке; первый — созданный последним."""
        user, post = setup_test_user, setup_test_user_post_via_service
        with setup_app.app_context():
            with step("Пользователь. SERVICE. Добавление второго комментария"):
                comment_service.create_comment(post_id=post.id, author_id=user.db_model.id, body="Второй")
            with step("SERVICE. Получение списка комментариев"):
                comments = comment_service.list_for_post(post.id)
                assert_equal(expect=2, actual=len(comments), name="Количество комментариев")
                assert_equal(expect="Второй", actual=comments[0].body, name="Первый комментарий в списке")

    @title("Ошибка при запросе списка для несуществующего поста")
    @severity(severity_level.CRITICAL)
    def test_list_unknown_post(self, setup_app: Flask):
        """Несуществующий пост даёт NotFoundError."""
        with setup_app.app_context(), raises(NotFoundError), step("SERVICE. Получение списка комментариев"):
            comment_service.list_for_post(10 ** 9)

    @title("Получение комментария по идентификатору")
    @severity(severity_level.BLOCKER)
    def test_get_comment(self, setup_app: Flask, setup_test_user_comment_via_service: Comment):
        """get_comment возвращает созданный комментарий, гвард автора пропускает своего."""
        created = setup_test_user_comment_via_service
        with setup_app.app_context(), step("Пользователь. SERVICE. Получение комментария"):
            found = comment_service.get_comment(comment_id=created.id)
            assert_equal(expect=created.id, actual=found.id, name="comment_id")
            assert_equal(expect=created.body, actual=found.body, name="body")

    @title("Ошибка при запросе несуществующего комментария")
    @severity(severity_level.CRITICAL)
    def test_get_unknown_comment(self, setup_app: Flask):
        """Несуществующий комментарий даёт NotFoundError."""
        with setup_app.app_context(), raises(NotFoundError), step("SERVICE. Получение комментария"):
            comment_service.get_comment(comment_id=10 ** 9)


@epic("Сервис")
@feature("Комментарии")
@story("Редактирование и удаление комментария")
class TestUpdateAndDelete:
    """Изменение и удаление комментариев."""

    @title("Успешное обновление текста комментария")
    @severity(severity_level.BLOCKER)
    def test_update_success(self, setup_app: Flask, setup_test_user_comment_via_service: Comment):
        """Обновление меняет тело и сохраняет его."""
        comment = setup_test_user_comment_via_service
        with setup_app.app_context(), step("SERVICE. Обновление комментария"):
            updated = comment_service.update_comment(comment=comment, body="  Новое  ")
            assert_equal(expect="Новое", actual=updated.body, name="body")

    @title("Ошибка при обновлении с пустым телом")
    @severity(severity_level.CRITICAL)
    def test_update_empty_body(self, setup_app: Flask, setup_test_user_comment_via_service: Comment):
        """Пустое тело при обновлении даёт BadRequestError."""
        comment = setup_test_user_comment_via_service
        with setup_app.app_context(), raises(BadRequestError), step("SERVICE. Обновление пустым телом"):
            comment_service.update_comment(comment=comment, body="   ")

    @title("Успешное удаление комментария")
    @severity(severity_level.BLOCKER)
    def test_delete_success(self, setup_app: Flask, setup_test_user_comment_via_service: Comment):
        """Удаление убирает комментарий; повторный запрос даёт NotFoundError."""
        comment = setup_test_user_comment_via_service
        with setup_app.app_context():
            with step("SERVICE. Удаление комментария"):
                comment_service.delete_comment(comment=comment)
            with raises(NotFoundError), step("SERVICE. Повторный запрос удалённого"):
                comment_service.get_comment(comment_id=comment.id)
