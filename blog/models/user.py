"""Модель пользователя."""

from typing import Any

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from blog.constants import DISPLAY_NAME_MAX_LENGTH, Roles, role_includes
from blog.extensions import db

# ARC-0051: display_name необязателен и неуникален — при None интерфейс
# показывает логин (свойство shown_name). Лимит длины — DISPLAY_NAME_MAX_LENGTH
# из constants: единая точка с сервисной проверкой user_service.
# avatar_filename — имя файла аватара в AVATAR_FOLDER (uuid4 + расширение);
# None — аватара нет, показывается автогенерация по shown_name.


class User(UserMixin, db.Model):
    """Модель пользователя."""

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Roles.USER)
    display_name = db.Column(db.String(DISPLAY_NAME_MAX_LENGTH), nullable=True)
    avatar_filename = db.Column(db.String(64), nullable=True)

    posts = db.relationship(
        "Post",
        back_populates="author",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    comments = db.relationship(
        "Comment",
        back_populates="author",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, username: str, role: str = Roles.USER, display_name: str | None = None):
        """Пользователь.

        Args:
            username: Логин пользователя.
            role: Роль пользователя, по умолчанию USER.
            display_name: Отображаемое имя; None — показывается логин.
        """
        super().__init__()
        self.username = username
        self.role = role
        self.display_name = display_name

    @property
    def is_admin(self) -> bool:
        """Проверяет наличие административных полномочий.

        SUPERADMIN наследует все полномочия ADMIN по иерархии ролей.

        Returns:
            True, если пользователь админ или супер-админ.
        """
        return role_includes(self.role, Roles.ADMIN)

    @property
    def shown_name(self) -> str:
        """Имя для отображения в интерфейсе.

        Единая точка решения «display_name или логин» (→ ARC-0051): шаблоны
        используют только это свойство, прямой вывод username в интерфейсе —
        только там, где логин нужен по своей прямой функции (админка, URL).

        Returns:
            display_name, если задан, иначе логин.
        """
        return self.display_name or self.username

    def set_password(self, raw_password: str):
        """Устанавливает пароль. Сохраняет его хэш в модель.

        Args:
            raw_password: Пароль в открытом виде.
        """
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Проверяет пароль пользователя.

        Args:
            raw_password: Пароль в открытом виде.

        Returns:
            True, если пароль совпал с хэшем.
        """
        return check_password_hash(self.password, raw_password)

    def __repr__(self) -> str:
        """Возвращает читаемое представление пользователя."""
        return f"<User {self.username!r}>"

    def to_dict(self) -> dict[str, Any]:
        """Приведение к словарю.

        Returns:
            Представление модели в виде словаря.
        """
        return {
            "id": self.id,
            "username": self.username,
            "password_hash": self.password,
            "role": self.role,
        }
