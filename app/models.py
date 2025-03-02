"""Модели БД."""

# pylint: disable=no-member  # Особенность асбтрактного представления моделей без существующего ещё приложения

from time import time
from typing import Dict, Optional, Union

from jwt import encode as jwt_encode, decode as jwt_decode, exceptions as jwt_exceptions
from passlib.apps import custom_app_context as pwd_context
from passlib.context import CryptContext
from flask import current_app
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Модель сущности Пользователь."""
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    roles = db.relationship('UserRoles', backref='user', lazy=True)

    def __repr__(self):
        return f"{self.to_dict()}"

    def to_dict(self):
        """Формирования модели в виде словаря."""
        user_info = {
            "id": self.id,
            "login": self.login,
            "email": self.email,
            "roles": [
                Role.query.filter_by(id=role.role_id).first().name
                if Role.query.filter_by(id=role.role_id).first() else None for role in self.roles
            ]
        }
        return user_info

    def hash_password(self, password: str):
        """Хэширование пароля.

        :param password: пароль.
        """
        cryptor = CryptContext(schemes=["sha256_crypt", "md5_crypt"])
        self.password_hash = cryptor.hash(password)

    def verify_password(self, password: str) -> bool:
        """Проверка пароля.

        :param password: пароль.
        :return: результат проверки пароля.
        """
        return pwd_context.verify(password, self.password_hash)

    def generate_token(self, expiration: int = None) -> str:
        """Создание JWT токена.

        :param expiration: время протухания в секундах.
        :return: токен.
        """
        expiration = expiration or current_app.config["TOKEN_EXPIRATION"]
        token = jwt_encode(
            {"id": self.id, "exp": time() + expiration},
            current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )
        return token

    @staticmethod
    def verify_token(token: str) -> Optional[db.Model]:
        """Проверка токена.

        :param token: JWT токен.
        :return: модель текущего пользователя в случае успешной проверки, иначе None.
        """
        try:
            decoded_signature = jwt_decode(
                token, current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
        except jwt_exceptions.ExpiredSignatureError:
            return None  # valid token, but expired
        except jwt_exceptions.InvalidSignatureError:
            return None  # invalid token
        user = User.query.get(decoded_signature["id"])
        return user


class Role(db.Model):
    """Модель сущности Роль."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(256))

    def to_dict(self) -> Dict[str, Union[str, int]]:
        """Формирование модели в виде словаря."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }

    def __repr__(self):
        """Представление объекта модели."""
        return str(self.to_dict())


class UserRoles(db.Model):  # pylint: disable=too-few-public-methods  # Такая модель
    """Модель связи ролей и пользователей."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

    def __repr__(self):
        """Представление объекта модели."""
        return f"<UserRole {self.user_id} {self.role_id}>"
