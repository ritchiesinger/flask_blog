"""Тесты модели комментария: repr, to_dict и значение по умолчанию."""

from flask import Flask
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.extensions import db
from blog.models import Comment, Post
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_equal


@epic("Модели")
@feature("Комментарии")
@story("Строковое представление и приведение к словарю")
class TestCommentModel:
    """Проверки модели комментария."""

    @title("repr возвращает читаемое представление с телом комментария")
    @severity(severity_level.MINOR)
    def test_repr(self, setup_app: Flask, setup_test_user_comment_model_via_orm: Comment):
        """Repr равен <Comment 'тело'>."""
        comment = setup_test_user_comment_model_via_orm
        with setup_app.app_context(), step("ORM. Получение repr для модели комментария"):
            assert_equal(expect="<Comment 'Текст для repr'>", actual=repr(comment), name="repr")

    @title("to_dict после сохранения возвращает полные данные, включая автора")
    @severity(severity_level.BLOCKER)
    def test_to_dict_full(
            self,
            setup_app: Flask,
            setup_test_user: UserObject,
            setup_test_user_post_via_service: Post,
            setup_test_user_comment_model_via_orm: Comment,
    ):
        """Словарь содержит id, post_id, body, автора и непустое created."""
        user, post = setup_test_user, setup_test_user_post_via_service
        comment = setup_test_user_comment_model_via_orm
        with setup_app.app_context():
            with step("ORM. Добавление комментария в БД"):
                db.session.add(comment)
                db.session.commit()
            with step("ORM. Приведение к словарю"):
                data = comment.to_dict()
                assert_equal(expect=comment.id, actual=data["id"], name="id")
                assert_equal(expect=post.id, actual=data["post_id"], name="post_id")
                assert_equal(expect=comment.body, actual=data["body"], name="body")
                assert_equal(expect=user.db_model.id, actual=data["author"]["id"], name="author.id")
                assert_equal(expect=user.db_model.username, actual=data["author"]["username"], name="author.username")
                assert_condition(
                    condition=data["created"] is not None,
                    allure_step_name="created непусто после сохранения",
                    error_text="created равен None после commit — колонка должна заполняться дефолтом!",
                )

    @title("to_dict для комментария с незаполненным created отдаёт None")
    @severity(severity_level.MINOR)
    def test_to_dict_created_none(
            self,
            setup_app: Flask,
            setup_test_user: UserObject,
            setup_test_user_post_via_service: Post,
    ):
        """Ветка ``created is None``: до flush дефолт ещё не проставлен.

        Автор подставляется в память явно (связь у объекта без flush
        не подгружается сама), сам объект в сессию не добавляется —
        значит, никакого flush и NOT NULL-ограничение не срабатывает.
        """
        user, post = setup_test_user, setup_test_user_post_via_service
        with setup_app.app_context(), step("Модель. to_dict до сохранения"):
            comment = Comment(body="Текст", post_id=post.id, author_id=user.db_model.id)
            comment.author = user.db_model
            assert_condition(
                condition=comment.to_dict()["created"] is None,
                allure_step_name="created равен None до flush",
                error_text="Ветка created=None сломана: to_dict вернул значение!",
            )
