"""Тесты CLI-команд clean-uploads и make-thumbs: чистка сирот и бэкфилл (→ ARC-0044).

Источник истины — БД: сирота — строка Image без записей в image_post (файлы удаляются вместе со строкой); файл без
строки — дрейф (загрузки до ARC-0044, не прошедшие make-thumbs). make-thumbs принимает файлы-дрейф в БД (author_id None
— автор неизвестен) и генерирует миниатюры; GIF — без миниатюры.
"""

import uuid
from pathlib import Path

from flask import Flask
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.cli import clean_uploads, make_thumbs
from blog.extensions import db
from blog.models import Image, Post
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition, assert_equal
from tests.tools.cli_tools import invoke_cli
from tests.tools.image_factory import make_gif_bytes, make_png_bytes


@epic("CLI")
@feature("Изображения")
@story("Чистка сирот")
class TestCleanUploads:
    """Проверки CLI-команды clean-uploads на новой семантике БД."""

    @title("Строка-сирота удаляется с файлом, цитируемая остаётся")
    @severity(severity_level.CRITICAL)
    def test_deletes_orphan_row_keeps_referenced(self, setup_app: Flask, setup_test_user: UserObject):
        """Image без постов удаляется (файл и миниатюра), Image в посте живёт.

        Загруженная, но не вставленная картинка удаляется при чистке —
        осознанное поведение (докстринг команды фиксирует).
        """
        upload_folder = Path(setup_app.config["UPLOAD_FOLDER"])
        upload_folder.mkdir(parents=True, exist_ok=True)
        referenced = f"{uuid.uuid4().hex}.png"
        orphan = f"{uuid.uuid4().hex}.png"
        (upload_folder / referenced).write_bytes(make_png_bytes())
        (upload_folder / orphan).write_bytes(make_png_bytes())

        with step("Подготовка. ORM. Две строки Image и пост со ссылкой на цитируемый"):
            with setup_app.app_context():
                ref_row = Image(filename=referenced, author_id=setup_test_user.db_model.id)
                db.session.add(ref_row)
                db.session.add(Image(filename=orphan))
                post = Post(
                    title="Пост с картинкой",
                    body=f"![кот](/uploads/{referenced})",
                    author_id=setup_test_user.db_model.id,
                )
                post.images.append(ref_row)
                db.session.add(post)
                db.session.commit()

        with step("Оператор. CLI. Запуск чистки сирот"):
            result = invoke_cli(setup_app, clean_uploads, [])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="Удалено строк-сирот: 1" in result.output and "Удалено файлов-дрейфа: 0" in result.output,
                allure_step_name="Счётчики: одна строка-сирота, дрейфа нет",
                error_text=f"Неожиданный вывод команды: {result.output}",
            )

        with step("Проверка состояния"):
            assert_condition(
                condition=(upload_folder / referenced).is_file(),
                allure_step_name="Цитируемый файл остался на диске",
                error_text="Цитируемый файл удалён ошибочно!",
            )
            assert_condition(
                condition=not (upload_folder / orphan).is_file(),
                allure_step_name="Файл сироты удалён вместе со строкой",
                error_text="Файл сироты остался на диске!",
            )
            with setup_app.app_context():
                remaining = set(db.session.scalars(db.select(Image.filename)).all())
                assert_condition(
                    condition=remaining == {referenced},
                    allure_step_name="Строка-сирота удалена, цитируемая осталась",
                    error_text=f"Неожиданный набор строк Image: {remaining}",
                )

    @title("Файл без строки в БД (дрейф) удаляется чисткой")
    @severity(severity_level.CRITICAL)
    def test_deletes_drift_files(self, setup_app: Flask, setup_test_user: UserObject):
        """Файл на диске без строки Image — дрейф: удаляется, счётчик в выводе.

        Дрейф появляется у загрузок, не прошедших make-thumbs после обновления.
        """
        upload_folder = Path(setup_app.config["UPLOAD_FOLDER"])
        upload_folder.mkdir(parents=True, exist_ok=True)
        drift = f"{uuid.uuid4().hex}.png"
        (upload_folder / drift).write_bytes(make_png_bytes())

        with step("Оператор. CLI. Запуск чистки сирот"):
            result = invoke_cli(setup_app, clean_uploads, [])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="Удалено файлов-дрейфа: 1" in result.output and "Удалено строк-сирот: 0" in result.output,
                allure_step_name="Счётчики: один файл-дрейф, строк-сирот нет",
                error_text=f"Неожиданный вывод команды: {result.output}",
            )

        with step("Проверка состояния"):
            assert_condition(
                condition=not (upload_folder / drift).is_file(),
                allure_step_name="Файл-дрейф удалён с диска",
                error_text="Файл-дрейф остался на диске!",
            )

    @title("На пустом состоянии чистка отчитывается нулями")
    def test_clean_with_nothing_reports_zero(self, setup_app: Flask):
        """Ни строк-сирот, ни файлов: команда завершается нулями и без ошибок."""
        with step("Оператор. CLI. Запуск чистки на пустом состоянии"):
            result = invoke_cli(setup_app, clean_uploads, [])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="Удалено строк-сирот: 0. Удалено файлов-дрейфа: 0." in result.output,
                allure_step_name="Команда отчиталась нулями удалений",
                error_text=f"Неожиданный вывод команды: {result.output}",
            )


