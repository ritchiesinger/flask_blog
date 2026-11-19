"""Юнит-тесты иерархии ролей."""

from blog.constants import ROLE_SCOPES, Roles, role_includes
from blog.models.user import User


class TestRoleScopes:
    """Карта иерархии: области ролей согласованы."""

    def test_scope_of_user_contains_only_user(self):
        """Область USER — только USER."""
        assert ROLE_SCOPES[Roles.USER] == frozenset((Roles.USER,))

    def test_scope_of_admin_contains_user_and_admin(self):
        """Область ADMIN — USER и ADMIN."""
        assert ROLE_SCOPES[Roles.ADMIN] == frozenset((Roles.USER, Roles.ADMIN))

    def test_scope_of_superadmin_contains_all_roles(self):
        """Область SUPERADMIN — все три роли."""
        assert ROLE_SCOPES[Roles.SUPERADMIN] == frozenset((Roles.USER, Roles.ADMIN, Roles.SUPERADMIN))


class TestRoleIncludes:
    """Проверка иерархии: нижние роли не проходят проверки верхних."""

    def test_user_passes_user_check(self):
        """USER проходит проверку USER."""
        assert role_includes(Roles.USER, Roles.USER) is True

    def test_user_fails_admin_check(self):
        """USER не проходит проверку ADMIN."""
        assert role_includes(Roles.USER, Roles.ADMIN) is False

    def test_admin_passes_admin_check(self):
        """ADMIN проходит проверку ADMIN."""
        assert role_includes(Roles.ADMIN, Roles.ADMIN) is True

    def test_admin_fails_superadmin_check(self):
        """ADMIN не проходит проверку SUPERADMIN."""
        assert role_includes(Roles.ADMIN, Roles.SUPERADMIN) is False

    def test_superadmin_passes_admin_check(self):
        """SUPERADMIN проходит проверку ADMIN — наследование полномочий."""
        assert role_includes(Roles.SUPERADMIN, Roles.ADMIN) is True


class TestIsAdmin:
    """Свойство is_admin учитывает иерархию."""

    def test_user_is_not_admin(self):
        """USER — не админ."""
        assert User(username="u", role=Roles.USER).is_admin is False

    def test_admin_is_admin(self):
        """ADMIN — админ."""
        assert User(username="u", role=Roles.ADMIN).is_admin is True

    def test_superadmin_is_admin(self):
        """SUPERADMIN — админ по наследованию полномочий."""
        assert User(username="u", role=Roles.SUPERADMIN).is_admin is True
