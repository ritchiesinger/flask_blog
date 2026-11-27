"""Юнит-тесты плагинов раунда С: :::img, :::gallery, :::carousel (→ ARC-0057, п. 29 бэклога)."""

from types import SimpleNamespace

from glamor import epic, feature, severity, severity_level, story, title

from blog.services.markdown import render_markdown
from blog.services.markdown.blocks import carousel_plugin, gallery_plugin, img_plugin
from tests.tools.asserters.base_asserters import assert_condition
from tests.tools.asserters.soft_asserters import SoftAssert

UPLOAD_NAME = "0123456789abcdef0123456789abcdef"
UPLOAD_PNG = f"/uploads/{UPLOAD_NAME}.png"
UPLOAD_THUMB = f"/uploads/thumbs/{UPLOAD_NAME}.png"
UPLOAD_GIF = f"/uploads/{UPLOAD_NAME}.gif"
EXTERNAL_URL = "https://rupixel.ru/images/cat.png"
WHITELIST = ("w-25", "w-50", "w-75", "w-100", "float-start", "float-end", "rounded")


@epic("UNIT")
@feature("Markdown")
@severity(severity_level.BLOCKER)
@story("Блок :::img: рендер с whitelist-классами")
class TestImgRendering:
    """img-fluid всегда, классы — только из whitelist; /uploads — миниатюра со ссылкой (→ ARC-0044, ARC-0057)."""

    @title("Без классов — img с одним img-fluid")
    def test_no_classes(self):
        """Пустые классы легитимны: class="img-fluid" ровно."""
        html = render_markdown(f":::img[Кот]({EXTERNAL_URL})")
        assert_condition(
            condition=f'<img src="{EXTERNAL_URL}" alt="Кот" class="img-fluid">' in html,
            allure_step_name="img собран без лишних классов",
            error_text=f"Ожидался чистый img, получено: {html}",
        )

    @title("Все классы whitelist применяются")
    def test_whitelist_classes(self):
        """Каждый класс из whitelist попадает в class после img-fluid."""
        checks = []
        for css_class in WHITELIST:
            html = render_markdown(f":::img[Кот]({EXTERNAL_URL}, {css_class})")
            checks.append(
                assert_condition(
                    condition=f'class="img-fluid {css_class}"' in html,
                    allure_step_name=f"класс {css_class} применён",
                    error_text=f"Класс {css_class} потерян: {html}",
                    soft_assert=True,
                )
            )
        SoftAssert(*checks)

    @title("Комбинация классов сохраняет порядок токенов")
    def test_class_combination(self):
        """float-start и rounded вместе — img-fluid первым, токены пользователя следом."""
        html = render_markdown(f":::img[Кот]({EXTERNAL_URL}, float-start rounded)")
        assert_condition(
            condition='class="img-fluid float-start rounded"' in html,
            allure_step_name="комбинация классов на месте",
            error_text=f"Комбинация сломалась: {html}",
        )

    @title("Alt с кавычками экранируется")
    def test_alt_escaped(self):
        """Кавычки в alt не выживают как атрибут — escape(quote=True)."""
        html = render_markdown(f':::img[Кот "Барсик"]({EXTERNAL_URL})')
        assert_condition(
            condition="Кот &quot;Барсик&quot;" in html,
            allure_step_name="alt экранирован",
            error_text=f"Кавычки alt не экранированы: {html}",
        )

    @title("Пустой alt — легитимная декоративная картинка")
    def test_empty_alt(self):
        """Пустые скобки alt разрешены (решение 5): alt="" пустой."""
        html = render_markdown(f":::img[]({EXTERNAL_URL})")
        assert_condition(
            condition=f'<img src="{EXTERNAL_URL}" alt="" class="img-fluid">' in html,
            allure_step_name="пустой alt дал alt=&quot;&quot;",
            error_text=f"Пустой alt сломал img: {html}",
        )

    @title("Путь /uploads даёт миниатюру со ссылкой на детальную")
    def test_uploads_thumb_link(self):
        """Ссылка на оригинал с target=_blank, внутри img на thumbs (→ ARC-0044)."""
        html = render_markdown(f":::img[Кот]({UPLOAD_PNG})")
        SoftAssert(
            assert_condition(
                condition=f'href="{UPLOAD_PNG}"' in html and 'target="_blank"' in html,
                allure_step_name="ссылка на детальную версию на месте",
                error_text=f"Ссылка на детальную потерялась: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition=f'src="{UPLOAD_THUMB}"' in html,
                allure_step_name="в src миниатюра thumbs",
                error_text=f"Миниатюра потерялась: {html}",
                soft_assert=True,
            ),
        )

    @title("GIF — оригинал без ссылки на детальную")
    def test_gif_original_no_link(self):
        """GIF не пережимается и миниатюры не имеет: src оригинальный, <a> нет."""
        html = render_markdown(f":::img[Кот]({UPLOAD_GIF})")
        SoftAssert(
            assert_condition(
                condition=f'src="{UPLOAD_GIF}"' in html,
                allure_step_name="GIF проносится оригиналом",
                error_text=f"GIF получил миниатюру: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="<a " not in html,
                allure_step_name="обёртки-ссылки нет",
                error_text=f"GIF обёрнут в ссылку: {html}",
                soft_assert=True,
            ),
        )

    @title("Внешний URL — обычный img без переписывания")
    def test_external_plain(self):
        """Не-/uploads путь проходит как есть."""
        html = render_markdown(f":::img[Кот]({EXTERNAL_URL}, rounded)")
        assert_condition(
            condition=f'src="{EXTERNAL_URL}"' in html and "/uploads/" not in html,
            allure_step_name="внешний URL не переписан",
            error_text=f"Внешний URL переписан: {html}",
        )

    @title("Запятая в пути трактуется как разделитель — деградация усечённым путём")
    def test_comma_in_path(self):
        """Документированный лимит синтаксиса: путь усекается, класс «foo» невалиден."""
        html = render_markdown(":::img[Фото](https://x.com/a.jpg,foo)")
        SoftAssert(
            assert_condition(
                condition='src="https://x.com/a.jpg"' in html,
                allure_step_name="путь продеградировал усечённым",
                error_text=f"Путь не усечён или потерян: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="img-fluid" not in html,
                allure_step_name="классов плагина нет — это деградация",
                error_text=f"Деградация выдала класс плагина: {html}",
                soft_assert=True,
            ),
        )

    @title("Конструкция в середине строки — не блочный плагин")
    def test_midtext_not_plugin(self):
        """Плагин блочный: только строка с начала строки; текст остаётся видимым."""
        html = render_markdown(f"Смотри: :::img[Кот]({EXTERNAL_URL})")
        assert_condition(
            condition=":::img" in html and "<img" not in html,
            allure_step_name="конструкция в середине строки осталась текстом",
            error_text=f"Плагин сработал в середине строки: {html}",
        )


