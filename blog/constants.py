"""Разные константы."""

from dataclasses import dataclass

POSTS_PER_PAGE = 5
USERS_PER_PAGE = 20
MAX_PER_PAGE = 50

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
