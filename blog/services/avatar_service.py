"""Загрузка и обслуживание аватарок: два квадрата — 400 (профиль) и 64 (кружок).

Кроп выполняет пользователь в браузере (виджет → ARC-0051): на сервер приходит
уже квадратный файл из canvas. Сервер на случай обхода виджета дорежет кадр
до квадрата по центру, пережмёт до AVATAR_SIZE и AVATAR_SMALL_SIZE и сохранит
пару файлов в подпапку avatars/ UPLOAD_FOLDER (малый — в avatars/thumbs/,
как миниатюры uploads, → ARC-0044). Формат результата: JPEG остаётся JPEG,
прочее — PNG (анимация GIF умирает при кропе, пользователь предупреждён
в модалке).

Аватарки не участвуют в clean-uploads: find_drift_files и чистка сирот
сканируют только верхний уровень UPLOAD_FOLDER — подпапка avatars мимо
по построению. При изменении сканирования на рекурсивное правило надо
перенести (файлы аватаров не имеют строк Image). Сироты в нормальном потоке
невозможны: замена и сброс удаляют старую пару, удаление пользователя чистит
файлы в delete_user.
"""

import uuid
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from flask import current_app
from PIL import Image as PILImage
from PIL.Image import Resampling

from blog.constants import (
    ALLOWED_IMAGE_EXTENSIONS,
    AVATAR_SIZE,
    AVATAR_SMALL_SIZE,
    IMAGE_EXTENSION_ALIASES,
    IMAGE_FORMAT_EXTENSIONS,
    JPEG_QUALITY,
)
from blog.extensions import db
from blog.models.user import User
from blog.services.base_errors import BadRequestError, ForbiddenError
from blog.services.uploads_service import THUMBS_DIR

# Имя подпапки аватаров внутри UPLOAD_FOLDER.
AVATARS_DIR = "avatars"


def _encode(pil: PILImage.Image, ext: str) -> bytes:
    """Кодирует аватар в байты выбранного формата.

    Args:
        pil: Квадратное изображение Pillow.
        ext: Каноничное расширение результата ("png" или "jpg").

    Returns:
        Содержимое файла в выбранном формате.
    """
    buffer = BytesIO()
    if ext == "jpg":
        if pil.mode not in ("RGB", "L"):
            pil = pil.convert("RGB")
        pil.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    else:
        pil.save(buffer, format="PNG")
    return buffer.getvalue()


def _square(pil: PILImage.Image) -> PILImage.Image:
    """Режет изображение до квадрата по центру (кроп виджета мог быть обойдён).

    Для квадратного исходника возвращается тот же объект — вызов обязан
    копировать результат перед мутацией (→ ARC-0052: thumbnail меняет
    изображение на месте, два размера из одного объекта дают два файла
    с малым размером).

    Args:
        pil: Изображение Pillow.

    Returns:
        Квадратное изображение Pillow (возможно, тот же объект).
    """
    width, height = pil.size
    side = min(width, height)
    if width == height:
        return pil
    left = (width - side) // 2
    top = (height - side) // 2
    return pil.crop((left, top, left + side, top + side))


def delete_avatar_files(name: str) -> None:
    """Удаляет пару файлов аватара (средний и малый) с диска.

    Args:
        name: Имя файла аватара (одинаково для обоих размеров).
    """
    avatar_dir = Path(current_app.config["UPLOAD_FOLDER"]) / AVATARS_DIR
    (avatar_dir / name).unlink(missing_ok=True)
    (avatar_dir / THUMBS_DIR / name).unlink(missing_ok=True)


def save_avatar(user: User, stream: BinaryIO, original_name: str, *, actor: User) -> None:
    """Проверяет, кропает и сохраняет аватар; перезаписывает предыдущий.

    Только владелец меняет свой аватар: гвард actor — defense-in-depth,
    WEB-роут прячет действие 404 раньше (→ ARC-0051). Валидация как у uploads
    (→ ARC-0044): расширение имени — первый фильтр, реальный формат определяет
    Pillow. Обход виджета (не-квадрат, произвольный формат) не ломает
    результат: лишнее срезается по центру, анимация умирает при перекодировании.
    Каждый размер строится из отдельной копии базового квадрата — thumbnail
    мутит изображение на месте (→ ARC-0052). Старая пара файлов удаляется
    после успешного сохранения новой — сбой между записью и commit оставит
    дрейф-пару, не потерю аватара.

    Args:
        user: Владелец аватара.
        stream: Файловый поток загруженного изображения.
        original_name: Оригинальное имя файла от пользователя.
        actor: Действующий пользователь; менять аватар может только владелец.

    Raises:
        ForbiddenError: Актёр не владелец.
        BadRequestError: расширение не из белого списка, содержимое не является
            изображением или формат не поддерживается.
    """
    if actor.id != user.id:
        raise ForbiddenError("Аватар меняет только владелец профиля")
    ext = Path(original_name).suffix.lower().lstrip(".")
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
    result_ext = "jpg" if detected == "jpg" else "png"
    base = _square(pil)
    middle = base.copy()
    middle.thumbnail((AVATAR_SIZE, AVATAR_SIZE), Resampling.LANCZOS)
    small = base.copy()
    small.thumbnail((AVATAR_SMALL_SIZE, AVATAR_SMALL_SIZE), Resampling.LANCZOS)
    filename = f"{uuid.uuid4().hex}.{result_ext}"
    avatar_dir = Path(current_app.config["UPLOAD_FOLDER"]) / AVATARS_DIR
    avatar_dir.mkdir(parents=True, exist_ok=True)
    (avatar_dir / filename).write_bytes(_encode(middle, result_ext))
    thumbs_dir = avatar_dir / THUMBS_DIR
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    (thumbs_dir / filename).write_bytes(_encode(small, result_ext))
    if user.avatar_filename:
        delete_avatar_files(user.avatar_filename)
    user.avatar_filename = filename
    db.session.commit()


def reset_avatar(user: User, *, actor: User) -> None:
    """Сбрасывает аватар: удаляет файлы и обнуляет ссылку (возврат к автогенерации).

    Гвард actor — defense-in-depth, как в save_avatar (→ ARC-0051).

    Args:
        user: Владелец аватара.
        actor: Действующий пользователь; сброс доступен только владельцу.

    Raises:
        ForbiddenError: Актёр не владелец.
    """
    if actor.id != user.id:
        raise ForbiddenError("Аватар меняет только владелец профиля")
    if user.avatar_filename:
        delete_avatar_files(user.avatar_filename)
        user.avatar_filename = None
        db.session.commit()
