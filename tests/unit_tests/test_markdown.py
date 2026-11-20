"""Юнит-тесты рендера Markdown: конвертация и санитизация."""
from uuid import uuid4

from glamor import epic, feature, severity, severity_level, step, story, title

from blog.services.markdown import render_markdown
from tests.tools.asserters.base_asserters import assert_condition
from tests.tools.asserters.soft_asserters import SoftAssert


@epic("UNIT")
@feature("Markdown")
@story("Рендер базовой разметки")
@severity(severity_level.BLOCKER)
class TestRenderMarkdownConverts:
    """Базовый синтаксис Markdown обязан доживать до HTML."""

    @title("Пустая строка даёт пустой выход")
    def test_empty_source_renders_empty(self):
        """Пустая строка даёт пустой выход: без артефактных обёрток."""
        with step("Рендеринг пустой строки"):
            assert_condition(
                render_markdown("") == "",
                allure_step_name="Рендер пустой строки возвращает пустую строку",
                error_text="Рендер пустой строки не возвращает пустую строку!",
            )

    @title("Успешный рендер **strong** и *em*")
    def test_paragraph_with_emphasis(self):
        """Акценты — самый частый синтаксис постов."""
        with (step("Рендеринг жирного текста и курсива")):
            html = render_markdown("Текст с **жирным** и *курсивом*.")
            SoftAssert(
                assert_condition(
                    "<strong>жирным</strong>" in html,
                    allure_step_name="Рендер жирного текста в HTML возвращает <strong>",
                    error_text="<strong> не найден в HTML!",
                    soft_assert=True,
                ),
                assert_condition(
                    "<em>курсивом</em>" in html,
                    allure_step_name="Рендер курсива в HTML возвращает <em>",
                    error_text="<em> не найден в HTML!",
                    soft_assert=True,
                )
            )

    @title("Успешный рендер заголовков (heading)")
    def test_headings(self):
        """Заголовки уровней 1-3 попадают в h1-h3."""
        with step("Рендеринг заголовков трёх уровней"):
            html = render_markdown("# Раз\n\n## Два\n\n### Три")
            SoftAssert(
                assert_condition(
                    "<h1>Раз</h1>" in html,
                    allure_step_name="Рендер заголовка первого уровня в HTML возвращает <h1>",
                    error_text="<h1> не найден в HTML!",
                    soft_assert=True,
                ),
                assert_condition(
                    "<h2>Два</h2>" in html,
                    allure_step_name="Рендер заголовка первого уровня в HTML возвращает <h2>",
                    error_text="<h2> не найден в HTML!",
                    soft_assert=True,
                ),
                assert_condition(
                    "<h3>Три</h3>" in html,
                    allure_step_name="Рендер заголовка первого уровня в HTML возвращает <h3>",
                    error_text="<h3> не найден в HTML!",
                    soft_assert=True,
                ),
            )

    @title("Успешный рендер неотсортированного списка")
    def test_unordered_list(self):
        """Списки — вторая по частоте структура."""
        html = render_markdown("- один\n- два\n- три")
        assert "<ul>" in html
        assert "<li>два</li>" in html

    @title("Успешный рендер блока кода")
    def test_code_block(self):
        """Блок кода сохраняется как pre+code — основа техпостов."""
        html = render_markdown("```\ncode\n```")
        assert "<pre>" in html
        assert "<code>" in html
        assert "code" in html

    @title("Успешный рендер блока цитирования")
    def test_blockquote(self):
        """Цитата оборачивается в blockquote."""
        html = render_markdown("> Цитата")
        assert '<blockquote class="blockquote">' in html
        assert "Цитата" in html

    @title("Успешный рендер ссылки")
    def test_link(self):
        """Ссылка сохраняет и URL, и текст-якорь."""
        html = render_markdown("[сайт](https://example.com)")
        assert 'href="https://example.com"' in html
        assert "сайт" in html

    @title("Картинка из markdown рендерится в img с src")
    def test_image_renders_as_img(self):
        """![alt](/uploads/x.png) превращается в <img> с сохранённым src.

        Закрепляет поведение цепочки mistune + nh3: картинка из нашего
        же хранилища обязана дожить до HTML — будущие обновления nh3
        не должны застать нас врасплох.
        """
        html = render_markdown("![кот](/uploads/abc.png)")
        assert_condition(
            condition='<img src="/uploads/abc.png"' in html,
            allure_step_name="Картинка рендерится в img с исходным src",
            error_text=f"Картинка не дожила до HTML: {html}",
        )


