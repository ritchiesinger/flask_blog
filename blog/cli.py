"""Команды консольной утилиты работы с приложением."""

from os import listdir, path, remove
from typing import cast

import click
from flask import current_app
from flask.cli import with_appcontext

from blog.constants import Roles
from blog.extensions import db
from blog.models import Post, User
from blog.services import uploads_service, user_service
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
    """Создать администратора в БД.

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
def clean_uploads() -> None:
    """Удаляет файлы изображений, на которые не ссылается ни один пост.

    Сиротой считается файл в папке uploads, путь /uploads/<имя> которого
    не встречается ни в одном теле поста — в том числе загруженный, но не
    вставленный в текст (файл будет удалён при следующей чистке, это
    осознанное поведение). Комментарии не сканируются: они plain text
    по дизайну, картинок в них нет.
    """
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    referenced: set[str] = set()
    for (body,) in db.session.execute(db.select(Post.body)):
        if body:
            referenced.update(uploads_service.UPLOAD_RE.findall(body))

    deleted = 0
    if path.isdir(upload_folder):
        for name in listdir(upload_folder):
            if name not in referenced:
                remove(path.join(upload_folder, name))
                deleted += 1
    click.echo(f"Удалено файлов-сирот: {deleted}.")
