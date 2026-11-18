"""Юнит-тесты сервиса админ-операций: проверки прав на уровне сервиса."""

from glamor import epic, feature, severity, severity_level, step, story, title
from pytest import raises

from blog.models import User
from blog.services.admin_service import delete_user
from blog.services.base_errors import ForbiddenError
from tests.tools.asserters.base_asserters import assert_equal


@epic("UNIT")
@feature("Возможности администратора", "Ролевая модель")
@story("Удаление пользователей")
class TestDeleteUserServiceGuard:
    """Сервисная защита delete_user: не-админ не проходит и мимо декоратора."""

    @severity(severity_level.CRITICAL)
    @title("Получение ForbiddenError до обращения к БД при попытке удаления пользователя без прав администратора")
    def test_non_admin_actor_raises_forbidden(self):
        """Обычный пользователь как actor → ForbiddenError до обращения к БД.

        Защита дублирует @role_required на роуте (defence-in-depth): декоратор отсеивает не-админов на уровне API,
        сервис обязан держать собственную проверку — его могут вызвать вне роутов.
        """
        with step("MODEL. Создание экземпляра User с ролью user"):
            non_admin = User(username="plainuser")  # role по умолчанию — Roles.USER
        with step("User. SERVICE. Попытка удаления самого себя"):
            with raises(ForbiddenError) as exc_info:
                delete_user(user_id=1, actor=non_admin)
                assert_equal(
                    expect="Требуются права администратора.",
                    actual=str(exc_info.value),
                    name="Текст ForbiddenError",
                )
