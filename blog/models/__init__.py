"""Модели приложения. Собирает модели в одной точке импорта."""

from blog.models.comment import Comment
from blog.models.image import Image, image_post
from blog.models.post import Post
from blog.models.user import User

__all__ = ["User", "Post", "Comment", "Image", "image_post"]
