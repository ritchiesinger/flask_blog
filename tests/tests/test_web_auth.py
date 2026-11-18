"""Тесты веб-интерфейса аутентификации: регистрация, вход и выход.

Запросы идут через WebClient (фасады над FlaskClient) — сессия живёт на клиенте.
Редиректы проверяются по Location двухшаговым каноном; тексты флешей и признаков
страниц проверяются на целевых страницах после отдельного запроса.

Пользователь, когда он нужен, берётся из фикстуры ``setup_test_user`` — существующая учётная запись в БД.
"""

from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from tests.constants.web_endpoints import WebEndpoints
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_equal, assert_status_code
from tests.tools.clients.web_client import WebClient


@epic("WEB")
@feature("Аутентификация")
@story("Регистрация")
class TestRegistration:
    """Проверки формы регистрации: успех и ошибки валидации."""

    @title("Успешная регистрация уводит на страницу логина с флешем об успехе")
    @severity(severity_level.BLOCKER)
    def test_register_success(self, setup_app_client: FlaskClient):
        """Успешная регистрация редиректит на страницу логина.

        Ожидание: POST формы 302, Location — путь логина; на странице логина флеш с именем нового пользователя.
        Прежнее название «возврат на главную» не соответствовало факту: роут ведёт на логин, исправлено при миграции.
        """
        guest = WebClient(app_client=setup_app_client)
        username, password = "newuser", "password123"
        with step("Гость. WEB. Отправка формы регистрации"):
            response = guest.auth.register(username=username, password=password)
            assert_status_code(expect=302, response=response)
            assert_equal(expect=WebEndpoints.AUTH.LOGIN, actual=response.headers["Location"], name="Заголовок Location")
        with step("Гость. WEB. Открытие страницы логина с флешем"):
            response = guest.auth.login_form()
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=username in response.get_data(as_text=True),
                allure_step_name="Имя пользователя есть во флеше",
                error_text="Флеш об успешной регистрации с именем пользователя не найден!",
            )

    @title("Повторная регистрация существующего имени отклоняется флешем")
    @severity(severity_level.CRITICAL)
    def test_register_duplicate_username(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """Сервис кидает ConflictError — форма перерисовывается с флешем.

        Ожидание: 200 (не редирект), в HTML флеш, что имя уже занято. Статус теперь проверяется — в прежней версии
        проверялся только текст.
        """
        user = setup_test_user
        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. Регистрация уже существующего имени"):
            response = guest.auth.register(username=user.db_model.username, password="password123")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="уже существует" in response.get_data(as_text=True),
                allure_step_name="Сообщение об ошибке выведено",
                error_text="Сообщение об ошибке не найдено!",
            )

    @title("Короткий пароль отклоняется флешем на странице регистрации")
    @severity(severity_level.CRITICAL)
    def test_register_short_password(self, setup_app_client: FlaskClient):
        """Сервис кидает BadRequestError — форма перерисовывается с флешем.

        Ожидание: 200, флеш про пароль. Проверка по корню слова «пароль» — формулировка может меняться, контракт о ней.
        """
        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. Регистрация с коротким паролем"):
            response = guest.auth.register(username="someone", password="123")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="пароль" in response.get_data(as_text=True).lower(),
                allure_step_name="Сообщение об ошибке выведено",
                error_text="Сообщение об ошибке не найдено!",
            )

    @title("Пустое имя отклоняется флешем на странице регистрации")
    @severity(severity_level.CRITICAL)
    def test_register_empty_username(self, setup_app_client: FlaskClient):
        """Сервис кидает BadRequestError — форма перерисовывается с флешем.

        Ожидание: 200, флеш про имя пользователя.
        """
        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. Регистрация с пустым именем"):
            response = guest.auth.register(username="", password="password123")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="имя" in response.get_data(as_text=True).lower(),
                allure_step_name="Сообщение об ошибке выведено",
                error_text="Сообщение об ошибке не найдено!",
            )

    @title("Залогиненный пользователь при попытке открыть регистрацию уходит на главную")
    @severity(severity_level.CRITICAL)
    def test_register_authenticated_redirects_to_index(self, setup_app_client: FlaskClient,
                                                       setup_test_user: UserObject):
        """GET /register под сессией не показывает форму — редирект на главную.

        Ожидание: 302, Location — «/».
        """
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Открытие страницы регистрации под сессией"):
            response = user.web.auth.register_form()
            assert_status_code(expect=302, response=response)
            assert_equal(expect="/", actual=response.headers["Location"], name="Заголовок Location")

    @title("Страница регистрации отдаёт форму гостю")
    @severity(severity_level.BLOCKER)
    def test_register_form_shows_to_guest(self, setup_app_client: FlaskClient):
        """GET /register без сессии отдаёт страницу с формой.

        Ожидание: 200. Единственный GET по этому роуту в наборе —
        закрывает ветку рендера формы.
        """
        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. Открытие страницы регистрации"):
            response = guest.auth.register_form()
            assert_status_code(expect=200, response=response)


