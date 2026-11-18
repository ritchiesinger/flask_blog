"""Юнит-тесты repr моделей: читаемое строковое представление без БД."""

from glamor import epic, feature, severity, severity_level, story, title

from blog.models import Post, User
from tests.tools.asserters.base_asserters import assert_equal


@epic("UNIT")
@feature("Модели")
@story("Текстовое представление объектов моделей")
@severity(severity_level.NORMAL)
class TestModelRepr:
    """repr моделей возвращает читаемое представление с данными объекта."""

    @title("Текстовое представление модели Post")
    def test_post_repr_contains_title(self):
        """Repr поста — <Post 'заголовок'>."""
        post = Post(title="Заголовок", body="Тело", author_id=1)
        assert_equal(expect="<Post 'Заголовок'>", actual=repr(post), name="repr поста")

    @title("Текстовое представление модели User")
    def test_user_repr_contains_username(self):
        """Repr пользователя — <User 'имя'>."""
        user = User(username="newuser")
        assert_equal(expect="<User 'newuser'>", actual=repr(user), name="repr пользователя")
