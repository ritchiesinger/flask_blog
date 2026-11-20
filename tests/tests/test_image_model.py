"""Тесты модели Image: repr и словарное представление (→ ARC-0044)."""

from flask import Flask
from glamor import epic, feature, step, story, title

from blog.extensions import db
from blog.models import Image
from tests.objects.user import UserObject
from tests.tools.asserters.base_asserters import assert_condition


@epic("Модели")
@feature("Изображения")
@story("Представление модели")
class TestImageModel:
    """repr и to_dict модели Image, включая ветку без автора (бэкфилл)."""

    @title("repr содержит имя файла")
    def test_repr_contains_filename(self):
        """repr(Image) несёт имя файла."""
        image = Image(filename="a1b2c3d4.png", author_id=1)
        with step("Проверка repr"):
            assert_condition(
                condition="a1b2c3d4.png" in repr(image),
                allure_step_name="repr содержит имя файла",
                error_text=f"Неожиданный repr: {image!r}",
            )

    @title("to_dict с автором несёт имя автора")
    def test_to_dict_with_author(self, setup_app: Flask, setup_test_user: UserObject):
        """Обычная загрузка: author.id и author.username заполнены."""
        with setup_app.app_context():
            with step("Подготовка. ORM. Строка Image с автором"):
                image = Image(filename="a.png", author_id=setup_test_user.db_model.id)
                db.session.add(image)
                db.session.commit()
            with step("Сервис. Словарное представление"):
                data = image.to_dict()
                assert_condition(
                    condition=data["author"]["username"] == setup_test_user.db_model.username,
                    allure_step_name="username автора присутствует",
                    error_text=f"Неожиданный словарь: {data}",
                )

    @title("to_dict бэкфилл-загрузки не ломается без автора")
    def test_to_dict_without_author(self, setup_app: Flask):
        """author_id=None (бэкфилл): username — None, словарь собирается."""
        with setup_app.app_context():
            with step("Подготовка. ORM. Строка Image без автора"):
                image = Image(filename="a.png")
                db.session.add(image)
                db.session.commit()
            with step("Сервис. Словарное представление"):
                data = image.to_dict()
                assert_condition(
                    condition=data["author"]["username"] is None,
                    allure_step_name="username пуст для загрузки без автора",
                    error_text=f"Неожиданный словарь: {data}",
                )