@epic("UNIT")
@feature("Markdown")
@severity(severity_level.CRITICAL)
@story("Блок :::img: деградация по неизвестному классу")
class TestImgDegradation:
    """Неизвестный токен — строка рендерится стандартной markdown-картинкой (→ ARC-0057).

    Канон «что написал, то и увидишь»: синтаксис не молчит, картинка не исчезает.
    """

    @title("Неизвестный класс — стандартная картинка без классов")
    def test_unknown_class_degrades(self):
        """Деградация через renderer.image: img без class, путь как есть."""
        html = render_markdown(f":::img[Кот]({EXTERNAL_URL}, foo)")
        assert_condition(
            condition="<img" in html and "class=" not in html,
            allure_step_name="неизвестный класс дал стандартную картинку",
            error_text=f"Деградация не сработала или потеряла картинку: {html}",
        )

    @title("Известный класс рядом с неизвестным — всё равно деградация")
    def test_known_plus_unknown_degrades(self):
        """Whitelist строгий: один плохой токен роняет всю строку."""
        html = render_markdown(f":::img[Кот]({EXTERNAL_URL}, w-50 foo)")
        assert_condition(
            condition="<img" in html and "class=" not in html,
            allure_step_name="смешанный набор дал деградацию",
            error_text=f"Смешанный набор прошёл как валидный: {html}",
        )

    @title("Деградация сохраняет переписывание миниатюр для /uploads")
    def test_degradation_preserves_uploads_rewrite(self):
        """renderer.image (_BootstrapRenderer) переписывает /uploads и в деградации."""
        html = render_markdown(f":::img[Кот]({UPLOAD_PNG}, foo)")
        SoftAssert(
            assert_condition(
                condition=f'src="{UPLOAD_THUMB}"' in html,
                allure_step_name="миниатюра на месте и в деградации",
                error_text=f"Переписывание миниатюр потерялось: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition=f'href="{UPLOAD_PNG}"' in html and 'target="_blank"' in html,
                allure_step_name="ссылка на детальную сохранена",
                error_text=f"Ссылка на детальную потерялась: {html}",
                soft_assert=True,
            ),
        )


