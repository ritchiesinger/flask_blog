"""WEB-профиль пользователя: публичный доступ, ленты, ролевые контролы.

Профиль публичен: гость видит ленты без контролов владения. Автор видит
управление своими сущностями; админ видит пункт «Удалить» у чужих сущностей
(интерфейсная доработка), но сервис пока ограничивает действие автором —
POST возвращает 403 (известное ограничение; после ревизии роли администратора
тест на 403 перестраивается на успех).
"""

from flask.testing import FlaskClient
from glamor import epic, feature, step, story, title

from blog.avatar import avatar_color
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_status_code
from tests.tools.clients.web_client import WebClient

PAGE_NOT_FOUND = "Страница не найдена."
NAV_MARK = "Постраничная навигация"


@epic("WEB")
@feature("Профиль пользователя")
@story("Публичный доступ")
class TestPublicAccess:
    """Профиль доступен без авторизации, включая мусор в query-параметрах."""

    @title("Гость видит профиль пользователя с лентами и раскрашенным аватаром")
    def test_guest_sees_profile(
            self,
            setup_app_client: FlaskClient,
            setup_test_user,
            setup_test_user_post,
            setup_test_user_post_comment,
    ):
        """Без сессии профиль открывается: 200, логин и оттенок аватара по хешу."""
        user = setup_test_user
        with step("Гость. WEB. Открытие профиля"):
            response = WebClient(setup_app_client).users.profile(username=user.db_model.username)
            assert_status_code(expect=200, response=response)
            body = response.get_data(as_text=True)
        with step("Проверка содержимого"):
            assert_condition(
                condition=user.db_model.username in body,
                allure_step_name="Логин пользователя на странице",
                error_text=f"Логин '{user.db_model.username}' не найден на странице профиля",
            )
            assert_condition(
                condition=f"avatar-palette-{avatar_color(user.db_model.username)}" in body,
                allure_step_name="Оттенок аватара детерминирован",
                error_text="Класс палитры аватара не соответствует md5-хешу имени",
            )

    @title("Профиль несуществующего пользователя — 404, фирменная страница")
    def test_unknown_username_404(self, setup_app_client: FlaskClient):
        """Неизвестный логин даёт 404-страницу, а не трейсбек."""
        with step("Гость. WEB. Открытие несуществующего профиля"):
            response = WebClient(setup_app_client).users.profile(username="no_such_user_xyz")
            assert_status_code(expect=404, response=response)
            assert_condition(
                condition=PAGE_NOT_FOUND in response.get_data(as_text=True),
                allure_step_name="Страница ошибки фирменная",
                error_text="На ответе 404 нет текста фирменной страницы",
            )

    @title("Мусорные page и comment_page отдают первую страницу без ошибки")
    def test_garbage_page_params(self, setup_app_client: FlaskClient, setup_test_user):
        """page=abc и comment_page=-3 не роняют профиль: 200 (error_out=False, защита page_from_args)."""
        user = setup_test_user
        with step("Гость. WEB. Открытие профиля с мусорными параметрами"):
            response = WebClient(setup_app_client).users.profile(
                username=user.db_model.username, page="abc", comment_page="-3",
            )
            assert_status_code(expect=200, response=response)


@epic("WEB")
@feature("Профиль пользователя")
@story("Содержимое лент")
class TestProfileContent:
    """Ленты постов и комментариев показывают данные и листаются независимо."""

    @title("Автор видит свои посты и комментарии в своём профиле")
    def test_owner_sees_own_entities(self, setup_test_user, setup_test_user_post, setup_test_user_post_comment):
        """Под сессией автора профиль содержит его пост и его комментарий."""
        user, post, comment = setup_test_user, setup_test_user_post, setup_test_user_post_comment
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Открытие своего профиля"):
            response = user.web.users.profile(username=user.db_model.username)
            assert_status_code(expect=200, response=response)
            body = response.get_data(as_text=True)
        with step("Проверка лент"):
            assert_condition(
                condition=post["title"] in body,
                allure_step_name="Заголовок поста в ленте",
                error_text=f"Пост '{post['title']}' не найден в ленте профиля",
            )
            assert_condition(
                condition=comment["body"][:20] in body,
                allure_step_name="Текст комментария в ленте",
                error_text="Начало комментария не найдено в ленте профиля",
            )

    @title("Пагинации постов и комментариев независимы: comment_page=2 меняет только комментарии")
    def test_independent_feeds_pagination(self, setup_test_user, setup_test_user_post):
        """Шесть комментариев дают две страницы: на comment_page=2 другой набор маркеров, посты на месте."""
        user, post = setup_test_user, setup_test_user_post
        markers = []
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. API. Создание шести комментариев с уникальными маркерами"):
            for i in range(1, 7):
                marker = f"token-{user.db_model.id}-{i}"
                markers.append(marker)
                response = user.api.create_comment(post_id=post["id"], body=f"{marker} " + "текст комментария")
                assert_status_code(expect=201, response=response)
        with step("Пользователь. WEB. Первая страница профиля"):
            page1 = user.web.users.profile(username=user.db_model.username)
            assert_status_code(expect=200, response=page1)
            body1 = page1.get_data(as_text=True)
        with step("Пользователь. WEB. Вторая страница комментариев"):
            page2 = user.web.users.profile(username=user.db_model.username, comment_page=2)
            assert_status_code(expect=200, response=page2)
            body2 = page2.get_data(as_text=True)
        with step("Проверка независимости лент"):
            assert_condition(
                condition=NAV_MARK in body1 and NAV_MARK in body2,
                allure_step_name="Навигация отрисована",
                error_text="Блок 'Постраничная навигация' не найден на одной из страниц",
            )
            set1 = {m for m in markers if m in body1}
            set2 = {m for m in markers if m in body2}
            assert_condition(
                condition=set1 and set2 and set1 != set2,
                allure_step_name="Наборы комментариев на страницах различаются",
                error_text=f"Наборы маркеров на страницах совпали или пусты: {set1} / {set2}",
            )
            assert_condition(
                condition=post["title"] in body2,
                allure_step_name="Посты не перескочили",
                error_text="Пост пользователя исчез со страницы при comment_page=2",
            )