@epic("UNIT")
@feature("Markdown")
@story("Безопасность")
@severity(severity_level.CRITICAL)
class TestRenderMarkdownSecurity:
    """Сырой HTML и опасные конструкции не выживают в выходе."""

    @title("Экранирование script без потери содержимого")
    def test_script_tag_is_neutralized_not_deleted(self):
        """Script экранируется, но содержимое не молча теряется."""
        html = render_markdown("До <script>alert(1)</script> После")
        assert "<script" not in html.lower()
        assert "alert(1)" in html
        assert "После" in html

    @title("Сырой HTML показывается как текст")
    def test_raw_html_shown_as_text(self):
        """Позиция «только Markdown»: чужой HTML виден как текст."""
        html = render_markdown("<b>не тег</b>")
        assert "<b>" not in html
        assert "не тег" in html

    @title("Безопасная обработка обхода экранирования script через синтаксис ссылок")
    def test_javascript_url_stripped(self):
        """javascript: — обход через валидный синтаксис ссылок."""
        html = render_markdown("[клик](javascript:alert(1))")
        assert "javascript:" not in html


@epic("Сервисы")
@feature("Изображения")
@story("Рендер картинок")
class TestRenderImageRewrite:
    """Переписывание ссылок на наши загрузки (→ ARC-0044)."""

    @title("Ссылка на нашу загрузку становится миниатюрой внутри ссылки на детальную версию")
    def test_our_image_rewritten_to_thumb(self):
        """<a href="детальная" target=_blank><img src="миниатюра" class=img-fluid></a>."""
        name = f"{uuid4().hex}.png"
        html = render_markdown(f"![кот](/uploads/{name})")
        assert_condition(
            condition=f'href="/uploads/{name}"' in html,
            allure_step_name="Ссылка ведёт на детальную версию",
            error_text=f"Нет ссылки на детальную версию: {html}",
        )
        assert_condition(
            condition=f'src="/uploads/thumbs/{name}"' in html,
            allure_step_name="Внутри ссылки — миниатюра",
            error_text=f"Миниатюра не подставлена: {html}",
        )
        assert_condition(
            condition='class="img-fluid"' in html,
            allure_step_name="Класс img-fluid пережил санитизацию",
            error_text=f"Класс потерян: {html}",
        )

    @title("Ссылка с заголовком сохраняет title")
    def test_our_image_with_title(self):
        """Заголовок картинки переносится в переписанный HTML."""
        name = f"{uuid4().hex}.png"
        html = render_markdown(f'![кот](/uploads/{name} "Заголовок")')
        assert_condition(
            condition='title="Заголовок"' in html,
            allure_step_name="title сохранён в переписанной картинке",
            error_text=f"title потерян: {html}",
        )

    @title("GIF не переписывается — ни миниатюры, ни обёртки")
    def test_gif_passes_through(self):
        """GIF-ссылка рендерится обычным img на детальный путь."""
        name = f"{uuid4().hex}.gif"
        html = render_markdown(f"![кот](/uploads/{name})")
        assert_condition(
            condition=f'src="/uploads/{name}"' in html,
            allure_step_name="GIF отдаётся как есть",
            error_text=f"Неожиданный HTML: {html}",
        )
        assert_condition(
            condition="/uploads/thumbs/" not in html,
            allure_step_name="Миниатюра для GIF не подставлялась",
            error_text=f"Неожиданная миниатюра: {html}",
        )

    @title("Внешняя картинка рендерится как раньше")
    def test_external_image_untouched(self):
        """Чужой URL не попадает под паттерн: обычный img без обёртки."""
        html = render_markdown("![кот](https://example.com/x.png)")
        assert_condition(
            condition='src="https://example.com/x.png"' in html,
            allure_step_name="Внешняя картинка не изменилась",
            error_text=f"Неожиданный HTML: {html}",
        )
        assert_condition(
            condition="/uploads/thumbs/" not in html,
            allure_step_name="Переписывание не задело внешний URL",
            error_text=f"Неожиданная миниатюра: {html}",
        )
