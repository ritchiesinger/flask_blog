"""Тесты WEB-роутов постов: happy-пути списка, создания, просмотра, правки и удаления."""

from flask import Flask
from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.extensions import db
from blog.models import Post
from tests.constants.web_endpoints import WebEndpoints
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_equal, assert_redirect, assert_status_code
from tests.tools.asserters.soft_asserters import SoftAssert
from tests.tools.clients.web_client import WebClient


@epic("WEB")
@feature("Посты")
@story("Список постов")
class TestIndex:
    """Главная страница показывает посты блога."""

    @title("Главная с постами отдаёт 200 и показывает созданный пост")
    @severity(severity_level.BLOCKER)
    def test_index_shows_post(self, setup_app_client: FlaskClient, setup_test_user_post: dict):
        """Созданный пост виден на главной без авторизации.

        Ожидание: 200, заголовок поста присутствует в разметке страницы.
        """
        post = setup_test_user_post
        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. Открытие главной страницы"):
            response = guest.posts.index()
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=post["title"] in response.get_data(as_text=True),
                allure_step_name="Заголовок поста виден на главной",
                error_text="Созданный пост не виден на главной странице!",
            )


@epic("WEB")
@feature("Посты")
@story("Создание поста")
class TestCreate:
    """Форма создания поста: отдаёт форму, сохраняет пост, флешит успех."""

    @title("Авторизованный пользователь создаёт пост через форму")
    @severity(severity_level.BLOCKER)
    def test_create_post(self, setup_app: Flask, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """POST формы создаёт пост и редиректит на главную.

        Ожидание: GET формы 200; POST 302 с Location на главную;
        пост в БД с данными формы и author_id пользователя; флеш на главной.
        """
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Открытие формы создания"):
            response = user.web.posts.create_form()
            assert_status_code(expect=200, response=response)
        with step("Пользователь. WEB. Отправка формы создания поста"):
            response = user.web.posts.create(title="Новый пост", body="Тело поста")
            assert_redirect(expect="/", response=response)
        with step("Пользователь. WEB. Проверка флеша на главной"):
            response = user.web.posts.index()
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="Пост успешно создан!" in response.get_data(as_text=True),
                allure_step_name="На главной есть флеш об успешном создании",
                error_text="Флеш «Пост успешно создан!» не найден на странице!",
            )
        with step("ORM. Проверка созданного поста в БД"):
            with setup_app.app_context():
                post = db.session.execute(db.select(Post).filter_by(title="Новый пост")).scalars().first()
                assert_condition(
                    condition=post is not None,
                    allure_step_name="Пост найден в БД",
                    error_text="Пост не найден в БД после создания через форму!",
                )
                SoftAssert(
                    assert_equal(expect="Тело поста", actual=post.body, name="Тело поста", soft_assert=True),
                    assert_equal(
                        expect=user.db_model.id,
                        actual=post.author_id,
                        name="Идентификатор автора",
                        soft_assert=True,
                    )
                )

    @title("Гость при отправке формы создания уходит на логин")
    @severity(severity_level.CRITICAL)
    def test_create_post_guest_redirects_to_login(self, setup_app_client: FlaskClient):
        """POST /create без сессии не создаёт пост — редирект на логин.

        Ожидание: 302, Location начинается с пути логина (формат next
        зависит от flask-login, поэтому сравнение не точное).
        """
        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. Отправка формы создания поста без авторизации"):
            response = guest.posts.create(title="Гостевой пост", body="Тело поста")
            assert_status_code(expect=302, response=response)
            assert_condition(
                condition=response.headers["Location"].startswith(WebEndpoints.AUTH.LOGIN),
                allure_step_name="Location ведёт на логин",
                error_text="Гость при создании поста не уходит на логин!",
            )

    @title("Пустой заголовок не создаёт пост: 200, флеш об ошибке, БД чиста")
    @severity(severity_level.MINOR)
    def test_create_post_empty_title_shows_error(self, setup_app: Flask, setup_app_client: FlaskClient,
                                                 setup_test_user: UserObject):
        """POST с пустым заголовком возвращает форму с ошибкой.

        Ожидание: 200 (не редирект), флеш «Заголовок обязателен.», в БД нет
        поста с отправленным телом.
        """
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Отправка формы с пустым заголовком"):
            response = user.web.posts.create(title="", body="Уникальное тело без заголовка")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="Заголовок обязателен." in response.get_data(as_text=True),
                allure_step_name="На странице есть флеш об ошибке",
                error_text="Флеш «Заголовок обязателен.» не найден!",
            )
        with step("ORM. Проверка, что пост не создан"):
            with setup_app.app_context():
                created = db.session.execute(
                    db.select(Post).filter_by(body="Уникальное тело без заголовка")
                ).scalars().first()
            assert_condition(
                condition=created is None,
                allure_step_name="Поста в БД нет",
                error_text="Пост создан вопреки пустому заголовку!",
            )

    @title("Заголовок из одних пробелов не создаёт пост: 200, флеш об ошибке, БД чиста")
    @severity(severity_level.MINOR)
    def test_create_post_whitespace_title_shows_error(self, setup_app: Flask, setup_app_client: FlaskClient,
                                                      setup_test_user: UserObject):
        """Заголовок из пробелов после strip() пуст — та же ветка валидации.

        Ожидание: 200, флеш «Заголовок обязателен.», в БД нет поста
        с отправленным телом.
        """
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Отправка формы с пробельным заголовком"):
            response = user.web.posts.create(title="   ", body="Уникальное тело пробельного заголовка")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="Заголовок обязателен." in response.get_data(as_text=True),
                allure_step_name="На странице есть флеш об ошибке",
                error_text="Флеш «Заголовок обязателен.» не найден!",
            )
        with step("ORM. Проверка, что пост не создан"):
            with setup_app.app_context():
                created = db.session.execute(
                    db.select(Post).filter_by(body="Уникальное тело пробельного заголовка")
                ).scalars().first()
            assert_condition(
                condition=created is None,
                allure_step_name="Поста в БД нет",
                error_text="Пост создан вопреки пробельному заголовку!",
            )


