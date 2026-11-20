"""Юнит-тесты полноты карт отображения ролей."""

from blog.constants import ROLE_BADGE_CLASSES, ROLE_DISPLAY_NAMES, Roles


class TestRoleMapsComplete:
    """Каждой роли сопоставлены человекочитаемое имя и класс бейджа."""

    def test_every_role_has_display_name(self):
        """Роль без названия в ROLE_DISPLAY_NAMES не должна появиться незаметно."""
        for role in (Roles.USER, Roles.ADMIN, Roles.SUPERADMIN):
            assert role in ROLE_DISPLAY_NAMES, f"Нет названия для роли {role!r}"

    def test_every_role_has_badge_class(self):
        """Роль без бейджа в ROLE_BADGE_CLASSES не должна появиться незаметно."""
        for role in (Roles.USER, Roles.ADMIN, Roles.SUPERADMIN):
            assert role in ROLE_BADGE_CLASSES, f"Нет бейджа для роли {role!r}"
