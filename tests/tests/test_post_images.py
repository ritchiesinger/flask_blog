"""Тесты синхронизации связей поста с изображениями (→ ARC-0044).

Связи image_post перестраиваются из UPLOAD_RE при создании и обновлении
поста: вставленные картинки получают связь, вырезанные — теряют её; ссылки
на несуществующие в БД имена не создают пустых строк. Логика сервисная —
накрывается напрямую, без интерфейсной обвязки.
"""

import uuid

from flask import Flask
from glamor import epic, feature, severity, severity_level, step, story, title

from blog.extensions import db
from blog.models import Image
from blog.services import post_service
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition


@epic("Сервисы")
@feature("Изображения")
@story("Синхронизация связей поста")
class TestSyncImageLinks:
    """Перестройка набора image_post при создании и обновлении поста."""

    @severity(severity_level.CRITICAL)
    @title("create_post связывает пост с существующими картинками из тела")
    def test_create_post_syncs_image_links(self, setup_app: Flask, setup_test_user: UserObject):
        """Ссылка на существующую строку Image создаёт связь image_post."""
        filename = f"{uuid.uuid4().hex}.png"
        with setup_app.app_context():
            with step("Подготовка. ORM. Строка Image"):
                db.session.add(Image(filename=filename))
                db.session.commit()
            with step("Сервис. Создание поста со ссылкой на картинку"):
                post = post_service.create_post(
                    title="С картинкой",
                    body=f"![кот](/uploads/{filename})",
                    author_id=setup_test_user.db_model.id,
                )
                assert_condition(
                    condition=[image.filename for image in post.images] == [filename],
                    allure_step_name="Связь поста с картинкой установлена",
                    error_text=f"Неожиданные изображения поста: {[i.filename for i in post.images]}",
                )

    @title("create_post не создаёт связь для несуществующего имени")
    def test_create_post_ignores_unknown_name(self, setup_app: Flask, setup_test_user: UserObject):
        """Ссылка на имя без строки Image не создаёт связь."""
        filename = f"{uuid.uuid4().hex}.png"
        with setup_app.app_context():
            with step("Сервис. Создание поста со ссылкой на несуществующую картинку"):
                post = post_service.create_post(
                    title="Без картинки",
                    body=f"![кот](/uploads/{filename})",
                    author_id=setup_test_user.db_model.id,
                )
                assert_condition(
                    condition=post.images == [],
                    allure_step_name="Связь не создана",
                    error_text=f"Неожиданные изображения поста: {post.images}",
                )

    @severity(severity_level.CRITICAL)
    @title("update_post снимает связь с вырезанной картинкой")
    def test_update_post_cuts_image_link(self, setup_app: Flask, setup_test_user: UserObject):
        """Картинка, убранная из тела при правке, теряет связь (сироты — чистке)."""
        filename = f"{uuid.uuid4().hex}.png"
        with setup_app.app_context():
            with step("Подготовка. ORM. Строка Image и пост со ссылкой"):
                db.session.add(Image(filename=filename))
                db.session.commit()
                post = post_service.create_post(
                    title="С картинкой",
                    body=f"![кот](/uploads/{filename})",
                    author_id=setup_test_user.db_model.id,
                )
            with step("Сервис. Обновление поста без картинки в теле"):
                post_service.update_post(post, title="С картинкой", body="Текст без картинки")
                db.session.refresh(post)
                assert_condition(
                    condition=post.images == [],
                    allure_step_name="Связь снята при обновлении",
                    error_text=f"Связь не снята: {post.images}",
                )
