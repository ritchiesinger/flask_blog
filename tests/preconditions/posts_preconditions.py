"""Предусловия, связанные с постами."""

from json import dumps
from typing import Any

from faker import Faker
from flask import Flask
from glamor import attach, attachment_type, step, title
from pytest import fixture

from blog.extensions import db
from blog.models import Post
from blog.services import post_service
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_status_code

fake = Faker()


@fixture
@title("Пользователь 1. API. Создан пост")
def setup_test_user_post(setup_test_user: UserObject) -> dict[str, Any]:
    """Создаёт пост от имени первого тестового пользователя.

    Args:
        setup_test_user: фикстура пользователя, от имени которого создаётся пост.

    Returns:
        JSON созданного поста: ``id``, ``title``, ``body``, ``author`` и прочие поля ответа.
    """
    user = setup_test_user
    with step("Создание поста"):
        response = user.api.create_post(title=fake.sentence(nb_words=3), body=fake.text(max_nb_chars=2000))
        assert_status_code(expect=201, response=response)
        post = response.get_json()
        attach(body=dumps(post, indent=2), name="Свойства созданного поста", attachment_type=attachment_type.JSON)
    return post


@fixture
@title("Пользователь 1. SERVICE. Создан пост")
def setup_test_user_post_via_service(setup_app: Flask, setup_test_user: UserObject) -> Post:
    """Создаёт пост через сервисный слой."""
    user = setup_test_user
    with setup_app.app_context(), step("Создание поста"):
        post = post_service.create_post(
            title=fake.sentence(nb_words=3),
            body=fake.text(max_nb_chars=2000),
            author_id=user.db_model.id,
        )
        db.session.refresh(post)  # материализуем все скаляры после expire_on_commit
        attach(
            body=dumps(post.to_dict(), indent=2),
            name="Свойства созданного поста",
            attachment_type=attachment_type.JSON
        )
        db.session.expunge(post)  # db_model живёт в тестах детачнутым: скаляры читаемы, связи — нет
        return post

