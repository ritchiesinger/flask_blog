"""WEB-тесты аватаров и отображаемого имени: доступ, обработка, замена, сброс, чистка при удалении.

Роуты профиля — POST /user/<username>/avatar, /avatar/reset, /display_name (→ ARC-0051): владелец — 302 с
флешем, гость — редирект на логин, не-владелец под сессией — 404 (скрытое действие). Успешные ветки сервиса
(нужны БД и диск) накрыты здесь, гварды и до-дисковая валидация — юнитами test_avatar_service. Интеграция:
delete_user сносит пару файлов аватара (→ ARC-0051).
"""

from io import BytesIO
from pathlib import Path

from flask import Flask
from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title
from PIL import Image as PILImage

from blog.avatar import avatar_color
from blog.models.user import User
from tests.constants.web_endpoints import WebEndpoints
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import (
    assert_condition,
    assert_equal,
    assert_redirect,
    assert_status_code,
)
from tests.tools.clients.web_client import WebClient
from tests.tools.image_factory import (
    make_cmyk_jpeg_bytes,
    make_gif_bytes,
    make_jpeg_bytes,
    make_png_bytes,
)

FLASH_AVATAR_UPDATED = "Аватар обновлён."
FLASH_AVATAR_RESET = "Аватар сброшен."
FLASH_NAME_UPDATED = "Отображаемое имя обновлено: "
GARBAGE_BYTES = b"not an image"
AVATARS_DIR = "avatars"
THUMBS_DIR = "thumbs"


def _avatar_dir(app: Flask) -> Path:
    """Папка аватаров тестового приложения.

    Args:
        app: тестовое приложение.

    Returns:
        Путь к uploads/avatars.
    """
    return Path(app.config["UPLOAD_FOLDER"]) / AVATARS_DIR


def _files(avatar_root: Path) -> list[Path]:
    """Список файлов папки аватаров (без вложенной папки thumbs).

    Args:
        avatar_root: папка avatars.

    Returns:
        Файлы непосредственно в папке avatars.
    """
    return [path for path in avatar_root.iterdir() if path.is_file()]


def _avatar_filename(app: Flask, username: str) -> str | None:
    """Читает ссылку на аватар пользователя из БД.

    Args:
        app: тестовое приложение.
        username: логин пользователя.

    Returns:
        Имя файла аватара или None при автогенерации.
    """
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        return user.avatar_filename if user else None


def _display_name(app: Flask, username: str) -> str | None:
    """Читает display_name пользователя из БД.

    Args:
        app: тестовое приложение.
        username: логин пользователя.

    Returns:
        Отображаемое имя или None, если не задано.
    """
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        return user.display_name if user else None


def _no_files(root: Path) -> bool:
    """Проверяет, что папка аватаров отсутствует или пуста (файлов нет).

    Args:
        root: папка avatars.

    Returns:
        True, если файлов аватаров на диске нет.
    """
    return not root.exists() or not _files(root)


