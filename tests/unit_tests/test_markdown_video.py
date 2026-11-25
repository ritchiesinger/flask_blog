"""Юнит-тесты плагина :::video: сборка embed, деградация, безопасность (→ ARC-0052; RuTube → ARC-0056)."""
from types import SimpleNamespace

from glamor import epic, feature, severity, severity_level, story, title

from blog.services.markdown import _video_plugin, render_markdown
from tests.tools.asserters.base_asserters import assert_condition
from tests.tools.asserters.soft_asserters import SoftAssert

YOUTUBE_ID = "dQw4w9WgXcQ"
YOUTUBE_WATCH = f"https://www.youtube.com/watch?v={YOUTUBE_ID}"
RUTUBE_ID = "a1b2c3d4e5f60718293a4b5c6d7e8f90"
RUTUBE_EMBED = f"https://rutube.ru/play/embed/{RUTUBE_ID}"
RUTUBE_EMBED_PRIVATE = f"{RUTUBE_EMBED}/?p=secretKey123"
RUTUBE_PAGE = f"https://rutube.ru/video/{RUTUBE_ID}/"
RUTUBE_PAGE_PRIVATE = f"https://rutube.ru/video/private/{RUTUBE_ID}/?p=secretKey123"


@epic("UNIT")
@feature("Markdown")
@severity(severity_level.BLOCKER)
@story("Плагин :::video: сборка embed из проверенных компонентов")
class TestVideoEmbed:
    """Валидные ссылки YouTube, VK и RuTube дают iframe с embed-адресом (→ ARC-0052, ARC-0056).

    nh3 экранирует & внутри значений атрибутов (&amp;) — ассерты src
    сверяются по этому виду, браузер расшифрует его обратно в &.
    """

    @title("YouTube watch-ссылка даёт iframe в обёртке")
    def test_youtube_watch(self):
        """Src собирается из ID, обёртка 16:9 и lazy-загрузка на месте."""
        html = render_markdown(f":::video[{YOUTUBE_WATCH}]")
        SoftAssert(
            assert_condition(
                condition=f'<iframe src="https://www.youtube.com/embed/{YOUTUBE_ID}"' in html,
                allure_step_name="src iframe собран из ID YouTube",
                error_text=f"Ожидался embed из ID, получено: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition='<div class="video-embed">' in html,
                allure_step_name="iframe обёрнут в video-embed",
                error_text=f"Обёртка video-embed не найдена: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition='loading="lazy"' in html and "allowfullscreen" in html,
                allure_step_name="lazy-загрузка и fullscreen на месте",
                error_text=f"Атрибуты iframe потеряны: {html}",
                soft_assert=True,
            ),
        )

    @title("YouTube shorts-ссылка даёт тот же embed")
    def test_youtube_shorts(self):
        """shorts/ и live/ — те же ID, что и watch."""
        html = render_markdown(f":::video[https://www.youtube.com/shorts/{YOUTUBE_ID}]")
        assert_condition(
            condition=f"https://www.youtube.com/embed/{YOUTUBE_ID}" in html,
            allure_step_name="shorts-ссылка дала embed",
            error_text=f"shorts не распознан: {html}",
        )

    @title("Короткая ссылка youtu.be даёт embed")
    def test_youtu_be(self):
        """youtu.be/<id> — валидная форма без параметров."""
        html = render_markdown(f":::video[https://youtu.be/{YOUTUBE_ID}]")
        assert_condition(
            condition=f"https://www.youtube.com/embed/{YOUTUBE_ID}" in html,
            allure_step_name="youtu.be дал embed",
            error_text=f"youtu.be не распознан: {html}",
        )

    @title("VK-ссылка с отрицательным oid даёт video_ext")
    def test_vk_negative_oid(self):
        """Отрицательный oid (сообщества) — рабочий случай VK; & приходит как &amp;."""
        html = render_markdown(":::video[https://vk.com/video-22822305_456239017]")
        assert_condition(
            condition="https://vk.com/video_ext.php?oid=-22822305&amp;id=456239017" in html,
            allure_step_name="oid и id перенесены в video_ext.php",
            error_text=f"VK-ссылка не собралась: {html}",
        )

    @title("Домен vkvideo.ru распознаётся как VK")
    def test_vkvideo_domain(self):
        """Свежий домен VK-видео — тот же плагин; & приходит как &amp;."""
        html = render_markdown(":::video[https://vkvideo.ru/video-1_2]")
        assert_condition(
            condition="https://vk.com/video_ext.php?oid=-1&amp;id=2" in html,
            allure_step_name="vkvideo.ru дал video_ext.php",
            error_text=f"vkvideo.ru не распознан: {html}",
        )

    @title("Домен vk.ru распознаётся как VK")
    def test_vk_ru_domain(self):
        """vk.ru — второй официальный домен VK (нашла глазная проверка шага 4)."""
        html = render_markdown(":::video[https://vk.ru/video-211479572_456239058]")
        assert_condition(
            condition="https://vk.com/video_ext.php?oid=-211479572&amp;id=456239058" in html,
            allure_step_name="vk.ru дал video_ext.php",
            error_text=f"vk.ru не распознан: {html}",
        )

    @title("VK-ссылка с hash переносит hash в embed")
    def test_vk_hash_carried(self):
        """Свежим VK-ссылкам для встраивания нужен hash — переносим из исходной."""
        html = render_markdown(":::video[https://vk.ru/video-211479572_456239058?hash=abc123def]")
        assert_condition(
            condition="https://vk.com/video_ext.php?oid=-211479572&amp;id=456239058&amp;hash=abc123def" in html,
            allure_step_name="hash перенесён в video_ext.php",
            error_text=f"hash потерялся: {html}",
        )

    @title("VK embed-адрес из «Встроить» распознаётся вместе с hash")
    def test_vk_embed_url_with_hash(self):
        """Форма video_ext.php?oid=..&id=..&hash=.. — официальный embed VK."""
        html = render_markdown(":::video[https://vk.com/video_ext.php?oid=-211479572&id=456239058&hash=abc123def]")
        assert_condition(
            condition="https://vk.com/video_ext.php?oid=-211479572&amp;id=456239058&amp;hash=abc123def" in html,
            allure_step_name="embed-адрес распознан, hash на месте",
            error_text=f"embed-адрес не собрался: {html}",
        )

    @title("Весь iframe-сниппет из «Встроить» разбирается search-матчем")
    def test_vk_full_embed_snippet(self):
        """Код встраивания можно вставить как есть — URL вынимается из сниппета."""
        snippet = (
            '<iframe src="https://vk.com/video_ext.php?oid=-211479572&id=456239058&hash=abc123def" '
            'width="853" height="480" allowfullscreen></iframe>'
        )
        html = render_markdown(f":::video[{snippet}]")
        SoftAssert(
            assert_condition(
                condition="https://vk.com/video_ext.php?oid=-211479572&amp;id=456239058&amp;hash=abc123def" in html,
                allure_step_name="URL вынут из сниппета, hash перенесён",
                error_text=f"Сниппет не разобрался: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition='width="853"' not in html,
                allure_step_name="чужие атрибуты сниппета не просочились",
                error_text=f"Атрибуты сниппета просочились: {html}",
                soft_assert=True,
            ),
        )

    @title("VK embed-адрес проносится как есть: домен и hd сохраняются")
    def test_vk_embed_url_verbatim(self):
        """Адрес из «Встроить» не пересобирается: hash привязан к точному виду."""
        html = render_markdown(
            ":::video[https://vk.ru/video_ext.php?oid=-211479572&id=456239058&hash=dd54ce9ef01a5320&hd=4]"
        )
        assert_condition(
            condition=(
                    "https://vk.ru/video_ext.php?oid=-211479572&amp;id=456239058&amp;hash=dd54ce9ef01a5320&amp;hd=4"
                    in html
            ),
            allure_step_name="embed-адрес проношу без пересборки",
            error_text=f"Адрес был пересобран или искажён: {html}",
        )

    @title("VK-ссылка без hash собирается без hash")
    def test_vk_without_hash(self):
        """Хвост с hash не обязателен: embed собирается и без него."""
        html = render_markdown(":::video[https://vk.ru/video-211479572_456239058]")
        assert_condition(
            condition='oid=-211479572&amp;id=456239058"' in html,
            allure_step_name="embed без hash, src закрывается кавычкой",
            error_text=f"Лишний hash или сломанный src: {html}",
        )

    @title("Хвосты ссылок не попадают в src")
    def test_tail_params_ignored(self):
        """search-матч берёт ID, плейлист и hash обрезаются."""
        html = render_markdown(f":::video[{YOUTUBE_WATCH}&list=PL123]")
        assert_condition(
            condition=f'src="https://www.youtube.com/embed/{YOUTUBE_ID}"' in html
            and "list=PL123" not in html,
            allure_step_name="src точен, хвост ссылки отброшен",
            error_text=f"Хвост ссылки просочился в iframe: {html}",
        )

    @title("RuTube embed-адрес проносится в iframe как есть")
    def test_rutube_embed_verbatim(self):
        """Адрес из «Код вставки плеера» не пересобирается (→ ARC-0056)."""
        html = render_markdown(f":::video[{RUTUBE_EMBED}]")
        assert_condition(
            condition=f'src="{RUTUBE_EMBED}"' in html,
            allure_step_name="embed-адрес RuTube в src без изменений",
            error_text=f"Адрес был пересобран или искажён: {html}",
        )

    @title("RuTube embed с ключом приватности проносится как есть")
    def test_rutube_embed_private_verbatim(self):
        """Ключ ?p= приватного ролика «по ссылке» обязан доехать до плеера."""
        html = render_markdown(f":::video[{RUTUBE_EMBED_PRIVATE}]")
        assert_condition(
            condition=f'src="{RUTUBE_EMBED_PRIVATE}"' in html,
            allure_step_name="embed с ключом p в src без изменений",
            error_text=f"Ключ приватности потерялся: {html}",
        )

    @title("Публичная страница RuTube пересобирается в embed")
    def test_rutube_page_rebuilt(self):
        """Ссылка «Поделиться» /video/<id>/ пересобирается в play/embed — hash нет, безопасно."""
        html = render_markdown(f":::video[{RUTUBE_PAGE}]")
        assert_condition(
            condition=f'src="{RUTUBE_EMBED}"' in html,
            allure_step_name="страница пересобрана в play/embed",
            error_text=f"Страница не пересобралась: {html}",
        )

    @title("Приватная страница RuTube пересобирается вместе с ключом")
    def test_rutube_private_page_rebuilt(self):
        """Ключ ?p=KEY из приватной ссылки переносится в embed-адрес."""
        html = render_markdown(f":::video[{RUTUBE_PAGE_PRIVATE}]")
        assert_condition(
            condition=f'src="{RUTUBE_EMBED_PRIVATE}"' in html,
            allure_step_name="страница пересобрана, ключ p перенесён",
            error_text=f"Ключ приватности потерялся: {html}",
        )

    @title("iframe-сниппет RuTube разбирается, чужие атрибуты не просачиваются")
    def test_rutube_embed_snippet(self):
        """Код вставки плеера можно вставить как есть — URL вынимается из сниппета."""
        snippet = (
            f'<iframe width="720" height="405" src="{RUTUBE_EMBED}" '
            'frameBorder="0" allow="autoplay; fullscreen;" allowfullscreen></iframe>'
        )
        html = render_markdown(f":::video[{snippet}]")
        SoftAssert(
            assert_condition(
                condition=f'src="{RUTUBE_EMBED}"' in html,
                allure_step_name="URL вынут из сниппета RuTube",
                error_text=f"Сниппет не разобрался: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition='width="720"' not in html,
                allure_step_name="чужие атрибуты сниппета не просочились",
                error_text=f"Атрибуты сниппета просочились: {html}",
                soft_assert=True,
            ),
        )