@epic("UNIT")
@feature("Markdown")
@severity(severity_level.BLOCKER)
@story("Блок :::gallery: сетка миниатюр")
class TestGallery:
    """div.gallery-grid со ссылками на оригинал; классы строк игнорируются (→ ARC-0057).

    Регрессия раунда С: в разметке нет утилит Bootstrap (d-flex, w-50) —
    они с !important ломали grid (урок ARC-0057).
    """

    @title("Структура сетки: gallery-grid без утилит Bootstrap")
    def test_structure(self):
        """Сетка — кастомный класс, d-flex/w-50 в разметке нет."""
        html = render_markdown(f":::gallery\n:::img[Кот]({EXTERNAL_URL})\n:::end")
        SoftAssert(
            assert_condition(
                condition='<div class="gallery-grid">' in html,
                allure_step_name="контейнер gallery-grid на месте",
                error_text=f"Контейнер сетки не найден: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="d-flex" not in html and "w-50" not in html,
                allure_step_name="утилит Bootstrap в разметке нет (→ ARC-0057)",
                error_text=f"Утилиты Bootstrap просочились: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition='<a href="' in html and 'class="img-fluid rounded"' in html,
                allure_step_name="картинка обёрнута в ссылку со стандартными классами",
                error_text=f"Карточка сетки сломана: {html}",
                soft_assert=True,
            ),
        )

    @title("Строка /uploads — миниатюра со ссылкой на детальную")
    def test_uploads_thumb_link(self):
        """Href на оригинал, src на thumbs — как в :::img (→ ARC-0044)."""
        html = render_markdown(f":::gallery\n:::img[Кот]({UPLOAD_PNG})\n:::end")
        SoftAssert(
            assert_condition(
                condition=f'href="{UPLOAD_PNG}"' in html,
                allure_step_name="href ведёт на детальную версию",
                error_text=f"href на детальную потерялся: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition=f'src="{UPLOAD_THUMB}"' in html,
                allure_step_name="src ведёт на миниатюру",
                error_text=f"Миниатюра потерялась: {html}",
                soft_assert=True,
            ),
        )

    @title("Внешняя строка — href и src равны пути")
    def test_external_item(self):
        """Не-/uploads путь: href=src без переписывания."""
        html = render_markdown(f":::gallery\n:::img[Кот]({EXTERNAL_URL})\n:::end")
        assert_condition(
            condition=f'href="{EXTERNAL_URL}"' in html and f'src="{EXTERNAL_URL}"' in html,
            allure_step_name="внешний путь не переписан",
            error_text=f"Внешний путь переписан: {html}",
        )

    @title("GIF — оригинал без миниатюры")
    def test_gif_item_original(self):
        """GIF в сетке: href=src на оригинал, thumbs нет."""
        html = render_markdown(f":::gallery\n:::img[Кот]({UPLOAD_GIF})\n:::end")
        assert_condition(
            condition=f'src="{UPLOAD_GIF}"' in html and "thumbs" not in html,
            allure_step_name="GIF проносится оригиналом",
            error_text=f"GIF получил миниатюру: {html}",
        )

    @title("Классы строк игнорируются — у миниатюры стандартный набор")
    def test_line_classes_ignored(self):
        """Решение 1: классы строк не проходят в сетку; w-50 в разметке нет."""
        html = render_markdown(f":::gallery\n:::img[Кот]({EXTERNAL_URL}, w-50 rounded)\n:::end")
        SoftAssert(
            assert_condition(
                condition='class="img-fluid rounded"' in html,
                allure_step_name="стандартный набор классов на месте",
                error_text=f"Классы строки просочились: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="w-50" not in html,
                allure_step_name="пользовательские классы отброшены",
                error_text=f"w-50 из строки просочился: {html}",
                soft_assert=True,
            ),
        )

    @title("Пустые строки между элементами пропускаются")
    def test_empty_lines_skipped(self):
        """Пустые строки не роняют блок (→ ARC-0057)."""
        html = render_markdown(f":::gallery\n\n:::img[Кот]({EXTERNAL_URL})\n\n:::img[Пёс]({EXTERNAL_URL})\n\n:::end")
        assert_condition(
            condition="gallery-grid" in html and html.count("<img") == 2,
            allure_step_name="обе картинки на месте, блок жив",
            error_text=f"Пустые строки сломали блок: {html}",
        )

    @title("Пустой контейнер — пустая сетка")
    def test_empty_container(self):
        """:::gallery сразу с :::end — div без картинок (решение в чате раунда С)."""
        html = render_markdown(":::gallery\n:::end")
        assert_condition(
            condition='<div class="gallery-grid"></div>' in html,
            allure_step_name="пустой контейнер дал пустую сетку",
            error_text=f"Пустой контейнер продеградировал: {html}",
        )

    @title(":::end с хвостовыми пробелами закрывает, текст после — живёт")
    def test_end_with_trailing_spaces(self):
        """Пробелы после :::end не ломают закрытие; хвост — обычный абзац."""
        html = render_markdown(f":::gallery\n:::img[Кот]({EXTERNAL_URL})\n:::end   \nОбычный текст")
        SoftAssert(
            assert_condition(
                condition="gallery-grid" in html,
                allure_step_name="контейнер закрыт с пробелами",
                error_text=f"Пробелы после :::end сломали закрытие: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="Обычный текст" in html,
                allure_step_name="текст после контейнера живёт",
                error_text=f"Текст после :::end потерян: {html}",
                soft_assert=True,
            ),
        )


