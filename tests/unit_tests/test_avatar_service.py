"""Юнит-тесты сервиса аватаров: ветки, срабатывающие до обращения к диску и БД.

Успешные save_avatar/reset_avatar (нужны БД и текущее приложение) накрыты WEB-пакетом профиля; здесь — гвард
владельца и валидация загрузки: каждый отказ поднимается до первого обращения к current_app и файловой системе
(канон test_user_service_roles: гварды и до-БД ветки на detached-моделях с явными id).
"""

from io import BytesIO

from glamor import epic, feature, severity, severity_level, step, story, title
from pytest import raises

from blog.models import User
from blog.services.avatar_service import reset_avatar, save_avatar
from blog.services.base_errors import BadRequestError, ForbiddenError
from tests.tools.asserters.base_asserters import assert_equal
from tests.tools.image_factory import make_bmp_bytes, make_png_bytes

GARBAGE_BYTES = b"not an image"


@epic("UNIT")
@feature("Аватары пользователя", "Профиль")
@story("Гвард владельца")
class TestSaveAvatarOwnerGuard:
    """Сервисная защита save_avatar: аватар меняет только владелец."""

    @severity(severity_level.CRITICAL)
    @title("Чужой актёр получает ForbiddenError до обращения к диску и валидации")
    def test_non_owner_raises_forbidden_before_validation(self):
        """Гвард срабатывает раньше валидации: ломаное содержимое не затмевает запрет.

        Ожидание: ForbiddenError даже при не-изображении в потоке — защита владельца стоит первой
        (defense-in-depth; WEB-роут прячет действие 404 раньше).
        """
        with step("MODEL. Создание владельца и чужого актёра с явными id"):
            owner = User(username="owner")
            owner.id = 1
            actor = User(username="stranger")
            actor.id = 2
        with step("User. SERVICE. Попытка загрузки аватара чужим актёром"):
            with raises(ForbiddenError) as exc_info:
                save_avatar(owner, BytesIO(GARBAGE_BYTES), "avatar.png", actor=actor)
        assert_equal(
            expect="Аватар меняет только владелец профиля",
            actual=str(exc_info.value),
            name="Текст ForbiddenError",
        )


@story("Валидация загрузки")
class TestSaveAvatarValidation:
    """Трёхступенчатая валидация save_avatar: расширение → содержимое → формат."""

    @severity(severity_level.CRITICAL)
    @title("Расширение вне белого списка отклоняется до разбора содержимого")
    def test_unsupported_extension_rejected(self):
        """Имя с расширением txt → BadRequestError, содержимое не открывается.

        Первый фильтр — по имени файла: в потоке валидный PNG, но ошибка должна говорить о расширении, не о
        содержимом — порядок проверок подтверждается самим текстом исключения.
        """
        with step("MODEL. Создание владельца-актёра"):
            owner = User(username="owner")
            owner.id = 1
        with step("User. SERVICE. Загрузка валидного PNG под именем avatar.txt"):
            with raises(BadRequestError) as exc_info:
                save_avatar(owner, BytesIO(make_png_bytes()), "avatar.txt", actor=owner)
        assert_equal(
            expect="Расширение файла не поддерживается: txt",
            actual=str(exc_info.value),
            name="Текст BadRequestError",
        )

    @severity(severity_level.CRITICAL)
    @title("Содержимое, не являющееся изображением, отклоняется BadRequestError")
    def test_non_image_content_rejected(self):
        """Произвольные байты под валидным именем → BadRequestError от провала Pillow.open.

        Ожидание: единый текст без деталей исходного исключения — доменная ошибка не роняет HTTP-слой.
        """
        with step("MODEL. Создание владельца-актёра"):
            owner = User(username="owner")
            owner.id = 1
        with step("User. SERVICE. Загрузка не-изображения под именем avatar.png"):
            with raises(BadRequestError) as exc_info:
                save_avatar(owner, BytesIO(GARBAGE_BYTES), "avatar.png", actor=owner)
        assert_equal(
            expect="Содержимое не является изображением.",
            actual=str(exc_info.value),
            name="Текст BadRequestError",
        )

    @severity(severity_level.CRITICAL)
    @title("Изображение формата вне карты отклоняется BadRequestError")
    def test_unsupported_content_format_rejected(self):
        """BMP под именем .png → BadRequestError: проверяется сигнатура, а не имя.

        Расширение png проходит белый список, Pillow открывает BMP — отсекает третий фильтр, карта форматов
        содержимого (расширение и содержимое расходятся сознательно, → ARC-0044).
        """
        with step("MODEL. Создание владельца-актёра"):
            owner = User(username="owner")
            owner.id = 1
        with step("User. SERVICE. Загрузка BMP под именем avatar.png"):
            with raises(BadRequestError) as exc_info:
                save_avatar(owner, BytesIO(make_bmp_bytes()), "avatar.png", actor=owner)
        assert_equal(
            expect="Формат содержимого не поддерживается.",
            actual=str(exc_info.value),
            name="Текст BadRequestError",
        )


@story("Сброс аватара")
class TestResetAvatar:
    """Гвард reset_avatar и no-op без установленного аватара."""

    @severity(severity_level.CRITICAL)
    @title("Чужой актёр получает ForbiddenError при попытке сброса")
    def test_non_owner_reset_raises_forbidden(self):
        """Сброс чужого аватара → ForbiddenError до обращения к диску и БД (defense-in-depth)."""
        with step("MODEL. Создание владельца и чужого актёра с явными id"):
            owner = User(username="owner")
            owner.id = 1
            actor = User(username="stranger")
            actor.id = 2
        with step("User. SERVICE. Попытка сброса аватара чужим актёром"):
            with raises(ForbiddenError) as exc_info:
                reset_avatar(owner, actor=actor)
        assert_equal(
            expect="Аватар меняет только владелец профиля",
            actual=str(exc_info.value),
            name="Текст ForbiddenError",
        )

    @severity(severity_level.NORMAL)
    @title("Сброс без установленного аватара — тихий no-op")
    def test_reset_without_avatar_is_noop(self):
        """avatar_filename пуст → сервис молча завершается: файлов нет, ссылка не меняется.

        Роут при этом всё равно показывает флеш об успехе — осознанный контракт (кнопка сброса видна и при
        автогенерации; → ARC-0051).
        """
        with step("MODEL. Создание владельца-актёра без аватара"):
            owner = User(username="owner")
            owner.id = 1
        with step("User. SERVICE. Сброс аватара, которого нет"):
            reset_avatar(owner, actor=owner)
        assert_equal(
            expect=None,
            actual=owner.avatar_filename,
            name="Ссылка на аватар осталась пустой",
        )