@epic("WEB")
@feature("Посты")
@story("Просмотр поста")
class TestView:
    """Страница поста публична и отдаёт содержимое."""

    @title("Пост открывается без авторизации и показывает заголовок и тело")
    @severity(severity_level.BLOCKER)
    def test_view_post_public(self, setup_app_client: FlaskClient, setup_test_user_post: dict):
        """Гость открывает пост: 200, заголовок и тело в разметке.

        Ожидание: страница поста не требует логина — проверка без cookies.
        """
        post = setup_test_user_post
        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. Открытие страницы поста без логина"):
            response = guest.posts.view(post_id=post["id"])
            assert_status_code(expect=200, response=response)
            page = response.get_data(as_text=True)
            assert_condition(
                condition=post["title"] in page,
                allure_step_name="Заголовок поста виден на странице",
                error_text="Заголовок поста не найден на странице!",
            )
            assert_condition(
                condition=post["body"] in page,
                allure_step_name="Тело поста видно на странице",
                error_text="Тело поста не найдено на странице!",
            )

    @title("Несуществующий пост гостю отдаёт 404")
    @severity(severity_level.CRITICAL)
    def test_view_post_not_found(self, setup_app_client: FlaskClient):
        """Сервис кидает NotFoundError, web_errors конвертирует в 404.

        Ожидание: 404 у гостя — публичная страница не раскрывает отсутствие
        авторизацией.
        """
        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. Открытие несуществующего поста"):
            response = guest.posts.view(post_id=999999)
            assert_status_code(expect=404, response=response)


