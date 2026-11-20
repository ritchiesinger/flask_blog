"""WEB-тесты загрузки изображений: доступ, валидация, обработка, отдача.

Загрузка — POST /uploads (только авторизованные), отдача — GET /uploads/<путь> (публично, включая миниатюры). Сервис
обрабатывает картинку: детальная версия до MAX_IMAGE_SIDE + миниатюра thumbs/<имя>; GIF — как есть, без миниатюры.
Реальный формат определяет Pillow: GIF под именем .png сохраняется как .gif (автозамена по содержимому, → ARC-0044).
"""

from io import BytesIO
from pathlib import Path

from flask import Flask
from flask.testing import FlaskClient
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.extensions import db
from blog.models import Image
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_status_code
from tests.tools.clients.web_client import WebClient
from tests.tools.image_factory import (
    make_bmp_bytes,
    make_cmyk_jpeg_bytes,
    make_gif_bytes,
    make_jpeg_bytes,
    make_png_bytes,
    make_webp_bytes,
)


def _upload(user: UserObject, data: bytes, name: str):
    """Загружает изображение от имени пользователя и возвращает ответ.

    Args:
        user: Объект пользователя.
        data: Содержимое изображения.
        name: Имя файла от пользователя.

    Returns:
        Ответ WEB-клиента.
    """
    return user.web.uploads.upload(stream=BytesIO(data), filename=name)


