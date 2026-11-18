"""WEB-роуты загрузки и отдачи изображений."""

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_login import login_required

from blog.services import uploads_service
from blog.services.base_errors import BadRequestError
from blog.web.errors import web_errors

bp = Blueprint("uploads", __name__)


@bp.post("/uploads")
@login_required
@web_errors
def upload_image():
    """Загружает изображение от имени авторизованного пользователя.

    Принимает multipart-поле 'file'. Возвращает JSON с url картинки,
    который EasyMDE вставляет в текст поста.

    Returns:
        JSON {"url": "/uploads/<имя>"} со статусом 200.

    Raises:
        BadRequestError: файл не передан или не прошёл валидацию сервиса.
    """
    file = request.files.get("file")
    if file is None or not file.filename:
        raise BadRequestError("Файл не передан.")
    url = uploads_service.save_image(file, file.filename)
    return jsonify({"url": url})


@bp.get("/uploads/<path:filename>")
def serve_image(filename: str):
    """Отдаёт загруженное изображение (публично — картинки в постах видят все).

    Args:
        filename: сгенерированное имя файла в папке uploads.

    Returns:
        Ответ с содержимым файла.
    """
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
