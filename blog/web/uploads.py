"""WEB-роуты загрузки и отдачи изображений."""

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_login import current_user, login_required

from blog.services import uploads_service
from blog.services.base_errors import BadRequestError
from blog.web.errors import web_errors

bp = Blueprint("uploads", __name__)


@bp.post("/uploads")
@login_required
@web_errors
def upload_image():
    """Загружает изображение от имени авторизованного пользователя.

    Принимает multipart-поле 'file'. Сервис обрабатывает картинку
    (детальная версия + миниатюра) и пишет строку Image в БД.
    Возвращает JSON с url картинки, который EasyMDE вставляет в текст.

    Returns:
        JSON {"url": "/uploads/<имя>"} со статусом 200.

    Raises:
        BadRequestError: файл не передан или не прошёл валидацию сервиса.
    """
    file = request.files.get("file")
    if file is None or not file.filename:
        raise BadRequestError("Файл не передан.")
    url = uploads_service.save_image(file, file.filename, author_id=current_user.id)
    return jsonify({"url": url})


@bp.get("/uploads/<path:filename>")
def serve_image(filename: str):
    """Отдаёт изображение из UPLOAD_FOLDER (публично, включая thumbs/).

    Args:
        filename: сгенерированное имя файла (в т. ч. "thumbs/<имя>").

    Returns:
        Ответ с содержимым файла.
    """
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