@epic("UNIT")
@feature("Markdown")
@severity(severity_level.CRITICAL)
@story("Блок :::gallery: деградация контейнера")
class TestGalleryDegradation:
    """«Мусор убивает весь блок»: pre с экранированным исходником (→ ARC-0057)."""

    @title("Мусорная строка роняет весь блок в pre")
    def test_garbage_line_broken(self):
        """Не-:::img строка внутри — pre с открывающей строкой и телом."""
        html = render_markdown(":::gallery\n:::img[Кот](https://x.com/a.png)\nхвост мусором\n:::end")
        SoftAssert(
            assert_condition(
                condition="<pre>" in html and "gallery-grid" not in html,
                allure_step_name="блок продеградировал в pre",
                error_text=f"Мусорная строка не уронила блок: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="хвост мусором" in html and ":::gallery" in html,
                allure_step_name="исходник виден пользователю",
                error_text=f"Исходник блока потерян: {html}",
                soft_assert=True,
            ),
        )

    @title("Незакрытый контейнер — pre со всем остатком поста")
    def test_unclosed_broken(self):
        """Хвост без :::end — токен broken со всем остатком (решение 2)."""
        html = render_markdown(f":::gallery\n:::img[Кот]({EXTERNAL_URL})\nтекст без закрытия")
        SoftAssert(
            assert_condition(
                condition="<pre>" in html,
                allure_step_name="открытый контейнер дал pre",
                error_text=f"Незакрытый блок не продеградировал: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="текст без закрытия" in html,
                allure_step_name="остаток поста виден текстом",
                error_text=f"Остаток поста потерян: {html}",
                soft_assert=True,
            ),
        )


