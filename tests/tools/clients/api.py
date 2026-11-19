"""Объектные обёртки над Flask-тестовым клиентом для вызовов API.

Каждый класс отвечает за свой раздел API и строится поверх общего `BaseClient`, который инкапсулирует формирование
параметров запроса (json-тело, заголовок Authorization) и работу с тестовым клиентом приложения. Эндпоинты берутся
из `tests.constants.endpoints.APIEndpoints`, поэтому в тестах адреса не задаются строками вручную.

Использование: тест собирает `Api` поверх клиента из фикстуры `setup_app_client` и вызывает методы вида
`api.auth.get_token(...)`.
"""

from typing import Any

from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from tests.constants.endpoints import APIEndpoints


class BaseClient:
    """Базовый класс API-клиентов с методами отправки HTTP-запросов.

    Хранит ссылку на тестовый клиент приложения и предоставляет приватные
    хелперы ``_post``/``_patch``/``_get``/``_delete``, которые собирают
    параметры запроса: json-тело и заголовок Authorization с Bearer-токеном.
    """

    def __init__(self, app_client: FlaskClient):
        """Сохраняет тестовый клиент приложения для последующих запросов.

        :param app_client: Клиент Flask-приложения (например, из фикстуры
            ``setup_app_client``).
        """
        self._app_client = app_client

    def _post(
            self,
            endpoint: str,
            json: dict[str, Any] | None = None,
            token: str | None = None
    ) -> TestResponse:
        """Отправляет POST-запрос на эндпоинт.

        :param endpoint: Адрес эндпоинта.
        :param json: JSON-тело запроса; None — тело не отправляется.
        :param token: Bearer-токен; None — запрос без авторизации.
        :return: Ответ приложения.
        """
        request_params = {
            **({"json": json} if json else {}),
            **({"headers": {"Authorization": f"Bearer {token}"}} if token is not None else {}),
        }
        return self._app_client.post(endpoint, **request_params)

    def _patch(
            self,
            endpoint: str,
            json: dict[str, Any] | None = None,
            token: str | None = None
    ) -> TestResponse:
        """Отправляет PATCH-запрос на эндпоинт. Параметры и поведение аналогичны `_post`."""
        request_params = {
            **({"json": json} if json else {}),
            **({"headers": {"Authorization": f"Bearer {token}"}} if token is not None else {}),
        }
        return self._app_client.patch(endpoint, **request_params)

    def _get(
            self,
            endpoint: str,
            token: str | None = None,
            query: dict[str, Any] | None = None,
    ) -> TestResponse:
        """Отправляет GET-запрос на эндпоинт.

        :param endpoint: Адрес эндпоинта.
        :param token: Bearer-токен; None — запрос без авторизации.
        :param query: Query-параметры; None или пустой словарь — без строки запроса.
        :return: Ответ приложения.
        """
        request_params = {
            **({"headers": {"Authorization": f"Bearer {token}"}} if token is not None else {}),
            **({"query_string": query} if query else {}),
        }
        return self._app_client.get(endpoint, **request_params)

    def _delete(self, endpoint: str, token: str | None = None) -> TestResponse:
        """Отправляет DELETE-запрос на эндпоинт. Параметры и поведение аналогичны `_get`."""
        request_params = {**({"headers": {"Authorization": f"Bearer {token}"}} if token is not None else {})}
        return self._app_client.delete(endpoint, **request_params)


class Auth(BaseClient):
    """Обёртка над эндпоинтами аутентификации."""

    def __init__(self, app_client: FlaskClient):
        """Инициализирует раздел аутентификации.

        :param app_client: Клиент Flask-приложения.
        """
        super().__init__(app_client)
        self._endpoints = APIEndpoints.AUTH

    def get_token(self, username: str, password: str) -> TestResponse:
        """Запрашивает токен по логину и паролю.

        :param username: Имя пользователя.
        :param password: Пароль.
        :return: Ответ с токеном или ошибкой аутентификации.
        """
        return self._post(endpoint=self._endpoints.TOKEN, json={"username": username, "password": password})

    def register(self, username: str, password: str) -> TestResponse:
        """Регистрирует нового пользователя.

        :param username: Имя пользователя.
        :param password: Пароль.
        :return: Ответ приложения (успех или ошибка валидации).
        """
        return self._post(endpoint=self._endpoints.REGISTER, json={"username": username, "password": password})


