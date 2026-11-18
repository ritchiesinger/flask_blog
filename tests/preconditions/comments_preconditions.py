"""Предусловия, связанные с комментариями."""

from json import dumps
from typing import Any

from faker import Faker
from flask import Flask
from glamor import attach, attachment_type, step, title
from pytest import fixture

from blog.extensions import db
from blog.models import Comment, Post
from blog.services import comment_service
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_status_code

fake = Faker()


@fixture
@title("Пользователь 1. API. Создан комментарий к своему посту")
def setup_test_user_post_comment(setup_test_user: UserObject, setup_test_user_post: dict[str, Any]) -> dict[str, Any]:
    """Создаёт комментарий автора под его же постом.

    Args:
        setup_test_user: автор поста и комментария.
        setup_test_user_post: JSON поста.

    Returns:
        JSON комментария.
    """
    user, post = setup_test_user, setup_test_user_post
    with step("Создание комментария"):
        response = user.api.create_comment(post_id=post["id"], body=fake.text(max_nb_chars=500))
        assert_status_code(expect=201, response=response)
    return response.get_json()


@fixture
@title("Пользователь 2. API. Создан комментарий к чужому посту (Пользователя 1)")
def setup_foreign_comment(setup_test_user_2: UserObject, setup_test_user_post: dict[str, Any]) -> dict[str, Any]:
    """Создаёт комментарий второго пользователя под постом первого.

    Args:
        setup_test_user_2: автор комментария; пост принадлежит другому пользователю.
        setup_test_user_post: JSON поста Пользователя 1, к которому пишется комментарий.

    Returns:
        JSON комментария.
    """
    user, post = setup_test_user_2, setup_test_user_post
    with step("Создание комментария вторым пользователем"):
        response = user.api.create_comment(post_id=post["id"], body=fake.text(max_nb_chars=500))
        assert_status_code(expect=201, response=response)
    return response.get_json()


@fixture
@title("Пользователь. ORM. Создана модель комментария (без коммита в БД)")
def setup_test_user_comment_model_via_orm(
        setup_app: Flask,
        setup_test_user: UserObject,
        setup_test_user_post_via_service: Post) -> Comment:
    """Создаёт комментарий через ORM."""
    user, post = setup_test_user, setup_test_user_post_via_service
    with setup_app.app_context(), step("Создание модели комментария"):
        return Comment(body="Текст для repr", post_id=post.id, author_id=user.db_model.id)


@fixture
@title("Пользователь. SERVICE. Создан комментарий к своему посту")
def setup_test_user_comment_via_service(
        setup_app: Flask,
        setup_test_user: UserObject,
        setup_test_user_post_via_service: Post) -> Comment:
    """Создаёт комментарий через сервисный слой."""
    user, post = setup_test_user, setup_test_user_post_via_service
    with setup_app.app_context(), step("Создание комментария"):
        comment = comment_service.create_comment(
            post_id=post.id,
            author_id=user.db_model.id,
            body=fake.text(max_nb_chars=500),
        )
        db.session.refresh(comment)  # материализуем все скаляры после expire_on_commit
        attach(
            body=dumps(comment.to_dict(), indent=2),
            name="Свойства созданного комментария",
            attachment_type=attachment_type.JSON
        )
        db.session.expunge(comment)  # db_model живёт в тестах детачнутым: скаляры читаемы, связи — нет
        return comment
