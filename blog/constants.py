"""Разные константы."""

from dataclasses import dataclass

POSTS_PER_PAGE = 5
USERS_PER_PAGE = 20
MAX_PER_PAGE = 50

PROFILE_TAB_POSTS = "posts"
PROFILE_TAB_COMMENTS = "comments"
PROFILE_TABS = (PROFILE_TAB_POSTS, PROFILE_TAB_COMMENTS)

COMMENTS_PER_PAGE = 10

# Лимит отображаемого имени (display_name, → ARC-0051): единая точка для
# колонки модели и сервисной проверки длины.
DISPLAY_NAME_MAX_LENGTH = 50

# Допустимые расширения загружаемых изображений (первый фильтр по имени;
# реальный формат содержимого определяет Pillow, → ARC-0044).
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# Алиасы расширений: как хранить (jpeg → jpg).
IMAGE_EXTENSION_ALIASES = {"jpeg": "jpg"}

# Обработка изображений при загрузке (→ ARC-0044): Pillow пережимает до
# MAX_IMAGE_SIDE по большей стороне (детальная версия), из неё генерируется
# миниатюра THUMB_MAX_SIDE; оригинал не хранится. JPEG/WebP пересжимаются
# с JPEG_QUALITY (заодно стреляется EXIF), PNG — пересохранение без потерь.
MAX_IMAGE_SIDE = 1600
THUMB_MAX_SIDE = 480
JPEG_QUALITY = 85

# Каноничное расширение по формату содержимого (Pillow format): имя файла
# генерируется под верный формат — PNG под именем .jpg становится .png.
IMAGE_FORMAT_EXTENSIONS = {"PNG": "png", "JPEG": "jpg", "GIF": "gif", "WEBP": "webp"}

# Аватарки (→ ARC-0051): пользователь кропает в браузере (виджет), сервер
# дорежет до квадрата по центру и хранит два квадрата — AVATAR_SIZE (профиль;
# 400 вместо 512 — решение пользователя: 512 занимал почти весь видимый
# экран в профиле) и AVATAR_SMALL_SIZE (кружок 2rem с запасом на retina).
AVATAR_SIZE = 400
AVATAR_SMALL_SIZE = 64


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