class Posts(BaseClient):
    """Обёртка над эндпоинтами постов."""

    def __init__(self, app_client: FlaskClient):
        """Инициализирует раздел постов.

        :param app_client: Клиент Flask-приложения.
        """
        super().__init__(app_client)
        self._endpoints = APIEndpoints.POSTS

    def create(self, title: str | None = None, body: str | None = None, token: str | None = None) -> TestResponse:
        """Создаёт пост с указанными полями. Поля со значением None или пустой строкой в тело не включаются.

        :param title: Заголовок поста; None — поле отсутствует в теле.
        :param body: Текст поста; None — поле отсутствует в теле.
        :param token: Bearer-токен автора; None — запрос без авторизации.
        :return: Ответ приложения.
        """
        create_params = {"title": title, "body": body}
        json_payload = {param_name: value for param_name, value in create_params.items() if value}
        return self._post(endpoint=self._endpoints.POSTS, json=json_payload, token=token)

    def list(
            self,
            token: str | None = None,
            page: int | None = None,
            per_page: int | None = None,
    ) -> TestResponse:
        """Возвращает список постов с пагинацией.

        :param token: Bearer-токен; None — запрос без авторизации.
        :param page: номер страницы; None — параметр не передаётся.
        :param per_page: размер страницы; None — параметр не передаётся.
        :return: Ответ приложения.
        """
        query = {
            **({"page": page} if page is not None else {}),
            **({"per_page": per_page} if per_page is not None else {}),
        }
        return self._get(endpoint=self._endpoints.POSTS, token=token, query=query or None)

    def update(
            self,
            post_id: int,
            title: str | None = None,
            body: str | None = None,
            token: str | None = None,
    ) -> TestResponse:
        """Частично обновляет пост по идентификатору.

        Как и в `create`, поля со значением None или пустой строкой в тело не включаются.

        :param post_id: Идентификатор поста.
        :param title: Новый заголовок; None — поле не меняется.
        :param body: Новый текст; None — поле не меняется.
        :param token: Bearer-токен автора; None — запрос без авторизации.
        :return: Ответ приложения.
        """
        edit_params = {"title": title, "body": body}
        json_payload = {param_name: value for param_name, value in edit_params.items() if value}
        return self._patch(endpoint=self._endpoints.POST.format(post_id), json=json_payload, token=token)

    def delete(self, post_id: int, token: str | None = None) -> TestResponse:
        """Удаляет пост по идентификатору.

        :param post_id: Идентификатор поста.
        :param token: Bearer-токен автора; None — запрос без авторизации.
        :return: Ответ приложения.
        """
        return self._delete(endpoint=self._endpoints.POST.format(post_id), token=token)