@epic("UNIT")
@feature("Markdown")
@severity(severity_level.BLOCKER)
@story("Блок :::carousel: слайды и классы")
class TestCarousel:
    """Нативная Bootstrap-карусель без кнопок; оригиналы в слайдах (→ ARC-0057, п. 30)."""

    @title("Структура карусели: data-bs-ride, первый слайд active, кнопок нет")
    def test_structure(self):
        """Слайды нумеруются: только первый с active; стрелки не рендерятся."""
        html = render_markdown(f":::carousel\n:::img[Один]({EXTERNAL_URL})\n:::img[Два]({EXTERNAL_URL})\n:::end")
        SoftAssert(
            assert_condition(
                condition='<div class="carousel slide" data-bs-ride="carousel">' in html,
                allure_step_name="обёртка с автопрокруткой на месте",
                error_text=f"Обёртка карусели сломана: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="carousel-inner" in html and html.count("carousel-item") == 2,
                allure_step_name="два слайда в carousel-inner",
                error_text=f"Слайды не собраны: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition='class="carousel-item active"' in html,
                allure_step_name="первый слайд активен",
                error_text=f"Активный слайд не первый: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="button" not in html,
                allure_step_name="кнопок нет — сознательно (п. 30)",
                error_text=f"Кнопки просочились в разметку: {html}",
                soft_assert=True,
            ),
        )

    @title("Слайд /uploads — оригинал без миниатюры")
    def test_uploads_original(self):
        """Решение 1: карусель показывает оригинал, не thumbs."""
        html = render_markdown(f":::carousel\n:::img[Кот]({UPLOAD_PNG})\n:::end")
        SoftAssert(
            assert_condition(
                condition=f'src="{UPLOAD_PNG}"' in html,
                allure_step_name="в слайде оригинал",
                error_text=f"Оригинал потерялся: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="thumbs" not in html,
                allure_step_name="миниатюры в карусели нет",
                error_text=f"Миниатюра просочилась в слайд: {html}",
                soft_assert=True,
            ),
        )

    @title("GIF-слайд — оригинал без миниатюры")
    def test_gif_original(self):
        """GIF в карусели: оригинальный путь, thumbs нет."""
        html = render_markdown(f":::carousel\n:::img[Кот]({UPLOAD_GIF})\n:::end")
        assert_condition(
            condition=f'src="{UPLOAD_GIF}"' in html and "thumbs" not in html,
            allure_step_name="GIF проносится оригиналом",
            error_text=f"GIF получил миниатюру: {html}",
        )

    @title("Непустой alt даёт подпись слайда")
    def test_caption_present(self):
        """carousel-caption с экранированным alt (решение 5)."""
        html = render_markdown(f':::carousel\n:::img[Кот "Барсик"]({EXTERNAL_URL})\n:::end')
        SoftAssert(
            assert_condition(
                condition="carousel-caption" in html,
                allure_step_name="подпись слайда на месте",
                error_text=f"Подпись не появилась: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="Кот &quot;Барсик&quot;" in html,
                allure_step_name="alt в подписи экранирован",
                error_text=f"Кавычки alt не экранированы: {html}",
                soft_assert=True,
            ),
        )

    @title("Пустой alt — слайд без подписи")
    def test_caption_absent(self):
        """Пустой alt — carousel-caption не рендерится."""
        html = render_markdown(f":::carousel\n:::img[]({EXTERNAL_URL})\n:::end")
        assert_condition(
            condition="carousel-caption" not in html,
            allure_step_name="подписи при пустом alt нет",
            error_text=f"Пустая подпись прорвалась: {html}",
        )

    @title("Whitelist-класс входит в слайд чистым токеном")
    def test_valid_class_clean(self):
        """Фикс раунда: классы валидируются, а не «расплющиваются» посимвольно."""
        html = render_markdown(f":::carousel\n:::img[Кот]({EXTERNAL_URL}, w-50)\n:::end")
        assert_condition(
            condition='class="d-block w-100 img-fluid w-50"' in html,
            allure_step_name="класс собран чистым токеном",
            error_text=f"Класс слайда сломан: {html}",
        )

    @title("Без классов — базовый набор слайда")
    def test_no_classes(self):
        """d-block w-100 img-fluid без пользовательских токенов."""
        html = render_markdown(f":::carousel\n:::img[Кот]({EXTERNAL_URL})\n:::end")
        assert_condition(
            condition='class="d-block w-100 img-fluid"' in html,
            allure_step_name="базовый набор классов слайда",
            error_text=f"Базовый набор слайда сломан: {html}",
        )