@epic("WEB")
@feature("Профиль пользователя")
@story("Ролевые контролы")
class TestManageControls:
    """Контролы владения видны автору, скрыты от гостя и чужого пользователя; админ видит удаление."""

    @title("Автор видит дропдауны у своих постов и комментариев")
    def test_author_sees_own_controls(self, setup_test_user, setup_test_user_post, setup_test_user_post_comment):
        """Под сессией автора на его профиле есть 'Редактировать' и удаление своих сущностей."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Открытие своего профиля"):
            body = user.web.users.profile(username=user.db_model.username).get_data(as_text=True)
        with step("Проверка контролов"):
            assert_condition(
                condition="Редактировать" in body and "delete_post" in body and "delete_comment" in body,
                allure_step_name="Контролы владения на месте",
                error_text="Дропдауны управления не отрендерены для автора",
            )

    @title("Гость не видит контролов владения")
    def test_guest_sees_no_controls(
            self, setup_app_client: FlaskClient, setup_test_user, setup_test_user_post, setup_test_user_post_comment,
    ):
        """Без сессии на профиле нет ни 'Редактировать', ни форм удаления."""
        user = setup_test_user
        with step("Гость. WEB. Открытие профиля"):
            body = WebClient(setup_app_client).users.profile(username=user.db_model.username).get_data(as_text=True)
        with step("Проверка отсутствия контролов"):
            assert_condition(
                condition="Редактировать" not in body and "delete_post" not in body,
                allure_step_name="Контролы владения скрыты от гостя",
                error_text="Гость видит контролы управления чужими сущностями",
            )

    @title("Обычный пользователь не видит контролов в чужом профиле")
    def test_regular_user_no_controls_on_foreign_profile(
            self, setup_test_user, setup_test_user_2, setup_test_user_post,
    ):
        """Пользователь 2 в профиле Пользователя 1 не видит дропдаунов."""
        user_1, user_2 = setup_test_user, setup_test_user_2
        with step("Пользователь 2. WEB. Авторизация"):
            user_2.web.auth.login(username=user_2.db_model.username, password=user_2.password)
        with step("Пользователь 2. WEB. Открытие чужого профиля"):
            body = user_2.web.users.profile(username=user_1.db_model.username).get_data(as_text=True)
        with step("Проверка отсутствия контролов"):
            assert_condition(
                condition="Редактировать" not in body and "delete_post" not in body,
                allure_step_name="Контролы владения скрыты от чужого пользователя",
                error_text="Чужой пользователь видит контролы управления не своими сущностями",
            )

    @title("Админ видит в чужом профиле удаление, но не редактирование")
    def test_admin_sees_delete_only(
            self,
            setup_admin_user: UserObject,
            setup_test_user: UserObject,
            setup_test_user_post: dict,
            setup_test_user_post_comment: dict,
    ):
        """Интерфейсная доработка: у админа есть 'Удалить', нет 'Редактировать'."""
        admin, user = setup_admin_user, setup_test_user
        with step("Администратор. WEB. Авторизация"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Администратор. WEB. Открытие чужого профиля"):
            body = admin.web.users.profile(username=user.db_model.username).get_data(as_text=True)
        with step("Проверка контролов"):
            assert_condition(
                condition="delete_post" in body and "delete_comment" in body,
                allure_step_name="Пункты удаления у админа есть",
                error_text="Админ не видит контролы удаления в чужом профиле",
            )
            assert_condition(
                condition="Редактировать" not in body,
                allure_step_name="Редактирование админу не показано",
                error_text="Админ видит пункт редактирования чужих сущностей",
            )

    @title("Попытка админа удалить чужой комментарий — 403 (известное ограничение)")
    def test_admin_delete_comment_403(self, setup_admin_user: UserObject, setup_foreign_comment: dict):
        """Сейчас сервис разрешает удаление только автору: POST от админа — 403. После ревизии роли тест меняется."""
        admin = setup_admin_user
        comment = setup_foreign_comment
        with step("Администратор. WEB. Авторизация"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Администратор. WEB. Попытка удаления чужого комментария"):
            response = admin.web.comments.delete_comment(comment_id=comment["id"])
            assert_status_code(expect=403, response=response)
