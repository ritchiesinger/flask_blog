"""Загрузка изображений: валидация, обработка Pillow и сохранение.

Три образа (→ ARC-0044): детальная версия (пережата до MAX_IMAGE_SIDE), миниатюра thumbs/<имя> (THUMB_MAX_SIDE) и
оригинал — оригинал не хранится вовсе. Анимированные файлы (GIF, анимированный WebP) хранятся как есть: пересохранение
убивает анимацию. Формат содержимого определяет Pillow — расширение исходного имени служит только первым фильтром.
"""

import re
import uuid
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from flask import current_app
from PIL import Image as PILImage
from PIL.Image import Resampling

from blog.constants import (
    ALLOWED_IMAGE_EXTENSIONS,
    IMAGE_EXTENSION_ALIASES,
    IMAGE_FORMAT_EXTENSIONS,
    JPEG_QUALITY,
    MAX_IMAGE_SIDE,
    THUMB_MAX_SIDE,
)
from blog.extensions import db
from blog.models.image import Image
from blog.services.base_errors import BadRequestError

# Ссылки на наши картинки в телах постов — для синхронизации связей
# (post_service) и чистки сирот (CLI). Имена генерируем сами: 32 hex-символа
# uuid4 + расширение; подпапка thumbs в паттерн не попадает.
UPLOAD_RE = re.compile(r"/uploads/([0-9a-f]{32}\.(?:png|jpg|gif|webp))")

# Имя подпапки миниатюр внутри UPLOAD_FOLDER.
THUMBS_DIR = "thumbs"


def _save_file(folder: str, name: str, data: bytes) -> None:
    """Записывает байты в файл папки uploads (папка создаётся при отсутствии).

    Args:
        folder: Папка UPLOAD_FOLDER.
        name: Сгенерированное имя файла.
        data: Содержимое файла.
    """
    upload_dir = Path(folder)
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / name).write_bytes(data)


def _encode(pil: PILImage.Image, ext: str) -> bytes:
    """Кодирует изображение в байты выбранного формата.

    Args:
        pil: Изображение Pillow.
        ext: Каноничное расширение ("png", "jpg", "webp").

    Returns:
        Содержимое файла в выбранном формате.
    """
    buffer = BytesIO()
    if ext == "jpg":
        if pil.mode not in ("RGB", "L"):
            pil = pil.convert("RGB")
        pil.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    elif ext == "webp":
        pil.save(buffer, format="WEBP", quality=JPEG_QUALITY)
    else:
        pil.save(buffer, format="PNG")
    return buffer.getvalue()


def _process_detailed(pil: PILImage.Image, ext: str) -> bytes:
    """Готовит детальную версию: уменьшает до MAX_IMAGE_SIDE, кодирует.

    thumbnail сохраняет пропорции и не увеличивает маленькие картинки.

    Args:
        pil: Изображение Pillow (не анимированное).
        ext: Каноничное расширение формата.

    Returns:
        Содержимое детальной версии.
    """
    pil.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Resampling.LANCZOS)
    return _encode(pil, ext)


def _save_thumb(folder: str, name: str, detailed: bytes) -> None:
    """Генерирует и записывает миниатюру из детальной версии.

    Args:
        folder: Папка UPLOAD_FOLDER.
        name: Сгенерированное имя файла (миниатюра — то же имя в thumbs/).
        detailed: Содержимое детальной версии.
    """
    thumbs_dir = Path(folder) / THUMBS_DIR
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    pil = PILImage.open(BytesIO(detailed))
    pil.thumbnail((THUMB_MAX_SIDE, THUMB_MAX_SIDE), Resampling.LANCZOS)
    ext = Path(name).suffix.lstrip(".")
    (thumbs_dir / name).write_bytes(_encode(pil, ext))


def generate_thumb_from_file(folder: str, name: str) -> None:
    """Генерирует миниатюру из уже сохранённой детальной версии.

    Используется CLI make-thumbs для бэкфилда и регенерации при смене
    THUMB_MAX_SIDE. GIF не обрабатываются по дизайну.

    Args:
        folder: Папка UPLOAD_FOLDER.
        name: Имя детального файла.
    """
    detailed = (Path(folder) / name).read_bytes()
    _save_thumb(folder, name, detailed)