@epic("WEB")
@feature("Изображения")
@story("Загрузка изображения")
class TestUpload:
    """POST /uploads: доступ, обработка, автозамена формата и валидация."""

    @title("Загрузка изображения без сессии ведёт на страницу авторизации")
    def test_guest_redirect_to_login(self, setup_app_client: FlaskClient):
        """Гость получает 302 на логин: upload — личное действие."""
        with step("WEB. Попытка загрузки без сессии"):
            response = WebClient(setup_app_client).uploads.upload(
                stream=BytesIO(make_png_bytes()), filename="pic.png",
            )
            assert_status_code(expect=302, response=response)

    @severity(severity_level.BLOCKER)
    @title("Успешная загрузка PNG: детальная версия, миниатюра и строка Image")
    def test_upload_success_saves_file(
            self, setup_app: Flask, setup_test_user: UserObject,
    ):
        """Валидный PNG: 200, файл и thumbs/<имя> на диске, строка Image в БД."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка валидного PNG"):
            response = _upload(user, make_png_bytes(), "pic.png")
            assert_status_code(expect=200, response=response)
            url = response.get_json()["url"]
            assert_condition(
                condition=url.startswith("/uploads/") and url.endswith(".png"),
                allure_step_name="Ответ несёт url внутри /uploads с расширением png",
                error_text=f"Неожиданный url в ответе: {url}",
            )
        name = Path(url).name
        folder = Path(setup_app.config["UPLOAD_FOLDER"])
        with step("Проверка сохранения"):
            detailed = folder / name
            assert_condition(
                condition=detailed.is_file(),
                allure_step_name="Детальная версия сохранена во временную папку",
                error_text=f"Файл не найден на диске: {detailed}",
            )
            thumb = folder / "thumbs" / name
            assert_condition(
                condition=thumb.is_file(),
                allure_step_name="Миниатюра сохранена в thumbs/ под тем же именем",
                error_text=f"Миниатюра не найдена на диске: {thumb}",
            )
        with step("Проверка строки в БД"):
            with setup_app.app_context():
                row = db.session.execute(db.select(Image).filter_by(filename=name)).scalars().first()
                assert_condition(
                    condition=row is not None,
                    allure_step_name="Загрузка отражена строкой Image в БД",
                    error_text=f"Строка Image не найдена для {name}",
                )

    @title("Успешная загрузка JPEG возвращает url с расширением jpg")
    def test_upload_jpeg(self, setup_test_user: UserObject):
        """Валидный JPEG проходит: 200 и url с .jpg."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка валидного JPEG"):
            response = _upload(user, make_jpeg_bytes(), "photo.jpg")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=response.get_json()["url"].endswith(".jpg"),
                allure_step_name="url несёт расширение jpg",
                error_text=f"Неожиданный ответ: {response.get_json()}",
            )

    @title("Успешная загрузка WEBP возвращает url с расширением webp")
    def test_upload_webp(self, setup_test_user: UserObject):
        """Валидный WEBP проходит: 200 и url с .webp."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка валидного WEBP"):
            response = _upload(user, make_webp_bytes(), "photo.webp")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=response.get_json()["url"].endswith(".webp"),
                allure_step_name="url несёт расширение webp",
                error_text=f"Неожиданный ответ: {response.get_json()}",
            )

    @severity(severity_level.CRITICAL)
    @title("GIF сохраняется без миниатюры (анимация не пересохраняется)")
    def test_upload_gif_no_thumb(
            self, setup_app: Flask, setup_test_user: UserObject,
    ):
        """GIF: 200, файл на диске, thumbs/<имя> отсутствует — по дизайну."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка GIF"):
            response = _upload(user, make_gif_bytes(), "anim.gif")
            assert_status_code(expect=200, response=response)
            url = response.get_json()["url"]
        name = Path(url).name
        folder = Path(setup_app.config["UPLOAD_FOLDER"])
        with step("Проверка сохранения"):
            assert_condition(
                condition=(folder / name).is_file(),
                allure_step_name="GIF сохранён в uploads",
                error_text=f"GIF не найден на диске: {folder / name}",
            )
            assert_condition(
                condition=not (folder / "thumbs" / name).is_file(),
                allure_step_name="Миниатюра для GIF не генерируется",
                error_text=f"Неожиданная миниатюра: {folder / 'thumbs' / name}",
            )

    @severity(severity_level.CRITICAL)
    @title("GIF-содержимое под именем .png сохраняется как .gif (автозамена)")
    def test_upload_format_mismatch_autocorrected(self, setup_test_user: UserObject):
        """Содержимое главнее имени: 200 и url с .gif вместо .png."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка GIF под именем fake.png"):
            response = _upload(user, make_gif_bytes(), "fake.png")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=response.get_json()["url"].endswith(".gif"),
                allure_step_name="Имя файла построено под реальный формат",
                error_text=f"Автозамена формата не сработала: {response.get_json()}",
            )

    @title("Файл с запрещённым расширением отклоняется (400)")
    def test_upload_rejects_bad_extension(self, setup_test_user: UserObject):
        """evil.exe не проходит первый фильтр: 400 — расширение не из белого списка."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Попытка загрузки exe-файла"):
            response = _upload(user, b"MZ...", "evil.exe")
            assert_status_code(expect=400, response=response)

    @title("Файл без расширения отклоняется (400)")
    def test_upload_rejects_no_extension(self, setup_test_user: UserObject):
        """Имя без расширения не проходит первый фильтр: 400."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Попытка загрузки файла без расширения"):
            response = _upload(user, make_png_bytes(), "noext")
            assert_status_code(expect=400, response=response)

    @title("Нераспознанное содержимое отклоняется (400)")
    def test_upload_rejects_unknown_format(self, setup_test_user: UserObject):
        """Текст под именем .png не открывается Pillow'ом: 400."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Попытка загрузки текста под именем png"):
            response = _upload(user, b"just text", "note.png")
            assert_status_code(expect=400, response=response)

    @title("Запрос без поля file отклоняется (400)")
    def test_upload_without_file_field(self, setup_test_user: UserObject):
        """POST без multipart-поля 'file' — 400 до валидации содержимого."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. POST /uploads без файла"):
            response = user.web.uploads.posts_no_file()
            assert_status_code(expect=400, response=response)

    @severity(severity_level.CRITICAL)
    @title("CMYK JPEG конвертируется в RGB при обработке")
    def test_upload_cmyk_jpeg(self, setup_test_user: UserObject):
        """JPEG в режиме CMYK: 200 — сервис конвертирует в RGB перед кодированием."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка CMYK JPEG"):
            response = _upload(user, make_cmyk_jpeg_bytes(), "print.jpg")
            assert_status_code(expect=200, response=response)
            assert_condition(
                condition=response.get_json()["url"].endswith(".jpg"),
                allure_step_name="CMYK JPEG обработан, url с расширением jpg",
                error_text=f"Неожиданный ответ: {response.get_json()}",
            )

    @title("Валидный формат вне белого списка отклоняется (400)")
    def test_upload_rejects_unlisted_format(self, setup_test_user: UserObject):
        """BMP под именем .png: расширение проходит фильтр, формат не в карте — 400."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Попытка загрузки BMP под именем png"):
            response = _upload(user, make_bmp_bytes(), "pic.png")
            assert_status_code(expect=400, response=response)

    @title("Файл больше серверного лимита отклоняется (413)")
    def test_upload_too_large_413(self, setup_app: Flask, setup_test_user: UserObject):
        """MAX_CONTENT_LENGTH: превышение тела запроса — 413 с JSON-ошибкой."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Сценарий. Сервер отклоняет файл больше MAX_CONTENT_LENGTH"):
            # 100 байт меньше любого multipart-запроса: даже крошечный PNG
            # гарантированно превышает лимит, и Werkzeug режет его до вью.
            setup_app.config["MAX_CONTENT_LENGTH"] = 100
            response = _upload(user, make_png_bytes((50, 50)), "big.png")
            assert_status_code(expect=413, response=response)
            assert_condition(
                condition="сервер принимает изображения до 50 МБ" in response.get_json()["error"],
                allure_step_name="Пользователю доступно сообщение о лимите",
                error_text=f"Неожиданный ответ: {response.get_json()}",
            )

    @title("Обходчик получает короткий 413 без упоминания лимита")
    def test_too_large_413_other_paths(self, setup_app: Flask, setup_test_user: UserObject):
        """Превышение тела вне /uploads — 413 с общим текстом."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Сценарий. Пост с телом больше MAX_CONTENT_LENGTH"):
            setup_app.config["MAX_CONTENT_LENGTH"] = 100
            response = user.web.posts.create(title="Большой пост", body="x" * 2048)
            assert_status_code(expect=413, response=response)
            assert_condition(
                condition=response.get_json()["error"] == "Запрос слишком большой.",
                allure_step_name="Общая ветка отвечает своим точным текстом",
                error_text=f"Неожиданный ответ: {response.get_json()}",
            )


@epic("WEB")
@feature("Изображения")
@story("Отдача изображения")
class TestServe:
    """GET /uploads/<путь>: публичная отдача детальной версии и миниатюры."""

    @title("Загруженная картинка доступна по своему url без авторизации")
    def test_serve_uploaded_image(
            self, setup_app: Flask, setup_app_client: FlaskClient, setup_test_user: UserObject,
    ):
        """Отдача публична: гость получает 200 и байты сохранённой версии."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка валидного PNG"):
            response = _upload(user, make_png_bytes(), "pic.png")
            url = response.get_json()["url"]
        name = Path(url).name
        saved = Path(setup_app.config["UPLOAD_FOLDER"]) / name
        with step("Гость. WEB. Запрос картинки без сессии"):
            served = setup_app_client.get(url)
            assert_status_code(expect=200, response=served)
            assert_condition(
                condition=served.data == saved.read_bytes(),
                allure_step_name="Отданные байты совпадают с сохранённой версией",
                error_text="Байты картинки искажены при отдаче!",
            )

    @title("Миниатюра доступна по пути thumbs/<имя>")
    def test_serve_thumb(self, setup_app_client: FlaskClient, setup_test_user: UserObject):
        """Гость получает 200 на /uploads/thumbs/<имя> — тот же публичный роут."""
        user = setup_test_user
        user.web.auth.login(username=user.db_model.username, password=user.password)
        with step("Пользователь. WEB. Загрузка валидного PNG"):
            response = _upload(user, make_png_bytes(), "pic.png")
            name = Path(response.get_json()["url"]).name
        with step("Гость. WEB. Запрос миниатюры без сессии"):
            served = setup_app_client.get(f"/uploads/thumbs/{name}")
            assert_status_code(expect=200, response=served)

    @title("Запрос несуществующего изображения даёт 404")
    def test_serve_unknown_image_404(self, setup_app_client: FlaskClient):
        """Отсутствующий файл — 404; имена сгенерированные, обход каталогов исключён."""
        with step("Гость. WEB. Запрос несуществующего файла"):
            response = setup_app_client.get("/uploads/00000000000000000000000000000000.png")
            assert_status_code(expect=404, response=response)
