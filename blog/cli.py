"""Команды консольной утилиты работы с приложением."""

from typing import cast

import click
from flask import current_app
from flask.cli import with_appcontext

from blog.constants import Roles
from blog.extensions import db
from blog.models import Image, User
from blog.services import post_service, uploads_service, user_service
from blog.services.base_errors import ConflictError, NotFoundError


@click.command("make-admin")
@click.argument("username")
@with_appcontext
def make_admin(username: str):
    """Делает существующего пользователя администратором.

    Args:
        username: Логин пользователя которого надо сделать администратором.
    """
    user = db.session.execute(db.select(User).filter_by(username=username)).scalars().first()
    if not user:
        click.echo(f"Пользователь {username} не найден!")
        return
    user.role = Roles.ADMIN
    db.session.commit()
    click.echo(f"{username} теперь администратор (role={user.role})")


make_admin = cast(click.Command, make_admin)


@click.command("create-admin")
@click.argument("username")
@click.argument("password")
@with_appcontext
def create_admin(username: str, password: str):
    """Создать администратор в БД.

    Args:
        username: Логин создаваемого администратора.
        password: Пароль создаваемого администратора.
    """
    user = db.session.execute(db.select(User).filter_by(username=username)).scalars().first()
    if user:
        click.echo(f"Пользователь {username} уже существует.")
        return
    admin = User(username=username, role=Roles.ADMIN)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    click.echo(f"Администратор {username} создан.")


create_admin = cast(click.Command, create_admin)


@click.command("make-superadmin")
@click.argument("username")
@with_appcontext
def make_superadmin(username: str):
    """Выдаёт пользователю роль SuperAdministrator.

    Роль уникальна: если SuperAdministrator уже существует, команда откажется.
    Смена хозяина блога — через CLI: удалить текущего супер-админа
    (delete-user), затем выдать роль новому.

    Args:
        username: Логин пользователя, который станет SuperAdministrator.
    """
    try:
        user_service.promote_to_superadmin(username)
    except NotFoundError:
        click.echo(f"Пользователь {username} не найден!")
        return
    except ConflictError as error:
        click.echo(str(error))
        return
    click.echo(f"{username} теперь SuperAdministrator (role={Roles.SUPERADMIN})")


make_superadmin = cast(click.Command, make_superadmin)


@click.command("delete-user")
@click.argument("username")
@with_appcontext
def delete_user(username: str):
    """Удаляет пользователя целиком: посты и комментарии уходят каскадом БД.

    Загруженные картинки остаются до чистки clean-uploads.

    Args:
        username: Логин удаляемого пользователя.
    """
    try:
        user = user_service.get_user_by_username(username)
        user_service.delete_user(user.id)
    except NotFoundError:
        click.echo(f"Пользователь {username} не найден!")
        return
    click.echo(f"Пользователь {username} удалён.")


delete_user = cast(click.Command, delete_user)


@click.command("clean-uploads")
@with_appcontext
def clean_uploads() -> None:
    """Удаляет изображения-сироты: строки БД без связей и файлы без строк.

    Источник истины — БД (→ ARC-0044). Сирота-строка — Image без записей в
    image_post: загруженная, но не вставленная картинка удаляется при
    следующей чистке (осознанное поведение, как и раньше). Файл без строки —
    дрейф (загрузки до ARC-0044 после прогонов make-thumbs): удаляется.
    Миниатюра удаляется вместе с детальной версией. Комментарии не
    участвуют: plain text по дизайну, картинок в них нет.
    """
    folder = current_app.config["UPLOAD_FOLDER"]
    orphans = db.session.execute(
        db.select(Image).where(~Image.posts.any())
    ).scalars().all()
    removed_rows = 0
    for image in orphans:
        uploads_service.delete_image_files(folder, image.filename)
        db.session.delete(image)
        removed_rows += 1
    db.session.commit()

    drift = uploads_service.find_drift_files(folder)
    for name in drift:
        uploads_service.delete_image_files(folder, name)
    click.echo(f"Удалено строк-сирот: {removed_rows}. Удалено файлов-дрейфа: {len(drift)}.")


clean_uploads = cast(click.Command, clean_uploads)


@click.command("make-thumbs")
@with_appcontext
def make_thumbs() -> None:
    """Бэкфилл БД, миниатюры и пересборка связей постов (→ ARC-0044).

    Одна команда закрывает миграцию старого сервера: файлы без строк
    принимаются в БД (author_id=None — автор неизвестен), генерируются
    недостающие миниатюры, для всех постов пересобираются связи
    image_post (посты, созданные до раунда, связей не имеют — без этого
    clean-uploads удалил бы их картинки как сироты). GIF не обрабатываются
    по дизайну: строка создаётся, миниатюра не генерируется. Команда
    идемпотентна и пригодна для регенерации при смене THUMB_MAX_SIDE.
    """
    folder = current_app.config["UPLOAD_FOLDER"]
    existing = set(db.session.scalars(db.select(Image.filename)).all())
    adopted, thumbs = uploads_service.backfill_files(folder, existing)
    synced = post_service.sync_all_post_links()
    click.echo(
        f"Принято в БД: {adopted}. Сгенерировано миниатюр: {thumbs}. "
        f"Связей пересобрано: {synced}."
    )

