"""Тесты каскадного удаления постов при удалении пользователя через API."""

from typing import Any

from flask import Flask
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.extensions import db
from blog.models import Post, User
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_status_code


@epic("API")
@feature("Возможности администратора")
@story("Каскадное удаление")
class TestAdminDeleteUserWithPosts:
    """Проверки удаления админом пользователя с постами и очистки его постов."""

    @title("Удаление админом пользователя с постами удаляет и его посты")
    @severity(severity_level.CRITICAL)
    def test_user_with_posts_is_deleted_and_posts_removed(
            self,
            setup_app: Flask,
            setup_admin_user: UserObject,
            setup_test_user: UserObject,
            setup_test_user_post: dict[str, Any],
    ):
        """Удаление пользователя с постами возвращает 204, сам пользователь и его посты исчезают из БД.

        Ожидание: 204; в БД нет ни удалённого автора, ни его постов. Проверка
        прямым запросом к БД, а не через ORM-список: сверяемся с тем же уровнем,
        где живёт каскад.
        """
        admin, author_id = setup_admin_user, setup_test_user.db_model.id
        admin.refresh_api_token()
        with step("Администратор. API. Удаление пользователя с постами"):
            response = admin.api.delete_user(user_id=author_id)
            assert_status_code(expect=204, response=response)
        with step("ORM. Проверка отсутствия удалённого автора и его постов"):
            with setup_app.app_context():
                deleted = db.session.scalars(db.select(User).where(User.id == author_id)).all()
                assert_condition(
                    condition=deleted == [],
                    allure_step_name="Удалённого автора в БД нет",
                    error_text="Пользователь не удалён из БД!",
                )
                remaining = db.session.scalars(db.select(Post).where(Post.author_id == author_id)).all()
                assert_condition(
                    condition=remaining == [],
                    allure_step_name="Постов удалённого автора в БД нет",
                    error_text="После удаления автора остались посты!",
                )


    @title("Каскадное удаление постов на уровне БД при прямом SQL-удалении пользователя")
    @severity(severity_level.CRITICAL)
    def test_db_level_cascade_removes_posts_without_orm(
            self,
            setup_app: Flask,
            setup_test_user: UserObject,
            setup_test_user_post: dict[str, Any]
    ):
        """Прямое SQL-удаление пользователя также убирает его посты: каскад живёт в схеме БД.

        Пользователь удаляется raw DELETE минуя ORM — ORM-каскады не задействованы,
        посты убирает только ondelete на уровне СУБД. ORM-удалением этот тест
        проверять нельзя, он теряет смысл.
        """
        user = setup_test_user
        user.refresh_api_token()
        author_id = user.db_model.id
        with step("БД. Прямое удаление пользователя SQL-запросом"):
            with setup_app.app_context():
                db.session.execute(db.text("DELETE FROM user WHERE id = :id"), {"id": author_id})
                db.session.commit()
        with step("ORM. Проверка отсутствия постов удалённого автора"):
            with setup_app.app_context():
                remaining = db.session.scalars(db.select(Post).where(Post.author_id == author_id)).all()
                assert_condition(
                    condition=remaining == [],
                    allure_step_name="Постов удалённого автора в БД нет",
                    error_text="Каскад на уровне БД не сработал, остались посты!",
                )
