"""Бизнес-логика аутентификации и регистрации пользователей."""

from blog.extensions import db
from blog.models import User
from blog.services.base_errors import BadRequestError, ConflictError


def authenticate(username: str, password: str) -> User | None:
    """Возвращает пользователя, если логин и пароль верны, иначе None."""
    user = db.session.execute(db.select(User).filter_by(username=username)).scalars().first()
    if user is None or not user.check_password(password):
        return None
    return user


def register_user(username: str, password: str) -> User:
    """Создаёт пользователя с проверкой логина и пароля.

    Args:
        username: Имя пользователя (логин).
        password: Пароль в открытом виде (хешируется внутри).

    Returns:
        Модель созданного пользователя.

    Raises:
        BadRequestError: Пустое имя или пароль короче 4 символов.
        ConflictError: Пользователь с таким именем уже существует.
    """
    if not username or not username.strip():
        raise BadRequestError("Имя пользователя не может быть пустым.")

    if len(password) < 4:
        raise BadRequestError("Пароль должен быть не короче 4 символов.")

    if db.session.execute(db.select(User).filter_by(username=username)).scalars().first():
        raise ConflictError(f"Пользователь с именем '{username}' уже существует.")

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return user
