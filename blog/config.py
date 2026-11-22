"""Конфигуратор приложения."""

import os

BASE_DIR = os.path.abspath(os.path.join(str(os.path.dirname(__file__)), ".."))


class Config:
    """Конфигуратор приложения."""
    SECRET_KEY = (
        "bd39dd86f3f8494ea3f6c29f1bcf4487ad3bd0c373643e26db524cb77e0bb095"  # позже вынесешь в переменную окружения
    )
    SQLALCHEMY_DATABASE_URI = "sqlite:///db.sqlite3"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "3d6018139c32cecd75d3284a744dea72cb786c41d07744979120cd4d6f897825"
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # токен живёт 1 час
    JWT_ERROR_MESSAGE_KEY = "error"
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    # Аватарки живут в подпапке UPLOAD_FOLDER/avatars (→ ARC-0051); отдельной
    # константы нет: сервис вычисляет путь от UPLOAD_FOLDER, тесты переопределяют
    # одну настройку. Отдача файлов — существующим роутом /uploads/<path>.
    # Лимит тела запроса: клиентский лимит изображения — 50 МБ (md_editor_init.js), здесь запас на служебные байты
    # multipart-запроса и на прочие POST-формы. Последняя инстанция против обхода клиентского кода.
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024
