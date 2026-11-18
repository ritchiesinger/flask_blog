"""Загрузка изображений: валидация и сохранение на файловую систему."""

import os
import re
import uuid
from typing import BinaryIO

from flask import current_app

from blog.constants import ALLOWED_IMAGE_EXTENSIONS, IMAGE_EXTENSION_ALIASES
from blog.services.base_errors import BadRequestError

# Ссылки на наши картинки в телах постов — для чистки сирот (CLI).
# Имена генерируем сами: 32 hex-символа uuid4 + расширение.
UPLOAD_RE = re.compile(r"/uploads/([0-9a-f]{32}\.(?:png|jpg|gif|webp))")


def _detect_image_format(head: bytes) -> str | None:
    """Определяет формат изображения по первым байтам (magic bytes).

    Args:
        head: Первые байты файла (минимум 12).

    Returns:
        Каноничное расширение формата (".png", ".jpg", ...) или None,
        если формат не распознан.
    """
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return ".webp"
    return None


def save_image(stream: BinaryIO, original_name: str) -> str:
    """Проверяет и сохраняет изображение в папку UPLOAD_FOLDER.

    Валидация двух уровней: расширение из белого списка (первый фильтр),
    затем magic bytes — расширение обязано совпасть с реальным форматом
    содержимого. Имя файла генерируется (uuid4), путь строится только из
    сгенерированного имени — обход каталогов исключён по построению.

    Args:
        stream: Файловый поток загруженного изображения (werkzeug FileStorage
            поддерживает read/seek/save).
        original_name: Оригинальное имя файла от пользователя.

    Returns:
        Относительный URL сохранённого файла: "/uploads/<имя>".

    Raises:
        BadRequestError: файл без расширения, расширение не из белого списка,
            или содержимое не является изображением заявленного формата.
    """
    ext = os.path.splitext(original_name)[1].lower().lstrip(".")
    if not ext:
        raise BadRequestError("Файл без расширения.")
    ext = IMAGE_EXTENSION_ALIASES.get(ext, ext)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise BadRequestError("Допустимы только изображения: png, jpg, gif, webp.")

    head = stream.read(12)
    if _detect_image_format(head) != f".{ext}":
        raise BadRequestError("Содержимое файла не соответствует изображению.")
    stream.seek(0)

    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    stream.save(os.path.join(upload_folder, filename))
    return f"/uploads/{filename}"