@epic("CLI")
@feature("Изображения")
@story("Бэкфилл и миниатюры")
class TestMakeThumbs:
    """Проверки CLI-команды make-thumbs: приём дрейфа и генерация миниатюр."""

    @title("make-thumbs принимает файлы без строк и генерирует миниатюры")
    @severity(severity_level.CRITICAL)
    def test_backfill_adopts_and_generates(self, setup_app: Flask, setup_test_user: UserObject):
        """PNG без строки: строка появляется (author None), миниатюра — на диске."""
        upload_folder = Path(setup_app.config["UPLOAD_FOLDER"])
        upload_folder.mkdir(parents=True, exist_ok=True)
        name = f"{uuid.uuid4().hex}.png"
        (upload_folder / name).write_bytes(make_png_bytes())

        with step("Оператор. CLI. Запуск бэкфилла"):
            result = invoke_cli(setup_app, make_thumbs, [])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="Принято в БД: 1. Сгенерировано миниатюр: 1." in result.output,
                allure_step_name="Счётчики: одна принятая строка, одна миниатюра",
                error_text=f"Неожиданный вывод команды: {result.output}",
            )

        with step("Проверка состояния"):
            with setup_app.app_context():
                row = db.session.execute(db.select(Image).filter_by(filename=name)).scalars().first()
                assert_condition(
                    condition=row is not None,
                    allure_step_name="Файл отражён строкой Image",
                    error_text=f"Строка Image не найдена для {name}",
                )
                assert_condition(
                    condition=row is not None and row.author_id is None,
                    allure_step_name="Автор бэкфилл-загрузки неизвестен (None)",
                    error_text=f"Неожиданный author_id у бэкфилл-строки: {row.author_id if row else None}",
                )
            assert_condition(
                condition=(upload_folder / "thumbs" / name).is_file(),
                allure_step_name="Миниатюра сгенерирована в thumbs/",
                error_text=f"Миниатюра не найдена: {upload_folder / 'thumbs' / name}",
            )

    @title("Повторный запуск make-thumbs ничего не делает (идемпотентен)")
    def test_second_run_reports_zero(self, setup_app: Flask, setup_test_user: UserObject):
        """Файл с уже существующей строкой не принимается повторно: нули в выводе."""
        upload_folder = Path(setup_app.config["UPLOAD_FOLDER"])
        upload_folder.mkdir(parents=True, exist_ok=True)
        name = f"{uuid.uuid4().hex}.png"
        (upload_folder / name).write_bytes(make_png_bytes())

        with step("Оператор. CLI. Первый запуск бэкфилла"):
            result = invoke_cli(setup_app, make_thumbs, [])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")

        with step("Оператор. CLI. Повторный запуск бэкфилла"):
            result = invoke_cli(setup_app, make_thumbs, [])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="Принято в БД: 0. Сгенерировано миниатюр: 0." in result.output,
                allure_step_name="Повторный запуск отчитался нулями",
                error_text=f"Неожиданный вывод повторного запуска: {result.output}",
            )

    @title("Нечитаемый файл принимается строкой, но без миниатюры")
    def test_garbage_file_adopted_without_thumb(self, setup_app: Flask, setup_test_user: UserObject):
        """Файл, не открывающийся Pillow'ом, получает строку, миниатюры нет.

        Покрывает защитную ветку backfill_files: битый файл не валит команду.
        """
        upload_folder = Path(setup_app.config["UPLOAD_FOLDER"])
        upload_folder.mkdir(parents=True, exist_ok=True)
        name = f"{uuid.uuid4().hex}.png"
        (upload_folder / name).write_bytes(b"not an image at all")

        with step("Оператор. CLI. Запуск бэкфилла с нечитаемым файлом"):
            result = invoke_cli(setup_app, make_thumbs, [])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="Принято в БД: 1. Сгенерировано миниатюр: 0." in result.output,
                allure_step_name="Счётчики: строка принята, миниатюр нет",
                error_text=f"Неожиданный вывод команды: {result.output}",
            )

        with step("Проверка состояния"):
            assert_condition(
                condition=not (upload_folder / "thumbs" / name).is_file(),
                allure_step_name="Миниатюра для нечитаемого файла не создавалась",
                error_text=f"Неожиданная миниатюра: {upload_folder / 'thumbs' / name}",
            )

    @title("GIF принимается строкой, но без миниатюры")
    def test_backfill_gif_no_thumb(self, setup_app: Flask, setup_test_user: UserObject):
        """GIF в бэкфилле: строка есть, миниатюра не генерируется (по дизайну)."""
        upload_folder = Path(setup_app.config["UPLOAD_FOLDER"])
        upload_folder.mkdir(parents=True, exist_ok=True)
        name = f"{uuid.uuid4().hex}.gif"
        (upload_folder / name).write_bytes(make_gif_bytes())

        with step("Оператор. CLI. Запуск бэкфилла с GIF"):
            result = invoke_cli(setup_app, make_thumbs, [])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="Принято в БД: 1. Сгенерировано миниатюр: 0." in result.output,
                allure_step_name="Счётчики: строка принята, миниатюр нет",
                error_text=f"Неожиданный вывод команды: {result.output}",
            )

        with step("Проверка состояния"):
            assert_condition(
                condition=not (upload_folder / "thumbs" / name).is_file(),
                allure_step_name="Миниатюра для GIF не создавалась",
                error_text=f"Неожиданная миниатюра: {upload_folder / 'thumbs' / name}",
            )

    @severity(severity_level.BLOCKER)
    @title("make-thumbs восстанавливает связи постов, созданных до раунда")
    def test_sync_rebuilds_old_post_links(self, setup_app: Flask, setup_test_user: UserObject):
        """Файл из тела старого поста без связи.

        make-thumbs строит image_post, после чего clean-uploads оставляет файл на диске.
        """
        upload_folder = Path(setup_app.config["UPLOAD_FOLDER"])
        upload_folder.mkdir(parents=True, exist_ok=True)
        name = f"{uuid.uuid4().hex}.png"
        (upload_folder / name).write_bytes(make_png_bytes())

        with step("Подготовка. ORM. Пост со ссылкой, без строки Image и без связи"):
            with setup_app.app_context():
                db.session.add(Post(
                    title="Старый пост",
                    body=f"![кот](/uploads/{name})",
                    author_id=setup_test_user.db_model.id,
                ))
                db.session.commit()

        with step("Оператор. CLI. make-thumbs пересобирает связи"):
            result = invoke_cli(setup_app, make_thumbs, [])
            assert_equal(expect=0, actual=result.exit_code, name="Exit code")
            assert_condition(
                condition="Принято в БД: 1. Сгенерировано миниатюр: 1. Связей пересобрано: 1." in result.output,
                allure_step_name="Связь старого поста восстановлена",
                error_text=f"Неожиданный вывод команды: {result.output}",
            )

        with step("Оператор. CLI. Чистка не трогает принятый файл"):
            result = invoke_cli(setup_app, clean_uploads, [])
            assert_condition(
                condition="Удалено строк-сирот: 0" in result.output,
                allure_step_name="Чистка не удалила связанную картинку",
                error_text=f"Неожиданный вывод команды: {result.output}",
            )
            assert_condition(
                condition=(upload_folder / name).is_file(),
                allure_step_name="Файл старого поста остался на диске",
                error_text="Файл связанного поста удалён чисткой!",
            )

