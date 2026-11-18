"""API-фасад от имени пользователя: подставляет его токен в каждый запрос."""

from typing import TYPE_CHECKING

from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from tests.tools.clients.api import Api

if TYPE_CHECKING:
    from tests.objects.user import UserObject


class ApiUserFacade:
    """Аутентифицированный фасад над Api: токен берётся из UserObject."""

    def __init__(self, app_client: FlaskClient, user: UserObject):
        """Связывает чистый Api с пользователем: токен фасад берёт из обёртки.

        Args:
            app_client: клиент, через который выполняются API-запросы.
            user: пользователь, от имени которого действует фасад.
        """
        self._api = Api(app_client=app_client)
        self._user = user

    def get_token(self, username: str | None = None, password: str | None = None) -> TestResponse:
        """Получение токена."""
        username = username if username is not None else self._user.db_model.username
        password = password if password is not None else self._user.password
        return self._api.auth.get_token(username=username, password=password)

    def create_post(self, title: str = "Заголовок статьи", body: str = "Пусто") -> TestResponse:
        """Создаёт пост от имени пользователя."""
        return self._api.posts.create(title=title, body=body, token=self._user.api_token)

    def edit_post(self, post_id: int, new_title: str | None = None, new_body: str | None = None) -> TestResponse:
        """Редактирует пост от имени пользователя."""
        return self._api.posts.update(
            post_id=post_id, title=new_title, body=new_body, token=self._user.api_token,
        )

    def delete_post(self, post_id: int) -> TestResponse:
        """Удаляет пост от имени пользователя."""
        return self._api.posts.delete(post_id=post_id, token=self._user.api_token)

    def get_posts_list(self, page: int | None = None, per_page: int | None = None) -> TestResponse:
        """Получает список постов — эндпоинт публичный, токен не нужен.

        Args:
            page: номер страницы; None — параметр не передаётся.
            per_page: размер страницы; None — параметр не передаётся.
        """
        return self._api.posts.list(page=page, per_page=per_page)

    def list_users(self, page: int | None = None, per_page: int | None = None) -> TestResponse:
        """Получает список пользователей с пагинацией (эндпоинт администратора).

        Args:
            page: номер страницы; None — параметр не передаётся.
            per_page: размер страницы; None — параметр не передаётся.
        """
        return self._api.users.list(token=self._user.api_token, page=page, per_page=per_page)

    def delete_user(self, user_id: int) -> TestResponse:
        """Удаляет пользователя от имени пользователя."""
        return self._api.users.delete(user_id=user_id, token=self._user.api_token)

    def create_comment(self, post_id: int, body: str = "Текст комментария") -> TestResponse:
        """Создаёт комментарий к посту от имени пользователя."""
        return self._api.comments.create(post_id=post_id, body=body, token=self._user.api_token)

    def edit_comment(self, comment_id: int, new_body: str | None = None) -> TestResponse:
        """Редактирует комментарий от имени пользователя."""
        return self._api.comments.update(comment_id=comment_id, body=new_body, token=self._user.api_token)

    def delete_comment(self, comment_id: int) -> TestResponse:
        """Удаляет комментарий от имени пользователя."""
        return self._api.comments.delete(comment_id=comment_id, token=self._user.api_token)

    def get_comments_list(self, post_id: int) -> TestResponse:
        """Получает список комментариев поста — эндпоинт публичный."""
        return self._api.comments.list_for_post(post_id=post_id)
