"""Утилиты аватара: детерминированный оттенок по имени пользователя."""

import hashlib

PALETTE_SIZE = 6


def avatar_color(username: str) -> int:
    """Возвращает номер оттенка аватара для имени (от 0 до PALETTE_SIZE - 1).

    MD5 выбран вместо встроенного hash(): тот солёный и меняется
    между запусками процесса, а оттенок должен быть постоянным.

    Args:
        username: Логин пользователя.

    Returns:
        Номер класса палитры в blog.css.
    """
    digest = hashlib.md5(username.encode("utf-8")).hexdigest()
    return int(digest, 16) % PALETTE_SIZE