@epic("UNIT")
@feature("Markdown")
@story("Плагин :::video: деградация в ссылку")
class TestVideoDegradation:
    """Нераспознанное не исчезает — остаётся видимым (→ ARC-0052).

    nh3 добавляет всем ссылкам rel="noopener noreferrer" — ассерты это учитывают.
    """

    @title("Неизвестный домен становится обычной ссылкой")
    def test_unknown_domain_becomes_link(self):
        """Философия «что написал, то и увидишь» — без iframe."""
        html = render_markdown(":::video[https://example.com/film]")
        SoftAssert(
            assert_condition(
                condition='href="https://example.com/film" rel="noopener noreferrer">' in html,
                allure_step_name="неизвестный домен дал ссылку",
                error_text=f"Ожидалась ссылка, получено: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition="iframe" not in html,
                allure_step_name="iframe для неизвестного домена нет",
                error_text=f"iframe просочился: {html}",
                soft_assert=True,
            ),
        )

    @title("YouTube ID короче 11 символов деградирует")
    def test_short_id_becomes_link(self):
        """Неполный ID не проходит whitelist длины."""
        html = render_markdown(":::video[https://www.youtube.com/watch?v=abcdefghij]")
        assert_condition(
            condition="iframe" not in html and "abcdefghij" in html,
            allure_step_name="короткий ID дал ссылку вместо iframe",
            error_text=f"Неполный ID собрал iframe: {html}",
        )

    @title("RuTube ID не из 32 hex-символов деградирует")
    def test_rutube_short_id_becomes_link(self):
        """Неполный ID (31 hex) не проходит whitelist длины (→ ARC-0056)."""
        short = RUTUBE_ID[:-1]
        html = render_markdown(f":::video[https://rutube.ru/video/{short}/]")
        assert_condition(
            condition="iframe" not in html and short in html,
            allure_step_name="короткий ID RuTube дал ссылку вместо iframe",
            error_text=f"Неполный ID собрал iframe: {html}",
        )

    @title("Синтаксис в середине строки остаётся текстом")
    def test_midtext_stays_plain(self):
        """Плагин — блочный: только строка с начала строки."""
        html = render_markdown(f"Смотри это: :::video[{YOUTUBE_WATCH}]")
        assert_condition(
            condition="iframe" not in html and ":::video[" in html,
            allure_step_name="конструкция в середине строки видна текстом",
            error_text=f"Блочный плагин сработал в середине строки: {html}",
        )

    @title("Текст после скобок ломает конструкцию — остаётся текстом")
    def test_suffix_text_stays_paragraph(self):
        """Конструкция обязана занимать строку целиком."""
        html = render_markdown(f":::video[{YOUTUBE_WATCH}] смотрите до конца")
        assert_condition(
            condition="iframe" not in html and ":::video" in html,
            allure_step_name="конструкция с хвостом осталась текстом",
            error_text=f"iframe собрался из кривой строки: {html}",
        )


