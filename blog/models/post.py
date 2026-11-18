"""Модель поста."""

from datetime import UTC, datetime
from typing import Any

from blog.extensions import db
from blog.models.comment import Comment


class Post(db.Model):
    """Модель поста."""
    __tablename__ = "post"

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    comment_count = db.column_property(
        db.select(db.func.count(Comment.id))
        .where(Comment.post_id == id)
        .correlate_except(Comment)
        .scalar_subquery()
    )

    author = db.relationship("User", back_populates="posts")
    comments = db.relationship(
        "Comment",
        back_populates="post",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, title: str, body: str, author_id: int, created: datetime | None = None):
        """Запись блога (пост).

        Args:
            title (str): Заголовок поста.
            body (str): Тело поста.
            author_id (int): Идентификатор автора.
            created (datetime | None): Время создания.

        """
        super().__init__()
        self.title = title
        self.body = body
        self.author_id = author_id
        self.created = created

    def __repr__(self) -> str:
        """Возвращает читаемое представление модели поста.

        Returns:
            Строковое представление модели.
        """
        return f"<Post {self.title!r}>"

    def to_dict(self) -> dict[str, Any]:
        """Приведение к словарю.

        Returns:
            Представление модели в виде словаря.
        """
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "created": self.created.isoformat() if self.created else None,
            "author": {"id": self.author_id, "username": self.author.username},
        }
