"""Модель комментария."""

from datetime import UTC, datetime
from typing import Any

from blog.extensions import db


class Comment(db.Model):
    """Модель комментария."""

    __tablename__ = "comment"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id", ondelete="CASCADE"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    body = db.Column(db.Text, nullable=False)

    post = db.relationship("Post", back_populates="comments")
    author = db.relationship("User", back_populates="comments")

    def __init__(self, body: str, post_id: int, author_id: int, created: datetime | None = None):
        """Комментарий к посту.

        Args:
            body (str): Текст комментария.
            post_id (int): Идентификатор поста.
            author_id (int): Идентификатор автора.
            created (datetime | None): Время создания.

        """
        super().__init__()
        self.body = body
        self.post_id = post_id
        self.author_id = author_id
        self.created = created

    def __repr__(self) -> str:
        """Возвращает читаемое представление модели комментария.

        Returns:
            Строковое представление модели.
        """
        return f"<Comment {self.body!r}>"

    def to_dict(self) -> dict[str, Any]:
        """Приведение к словарю.

        Returns:
            Представление модели в виде словаря.
        """
        return {
            "id": self.id,
            "post_id": self.post_id,
            "body": self.body,
            "created": self.created.isoformat() if self.created else None,
            "author": {"id": self.author_id, "username": self.author.username},
        }
