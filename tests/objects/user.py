"""Обёртка пользователя: фасады API и WEB, действующие от его имени."""

from flask.testing import FlaskClient
from glamor import step

from blog.models import User
from tests.tools.asserters.base_asserters import assert_condition, assert_status_code
from tests.tools.clients.api_user_facade import ApiUserFacade
from tests.tools.clients.web_client import WebClient


class UserObject:
    """Пользователь теста: модель из БД, персональные данные и клиенты по слоям."""

    def __init__(self, client: FlaskClient, db_model: User, password: str):
        """Инициализирует обёртку над пользователем.

        Args:
            client: клиент, от имени которого выполняются запросы; на нём же живёт web-сессия.
            db_model: модель пользователя из БД.
            password: пароль открытым текстом — нужен для получения токена и web-логина.
        """
        self._flask_client = client
        self.db_model = db_model
        self.password = password
        self._api_token: str | None = None
        self.api = ApiUserFacade(app_client=self._flask_client, user=self)
        self.web = WebClient(app_client=self._flask_client)

    @property
    def client(self) -> FlaskClient:
        """Клиент, от имени которого действуют фасады: для ORM-посева и прямых запросов (→ ARC-0061)."""
        return self._flask_client

    @property
    def api_token(self) -> str:
        """JWT-токен пользователя: при первом обращении запрашивается и кэшируется."""
        if not self._api_token:
            with step("Получение JWT токена"):
                response = self.api.get_token()
                assert_status_code(expect=200, response=response)
                data = response.get_json()
                assert_condition(
                    condition=data.get("access_token") is not None,
                    allure_step_name="В теле ответа найден 'access_token'",
                    error_text="Токен не найден в ответе!",
                )
                self._api_token = data["access_token"]
        return self._api_token

    def refresh_api_token(self) -> str:
        """Сбрасывает кэш токена и возвращает полученный."""
        self._api_token = None
        return self.api_token
