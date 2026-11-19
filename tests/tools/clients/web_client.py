"""WEB-клиент: действия с web-роутами. Сессия живёт на переданном FlaskClient."""

from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from tests.constants.web_endpoints import WebEndpoints


class WebClient:
    """Клиент web-интерфейса: фасады по разделам поверх общего FlaskClient."""

    def __init__(self, app_client: FlaskClient):
        """Создаёт клиент web-интерфейса и его фасады по разделам.

        Args:
            app_client: клиент, через который выполняются web-запросы; на нём же живёт сессия после логина.
        """
        self.app_client = app_client
        self.auth = _WebAuth(client=self)
        self.posts = _WebPosts(client=self)
        self.comments = _WebComments(client=self)
        self.admin = _Admin(client=self)
        self.uploads = _WebUploads(client=self)
        self.users = _WebUsers(client=self)


class _Admin:
    """Фасад WEB-админки: сырые ответы без ассертов."""

    def __init__(self, client: WebClient):
        self._client = client

    def users(self):
        """GET списка пользователей."""
        return self._client.app_client.get(WebEndpoints.ADMIN.USERS)

    def delete_user(self, user_id):
        """POST удаления пользователя."""
        return self._client.app_client.post(WebEndpoints.ADMIN.DELETE_USER.format(user_id=user_id))



class _WebAuth:
    """Аутентификация через web-форму."""

    def __init__(self, client: WebClient):
        self._client = client

    def login(self, username: str, password: str, next_url: str | None = None) -> TestResponse:
        """Логинит через форму; сессия закрепляется на клиенте.

        Args:
            username: имя пользователя.
            password: пароль открытым текстом.
            next_url: необязательный next-параметр строки запроса.
        """
        url = WebEndpoints.AUTH.LOGIN
        if next_url:
            url = f"{url}?next={next_url}"
        return self._client.app_client.post(url, data={"username": username, "password": password})

    def login_form(self) -> TestResponse:
        """Открывает страницу логина — публичная."""
        return self._client.app_client.get(WebEndpoints.AUTH.LOGIN)

    def logout(self) -> TestResponse:
        """Выполняет выход GET-запросом; редирект не следует автоматически."""
        return self._client.app_client.get(WebEndpoints.AUTH.LOGOUT)

    def register(self, username: str, password: str) -> TestResponse:
        """Отправляет форму регистрации; редирект не следует автоматически."""
        return self._client.app_client.post(
            WebEndpoints.AUTH.REGISTER, data={"username": username, "password": password},
        )

    def register_form(self) -> TestResponse:
        """Открывает страницу регистрации — публичная."""
        return self._client.app_client.get(WebEndpoints.AUTH.REGISTER)


class _WebPosts:
    """Действия с постами через web-роуты."""

    def __init__(self, client: WebClient):
        self._client = client

    def index(self, page: int | None = None) -> TestResponse:
        """Открывает главную страницу со списком постов — публичная.

        Args:
            page: номер страницы; None — параметр в запрос не передаётся.
        """
        query = {"page": page} if page is not None else None
        return self._client.app_client.get(WebEndpoints.POSTS.INDEX, query_string=query)

    def create(self, title: str, body: str) -> TestResponse:
        """Отправляет форму создания поста — требует сессию на клиенте."""
        return self._client.app_client.post(WebEndpoints.POSTS.CREATE, data={"title": title, "body": body})

    def view(self, post_id: int) -> TestResponse:
        """Открывает страницу поста — публичная."""
        return self._client.app_client.get(WebEndpoints.POSTS.VIEW.format(post_id=post_id))

    def update(self, post_id: int, title: str, body: str) -> TestResponse:
        """Отправляет форму редактирования поста — требует сессию на клиенте."""
        return self._client.app_client.post(
            WebEndpoints.POSTS.UPDATE.format(post_id=post_id),
            data={"title": title, "body": body},
        )

    def delete(self, post_id: int) -> TestResponse:
        """Удаляет пост POST-ом — требует сессию на клиенте."""
        return self._client.app_client.post(WebEndpoints.POSTS.DELETE.format(post_id=post_id))

    def create_form(self) -> TestResponse:
        """Открывает форму создания поста — требует сессию на клиенте."""
        return self._client.app_client.get(WebEndpoints.POSTS.CREATE)

    def update_form(self, post_id: int) -> TestResponse:
        """Открывает форму редактирования поста — требует сессию на клиенте."""
        return self._client.app_client.get(WebEndpoints.POSTS.UPDATE.format(post_id=post_id))


class _WebComments:
    """Фасад WEB-комментариев: сырые ответы без assert."""

    def __init__(self, client: WebClient):
        self._client = client

    def view_post(self, post_id: int, page: int | str | None = None) -> TestResponse:
        """GET страницы поста — публичная.

        Args:
            post_id: идентификатор поста.
            page: номер страницы комментариев; None — параметр не передаётся.
        """
        query = {"page": page} if page is not None else None
        return self._client.app_client.get(
            WebEndpoints.POSTS.VIEW.format(post_id=post_id), query_string=query,
        )

    def create_comment(self, post_id: int, body: str) -> TestResponse:
        """POST формы комментария; редирект не следует автоматически."""
        return self._client.app_client.post(
            WebEndpoints.COMMENTS.CREATE.format(post_id=post_id), data={"body": body},
        )

    def update_comment_form(self, comment_id: int) -> TestResponse:
        """GET формы редактирования комментария."""
        return self._client.app_client.get(WebEndpoints.COMMENTS.UPDATE.format(comment_id=comment_id))

    def update_comment(self, comment_id: int, body: str) -> TestResponse:
        """POST формы редактирования; редирект не следует автоматически."""
        return self._client.app_client.post(
            WebEndpoints.COMMENTS.UPDATE.format(comment_id=comment_id), data={"body": body},
        )

    def delete_comment(self, comment_id: int) -> TestResponse:
        """POST формы удаления; редирект не следует автоматически."""
        return self._client.app_client.post(WebEndpoints.COMMENTS.DELETE.format(comment_id=comment_id))


class _WebUploads:
    """Загрузка изображений: multipart-запросы от имени текущей сессии."""

    def __init__(self, client: WebClient):
        self._client = client

    def upload(self, stream, filename: str) -> TestResponse:
        """POST загрузки изображения; файл уходит multipart-полем 'file'.

        Args:
            stream: байтовый поток содержимого файла (BytesIO).
            filename: имя файла с расширением — его проверяет валидация.
        """
        return self._client.app_client.post(
            WebEndpoints.UPLOADS.UPLOAD,
            data={"file": (stream, filename)},
            content_type="multipart/form-data",
        )

    def posts_no_file(self) -> TestResponse:
        """POST /uploads без поля 'file' — для проверки ошибки отсутствия файла."""
        return self._client.app_client.post(
            WebEndpoints.UPLOADS.UPLOAD,
            data={},
            content_type="multipart/form-data",
        )


class _WebUsers:
    """Фасад WEB-профиля: сырые ответы без ассертов."""

    def __init__(self, client: WebClient):
        self._client = client

    def profile(
            self,
            username: str,
            tab: str | None = None,
            page: int | str | None = None,
    ) -> TestResponse:
        """GET страницы профиля — публичная.

        Args:
            username: логин пользователя.
            tab: вкладка ленты (posts/comments); None — параметр не передаётся.
            page: номер страницы активной ленты; None — не передаётся.
        """
        query = {}
        if tab is not None:
            query["tab"] = tab
        if page is not None:
            query["page"] = page
        return self._client.app_client.get(
            WebEndpoints.USER.PROFILE.format(username=username),
            query_string=query or None,
        )
