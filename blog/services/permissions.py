"""Единая модель прав на контент для WEB и API.

Единственное место, где описано, кто и что может делать с сущностями: автор — любое действие со своим;
администратору разрешено только удаление чужого (редактирование остаётся авторским); остальным — ничего.
"""

from enum import Enum

from blog.constants import Roles
from blog.models.user import User

from .base_errors import ForbiddenError


class Action(Enum):
    """Действия над сущностью, требующие проверки прав."""

    UPDATE = "update"
    DELETE = "delete"


_ADMIN_MAY: frozenset[Action] = frozenset({Action.DELETE})


def ensure_allowed(author_id: int, *, actor: User, action: Action, subject: str) -> None:
    """Проверяет право актёра на действие над сущностью автора.

    Автору разрешено любое действие над своей сущностью; администратору — только действия из _ADMIN_MAY над
    чужой (сейчас — удаление); остальным — ничего.

    Args:
        author_id: Идентификатор автора сущности.
        actor: Действующий пользователь (Flask-Login и JWT загружают одну модель User).
        action: Совершаемое действие.
        subject: Название сущности в родительном падеже для текста ошибки («поста», «комментария»).

    Raises:
        ForbiddenError: Права на действие отсутствуют.
    """
    if actor.id == author_id:
        return
    if actor.role == Roles.ADMIN and action in _ADMIN_MAY:
        return
    raise ForbiddenError(f"Вы не являетесь автором этого {subject}!")