def save_image(stream: BinaryIO, original_name: str, author_id: int | None) -> str:
    """Проверяет, обрабатывает и сохраняет изображение; пишет строку в БД.

    Валидация: расширение исходного имени — первый фильтр (белый список),
    затем Pillow определяет реальный формат содержимого. Имя файла
    генерируется под верный формат (PNG под именем .jpg сохранится как
    .png); путь строится только из сгенерированного имени — обход
    каталогов исключён по построению. Анимированные и GIF хранятся
    как есть (без детальной версии и миниатюры); остальные — пережимаются
    до MAX_IMAGE_SIDE, из детальной версии генерируется миниатюра.

    Args:
        stream: Файловый поток загруженного изображения.
        original_name: Оригинальное имя файла от пользователя.
        author_id: Идентификатор загрузившего пользователя.

    Returns:
        Относительный URL детальной версии: "/uploads/<имя>".

    Raises:
        BadRequestError: файл без расширения, расширение не из белого
            списка, содержимое не является изображением или формат
            не поддерживается.
    """
    ext = Path(original_name).suffix.lower().lstrip(".")
    if not ext:
        raise BadRequestError("Файл без расширения.")
    ext = IMAGE_EXTENSION_ALIASES.get(ext, ext)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise BadRequestError(f"Расширение файла не поддерживается: {ext}")
    try:
        pil = PILImage.open(stream)
    except Exception:
        raise BadRequestError("Содержимое не является изображением.") from None
    detected = IMAGE_FORMAT_EXTENSIONS.get(pil.format or "")
    if detected is None:
        raise BadRequestError("Формат содержимого не поддерживается.")
    filename = f"{uuid.uuid4().hex}.{detected}"
    folder = current_app.config["UPLOAD_FOLDER"]
    if getattr(pil, "is_animated", False) or detected == "gif":
        stream.seek(0)
        _save_file(folder, filename, stream.read())
    else:
        detailed = _process_detailed(pil, detected)
        _save_file(folder, filename, detailed)
        _save_thumb(folder, filename, detailed)
    db.session.add(Image(filename=filename, author_id=author_id))
    db.session.commit()
    return f"/uploads/{filename}"


def delete_image_files(folder: str, name: str) -> None:
    """Удаляет детальную версию и миниатюру (если есть) с диска.

    Args:
        folder: Папка UPLOAD_FOLDER.
        name: Сгенерированное имя файла.
    """
    (Path(folder) / name).unlink(missing_ok=True)
    (Path(folder) / THUMBS_DIR / name).unlink(missing_ok=True)


def find_drift_files(folder: str) -> list[str]:
    """Возвращает имена файлов uploads без строк в БД (дрейф).

    Args:
        folder: Папка UPLOAD_FOLDER.

    Returns:
        Список имён файлов-дрейфа.
    """
    upload_dir = Path(folder)
    if not upload_dir.is_dir():
        return []
    names = {item.name for item in upload_dir.iterdir() if item.is_file()}
    return sorted(names - set(db.session.scalars(db.select(Image.filename)).all()))


def backfill_files(folder: str, existing: set[str]) -> tuple[int, int]:
    """Принимает файлы без строк в БД и генерирует недостающие миниатюры.

    Args:
        folder: Папка UPLOAD_FOLDER.
        existing: Множество имён уже известных Image (передаётся CLI).

    Returns:
        (Число принятых строк, число сгенерированных миниатюр).
    """
    adopted = 0
    thumbs = 0
    for name in find_drift_files(folder):
        db.session.add(Image(filename=name))
        db.session.commit()
        adopted += 1
        if Path(name).suffix.lower().lstrip(".") == "gif":
            continue  # GIF без миниатюры по дизайну: пересохранение убивает анимацию
        try:
            generate_thumb_from_file(folder, name)
            thumbs += 1
        except Exception:
            pass  # нечитаемый файл принят строкой, остаётся без миниатюры
    return adopted, thumbs

