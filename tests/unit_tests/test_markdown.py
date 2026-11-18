"""Юнит-тесты рендера Markdown: конвертация и санитизация."""

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