@epic("WEB")
@feature("Аутентификация")
class TestLogin:
    """Проверки входа в систему и выхода из неё."""

    @story("Вход (Login)")
    @title("Успешный вход редиректит на главную, на ней есть признак вошедшего")
    @severity(severity_level.BLOCKER)
    def test_login_success(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """Вход редиректит на главную; признак вошедшего появляется.

        Ожидание: POST логина 302, Location — «/»; на главной есть «Добавить» — элемент, недоступный гостю.
        """
        user = setup_test_user
        with step("Пользователь. WEB. Вход в систему"):
            response = user.web.auth.login(username=user.db_model.username, password=user.password)
            assert_status_code(expect=302, response=response)
            assert_equal(expect="/", actual=response.headers["Location"], name="Заголовок Location")
        with step("Пользователь. WEB. Проверка признака вошедшего на главной"):
            response = user.web.posts.index()
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition='data-action="create_blog"' in response.get_data(as_text=True),
                allure_step_name="Возможность добавить пост присутствует",
                error_text="Возможность добавить пост отсутствует!",
            )

    @story("Вход (Login)")
    @title("Неверный пароль отклоняется флешем на странице логина")
    @severity(severity_level.CRITICAL)
    def test_login_wrong_password(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """Аутентификация не проходит — форма перерисовывается с флешем.

        Ожидание: 200 (не редирект), флеш «неверн…». Проверка по корню слова — контракт о едином сообщении, а не о
        формулировке.
        """
        user = setup_test_user
        with step("Пользователь. WEB. Попытка входа с неправильным паролем"):
            response = user.web.auth.login(username=user.db_model.username, password="wrong-password")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="неверн" in response.get_data(as_text=True).lower(),
                allure_step_name="Сообщение об ошибке выведено",
                error_text="Сообщение об ошибке не найдено!",
            )

    @story("Вход (Login)")
    @title("Несуществующее имя отклоняется тем же флешем, что и неверный пароль")
    @severity(severity_level.CRITICAL)
    def test_login_unknown_user(self, setup_app_client: FlaskClient):
        """Ответ на несуществующее имя совпадает с ответом на неверный пароль.

        Ожидание: 200, флеш «неверн…» — единое сообщение не раскрывает,
        существует ли пользователь.
        """
        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. Попытка входа с несуществующим именем"):
            response = guest.auth.login(username="ghost", password="password123")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="неверн" in response.get_data(as_text=True).lower(),
                allure_step_name="Сообщение об ошибке выведено",
                error_text="Сообщение об ошибке не найдено!",
            )

    @story("Выход (Logout)")
    @title("После выхода признаки вошедшего пользователя исчезают")
    @severity(severity_level.CRITICAL)
    def test_logout(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """Выход сбрасывает сессию: редирект на главную гостя.

        Ожидание: до выхода на главной есть «Добавить»; GET /logout — 302
        на «/»; после выхода признак на главной отсутствует.
        """
        user = setup_test_user
        with step("Пользователь. WEB. Вход в систему"):
            response = user.web.auth.login(username=user.db_model.username, password=user.password)
            assert_status_code(expect=302, response=response)
            assert_equal(expect="/", actual=response.headers["Location"], name="Заголовок Location")
        with step("Пользователь. WEB. Проверка признака вошедшего на главной"):
            response = user.web.posts.index()
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition='data-action="create_blog"' in response.get_data(as_text=True),
                allure_step_name="Возможность добавить пост присутствует",
                error_text="Возможность добавить пост отсутствует!",
            )
        with step("Пользователь. WEB. Выход из системы"):
            response = user.web.auth.logout()
            assert_status_code(expect=302, response=response)
            assert_equal(expect="/", actual=response.headers["Location"], name="Заголовок Location")
        with step("Пользователь. WEB. Проверка отсутствия признака на главной"):
            response = user.web.posts.index()
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition='data-action="create_blog"' not in response.get_data(as_text=True),
                allure_step_name="Возможность добавить пост отсутствует",
                error_text="Возможность добавить пост присутствует!",
            )

    @story("Вход (Login)")
    @title("Залогиненный пользователь при попытке открыть логин уходит на главную")
    @severity(severity_level.CRITICAL)
    def test_login_authenticated_redirects_to_index(self, setup_app_client: FlaskClient,
                                                    setup_test_user: UserObject):
        """GET /login под сессией не показывает форму — редирект на главную.

        Ожидание: 302, Location — «/».
        """
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Открытие страницы логина под сессией"):
            response = user.web.auth.login_form()
            assert_status_code(expect=302, response=response)
            assert_equal(expect="/", actual=response.headers["Location"], name="Заголовок Location")
