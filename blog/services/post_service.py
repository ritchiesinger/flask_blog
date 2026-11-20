"""Бизнес-логика работы с постами."""

from flask_sqlalchemy.pagination import Pagination

from blog.constants import POSTS_PER_PAGE
from blog.extensions import db
from blog.models.image import Image
from blog.models.post import Post
from blog.services import uploads_service

from .base_errors import NotFoundError


def _sync_image_links(post: Post) -> None:
    """Синхронизирует связи поста с картинками по телу (→ ARC-0044).

    Набор связей перестраивается заново из UPLOAD_RE: вставленные картинки
    остаются, вырезанные — теряют связь (сироты дорабатывает clean-uploads).
    Ссылки на несуществующие в БД имена пропускаются — несуществующий
    /uploads/... в теле не создаёт пустую строку.

    Args:
        post: Пост с присвоенным (новым или обновлённым) телом.
    """
    referenced = set(uploads_service.UPLOAD_RE.findall(post.body or ""))
    if referenced:
        found = db.session.execute(
            db.select(Image).where(Image.filename.in_(referenced))
        ).scalars().all()
    else:
        found = []
    post.images = found


def list_posts(page: int = 1, per_page: int = POSTS_PER_PAGE) -> Pagination:
    """Возвращает страницу постов, новые первыми.

    Args:
        page: Номер страницы, начиная с 1; по умолчанию — первая.
        per_page: Размер страницы; по умолчанию POSTS_PER_PAGE.

    Returns:
        Объект Pagination: items — посты страницы, total, pages,
        has_prev/has_next.
    """
    stmt = db.select(Post).order_by(Post.created.desc(), Post.id.desc())
    return db.paginate(stmt, page=page, per_page=per_page, error_out=False)


def get_post(post_id: int) -> Post:
    """Возвращает пост по идентификатору.

    Args:
        post_id: Идентификатор поста.

    Returns:
        Модель поста.

    Raises:
        NotFoundError: Пост не существует.
    """
    post = db.session.get(Post, post_id)
    if post is None:
        raise NotFoundError(f"Post id {post_id} doesn't exist.")
    return post


def create_post(title: str, body: str, author_id: int) -> Post:
    """Создаёт пост, сохраняет его в базу и синхронизирует связи с картинками.

    Args:
        title: Заголовок поста.
        body: Тело поста.
        author_id: Идентификатор автора поста.

    Returns:
        Модель созданного поста.
    """
    post = Post(title=title, body=body, author_id=author_id)
    _sync_image_links(post)
    db.session.add(post)
    db.session.commit()
    return post


def update_post(post: Post, title: str, body: str) -> Post:
    """Обновляет заголовок, тело поста и пересобирает связи с картинками.

    Args:
        post: Модель поста.
        title: Новый заголовок.
        body: Новое тело.

    Returns:
        Обновлённая модель поста.
    """
    post.title = title
    post.body = body
    _sync_image_links(post)
    db.session.commit()
    return post


def delete_post(post: Post) -> None:
    """Удаляет пост.

    Args:
        post: Модель поста.
    """
    db.session.delete(post)
    db.session.commit()


def sync_all_post_links() -> int:
    """Пересобирает связи image_post для всех постов (одноразовая миграция).

    Посты, созданные до ARC-0044, не имеют записей в image_post: без
    пересборки clean-uploads считает их картинки сиротами и удаляет файлы.
    Вызывается CLI make-thumbs перед чисткой.

    Returns:
        Число постов, у которых набор связей изменился.
    """
    changed = 0
    for post in db.session.scalars(db.select(Post)).all():
        before = {image.id for image in post.images}
        _sync_image_links(post)
        db.session.flush()
        if {image.id for image in post.images} != before:
            changed += 1
    db.session.commit()
    return changed