@epic("WEB")
@feature("Посты")
@story("Редактирование поста")
class TestUpdate:
    """Форма редактирования: своя запись, сохранение изменений."""

    @title("Автор правит свой пост: форма заполнена, изменения сохраняются")
    @severity(severity_level.BLOCKER)
    def test_update_post(
            self,
            setup_app: Flask,
            setup_app_client: FlaskClient,
            setup_test_user: UserObject,
            setup_test_user_post: dict
    ):
        """POST формы обновляет пост и редиректит на страницу поста.

        Ожидание: GET формы 200 с текущим заголовком в разметке; POST 302
        на просмотр этого же поста; в БД новые данные, старые ушли; флеш на странице поста.
        """
        user, post = setup_test_user, setup_test_user_post
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Открытие формы редактирования"):
            response = user.web.posts.update_form(post_id=post["id"])
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=post["title"] in response.get_data(as_text=True),
                allure_step_name="Форма заполнена текущим заголовком",
                error_text="Текущий заголовок не найден в форме редактирования!",
            )
        with step("Пользователь. WEB. Отправка формы редактирования"):
            response = user.web.posts.update(post_id=post["id"], title="Обновлённый заголовок", body="Обновлённое тело")
            assert_redirect(expect=f"/{post['id']}", response=response)
        with step("Пользователь. WEB. Проверка флеша на странице поста"):
            response = user.web.posts.view(post_id=post["id"])
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="Пост обновлён!" in response.get_data(as_text=True),
                allure_step_name="На странице поста есть флеш об обновлении",
                error_text="Флеш «Пост обновлён!» не найден!",
            )
        with step("ORM. Проверка обновлённого поста в БД"):
            with setup_app.app_context():
                refreshed = db.session.get(Post, post["id"])
            assert_condition(
                condition=refreshed.title == "Обновлённый заголовок",
                allure_step_name="Заголовок обновлён",
                error_text="Заголовок поста не обновлён!",
            )
            assert_condition(
                condition=refreshed.body == "Обновлённое тело",
                allure_step_name="Тело обновлено",
                error_text="Тело поста не обновлено!",
            )

    @title("Чужому пользователю GET формы редактирования отдаёт 403")
    @severity(severity_level.CRITICAL)
    def test_update_form_forbidden_for_non_author(self, setup_app_client: FlaskClient,
                                                  setup_test_user_2: UserObject, setup_test_user_post: dict):
        """Проверка авторства срабатывает до рендера формы (check_author в сервисе).

        Ожидание: 403 на GET — не только на POST формы.
        """
        user2, post = setup_test_user_2, setup_test_user_post
        with step("Пользователь 2. WEB. Авторизация"):
            user2.web.auth.login(username=user2.db_model.username, password=user2.password)
        with step("Пользователь 2. WEB. Открытие формы чужого поста"):
            response = user2.web.posts.update_form(post_id=post["id"])
            assert_status_code(expect=403, response=response)

    @title("Чужому пользователю POST формы редактирования отдаёт 403, пост неизменен")
    @severity(severity_level.CRITICAL)
    def test_update_post_forbidden_for_non_author(self, setup_app: Flask, setup_app_client: FlaskClient,
                                                  setup_test_user_2: UserObject, setup_test_user_post: dict):
        """Пост другого автора не обновляется чужим пользователем.

        Ожидание: 403; в БД заголовок и тело остались исходными.
        """
        user2, post = setup_test_user_2, setup_test_user_post
        with step("Пользователь 2. WEB. Авторизация"):
            user2.web.auth.login(username=user2.db_model.username, password=user2.password)
        with step("Пользователь 2. WEB. Отправка формы чужого поста"):
            response = user2.web.posts.update(
                post_id=post["id"], title="Взломанный заголовок", body="Взломанное тело",
            )
            assert_status_code(expect=403, response=response)
        with step("ORM. Проверка неизменности поста"):
            with setup_app.app_context():
                unchanged = db.session.get(Post, post["id"])
                SoftAssert(
                    assert_equal(
                        expect=post["title"],
                        actual=unchanged.title,
                        name="Заголовок поста",
                        soft_assert=True
                    ),
                    assert_equal(expect=post["body"], actual=unchanged.body, name="Тело поста", soft_assert=True),
                )

    @title("Пустой заголовок не обновляет пост: 200, флеш об ошибке, БД неизменна")
    @severity(severity_level.MINOR)
    def test_update_post_empty_title_keeps_post(self, setup_app: Flask, setup_app_client: FlaskClient,
                                                setup_test_user: UserObject, setup_test_user_post: dict):
        """POST с пустым заголовком возвращает форму, пост остаётся прежним.

        Ожидание: 200 (не редирект), флеш «Заголовок обязателен.»,
        в БД исходные title и body.
        """
        user, post = setup_test_user, setup_test_user_post
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Отправка формы с пустым заголовком"):
            response = user.web.posts.update(post_id=post["id"], title="", body="Новое тело без заголовка")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="Заголовок обязателен." in response.get_data(as_text=True),
                allure_step_name="На странице есть флеш об ошибке",
                error_text="Флеш «Заголовок обязателен.» не найден!",
            )
        with step("ORM. Проверка неизменности поста"):
            with setup_app.app_context():
                unchanged = db.session.get(Post, post["id"])
                SoftAssert(
                    assert_equal(
                        expect=post["title"],
                        actual=unchanged.title,
                        name="Заголовок поста",
                        soft_assert=True
                    ),
                    assert_equal(expect=post["body"], actual=unchanged.body, name="Тело поста", soft_assert=True),
                )

    @title("Пробельный заголовок не обновляет пост: 200, флеш об ошибке, БД неизменна")
    @severity(severity_level.MINOR)
    def test_update_post_whitespace_title_keeps_post(self, setup_app: Flask, setup_app_client: FlaskClient,
                                                     setup_test_user: UserObject, setup_test_user_post: dict):
        """Заголовок из пробелов после strip() пуст — та же ветка валидации.

        Ожидание: 200, флеш «Заголовок обязателен.», в БД исходные title и body.
        """
        user, post = setup_test_user, setup_test_user_post
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Отправка формы с пробельным заголовком"):
            response = user.web.posts.update(post_id=post["id"], title="   ", body="Новое тело пробельного заголовка")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="Заголовок обязателен." in response.get_data(as_text=True),
                allure_step_name="На странице есть флеш об ошибке",
                error_text="Флеш «Заголовок обязателен.» не найден!",
            )
        with step("ORM. Проверка неизменности поста"):
            with setup_app.app_context():
                unchanged = db.session.get(Post, post["id"])
                SoftAssert(
                    assert_equal(
                        expect=post["title"],
                        actual=unchanged.title,
                        name="Заголовок поста",
                        soft_assert=True
                    ),
                    assert_equal(expect=post["body"], actual=unchanged.body, name="Тело поста", soft_assert=True),
                )

    @title("Несуществующий пост при редактировании отдаёт 404")
    @severity(severity_level.CRITICAL)
    def test_update_post_not_found(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """POST /<несуществующий>/update — NotFoundError конвертируется в 404.

        Ожидание: 404 до какой-либо проверки авторства — поста просто нет.
        GET формы того же адреса падает в ту же ветку get_post.
        """
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Отправка формы несуществующего поста"):
            response = user.web.posts.update(post_id=999999, title="Заголовок", body="Тело")
            assert_status_code(expect=404, response=response)



@epic("WEB")
@feature("Посты")
@story("Удаление поста")
class TestDelete:
    """Удаление своего поста POST-ом."""

    @title("Автор удаляет свой пост POST-ом: редирект на главную, поста нет в БД")
    @severity(severity_level.BLOCKER)
    def test_delete_post(self, setup_app: Flask, setup_app_client: FlaskClient, setup_test_user: UserObject,
                         setup_test_user_post: dict):
        """POST на /<id>/delete удаляет пост.

        Ожидание: 302 на главную; флеш «Пост удалён.» на главной; записи в БД больше нет.
        """
        user, post = setup_test_user, setup_test_user_post
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Удаление поста POST-ом"):
            response = user.web.posts.delete(post_id=post["id"])
            assert_redirect(expect="/", response=response)
        with step("Пользователь. WEB. Проверка флеша на главной"):
            response = user.web.posts.index()
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="Пост удалён." in response.get_data(as_text=True),
                allure_step_name="На главной есть флеш об удалении",
                error_text="Флеш «Пост удалён.» не найден!",
            )

        with step("ORM. Проверка отсутствия поста в БД"):
            with setup_app.app_context():
                gone = db.session.get(Post, post["id"])
            assert_condition(
                condition=gone is None,
                allure_step_name="Поста в БД больше нет",
                error_text="Пост не удалён из БД!",
            )

    @title("Чужому пользователю удаление поста отдаёт 403, пост жив")
    @severity(severity_level.CRITICAL)
    def test_delete_post_forbidden_for_non_author(self, setup_app: Flask, setup_app_client: FlaskClient,
                                                  setup_test_user_2: UserObject, setup_test_user_post: dict):
        """Пост другого автора не удаляется чужим пользователем.

        Ожидание: 403; запись в БД осталась.
        """
        user2, post = setup_test_user_2, setup_test_user_post
        with step("Пользователь 2. WEB. Авторизация"):
            user2.web.auth.login(username=user2.db_model.username, password=user2.password)
        with step("Пользователь 2. WEB. Отправка удаления чужого поста"):
            response = user2.web.posts.delete(post_id=post["id"])
            assert_status_code(expect=403, response=response)
        with step("ORM. Проверка, что пост жив"):
            with setup_app.app_context():
                alive = db.session.get(Post, post["id"])
            assert_condition(
                condition=alive is not None,
                allure_step_name="Пост остался в БД",
                error_text="Пост удалён вопреки запрету!",
            )

    @title("Удаление несуществующего поста отдаёт 404")
    @severity(severity_level.CRITICAL)
    def test_delete_post_not_found(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """POST /<несуществующий>/delete — NotFoundError конвертируется в 404.

        Ожидание: 404 у залогиненного пользователя.
        """
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Отправка удаления несуществующего поста"):
            response = user.web.posts.delete(post_id=999999)
            assert_status_code(expect=404, response=response)

    @title("GET на адрес удаления отдаёт 405 — POST-only")
    @severity(severity_level.MINOR)
    def test_delete_get_method_not_allowed(self, setup_app_client: FlaskClient, setup_test_user_post: dict):
        """Адрес /<id>/delete отвечает только на POST — защита от GET-удаления.

        Ожидание: 405. GET-запрос идёт напрямую через клиент (вне фасада):
        GET-метода delete в WebClient быть не должно — предмет теста именно
        отсутствие такого роута в приложении.
        """
        post = setup_test_user_post
        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. GET на адрес удаления поста"):
            response = guest.app_client.get(WebEndpoints.POSTS.DELETE.format(post_id=post["id"]))
            assert_status_code(expect=405, response=response)


@epic("WEB")
@feature("Посты")
@story("Пагинация ленты")
class TestIndexPagination:
    """Пагинация главной: разбиение по страницам, санитизация номера страницы."""

    @title("7 постов делятся на страницу из 5 и страницу из 2")
    @severity(severity_level.CRITICAL)
    def test_index_pagination_splits_feed(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """Лента делится по POSTS_PER_PAGE: свежие на первой, старейшие на второй.

        Ожидание: на стр. 1 — посты 07..03, на стр. 2 — посты 02 и 01.
        """
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Создание 7 постов с нумерацией 01..07"):
            for number in range(1, 8):
                response = user.web.posts.create(title=f"Пост {number:02d}", body=f"Тело поста {number:02d}")
                assert_status_code(expect=302, response=response)

        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. Открытие первой страницы"):
            first = guest.posts.index(page=1)
            assert_status_code(expect=200, response=first)
        with step("Проверка: на первой странице свежие посты, старейших нет"):
            page_text = first.get_data(as_text=True)
            assert_condition(
                condition="Пост 07" in page_text and "Пост 03" in page_text,
                allure_step_name="На первой странице новейшие посты",
                error_text="Свежие посты не найдены на первой странице!",
            )
            assert_condition(
                condition="Пост 01" not in page_text and "Пост 02" not in page_text,
                allure_step_name="Старейшие посты уходят со второй страницы",
                error_text="Старые посты попали на первую страницу!",
            )
        with step("Гость. WEB. Открытие второй страницы"):
            second = guest.posts.index(page=2)
            assert_status_code(expect=200, response=second)
        with step("Проверка: на второй странице ровно два старейших поста"):
            page_text = second.get_data(as_text=True)
            assert_condition(
                condition="Пост 01" in page_text and "Пост 02" in page_text,
                allure_step_name="На второй странице старейшие посты",
                error_text="Старейшие посты не найдены на второй странице!",
            )
            assert_condition(
                condition="Пост 03" not in page_text and "Пост 07" not in page_text,
                allure_step_name="Свежие посты не попадают на вторую страницу",
                error_text="Свежие посты продублировались на второй странице!",
            )

    @title("Мусор и некорректный page дают первую страницу без ошибок")
    @severity(severity_level.MINOR)
    def test_index_page_sanitization(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """?page=abc, 0, -5 → 200 и первая страница (fallback без исключений)."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация и создание поста"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
            user.web.posts.create(title="Пост для санитизации", body="Тело")

        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. ?page=0 и ?page=-5 через фасад"):
            for bad_page in (0, -5):
                response = guest.posts.index(page=bad_page)
                assert_status_code(expect=200, response=response)
                assert_condition(
                    condition="Пост для санитизации" in response.get_data(as_text=True),
                    allure_step_name=f"page={bad_page} даёт первую страницу",
                    error_text=f"page={bad_page} сломал ленту!",
                )
        with step("Гость. WEB. ?page=abc — сырой клиент, фасад не принимает нечисловые"):
            response = setup_app_client.get(WebEndpoints.POSTS.INDEX, query_string={"page": "abc"})
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="Пост для санитизации" in response.get_data(as_text=True),
                allure_step_name="page=abc даёт первую страницу",
                error_text="page=abc сломал ленту!",
            )

    @title("Страница за пределами total отдаёт 200 и пустую ленту")
    @severity(severity_level.MINOR)
    def test_index_page_beyond_total(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """?page=999 → 200, пустая лента (error_out=False)."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация и создание поста"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
            user.web.posts.create(title="Пост для границ", body="Тело")

        guest = WebClient(app_client=setup_app_client)
        with step("Гость. WEB. Открытие страницы 999"):
            response = guest.posts.index(page=999)
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition="Пост для границ" not in response.get_data(as_text=True),
                allure_step_name="Лента за пределами total пуста",
                error_text="За пределами total лента не пуста!",
            )
