"""Юнит-тесты сервиса ролей: гварды change_role до обращения к БД.

Успешная смена роли (нужна БД) накрыта API- и WEB-пакетами; здесь — три
запретных пути, каждый срабатывает до первого запроса к БД, как канон
test_admin_service.
"""

from glamor import epic, feature, severity, severity_level, step, story, title
from pytest import raises

from blog.constants import Roles
from blog.models import User
from blog.services.base_errors import BadRequestError, ForbiddenError
from blog.services.user_service import change_role
from tests.tools.asserters.base_asserters import assert_equal


@epic("UNIT")
@feature("Управление ролями", "Ролевая модель")
@story("Смена роли")
class TestChangeRoleServiceGuard:
    """Сервисная защита change_role: дублирует декоратор и видимость контролов."""

    @severity(severity_level.CRITICAL)
    @title("Не-супер-админ получает ForbiddenError до обращения к БД")
    def test_non_super_actor_raises_forbidden(self):
        """USER/ADMIN как actor → ForbiddenError до первого запроса к БД.

        Защита дублирует @role_required(Roles.SUPERADMIN) на роуте
        (defense-in-depth): сервис могут вызвать вне роутов.
        """
        with step("MODEL. Создание актёра с ролью user и цели с явным id"):
            actor = User(username="plainuser")
            actor.id = 1
            target = User(username="target")
            target.id = 2
        with step("User. SERVICE. Попытка смены роли не-супер-админом"):
            with raises(ForbiddenError) as exc_info:
                change_role(user_id=target.id, new_role=Roles.ADMIN, actor=actor)
        assert_equal(
            expect="Смену ролей выполняет только SuperAdministrator",
            actual=str(exc_info.value),
            name="Текст ForbiddenError",
        )

    @severity(severity_level.CRITICAL)
    @title("Супер-админ не может сменить собственную роль")
    def test_self_change_raises_forbidden(self):
        """Смена собственной роли → ForbiddenError до обращения к БД (→ ARC-0041)."""
        with step("MODEL. Создание супер-админа-актёра, цель — он же"):
            actor = User(username="boss", role=Roles.SUPERADMIN)
            actor.id = 1
        with step("User. SERVICE. Попытка смены собственной роли"):
            with raises(ForbiddenError) as exc_info:
                change_role(user_id=actor.id, new_role=Roles.ADMIN, actor=actor)
        assert_equal(
            expect="Свою роль менять нельзя",
            actual=str(exc_info.value),
            name="Текст ForbiddenError",
        )

    @severity(severity_level.NORMAL)
    @title("Роль вне поверхности USER/ADMIN отклоняется BadRequestError")
    def test_superadmin_role_not_assignable(self):
        """SUPERADMIN и прочие роли вне поверхности → BadRequestError до БД.

        Роль уникальна и через интерфейсы не выдаётся (→ ARC-0041).
        """
        with step("MODEL. Создание супер-админа-актёра и цели с иным id"):
            actor = User(username="boss", role=Roles.SUPERADMIN)
            actor.id = 1
            target = User(username="target")
            target.id = 2
        with step("User. SERVICE. Попытка выдать роль SUPERADMIN через сервис"):
            with raises(BadRequestError) as exc_info:
                change_role(user_id=target.id, new_role=Roles.SUPERADMIN, actor=actor)
        assert_equal(
            expect=f"Роль '{Roles.SUPERADMIN}' недоступна для назначения",
            actual=str(exc_info.value),
            name="Текст BadRequestError",
        )