@epic("UNIT")
@feature("Markdown")
@severity(severity_level.CRITICAL)
@story("Блок :::carousel: деградация контейнера")
class TestCarouselDegradation:
    """Тот же канон «мусор убивает весь блок», плюс ветка фикса классов."""

    @title("Мусорная строка роняет карусель в pre")
    def test_garbage_line_broken(self):
        """Не-:::img строка внутри — pre с исходником, карусели нет."""
        html = render_markdown(":::carousel\n:::img[Кот](https://x.com/a.png)\nмусор\n:::end")
        SoftAssert(
            assert_condition(
                condition="<pre>" in html and "carousel-inner" not in html,
                allure_step_name="карусель продеградировала в pre",
                error_text=f"Мусорная строка не уронила блок: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="мусор" in html,
                allure_step_name="исходник виден пользователю",
                error_text=f"Исходник потерян: {html}",
                soft_assert=True,
            ),
        )

    @title("Незакрытая карусель — pre со всем остатком")
    def test_unclosed_broken(self):
        """Хвост без :::end — broken со всем остатком поста."""
        html = render_markdown(f":::carousel\n:::img[Кот]({EXTERNAL_URL})\nхвост без закрытия")
        SoftAssert(
            assert_condition(
                condition="<pre>" in html,
                allure_step_name="открытый контейнер дал pre",
                error_text=f"Незакрытый блок не продеградировал: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="хвост без закрытия" in html,
                allure_step_name="остаток поста виден текстом",
                error_text=f"Остаток поста потерян: {html}",
                soft_assert=True,
            ),
        )

    @title("Неизвестный класс слайда — деградация всего блока (ветка фикса)")
    def test_unknown_class_broken(self):
        """Фикс карусели: whitelist применяется, плохой класс роняет блок в pre."""
        html = render_markdown(f":::carousel\n:::img[Кот]({EXTERNAL_URL}, foo)\n:::end")
        SoftAssert(
            assert_condition(
                condition="<pre>" in html and "carousel-inner" not in html,
                allure_step_name="неизвестный класс продеградировал в pre",
                error_text=f"Плохой класс не уронил блок: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="carousel-item" not in html and "d-block" not in html,
                allure_step_name="карусельной разметки не собралось",
                error_text=f"Мусор просочился в разметку: {html}",
                soft_assert=True,
            ),
        )

    @title("Валидный класс рядом с неизвестным — деградация всего блока")
    def test_valid_plus_unknown_broken(self):
        """Один плохой слайд роняет весь контейнер — частичной карусели нет."""
        html = render_markdown(
            f":::carousel\n:::img[Кот]({EXTERNAL_URL}, w-50)\n:::img[Пёс]({EXTERNAL_URL}, foo)\n:::end"
        )
        assert_condition(
            condition="<pre>" in html and "carousel-inner" not in html,
            allure_step_name="смешанный набор продеградировал целиком",
            error_text=f"Частичная карусель собралась: {html}",
        )


