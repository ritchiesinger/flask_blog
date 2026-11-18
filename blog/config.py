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
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 МБ — лимит на запрос с файлом
