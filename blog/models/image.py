"""Модель загруженного изображения и связь с постами."""

from datetime import UTC, datetime
from typing import Any

from blog.extensions import db

# Связь многие-ко-многим: картинка может вставляться в несколько постов, пост —
# содержать несколько картинок. Оба FK каскадные: удаление поста снимает только
# связи, файлы дорабатывает clean-uploads (→ ARC-0044). Сирота — строка без
# записей в image_post.
image_post = db.Table(
    "image_post",
    db.Column("image_id", db.Integer, db.ForeignKey("image.id", ondelete="CASCADE"), primary_key=True),
    db.Column("post_id", db.Integer, db.ForeignKey("post.id", ondelete="CASCADE"), primary_key=True),
)


class Image(db.Model):
    """Модель загруженного изображения."""

    __tablename__ = "image"

    id = db.Column(db.Integer, primary_key=True)
    # Имя генерируется сервисом (uuid4 + расширение): уникально, длина 36+1+4.
    filename = db.Column(db.String(64), nullable=False, unique=True)
    # Nullable осознанно: None — файл, загруженный до ARC-0044 и принятый в
    # БД командой make-thumbs (бэкфилл); автор таких загрузок неизвестен.
    author_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True)
    created = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    author = db.relationship("User")
    posts = db.relationship("Post", secondary=image_post, back_populates="images", passive_deletes=True)

    def __init__(self, filename: str, author_id: int | None = None, created: datetime | None = None):
        """Загруженное изображение.

        Args:
            filename (str): Сгенерированное имя файла (uuid4 + расширение).
            author_id (int | None): Идентификатор загрузившего пользователя
                (None для файлов, принятых бэкфиллом до ARC-0044).
            created (datetime | None): Время загрузки.

        """
        super().__init__()
        self.filename = filename
        self.author_id = author_id
        self.created = created

    def __repr__(self) -> str:
        """Возвращает читаемое представление модели изображения.

        Returns:
            Строковое представление модели.
        """
        return f"<Image {self.filename!r}>"

    def to_dict(self) -> dict[str, Any]:
        """Приведение к словарю.

        Returns:
            Представление модели в виде словаря.
        """
        return {
            "id": self.id,
            "filename": self.filename,
            "url": f"/uploads/{self.filename}",
            "created": self.created.isoformat() if self.created else None,
            "author": {"id": self.author_id, "username": self.author.username if self.author else None},
        }
