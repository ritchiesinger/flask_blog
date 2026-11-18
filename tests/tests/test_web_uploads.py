"""WEB-тесты загрузки изображений: доступ, валидация, отдача файлов.

Загрузка — POST /uploads (только авторизованные), отдача — GET /uploads/<имя>
(публично: картинки в постах видят все). Валидация двух уровней: расширение
из белого списка и magic bytes — содержимое обязано совпасть с заявленным
форматом. UPLOAD_FOLDER в тестах — временная папка (проверка файла на диске
идёт через setup_app.config, рабочая папка проекта не затрагивается).
"""

from io import BytesIO
from pathlib import Path

from flask import Flask
from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_status_code
from tests.tools.clients.web_client import WebClient

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
GIF_BYTES = b"GIF89a" + b"\x00" * 8
JPEG_BYTES = b"\xff\xd8\xff" + b"\x00" * 16
WEBP_BYTES = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 8


@epic("WEB")
@feature("Изображения")
@story("Загрузка изображения")
class TestUpload:
    """POST /uploads: доступ, успешная загрузка и оба уровня валидации."""

    @title("Загрузка изображения без сессии ведёт на страницу авторизации")
    def test_guest_redirect_to_login(self, setup_app_client: FlaskClient):
        """Гость получает 302 на логин: upload — личное действие."""
        with step("WEB. Попытка загрузки без сессии"):
            response = WebClient(setup_app_client).uploads.upload(
                stream=BytesIO(PNG_BYTES), filename="pic.png",
            )
            assert_status_code(expect=302, response=response)

    @title("Успешная загрузка возвращает url и файл появляется на диске")
    @severity(severity_level.CRITICAL)
    def test_upload_success_saves_file(
            self, setup_app: Flask, setup_test_user: UserObject,
    ):
        """Валидный PNG: 200, в ответе url /uploads/<имя>, файл лежит в UPLOAD_FOLDER."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка валидного PNG"):
            response = user.web.uploads.upload(stream=BytesIO(PNG_BYTES), filename="pic.png")
            assert_status_code(expect=200, response=response)
            url = response.get_json()["url"]
            assert_condition(
                condition=url.startswith("/uploads/") and url.endswith(".png"),
                allure_step_name="Ответ несёт url внутри /uploads с расширением png",
                error_text=f"Неожиданный url в ответе: {url}",
            )
        with step("Проверка файла на диске"):
            name = Path(url).name
            saved = Path(setup_app.config["UPLOAD_FOLDER"]) / name
            assert_condition(
                condition=saved.is_file(),
                allure_step_name="Файл сохранён во временную папку uploads",
                error_text=f"Файл не найден на диске: {saved}",
            )
            assert_condition(
                condition=saved.read_bytes() == PNG_BYTES,
                allure_step_name="Содержимое файла сохранено без изменений",
                error_text="Содержимое сохранённого файла не совпадает с отправленным!",
            )

    @title("Файл с запрещённым расширением отклоняется (400)")
    def test_upload_rejects_bad_extension(self, setup_test_user: UserObject):
        """evil.exe не проходит первый фильтр: 400 — расширение не из белого списка."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Попытка загрузки exe-файла"):
            response = user.web.uploads.upload(stream=BytesIO(b"MZ..."), filename="evil.exe")
            assert_status_code(expect=400, response=response)

    @title("Расхождение расширения и содержимого отклоняется (400)")
    def test_upload_rejects_format_mismatch(self, setup_test_user: UserObject):
        """GIF-содержимое под именем .png не проходит второй фильтр: 400."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Попытка загрузки GIF под именем png"):
            response = user.web.uploads.upload(stream=BytesIO(GIF_BYTES), filename="fake.png")
            assert_status_code(expect=400, response=response)

    @title("Успешная загрузка JPEG возвращает url с расширением jpg")
    def test_upload_jpeg(self, setup_test_user: UserObject):
        """Валидный JPEG проходит оба фильтра: 200 и url с .jpg."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка валидного JPEG"):
            response = user.web.uploads.upload(stream=BytesIO(JPEG_BYTES), filename="photo.jpg")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=response.get_json()["url"].endswith(".jpg"),
                allure_step_name="url несёт расширение jpg",
                error_text=f"Неожиданный ответ: {response.get_json()}",
            )

    @title("Успешная загрузка WEBP возвращает url с расширением webp")
    def test_upload_webp(self, setup_test_user: UserObject):
        """Валидный WEBP проходит оба фильтра: 200 и url с .webp."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка валидного WEBP"):
            response = user.web.uploads.upload(stream=BytesIO(WEBP_BYTES), filename="photo.webp")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=response.get_json()["url"].endswith(".webp"),
                allure_step_name="url несёт расширение webp",
                error_text=f"Неожиданный ответ: {response.get_json()}",
            )

    @title("Файл без расширения отклоняется (400)")
    def test_upload_rejects_no_extension(self, setup_test_user: UserObject):
        """Имя без расширения не проходит первый фильтр: 400."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Попытка загрузки файла без расширения"):
            response = user.web.uploads.upload(stream=BytesIO(PNG_BYTES), filename="noext")
            assert_status_code(expect=400, response=response)

    @title("Нераспознанное содержимое отклоняется (400)")
    def test_upload_rejects_unknown_format(self, setup_test_user: UserObject):
        """Текст под именем .png не совпадает ни с одной сигнатурой: 400."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Попытка загрузки текста под именем png"):
            response = user.web.uploads.upload(stream=BytesIO(b"just text"), filename="note.png")
            assert_status_code(expect=400, response=response)

    @title("Запрос без поля file отклоняется (400)")
    def test_upload_without_file_field(self, setup_test_user: UserObject):
        """POST без multipart-поля 'file' — 400 до валидации содержимого."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. POST /uploads без файла"):
            response = user.web.uploads.posts_no_file()
            assert_status_code(expect=400, response=response)


@epic("WEB")
@feature("Изображения")
@story("Отдача изображения")
class TestServe:
    """GET /uploads/<имя>: публичная отдача и честная 404."""

    @title("Загруженная картинка доступна по своему url без авторизации")
    def test_serve_uploaded_image(
            self, setup_app_client: FlaskClient, setup_test_user: UserObject,
    ):
        """Отдача публична: гость получает 200 и байты, совпадающие с загруженными."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка валидного PNG"):
            response = user.web.uploads.upload(stream=BytesIO(PNG_BYTES), filename="pic.png")
            url = response.get_json()["url"]
        with step("Гость. WEB. Запрос картинки без сессии"):
            served = setup_app_client.get(url)
            assert_status_code(expect=200, response=served)
            assert_condition(
                condition=served.data == PNG_BYTES,
                allure_step_name="Отданные байты совпадают с загруженными",
                error_text="Байты картинки искажены при отдаче!",
            )

    @title("Запрос несуществующего изображения даёт 404")
    def test_serve_unknown_image_404(self, setup_app_client: FlaskClient):
        """Отсутствующий файл — 404; имена сгенерированные, обход каталогов исключён."""
        with step("Гость. WEB. Запрос несуществующего файла"):
            response = setup_app_client.get("/uploads/00000000000000000000000000000000.png")
            assert_status_code(expect=404, response=response)
