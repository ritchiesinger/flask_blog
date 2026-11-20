"""Разные константы."""

from dataclasses import dataclass

POSTS_PER_PAGE = 5
USERS_PER_PAGE = 20
MAX_PER_PAGE = 50

PROFILE_TAB_POSTS = "posts"
PROFILE_TAB_COMMENTS = "comments"
PROFILE_TABS = (PROFILE_TAB_POSTS, PROFILE_TAB_COMMENTS)

COMMENTS_PER_PAGE = 10

# Допустимые расширения загружаемых изображений (первый фильтр; вторая
# инстанция — magic bytes в uploads_service).
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# Алиасы расширений: как хранить (jpeg → jpg).
IMAGE_EXTENSION_ALIASES = {"jpeg": "jpg"}


@dataclass
class Roles:
    """Роли пользователя."""

    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


# Иерархия ролей (→ ARC-0041): область роли включает все перечисленные в ней роли.
# SUPERADMIN наследует все полномочия ADMIN плюс собственные. Единственное место
# описания иерархии: новые проверки ролей — только через role_includes.
ROLE_SCOPES: dict[str, frozenset[str]] = {
    Roles.USER: frozenset((Roles.USER,)),
    Roles.ADMIN: frozenset((Roles.USER, Roles.ADMIN)),
    Roles.SUPERADMIN: frozenset((Roles.USER, Roles.ADMIN, Roles.SUPERADMIN)),
}


def role_includes(role: str, required: str) -> bool:
    """Проверяет, что роль включает требуемую роль по иерархии.

    Args:
        role: Роль пользователя.
        required: Требуемая роль.

    Returns:
        True, если пользователь с ролью role проходит проверку required.
    """
    return required in ROLE_SCOPES[role]


# Человекочитаемые названия ролей (→ ARC-0043): единый язык UI — флеш,
# подписи dropdown и текст бейджей. Машинные значения остаются в value
# dropdown, протоколе API и БД.
ROLE_DISPLAY_NAMES = {
    Roles.USER: "User",
    Roles.ADMIN: "Administrator",
    Roles.SUPERADMIN: "SuperAdministrator",
}

# Цвет бейджа роли в шаблонах (профиль, список пользователей админки).
ROLE_BADGE_CLASSES = {
    Roles.USER: "bg-secondary",
    Roles.ADMIN: "bg-primary",
    Roles.SUPERADMIN: "bg-dark",
}

# Поверхность смены роли через интерфейсы — только USER <-> ADMIN: SUPERADMIN
# не выдаётся и не снимается (роль уникальна, → ARC-0041). Ключ — текущая
# роль цели; SUPERADMIN в карте нет, ему контролов не рисуют.
ROLE_TARGET_OPTIONS = {
    Roles.USER: (Roles.ADMIN,),
    Roles.ADMIN: (Roles.USER,),
}
