"""Фабрика настоящих тестовых изображений через Pillow (→ ARC-0044).

Байты-заглушки (заголовок + нули) новому сервису не валидны: он открывает содержимое Pillow'ом. Тесты строят настоящие
картинки — маленькие, но корректные по формату.
"""

from io import BytesIO
from typing import Any

from PIL import Image as PILImage


def _encode(image: PILImage.Image, format_name: str, **options: Any) -> bytes:
    """Кодирует изображение в байты указанного формата.

    Args:
        image: Изображение Pillow.
        format_name: Формат сохранения ("PNG", "JPEG", "GIF", "WEBP").
        **options: Дополнительные параметры сохранения (quality и прочее).

    Returns:
        Содержимое изображения в указанном формате.
    """
    buffer = BytesIO()
    image.save(buffer, format=format_name, **options)
    return buffer.getvalue()


def make_png_bytes(size: tuple[int, int] = (1, 1)) -> bytes:
    """Собирает валидный PNG заданного размера.

    Args:
        size: Размер изображения в пикселях.

    Returns:
        Содержимое PNG-файла.
    """
    return _encode(PILImage.new("RGB", size, color=(255, 0, 0)), "PNG")


def make_jpeg_bytes(size: tuple[int, int] = (1, 1)) -> bytes:
    """Собирает валидный JPEG заданного размера.

    Args:
        size: Размер изображения в пикселях.

    Returns:
        Содержимое JPEG-файла.
    """
    return _encode(PILImage.new("RGB", size, color=(0, 255, 0)), "JPEG")


def make_gif_bytes(size: tuple[int, int] = (1, 1)) -> bytes:
    """Собирает валидный (статичный) GIF заданного размера.

    Args:
        size: Размер изображения в пикселях.

    Returns:
        Содержимое GIF-файла.
    """
    return _encode(PILImage.new("RGB", size, color=(0, 0, 255)), "GIF")


def make_webp_bytes(size: tuple[int, int] = (1, 1)) -> bytes:
    """Собирает валидный WEBP заданного размера.

    Args:
        size: Размер изображения в пикселях.

    Returns:
        Содержимое WEBP-файла.
    """
    return _encode(PILImage.new("RGB", size, color=(255, 255, 0)), "WEBP")


def make_cmyk_jpeg_bytes(size: tuple[int, int] = (1, 1)) -> bytes:
    """Собирает валидный JPEG в режиме CMYK (не RGB/L).

    Args:
        size: Размер изображения в пикселях.

    Returns:
        Содержимое JPEG-файла.
    """
    return _encode(PILImage.new("CMYK", size, color=(255, 0, 0, 0)), "JPEG")


def make_bmp_bytes(size: tuple[int, int] = (1, 1)) -> bytes:
    """Собирает валидный BMP — формат вне белого списка сервера.

    Args:
        size: Размер изображения в пикселях.

    Returns:
        Содержимое BMP-файла.
    """
    return _encode(PILImage.new("RGB", size, color=(0, 0, 255)), "BMP")