@epic("UNIT")
@feature("Markdown")
@story("Базовый уровень: комментарии не получают блоки раунда С")
class TestBlocksBasicLevel:
    """Кастомные плагины сознательно не наследуются базовым уровнем (→ ARC-0054).

    Нюанс :::img: `[alt](url)` — валидный inline-синтаксис, в комментарии он
    превращается в ссылку; ассерт — на отсутствие вывода плагина, не на вид скобок.
    """

    @title("В комментарии :::img остаётся текстом без img")
    def test_img_stays_text(self):
        """Плагин не подключён базовому рендеру; img вне _BASIC_TAGS."""
        html = render_markdown(":::img[alt](https://x.com/a.png)", basic=True)
        assert_condition(
            condition=":::img" in html and "<img" not in html,
            allure_step_name="синтаксис виден текстом, img нет",
            error_text=f":::img сработал в базовом уровне: {html}",
        )

    @title("В комментарии :::gallery остаётся текстом")
    def test_gallery_stays_text(self):
        """Контейнеры не регистрируются базовому рендеру."""
        html = render_markdown(":::gallery\n:::img[a](https://x.com/a.png)\n:::end", basic=True)
        assert_condition(
            condition=":::gallery" in html and "gallery-grid" not in html,
            allure_step_name="синтаксис виден текстом, сетки нет",
            error_text=f":::gallery сработал в базовом уровне: {html}",
        )

    @title("В комментарии :::carousel остаётся текстом")
    def test_carousel_stays_text(self):
        """Контейнеры не регистрируются базовому рендеру."""
        html = render_markdown(":::carousel\n:::img[a](https://x.com/a.png)\n:::end", basic=True)
        assert_condition(
            condition=":::carousel" in html and "carousel-inner" not in html,
            allure_step_name="синтаксис виден текстом, карусели нет",
            error_text=f":::carousel сработал в базовом уровне: {html}",
        )


@epic("UNIT")
@feature("Markdown")
@story("Регистрация плагинов раунда С")
class TestBlocksRegistration:
    """Гварды рендера в плагинах: недостижимая через интерфейсы ветка (→ ARC-0050)."""

    @title("img_plugin без рендера регистрирует только блок")
    def test_img_registration(self):
        """AST-сценарий mistune: блок регистрируется, рендер пропускается."""
        registered = []
        md = SimpleNamespace(
            block=SimpleNamespace(register=lambda *args, **kwargs: registered.append(args[0])),
            renderer=None,
        )
        img_plugin(md)
        assert_condition(
            condition=registered == ["img"],
            allure_step_name="блок img зарегистрирован и без рендера",
            error_text=f"Регистрация не состоялась: {registered}",
        )

    @title("gallery_plugin без рендера регистрирует только блок")
    def test_gallery_registration(self):
        """AST-сценарий mistune: broken регистрируется только с рендером."""
        registered = []
        md = SimpleNamespace(
            block=SimpleNamespace(register=lambda *args, **kwargs: registered.append(args[0])),
            renderer=None,
        )
        gallery_plugin(md)
        assert_condition(
            condition=registered == ["gallery"],
            allure_step_name="блок gallery зарегистрирован и без рендера",
            error_text=f"Регистрация не состоялась: {registered}",
        )

    @title("carousel_plugin без рендера регистрирует только блок")
    def test_carousel_registration(self):
        """AST-сценарий mistune: блок регистрируется, рендер пропускается."""
        registered = []
        md = SimpleNamespace(
            block=SimpleNamespace(register=lambda *args, **kwargs: registered.append(args[0])),
            renderer=None,
        )
        carousel_plugin(md)
        assert_condition(
            condition=registered == ["carousel"],
            allure_step_name="блок carousel зарегистрирован и без рендера",
            error_text=f"Регистрация не состоялась: {registered}",
        )