@epic("UNIT")
@feature("Markdown")
@story("Базовый уровень: комментарии не получают видео")
class TestVideoBasicLevel:
    """Расширенные плагины сознательно не наследуются базовым уровнем."""

    @title("В комментарии :::video остаётся экранированным текстом")
    def test_basic_stays_text(self):
        """Плагин подключён только расширенному рендеру."""
        html = render_markdown(f":::video[{YOUTUBE_WATCH}]", basic=True)
        SoftAssert(
            assert_condition(
                condition="iframe" not in html and "video-embed" not in html,
                allure_step_name="iframe в комментарии не появился",
                error_text=f"Видео просочилось в базовый уровень: {html}",
                soft_assert=True,
            ),
            assert_condition(
                condition=":::video[" in html,
                allure_step_name="синтаксис виден пользователю как текст",
                error_text=f"Синтаксис исчез: {html}",
                soft_assert=True,
            ),
        )


@epic("UNIT")
@feature("Markdown")
@severity(severity_level.CRITICAL)
@story("Плагин :::video: безопасность")
class TestVideoSecurity:
    """Сырой URL не попадает в iframe — src только из проверенных компонентов.

    Урок прогона: nh3 снимает href целиком, если URL невалиден (кавычки,
    пробелы) — инъекция не выживает как атрибут, а остаётся видимым текстом.
    """

    @title("Инъекция через невалидный URL: href снят nh3 целиком")
    def test_unknown_url_escaped(self):
        """Кавычки делают URL невалидным: nh3 снимает href, текст остаётся видимым."""
        html = render_markdown(':::video[https://evil.com" onmouseover="x()]')
        assert_condition(
            condition="href" not in html and 'onmouseover="x()' in html,
            allure_step_name="href снят, инъекция осталась текстом ссылки",
            error_text=f"Инъекция выжила как атрибут: {html}",
        )

    @title("Инъекция в видео-URL отбрасывается сборкой embed")
    def test_injection_in_video_url_dropped(self):
        """Мусор после валидного ID не доезжает до src."""
        html = render_markdown(f':::video[{YOUTUBE_WATCH}" onerror="x()]')
        assert_condition(
            condition=f'src="https://www.youtube.com/embed/{YOUTUBE_ID}"' in html
            and "onerror" not in html,
            allure_step_name="в src только ID, инъекция отброшена",
            error_text=f"Инъекция доехала до iframe: {html}",
        )


@epic("UNIT")
@feature("Markdown")
@story("Регистрация плагина")
class TestVideoPluginRegistration:
    """Гвард рендера в плагине: недостижимая через интерфейсы ветка (→ ARC-0050)."""

    @title("Рендер-меньший Markdown не роняет плагин")
    def test_renderer_less_markdown_does_not_crash(self):
        """AST-сценарий mistune без рендера: блок регистрируется, рендер пропускается."""
        registered = []
        md = SimpleNamespace(
            block=SimpleNamespace(register=lambda *args, **kwargs: registered.append(args[0])),
            renderer=None,
        )
        _video_plugin(md)
        assert_condition(
            condition=registered == ["video"],
            allure_step_name="блок зарегистрирован и без рендера",
            error_text=f"Регистрация не состоялась: {registered}",
        )
