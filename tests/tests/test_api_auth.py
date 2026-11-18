"""Тесты API-аутентификации: получение JWT-токена и регистрация."""

from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_status_code
from tests.tools.clients.api import Api


@epic("API")
@feature("Аутентификация")
@story("Получение токена")
class TestToken:
    """Проверки выдачи JWT-токена: успех и отказы при неверных учётных данных."""

    @title("Токен выдаётся пользователю с корректными учётными данными")
    @severity(severity_level.BLOCKER)
    def test_token_success(self, setup_test_user: UserObject):
        """Корректные учётные данные проходят аутентификацию, в ответе — непустой access_token.

        Валидность самого токена здесь не проверяется: она доказывается работой
        защищённых эндпоинтов в других модулях.
        """
        user = setup_test_user
        with step("Пользователь. API. Запрос токена"):
            response = user.api.get_token(username=user.db_model.username, password=user.password)
            assert_status_code(expect=200, response=response)
            token = response.get_json()["access_token"]
            assert_condition(
                condition=bool(token),
                allure_step_name="В ответе присутствует непустой access_token",
                error_text="Поле access_token отсутствует или пусто!",
            )

    @title("Получение ошибки при запросе токена с неверным паролем")
    @severity(severity_level.CRITICAL)
    def test_token_wrong_password(self, setup_test_user: UserObject):
        """Неверный пароль отклоняется: аутентификация не проходит.

        Ожидание: 401 и поле error в JSON (JWT-конфигурация отдаёт ошибки с ключом
        ``error``). Код именно 401, а не 400: личность по имени установлена,
        но учётные данные не подтверждаются.
        """
        user = setup_test_user
        with step("Пользователь. API. Попытка получения токена с неверным паролем"):
            response = user.api.get_token(username=user.db_model.username, password="wrong_password")
            assert_status_code(expect=401, response=response)
            assert_condition(
                condition="error" in response.get_json(),
                allure_step_name="В ответе присутствует поле error",
                error_text="Поле error отсутствует в JSON ответа!",
            )

    @title("Получение ошибки при запросе токена с несуществующим именем")
    @severity(severity_level.CRITICAL)
    def test_token_unknown_user(self, setup_app_client: FlaskClient):
        """Несуществующее имя отклоняется тем же ответом, что и неверный пароль.

        Ожидание совпадает с ``test_token_wrong_password`` (401 и error): единый
        ответ не раскрывает, существует ли пользователь.
        """
        api = Api(setup_app_client)
        with step("API. Попытка получения токена с несуществующим именем"):
            response = api.auth.get_token(username="unknown", password="password123")
            assert_status_code(expect=401, response=response)
            assert_condition(
                condition="error" in response.get_json(),
                allure_step_name="В ответе присутствует поле error",
                error_text="Поле error отсутствует в JSON ответа!",
            )


@epic("API")
@feature("Аутентификация")
@story("Регистрация")
class TestRegister:
    """Проверки регистрации через API."""


    @title("Успешная регистрация нового пользователя")
    @severity(severity_level.BLOCKER)
    def test_register_success(self, setup_app_client: FlaskClient):
        """Регистрация несуществующего имени создаёт учётную запись.

        Ожидание: код 201 и данные созданного пользователя в ответе —
        ``{"user": {"id": ..., "username": ...}}``.
        """
        api = Api(setup_app_client)
        with step("API. Регистрация нового пользователя"):
            response = api.auth.register(username="apiuser", password="password123")
            assert_status_code(expect=201, response=response)
            user_data = response.get_json()["user"]
            assert_condition(
                condition=bool(user_data["id"]),
                allure_step_name="В ответе присутствует id созданного пользователя",
                error_text="Поле user.id отсутствует или пусто!",
            )
            assert_condition(
                condition=user_data["username"] == "apiuser",
                allure_step_name="В ответе возвращено имя созданного пользователя",
                error_text="Имя пользователя в ответе не совпадает с отправленным!",
            )

    @title("Получение ошибки при регистрации с коротким паролем")
    @severity(severity_level.CRITICAL)
    def test_register_short_password(self, setup_app_client: FlaskClient):
        """Пароль короче 4 символов отклоняется валидацией сервиса (BadRequestError).

        Ожидание: 400 и поле error в JSON. Тело ошибки общее с пустым именем
        (``test_register_empty_username``): в сервисе одно правило —
        «пустое имя или пароль короче 4 символов».

        Имя «someone» выбрано заведомо корректным: проверяется именно правило
        про пароль, а не валидация имени.
        """
        api = Api(setup_app_client)
        with step("API. Попытка регистрации с коротким паролем"):
            response = api.auth.register(username="someone", password="123")
            assert_status_code(expect=400, response=response)
            assert_condition(
                condition="error" in response.get_json(),
                allure_step_name="В ответе присутствует поле error",
                error_text="Поле error отсутствует в JSON ответа!",
            )


    @title("Получение ошибки при регистрации уже существующего имени")
    @severity(severity_level.CRITICAL)
    def test_register_duplicate(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """Повторная регистрация существующего имени отклоняется сервисом (ConflictError).

        Ожидание: 409 и поле error в JSON.
        """
        api = Api(setup_app_client)
        with step("API. Попытка регистрации уже существующего имени"):
            response = api.auth.register(username=setup_test_user.db_model.username, password=setup_test_user.password)
            assert_status_code(expect=409, response=response)
            assert_condition(
                condition="error" in response.get_json(),
                allure_step_name="В ответе присутствует поле error",
                error_text="Поле error отсутствует в JSON ответа!",
            )

    @title("Получение ошибки при регистрации с пустым именем")
    @severity(severity_level.CRITICAL)
    def test_register_empty_username(self, setup_app_client: FlaskClient):
        """Пустое имя отклоняется валидацией сервиса (BadRequestError).

        Ожидание: 400 и поле error в JSON.
        """
        api = Api(setup_app_client)
        with step("API. Попытка регистрации с пустым именем"):
            response = api.auth.register(username="", password="password123")
            assert_status_code(expect=400, response=response)
            assert_condition(
                condition="error" in response.get_json(),
                allure_step_name="В ответе присутствует поле error",
                error_text="Поле error отсутствует в JSON ответа!",
            )
