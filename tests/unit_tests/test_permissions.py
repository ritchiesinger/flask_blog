"""Юнит-тесты единой модели прав: blog.services.permissions."""

from pytest import raises

from blog.constants import Roles
from blog.models import User
from blog.services.base_errors import ForbiddenError
from blog.services.permissions import Action, ensure_allowed


def _user(user_id: int, role: str) -> User:
    """Собирает отсоединённую модель пользователя с заданными id и ролью."""
    user = User(username=f"user_{user_id}", role=role)
    user.id = user_id
    return user


class TestEnsureAllowed:
    """Матрица прав: автор / администратор / обычный пользователь."""

    def test_author_any_action(self):
        """Автору разрешены и правка, и удаление его сущности."""
        author = _user(user_id=2, role=Roles.USER)
        ensure_allowed(author.id, actor=author, action=Action.UPDATE, subject="поста")
        ensure_allowed(author.id, actor=author, action=Action.DELETE, subject="поста")

    def test_admin_may_delete_foreign(self):
        """Администратору разрешено удаление чужой сущности."""
        ensure_allowed(2, actor=_user(user_id=1, role=Roles.ADMIN), action=Action.DELETE, subject="комментария")

    def test_regular_user_foreign_forbidden(self):
        """Обычный пользователь не получает прав на чужую сущность."""
        with raises(ForbiddenError):
            ensure_allowed(2, actor=_user(user_id=3, role=Roles.USER), action=Action.DELETE, subject="поста")

    def test_admin_cannot_update_foreign(self):
        """Редактирование чужого админу не открывается — правка остаётся авторской."""
        with raises(ForbiddenError):
            ensure_allowed(2, actor=_user(user_id=1, role=Roles.ADMIN), action=Action.UPDATE, subject="поста")

    def test_error_message_names_subject(self):
        """Текст ошибки называет сущность в родительном падеже."""
        with raises(ForbiddenError, match="поста"):
            ensure_allowed(2, actor=_user(user_id=3, role=Roles.USER), action=Action.UPDATE, subject="поста")