@epic("WEB")
@feature("Аватары пользователя")
@story("Загрузка аватара")
class TestAvatarUpload:
    """POST /user/<username>/avatar: владелец сохраняет пару файлов, чужие — не проходят."""

    @severity(severity_level.BLOCKER)
    @title("Владелец загружает квадратный JPEG: редирект, флеш, пара 400/64 и ссылка в БД")
    def test_owner_uploads_jpeg(self, setup_app: Flask, setup_test_user: UserObject):
        """Успешная загрузка: пара файлов на диске, средний 400×400, малый 64×64 (→ ARC-0052)."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка аватара 400×400 JPEG"):
            response = user.web.users.upload_avatar(
                username=user.db_model.username,
                stream=BytesIO(make_jpeg_bytes((400, 400))),
                filename="me.jpg",
            )
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user.db_model.username),
                response=response,
            )
        with step("ORM. Чтение ссылки на аватар"):
            filename = _avatar_filename(setup_app, user.db_model.username)
            assert_condition(
                condition=filename is not None and filename.endswith(".jpg"),
                allure_step_name="Ссылка на аватар записана в БД",
                error_text=f"Ожидалось имя с расширением jpg, получено: {filename}",
            )
        with step("Проверка пары файлов на диске"):
            root = _avatar_dir(setup_app)
            middle = PILImage.open(root / filename)
            small = PILImage.open(root / THUMBS_DIR / filename)
            assert_equal(expect=(400, 400), actual=middle.size, name="Размер среднего аватара")
            assert_equal(expect="JPEG", actual=middle.format, name="Формат среднего аватара")
            assert_equal(expect=(64, 64), actual=small.size, name="Размер малого аватара")
        with step("Пользователь. WEB. Профиль после загрузки"):
            page = user.web.users.profile(username=user.db_model.username)
            assert_status_code(expect=200, response=page)
            body = page.get_data(as_text=True)
            assert_condition(
                condition=FLASH_AVATAR_UPDATED in body and f"/uploads/avatars/{filename}" in body,
                allure_step_name="Флеш и ссылка на аватар на профиле",
                error_text="Профиль не показывает флеш загрузки или аватар",
            )

    @severity(severity_level.CRITICAL)
    @title("Неквадратный PNG обрезается по центру: оба файла 400×400 и 64×64")
    def test_non_square_cropped_center(self, setup_app: Flask, setup_test_user: UserObject):
        """800×600 под .png: обход виджета не ломает результат — центр-кроп до квадрата (→ ARC-0051)."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка неквадратного PNG 800×600"):
            response = user.web.users.upload_avatar(
                username=user.db_model.username,
                stream=BytesIO(make_png_bytes((800, 600))),
                filename="wide.png",
            )
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user.db_model.username),
                response=response,
            )
        with step("ORM. Чтение ссылки на аватар"):
            filename = _avatar_filename(setup_app, user.db_model.username)
        with step("Проверка размеров пары после кропа"):
            root = _avatar_dir(setup_app)
            middle = PILImage.open(root / filename)
            small = PILImage.open(root / THUMBS_DIR / filename)
            assert_equal(expect=(400, 400), actual=middle.size, name="Средний аватар после кропа")
            assert_equal(expect=(64, 64), actual=small.size, name="Малый аватар после кропа")

    @severity(severity_level.NORMAL)
    @title("GIF-содержимое сохраняется как PNG: анимация не хранится")
    def test_gif_saved_as_png(self, setup_app: Flask, setup_test_user: UserObject):
        """GIF умирает при перекодировании (→ ARC-0051): файл на диске — PNG, имя с расширением png."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка GIF"):
            response = user.web.users.upload_avatar(
                username=user.db_model.username,
                stream=BytesIO(make_gif_bytes()),
                filename="animated.gif",
            )
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user.db_model.username),
                response=response,
            )
        with step("Проверка формата сохранённого файла"):
            filename = _avatar_filename(setup_app, user.db_model.username)
            assert_condition(
                condition=filename is not None and filename.endswith(".png"),
                allure_step_name="Имя файла с расширением png",
                error_text=f"Ожидалось имя с расширением png, получено: {filename}",
            )
            saved = PILImage.open(_avatar_dir(setup_app) / filename)
            assert_equal(expect="PNG", actual=saved.format, name="Формат содержимого сохранённого аватара")

    @severity(severity_level.NORMAL)
    @title("CMYK-JPEG конвертируется в RGB при сохранении")
    def test_cmyk_jpeg_converted_to_rgb(self, setup_app: Flask, setup_test_user: UserObject):
        """CMYK-исходник: средний файл сохранён в RGB-режиме — перекодирование не падает (→ ARC-0051)."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка CMYK-JPEG"):
            response = user.web.users.upload_avatar(
                username=user.db_model.username,
                stream=BytesIO(make_cmyk_jpeg_bytes((10, 10))),
                filename="cmyk.jpg",
            )
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user.db_model.username),
                response=response,
            )
        with step("Проверка режима сохранённого файла"):
            filename = _avatar_filename(setup_app, user.db_model.username)
            middle = PILImage.open(_avatar_dir(setup_app) / filename)
            assert_equal(expect="RGB", actual=middle.mode, name="Режим сохранённого аватара")

    @severity(severity_level.CRITICAL)
    @title("Замена аватара сносит предыдущую пару файлов")
    def test_replacement_deletes_old_pair(self, setup_app: Flask, setup_test_user: UserObject):
        """Вторая загрузка удаляет файлы первой: на диске ровно новая пара, ссылка обновлена."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Первая загрузка PNG"):
            first_response = user.web.users.upload_avatar(
                username=user.db_model.username,
                stream=BytesIO(make_png_bytes()),
                filename="first.png",
            )
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user.db_model.username),
                response=first_response,
            )
        with step("ORM. Имя первой пары"):
            first = _avatar_filename(setup_app, user.db_model.username)
        with step("Пользователь. WEB. Вторая загрузка JPEG"):
            second_response = user.web.users.upload_avatar(
                username=user.db_model.username,
                stream=BytesIO(make_jpeg_bytes()),
                filename="second.jpg",
            )
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user.db_model.username),
                response=second_response,
            )
        with step("ORM. Имя второй пары"):
            second = _avatar_filename(setup_app, user.db_model.username)
        with step("Проверка замены"):
            root = _avatar_dir(setup_app)
            files = _files(root)
            thumbs = _files(root / THUMBS_DIR)
            assert_condition(
                condition=first != second,
                allure_step_name="Имя пары обновилось",
                error_text=f"Вторая загрузка оставила прежнее имя: {first}",
            )
            assert_condition(
                condition=len(files) == 1 and files[0].name == second,
                allure_step_name="В avatars ровно новая пара",
                error_text=f"Файлы аватаров не снесены: {[path.name for path in files]}",
            )
            assert_condition(
                condition=len(thumbs) == 1 and thumbs[0].name == second,
                allure_step_name="В avatars/thumbs ровно новая пара",
                error_text=f"Миниатюры не снесены: {[path.name for path in thumbs]}",
            )

    @severity(severity_level.CRITICAL)
    @title("Гость на загрузке аватара уходит на логин, файлы не создаются")
    def test_guest_redirect_to_login(
            self, setup_app: Flask, setup_app_client: FlaskClient, setup_test_user: UserObject,
    ):
        """Без сессии POST аватара — 302 на логин; пары файлов нет."""
        user = setup_test_user
        with step("Гость. WEB. Попытка загрузки аватара без сессии"):
            response = WebClient(setup_app_client).users.upload_avatar(
                username=user.db_model.username,
                stream=BytesIO(make_png_bytes()),
                filename="guest.png",
            )
            assert_status_code(expect=302, response=response)
            assert_condition(
                condition=response.headers.get("Location", "").startswith(WebEndpoints.AUTH.LOGIN),
                allure_step_name="Редирект ведёт на страницу логина",
                error_text=f"Ожидался редирект на логин, получено: {str(response.headers.get('Location'))}",
            )
        with step("Проверка отсутствия файлов"):
            assert_condition(
                condition=_no_files(_avatar_dir(setup_app)),
                allure_step_name="Файлы аватаров не созданы",
                error_text="Гостевая загрузка оставила файлы на диске",
            )

    @severity(severity_level.CRITICAL)
    @title("Не-владелец под сессией получает 404, файлы не создаются")
    def test_foreign_user_404(self, setup_app: Flask, setup_test_user: UserObject, setup_test_user_2: UserObject):
        """Пользователь 2 грузит аватар в профиль Пользователя 1: скрытое действие — 404."""
        user_1, user_2 = setup_test_user, setup_test_user_2
        with step("Пользователь 2. WEB. Авторизация"):
            user_2.web.auth.login(username=user_2.db_model.username, password=user_2.password)
        with step("Пользователь 2. WEB. Попытка загрузки аватара в чужой профиль"):
            response = user_2.web.users.upload_avatar(
                username=user_1.db_model.username,
                stream=BytesIO(make_png_bytes()),
                filename="intruder.png",
            )
            assert_status_code(expect=404, response=response)
        with step("Проверка отсутствия файлов и ссылки"):
            assert_condition(
                condition=_no_files(_avatar_dir(setup_app)),
                allure_step_name="Файлы аватаров не созданы",
                error_text="Чужая загрузка оставила файлы на диске",
            )
            assert_equal(
                expect=None,
                actual=_avatar_filename(setup_app, user_1.db_model.username),
                name="Ссылка на аватар владельца",
            )

    @severity(severity_level.NORMAL)
    @title("POST аватара без поля file — 400")
    def test_no_file_400(self, setup_test_user: UserObject):
        """Файл не передан: BadRequestError роута → 400 (до обращения к сервису)."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. POST аватара без файла"):
            response = user.web.users.upload_avatar_no_file(username=user.db_model.username)
            assert_status_code(expect=400, response=response)

    @severity(severity_level.CRITICAL)
    @title("Не-изображение под валидным именем — 400, файлы не создаются")
    def test_garbage_content_400(self, setup_app: Flask, setup_test_user: UserObject):
        """Валидное имя, мусорное содержимое: BadRequestError сервиса → 400."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка не-изображения под именем avatar.png"):
            response = user.web.users.upload_avatar(
                username=user.db_model.username,
                stream=BytesIO(GARBAGE_BYTES),
                filename="avatar.png",
            )
            assert_status_code(expect=400, response=response)
        with step("Проверка отсутствия файлов"):
            assert_condition(
                condition=_no_files(_avatar_dir(setup_app)),
                allure_step_name="Файлы аватаров не созданы",
                error_text="Невалидная загрузка оставила файлы на диске",
            )


@epic("WEB")
@feature("Аватары пользователя")
@story("Сброс аватара")
class TestAvatarReset:
    """POST /user/<username>/avatar/reset: владелец возвращает автогенерацию."""

    @severity(severity_level.BLOCKER)
    @title("Владелец сбрасывает аватар: файлы снесены, ссылка пуста, профиль показывает автогенерацию")
    def test_owner_resets(self, setup_app: Flask, setup_test_user: UserObject):
        """Полный цикл загрузка → сброс: файлы удалены, автогенерация вернулась."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка аватара (предусловие)"):
            upload = user.web.users.upload_avatar(
                username=user.db_model.username,
                stream=BytesIO(make_png_bytes((100, 100))),
                filename="to_reset.png",
            )
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user.db_model.username),
                response=upload,
            )
        with step("ORM. Имя файла аватара"):
            filename = _avatar_filename(setup_app, user.db_model.username)
            assert_condition(
                condition=filename is not None,
                allure_step_name="Аватар загружен",
                error_text="Ссылка на аватар пуста после загрузки",
            )
        with step("Пользователь. WEB. Сброс аватара"):
            response = user.web.users.reset_avatar(username=user.db_model.username)
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user.db_model.username),
                response=response,
            )
        with step("ORM. Ссылка обнулена"):
            assert_equal(
                expect=None,
                actual=_avatar_filename(setup_app, user.db_model.username),
                name="Ссылка на аватар",
            )
        with step("Проверка удаления файлов"):
            root = _avatar_dir(setup_app)
            remaining = [path.name for path in _files(root) if path.name == filename]
            remaining += [path.name for path in _files(root / THUMBS_DIR) if path.name == filename]
            assert_condition(
                condition=not remaining,
                allure_step_name="Пара файлов снесена",
                error_text=f"После сброса остались файлы: {remaining}",
            )
        with step("Пользователь. WEB. Профиль после сброса"):
            page = user.web.users.profile(username=user.db_model.username)
            assert_status_code(expect=200, response=page)
            body = page.get_data(as_text=True)
            assert_condition(
                condition=(
                    FLASH_AVATAR_RESET in body
                    and f"avatar-palette-{avatar_color(user.db_model.username)}" in body
                    and "/uploads/avatars/" not in body
                ),
                allure_step_name="Флеш сброса и автогенерация на профиле",
                error_text="Профиль после сброса не вернул автогенерацию",
            )

    @severity(severity_level.NORMAL)
    @title("Гость на сбросе уходит на логин, аватар сохраняется")
    def test_guest_reset_redirect_to_login(
            self, setup_app: Flask, setup_app_client: FlaskClient, setup_test_user: UserObject,
    ):
        """Без сессии POST сброса — 302 на логин; файлы и ссылка на месте."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка аватара (предусловие)"):
            upload = user.web.users.upload_avatar(
                username=user.db_model.username,
                stream=BytesIO(make_png_bytes()),
                filename="keep.png",
            )
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user.db_model.username),
                response=upload,
            )
        with step("Пользователь. WEB. Выход из системы"):
            user.web.auth.logout()
        with step("Гость. WEB. Попытка сброса аватара"):
            response = WebClient(setup_app_client).users.reset_avatar(username=user.db_model.username)
            assert_status_code(expect=302, response=response)
            assert_condition(
                condition=response.headers.get("Location", "").startswith(WebEndpoints.AUTH.LOGIN),
                allure_step_name="Редирект ведёт на страницу логина",
                error_text=f"Ожидался редирект на логин, получено: {str(response.headers.get('Location'))}",
            )
        with step("Проверка сохранности аватара"):
            filename = _avatar_filename(setup_app, user.db_model.username)
            assert_condition(
                condition=filename is not None and (_avatar_dir(setup_app) / filename).exists(),
                allure_step_name="Файл аватара на месте",
                error_text="Гостевая попытка сброса затронула аватар",
            )

    @severity(severity_level.CRITICAL)
    @title("Не-владелец под сессией получает 404, аватар сохраняется")
    def test_foreign_reset_404(self, setup_app: Flask, setup_test_user: UserObject, setup_test_user_2: UserObject):
        """Пользователь 2 сбрасывает аватар Пользователя 1: скрытое действие — 404."""
        user_1, user_2 = setup_test_user, setup_test_user_2
        with step("Пользователь 1. WEB. Авторизация"):
            user_1.web.auth.login(username=user_1.db_model.username, password=user_1.password)
        with step("Пользователь 1. WEB. Загрузка аватара (предусловие)"):
            upload = user_1.web.users.upload_avatar(
                username=user_1.db_model.username,
                stream=BytesIO(make_png_bytes()),
                filename="stay.png",
            )
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user_1.db_model.username),
                response=upload,
            )
        with step("Пользователь 1. WEB. Выход из системы"):
            user_1.web.auth.logout()
        with step("Пользователь 2. WEB. Авторизация"):
            user_2.web.auth.login(username=user_2.db_model.username, password=user_2.password)
        with step("Пользователь 2. WEB. Попытка сброса чужого аватара"):
            response = user_2.web.users.reset_avatar(username=user_1.db_model.username)
            assert_status_code(expect=404, response=response)
        with step("Проверка сохранности аватара"):
            filename = _avatar_filename(setup_app, user_1.db_model.username)
            root = _avatar_dir(setup_app)
            assert_condition(
                condition=(
                    filename is not None
                    and (root / filename).exists()
                    and (root / THUMBS_DIR / filename).exists()
                ),
                allure_step_name="Пара файлов чужого аватара на месте",
                error_text="Чужой сброс затронул аватар",
            )


@epic("WEB")
@feature("Аватары пользователя")
@story("Отображаемое имя")
class TestDisplayName:
    """POST /user/<username>/display_name: владелец задаёт и сбрасывает имя."""

    @severity(severity_level.BLOCKER)
    @title("Владелец задаёт отображаемое имя: флеш, БД и автогенерация по имени")
    def test_owner_sets_name(self, setup_app: Flask, setup_test_user: UserObject):
        """Имя меняет показ на профиле: флеш с новым shown_name, буквы аватара — от имени, цвет — по логину."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Смена отображаемого имени"):
            response = user.web.users.change_display_name(
                username=user.db_model.username,
                display_name="Кот Барсик",
            )
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user.db_model.username),
                response=response,
            )
        with step("Пользователь. WEB. Профиль после смены"):
            page = user.web.users.profile(username=user.db_model.username)
            assert_status_code(expect=200, response=page)
            body = page.get_data(as_text=True)
            assert_condition(
                condition=f"{FLASH_NAME_UPDATED}Кот Барсик." in body,
                allure_step_name="Флеш с новым именем",
                error_text="Флеш смены имени не найден на профиле",
            )
            assert_condition(
                condition="Кот Барсик" in body and f"avatar-palette-{avatar_color(user.db_model.username)}" in body,
                allure_step_name="Имя на профиле, цвет аватара по логину",
                error_text="Профиль не показывает новое имя или сбил цвет автогенерации",
            )
            assert_condition(
                condition="КО" in body,
                allure_step_name="Автогенерация по первым буквам имени",
                error_text="Буквы аватара не перестроились на display_name",
            )
        with step("ORM. display_name в БД"):
            assert_equal(
                expect="Кот Барсик",
                actual=_display_name(setup_app, user.db_model.username),
                name="display_name",
            )

    @severity(severity_level.NORMAL)
    @title("Пустое значение сбрасывает имя к логину")
    def test_owner_clears_name(self, setup_app: Flask, setup_test_user: UserObject):
        """Сначала задаётся имя, потом пустое значение: shown_name возвращается к логину."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Задание имени (предусловие)"):
            set_response = user.web.users.change_display_name(
                username=user.db_model.username,
                display_name="Кот Барсик",
            )
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user.db_model.username),
                response=set_response,
            )
        with step("Пользователь. WEB. Сброс имени пустым значением"):
            response = user.web.users.change_display_name(
                username=user.db_model.username,
                display_name="",
            )
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user.db_model.username),
                response=response,
            )
        with step("Пользователь. WEB. Профиль после сброса"):
            page = user.web.users.profile(username=user.db_model.username)
            assert_status_code(expect=200, response=page)
            body = page.get_data(as_text=True)
            assert_condition(
                condition=f"{FLASH_NAME_UPDATED}{user.db_model.username}." in body,
                allure_step_name="Флеш с возвратом к логину",
                error_text="Флеш сброса имени не найден на профиле",
            )
        with step("ORM. display_name обнулён"):
            assert_equal(
                expect=None,
                actual=_display_name(setup_app, user.db_model.username),
                name="display_name",
            )

    @severity(severity_level.CRITICAL)
    @title("Имя длиннее лимита — 400, БД не меняется")
    def test_too_long_name_400(self, setup_app: Flask, setup_test_user: UserObject):
        """51 символ сверх лимита DISPLAY_NAME_MAX_LENGTH: BadRequestError → 400."""
        user = setup_test_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Смена имени на 51 символ"):
            response = user.web.users.change_display_name(
                username=user.db_model.username,
                display_name="а" * 51,
            )
            assert_status_code(expect=400, response=response)
        with step("ORM. Имя не изменено"):
            assert_equal(
                expect=None,
                actual=_display_name(setup_app, user.db_model.username),
                name="display_name",
            )

    @severity(severity_level.CRITICAL)
    @title("Не-владелец меняет имя чужого профиля — 404")
    def test_foreign_change_404(self, setup_test_user: UserObject, setup_test_user_2: UserObject):
        """Пользователь 2 POST-ит имя в профиль Пользователя 1: скрытое действие — 404."""
        user_1, user_2 = setup_test_user, setup_test_user_2
        with step("Пользователь 2. WEB. Авторизация"):
            user_2.web.auth.login(username=user_2.db_model.username, password=user_2.password)
        with step("Пользователь 2. WEB. Попытка смены чужого имени"):
            response = user_2.web.users.change_display_name(
                username=user_1.db_model.username,
                display_name="Взломано",
            )
            assert_status_code(expect=404, response=response)

    @severity(severity_level.NORMAL)
    @title("Гость на смене имени уходит на логин")
    def test_guest_redirect_to_login(
            self, setup_app_client: FlaskClient, setup_test_user: UserObject,
    ):
        """Без сессии POST display_name — 302 на логин (login_required)."""
        user = setup_test_user
        with step("Гость. WEB. Попытка смены имени без сессии"):
            response = WebClient(setup_app_client).users.change_display_name(
                username=user.db_model.username,
                display_name="Гость тут был",
            )
            assert_status_code(expect=302, response=response)
            assert_condition(
                condition=response.headers.get("Location", "").startswith(WebEndpoints.AUTH.LOGIN),
                allure_step_name="Редирект ведёт на страницу логина",
                error_text=f"Ожидался редирект на логин, получено: {str(response.headers.get('Location'))}",
            )


@epic("WEB")
@feature("Аватары пользователя")
@story("Удаление пользователя")
class TestDeleteUserAvatarFiles:
    """Интеграция delete_user: пара файлов аватара уходит с диска (→ ARC-0051)."""

    @severity(severity_level.CRITICAL)
    @title("Удаление пользователя сносит файлы его аватара")
    def test_admin_delete_removes_avatar_files(
            self, setup_app: Flask, setup_admin_user: UserObject, setup_test_user: UserObject,
    ):
        """Админ удаляет пользователя с аватаром: оба файла исчезают с диске."""
        user, admin = setup_test_user, setup_admin_user
        with step("Пользователь. WEB. Авторизация"):
            user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка аватара"):
            upload = user.web.users.upload_avatar(
                username=user.db_model.username,
                stream=BytesIO(make_png_bytes((100, 100))),
                filename="doomed.png",
            )
            assert_redirect(
                expect=WebEndpoints.USER.PROFILE.format(username=user.db_model.username),
                response=upload,
            )
        with step("ORM. Имя файла аватара"):
            filename = _avatar_filename(setup_app, user.db_model.username)
            assert_condition(
                condition=filename is not None,
                allure_step_name="Аватар загружен",
                error_text="Ссылка на аватар пуста после загрузки",
            )
        with step("Пользователь. WEB. Выход из системы"):
            user.web.auth.logout()
        with step("Администратор. WEB. Авторизация"):
            admin.web.auth.login(username=admin.db_model.username, password=admin.password)
        with step("Администратор. WEB. Удаление пользователя"):
            response = admin.web.admin.delete_user(user_id=user.db_model.id)
            assert_redirect(expect=WebEndpoints.ADMIN.USERS, response=response)
        with step("Проверка чистки файлов"):
            root = _avatar_dir(setup_app)
            remaining = [path.name for path in _files(root) if path.name == filename]
            remaining += [path.name for path in _files(root / THUMBS_DIR) if path.name == filename]
            assert_condition(
                condition=not remaining,
                allure_step_name="Пара файлов снесена после удаления пользователя",
                error_text=f"Файлы аватара остались после delete_user: {remaining}",
            )