class CommentsApi(BaseClient):
    """Обёртка над эндпоинтами API комментариев."""

    def __init__(self, app_client: FlaskClient):
        """Инициализирует раздел комментариев.

        :param app_client: Клиент Flask-приложения.
        """
        super().__init__(app_client)
        self._endpoints = APIEndpoints.POSTS

    def list_for_post(
            self,
            post_id: int,
            token: str | None = None,
            page: int | None = None,
            per_page: int | None = None,
    ) -> TestResponse:
        """Возвращает список комментариев поста в конверте с пагинацией.

        :param post_id: Идентификатор поста.
        :param token: Bearer-токен; None — запрос без авторизации (эндпоинт публичный).
        :param page: Номер страницы; None — параметр не передаётся.
        :param per_page: Размер страницы; None — параметр не передаётся.
        :return: Ответ приложения.
        """
        query = {
            **({"page": page} if page is not None else {}),
            **({"per_page": per_page} if per_page is not None else {}),
        }
        return self._get(
            self._endpoints.POST_COMMENTS.format(post_id=post_id),
            token=token,
            query=query or None,
        )

    def create(self, post_id: int, body: str, token: str | None = None) -> TestResponse:
        """Создаёт комментарий к посту.

        :param post_id: Идентификатор поста.
        :param body: Текст комментария.
        :param token: Bearer-токен; None — запрос без авторизации.
        :return: Ответ приложения.
        """
        return self._post(self._endpoints.POST_COMMENTS.format(post_id=post_id), json={"body": body}, token=token)

    def update(self, comment_id: int, body: str | None = None, token: str | None = None) -> TestResponse:
        """Обновляет комментарий.

        :param comment_id: Идентификатор комментария.
        :param body: Новый текст; None — запрос без ключа 'body' (частичное обновление).
        :param token: Bearer-токен; None — запрос без авторизации.
        :return: Ответ приложения.
        """
        json_payload = {"body": body} if body is not None else {}
        return self._patch(self._endpoints.COMMENT.format(comment_id=comment_id), json=json_payload, token=token)

    def delete(self, comment_id: int, token: str | None = None) -> TestResponse:
        """Удаляет комментарий.

        :param comment_id: Идентификатор комментария.
        :param token: Bearer-токен; None — запрос без авторизации.
        :return: Ответ приложения.
        """
        return self._delete(self._endpoints.COMMENT.format(comment_id=comment_id), token=token)


class Users(BaseClient):
    """Обёртка над эндпоинтами пользователей."""

    def __init__(self, app_client: FlaskClient):
        """Инициализирует раздел пользователей.

        :param app_client: Клиент Flask-приложения.
        """
        super().__init__(app_client)
        self._endpoints = APIEndpoints.USERS

    def list(
            self,
            token: str | None = None,
            page: int | None = None,
            per_page: int | None = None,
    ) -> TestResponse:
        """Возвращает список пользователей с пагинацией (эндпоинт администратора).

        :param token: Bearer-токен администратора; None — запрос без авторизации.
        :param page: Номер страницы; None — параметр не передаётся.
        :param per_page: Размер страницы; None — параметр не передаётся.
        :return: Ответ приложения.
        """
        query = {
            **({"page": page} if page is not None else {}),
            **({"per_page": per_page} if per_page is not None else {}),
        }
        return self._get(endpoint=self._endpoints.USERS, token=token, query=query or None)

    def change_role(self, user_id: int, role: str | None = None, token: str | None = None) -> TestResponse:
        """Меняет роль пользователя (эндпоинт супер-администратора).

        Ключ роли в тело не включается, если role — None или пустая строка:
        тест «запрос без ключа role» собирается ролью None.

        :param user_id: Идентификатор пользователя.
        :param role: Новая роль; None — запрос без ключа 'role' в теле.
        :param token: Bearer-токен супер-администратора; None — запрос без авторизации.
        :return: Ответ приложения.
        """
        json_payload = {"role": role} if role else {}
        return self._patch(endpoint=self._endpoints.USER.format(user_id), json=json_payload, token=token)

    def delete(self, user_id: int, token: str | None = None) -> TestResponse:
        """Удаляет пользователя по идентификатору (эндпоинт администратора).

        :param user_id: Идентификатор пользователя.
        :param token: Bearer-токен администратора; None — запрос без авторизации.
        :return: Ответ приложения.
        """
        return self._delete(endpoint=self._endpoints.USER.format(user_id), token=token)


class Api:
    """Фасад над разделами API: auth, posts, comments, users.

    Единственная точка входа для тестов: создаётся поверх клиент-фикстуры
    и открывает разделы как атрибуты — ``api.auth.register(...)``,
    ``api.posts.create(...)``, ``api.users.delete(...)``.
    """

    def __init__(self, app_client: FlaskClient):
        """Собирает все разделы API поверх одного тестового клиента.

        :param app_client: Клиент Flask-приложения.
        """
        self._app_client = app_client
        self.auth = Auth(self._app_client)
        self.posts = Posts(self._app_client)
        self.comments = CommentsApi(self._app_client)
        self.users = Users(self._app_client)
