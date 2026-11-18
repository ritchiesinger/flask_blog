"""Тесты CLI-команды clean-uploads: чистка файлов-сирот."""

import uuid
from pathlib import Path

from flask import Flask
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.cli import clean_uploads
from blog.extensions import db
from blog.models import Post
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_equal
from tests.tools.cli_tools import invoke_cli


@epic("CLI")
@feature("Изображения")
@story("Чистка файлов-сирот")
class TestCleanUploads:
    """Проверки CLI-команды clean-uploads."""

    @title("Сирота удаляется, файл, на который ссылается пост, остаётся")
    @severity(severity_level.CRITICAL)
    def test_deletes_orphans_keeps_referenced(self, setup_app: Flask, setup_test_user: UserObject):
        """Файл без упоминания в постах удаляется, цитируемый остаётся на диске.

        Сиротой считается и загруженный, но не вставленный в текст файл —
        это осознанное поведение команды (докстринг фиксирует).
        """
        upload_folder = Path(setup_app.config["UPLOAD_FOLDER"])
        upload_folder.mkdir(parents=True, exist_ok=True)
        referenced = f"{uuid.uuid4().hex}.png"
        orphan = f"{uuid.uuid4().hex}.png"
        (upload_folder / referenced).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        (upload_folder / orphan).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)

        with step("Подготовка. ORM. Пост со ссылкой на цитируемый файл"):
            with setup_app.app_context():
                post = Post(
                    title="Пост с картинкой",
                    body=f"![кот](/uploads/{referenced})",
                    author_id=setup_test_user.db_model.id,
                )
                db.session.add(post)
                db.session.commit()

        with step("Оператор. CLI. Запуск чистки сирот"):
            result = invoke_cli(setup_app, clean_uploads, [])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="Удалено файлов-сирот: 1" in result.output,
                allure_step_name="В выводе счётчик с одной удалённой сиротой",
                error_text=f"Неожиданный вывод команды: {result.output}",
            )

        with step("Проверка файлов на диске"):
            assert_condition(
                condition=(upload_folder / referenced).is_file(),
                allure_step_name="Цитируемый файл остался на диске",
                error_text="Цитируемый файл удалён командой!",
            )
            assert_condition(
                condition=not (upload_folder / orphan).is_file(),
                allure_step_name="Файл-сирота удалён",
                error_text="Сирота осталась на диске!",
            )

    @title("Чистка без папки uploads и без постов отчитывается нулём удалений")
    @severity(severity_level.MINOR)
    def test_clean_with_no_uploads_reports_zero(self, setup_app: Flask):
        """Отсутствующая папка uploads не ломает команду: exit 0, «Удалено файлов-сирот: 0»."""
        with step("Оператор. CLI. Запуск чистки без папки uploads"):
            result = invoke_cli(setup_app, clean_uploads, [])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="Удалено файлов-сирот: 0" in result.output,
                allure_step_name="Команда отчиталась нулём удалений",
                error_text=f"Неожиданный вывод команды: {result.output}",
            )

    @title("Пост с пустым телом не ломает чистку")
    def test_clean_skips_empty_body(self, setup_app: Flask, setup_test_user: UserObject):
        """Пост без тела не падает в регулярку: команда завершается нулём.

        Закрывает ветку «тело пустое/None» — цикл по постам обязан
        переживать посты без содержимого.
        """
        with step("Подготовка. ORM. Пост с пустым телом"):
            with setup_app.app_context():
                post = Post(title="Без тела", body="", author_id=setup_test_user.db_model.id)
                db.session.add(post)
                db.session.commit()
        with step("Оператор. CLI. Запуск чистки сирот"):
            result = invoke_cli(setup_app, clean_uploads, [])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="Удалено файлов-сирот: 0" in result.output,
                allure_step_name="Команда отчиталась нулём удалений",
                error_text=f"Неожиданный вывод команды: {result.output}",
            )