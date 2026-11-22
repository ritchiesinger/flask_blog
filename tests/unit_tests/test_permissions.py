"""Юнит-тесты единой модели прав: blog.services.permissions."""

from glamor import epic, feature, severity, severity_level, step, story, title
from pytest import raises

from blog.models import User
from blog.services.base_errors import ForbiddenError
from blog.services.permissions import Action, ensure_allowed


@epic("UNIT")
@feature("Ролевая модель")
@story("Матрица прав")
@severity(severity_level.BLOCKER)
class TestEnsureAllowed:
    """Матрица прав: автор / администратор / обычный пользователь."""

    @title("Автору разрешены и правка, и удаление его сущности")
    def test_author_any_action(self, setup_test_user_model: User):
        """Оба действия автора над собственной сущностью проходят без исключений.

        Ожидание: ensure_allowed молчит при UPDATE и DELETE — авторские права полные (→ ARC-0038).
        """
        author = setup_test_user_model
        with step("Автору разрешена правка своей сущности"):
            ensure_allowed(author.id, actor=author, action=Action.UPDATE, subject="поста")
        with step("Автору разрешено удаление своей сущности"):
            ensure_allowed(author.id, actor=author, action=Action.DELETE, subject="поста")

    @title("Администратору разрешено удаление чужой сущности")
    def test_admin_may_delete_foreign(self, setup_test_admin_model: User):
        """Удаление чужой сущности администратору разрешено.

        Ожидание: ensure_allowed проходит при author_id вне своего — админ-поверхность включает DELETE
        (→ ARC-0038).
        """
        admin = setup_test_admin_model
        with step("Операция удаления администратору разрешается"):
            ensure_allowed(author_id=2, actor=admin, action=Action.DELETE, subject="комментария")

    @title("Обычный пользователь не получает прав на чужую сущность")
    def test_regular_user_foreign_forbidden(self, setup_test_user_model: User):
        """Чужая сущность для обычного пользователя закрыта: ForbiddenError.

        Ожидание: проверено на DELETE — единственный легальный путь пользователя к чужому — чтение,
        не правка и не удаление.
        """
        user = setup_test_user_model
        with step("Операция удаления чужой сущности запрещена пользователю"):
            with raises(ForbiddenError):
                ensure_allowed(author_id=2, actor=user, action=Action.DELETE, subject="поста")

    @title("Редактирование чужого админу не открывается — правка остаётся авторской")
    def test_admin_cannot_update_foreign(self, setup_test_admin_model: User):
        """Правка чужой сущности администратору запрещена: ForbiddenError.

        Ожидание: админ-поверхность не включает UPDATE (→ ARC-0038) — повышением прав через правку
        контент не забрать.
        """
        admin = setup_test_admin_model
        with step("Операция редактирования чужой сущности запрещена администратору"):
            with raises(ForbiddenError):
                ensure_allowed(author_id=2, actor=admin, action=Action.UPDATE, subject="поста")

    @title("Текст ошибки называет сущность в родительном падеже.")
    def test_error_message_names_subject(self, setup_test_user_model: User):
        """Текст ForbiddenError называет сущность родительным падежом.

        Ожидание: в сообщении фигурирует «поста» — универсальная формулировка для постов и комментариев:
        пользователь понимает, что именно запрещено.
        """
        user = setup_test_user_model
        with step('Проверка вхождения "поста" в текст ошибки'):
            with raises(ForbiddenError, match="поста"):
                ensure_allowed(author_id=2, actor=user, action=Action.UPDATE, subject="поста")
