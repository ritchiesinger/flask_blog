"""Рендер сырого Markdown из БД в безопасный HTML."""

import re
from collections.abc import Callable
from copy import deepcopy
from html import escape, unescape

import mistune
import nh3

from blog.services import uploads_service


class _BootstrapRenderer(mistune.HTMLRenderer):
    """Добавляет Bootstrap-классы элементам без дефолтных стилей."""

    def block_quote(self, text: str) -> str:
        return f'<blockquote class="blockquote">\n{text}</blockquote>\n'

    def image(self, text: str, url: str, title: str | None = None) -> str:
        """Переписывает ссылки на наши загрузки: миниатюра в посте, детальная по клику (→ ARC-0044).

        Ссылка /uploads/<имя> оборачивается: ссылка на детальную версию, внутри img
        на миниатюру thumbs/<имя> с классом img-fluid. GIF проносится без переписывания.
        text приходит уже экранированным (escape=True mistune): повторное экранирование
        сломало бы альт-текст; rel всем ссылкам проставляет nh3, финальная санитизация — nh3.

        Args:
            text: Alt-текст картинки (уже экранирован mistune).
            url: Ссылка из Markdown.
            title: Необязательный заголовок картинки.

        Returns:
            HTML картинки.
        """
        match = uploads_service.UPLOAD_RE.fullmatch(url)
        if match is None or url.endswith(".gif"):
            return super().image(text, url, title)
        name = match.group(1)
        title_attr = f' title="{escape(title, quote=True)}"' if title else ""
        return (
            f'<a href="/uploads/{name}" target="_blank">'
            f'<img src="/uploads/thumbs/{name}" alt="{text}"{title_attr} class="img-fluid"></a>'
        )


class _BasicRenderer(_BootstrapRenderer):
    """Рендер базового уровня (комментарии): whitelisted-подмножество (→ ARC-0054).

    Уровень задаётся списком тегов _BASIC_TAGS, а не разбором синтаксиса:
    движок рендерит как обычно, nh3 снимает теги вне набора — текст сохраняется.
    Исключение — картинки: img вне набора, а молча прятать нельзя — рендерится
    сам синтаксис («что написал, то и увидишь»); переписывание миниатюр из
    _BootstrapRenderer не применяется — это поверхность постов.
    """

    def image(self, text: str, url: str, title: str | None = None) -> str:
        """Показывает синтаксис картинки как текст: в комментариях ей не место.

        Args:
            text: Alt-текст картинки (уже экранирован mistune).
            url: Ссылка из Markdown.
            title: Необязательный заголовок картинки (теряется: вне базового набора).

        Returns:
            Экранированный текст синтаксиса картинки.
        """
        literal = f"![{unescape(text)}]({url})"
        return escape(literal)


# --- Плагин :::video (раунд В, п. 28; → ARC-0052) ---
# Block-плагин mistune 3.4.0 по образцу встроенного footnotes (эталон с диска):
# md.block.register(name, regex, parse, before=...), parse возвращает m.end(),
# рендер — md.renderer.register(type, func) только для HTML-рендера.
# Уровень — только расширенный: в комментариях :::video остаётся текстом абзаца.
# Регэкспы переживают конвейер чата: YouTube/VK — без обратных слешей (точка
# и знак вопроса в символьных классах), в _VIDEO_PATTERN — hex-коды
# (0x5B/0x5D — скобки, 0x0A — перенос, 0x09 — таб). Продолжение урока ARC-0049.
_VIDEO_PATTERN = r"^:::video\x5B(?P<video_url>[^\x5D\x0A]+)\x5D[ \x09]*(?:[\x0A]|$)"

# Извлечение embed: не сырой URL в iframe, а сборка из проверенных компонентов (решение шага 1 раунда В).
# YouTube: watch?v=, embed/, shorts/, live/, youtu.be — ID ровно 11 символов. VK: vk.com, vk.ru и vkvideo.ru,
# /video<oid>_<id> → video_ext.php. search, не fullmatch: хвосты (&list=, ?hash=) не мешают. Известное ограничение
# (шаг 4): свежим VK-ссылкам для встраивания нужен hash — если он есть в исходной ссылке, переносится в embed;
# hash ограничен [0-9A-Za-z_-].
_YOUTUBE_RE = re.compile(
    r"https?://(?:www[.])?youtu(?:[.]be/|be[.]com/(?:watch[?]v=|embed/|shorts/|live/))(?P<id>[0-9A-Za-z_-]{11})"
)
_VK_RE = re.compile(
    r"https?://(?:vk[.]com|vkvideo[.]ru|vk[.]ru)/"
    r"video(?P<oid>-?[0-9]+)_(?P<id>[0-9]+)(?:[?&]hash=(?P<hash>[0-9A-Za-z_-]+))?"
)
# VK embed-адрес из «Встроить»: пользователь может вставить и саму ссылку,
# и весь iframe-сниппет — search вытянет URL из середины сниппета. hd —
# разрешение из кода встраивания, опционально.
_VK_EMBED_RE = re.compile(
    r"https?://(?:vk[.]com|vkvideo[.]ru|vk[.]ru)/"
    r"video_ext[.]php[?]oid=(?P<oid>-?[0-9]+)&id=(?P<id>[0-9]+)(?:&hash=(?P<hash>[0-9A-Za-z_-]+))?(?:&hd=[0-9]+)?"
)
_VIDEO_IFRAME_ALLOW = (
    "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
)


def _embed_url(url: str) -> str | None:
    """Извлекает embed-адрес из ссылки на видео или возвращает None.

    Args:
        url: Ссылка на YouTube или VK из синтаксиса :::video.

    Returns:
        Готовый embed-адрес из проверенных компонентов; None — домен не распознан.
    """
    match = _YOUTUBE_RE.search(url)
    if match:
        return f"https://www.youtube.com/embed/{match.group('id')}"
    embed_match = _VK_EMBED_RE.search(url)
    if embed_match:
        # Embed-адрес от VK проносится как есть: он целиком прошёл whitelist-регэксп
        # (домен из списка, oid/id — числа, hash/hd — ограниченные наборы символов),
        # каждый символ учтён; пересборка ломает hash — он привязан к точному виду
        # адреса, который сгенерировал сам VK (глазная проверка шага 4).
        return embed_match.group(0)
    match = _VK_RE.search(url)
    if match:
        hash_param = match.group("hash")
        hash_suffix = f"&hash={hash_param}" if hash_param else ""
        return f"https://vk.com/video_ext.php?oid={match.group('oid')}&id={match.group('id')}{hash_suffix}"
    return None

    return None


def _parse_video(block, m: re.Match[str], state) -> int:
    """Разбор :::video[url]: токен типа video с сырым URL.

    Args:
        block: Блочный парсер mistune.
        m: Совпадение регэкспа _VIDEO_PATTERN.
        state: Состояние блочного разбора.

    Returns:
        Конец совпадения (m.end()) — канон mistune для block-плагинов.
    """
    state.append_token({"type": "video", "raw": m.group("video_url")})
    return m.end()


def _render_video(renderer, text: str) -> str:
    """Рендерит токен video: iframe embed или деградация в ссылку.

    Неизвестный домен — обычная ссылка (философия «что написал, то и увидишь»).
    src iframe собирается только из проверенных компонентов (ID по регэкспам),
    сырой URL в iframe не попадает никогда; экранирование — escape(quote=True).

    Args:
        renderer: Активный рендер mistune (не используется — HTML собирается здесь).
        text: Сырой URL из токена.

    Returns:
        HTML блока видео или ссылку.
    """
    embed = _embed_url(text)
    if embed is None:
        safe = escape(text, quote=True)
        return f'<p><a href="{safe}">{safe}</a></p>'
    return (
        '<div class="video-embed">'
        f'<iframe src="{escape(embed, quote=True)}" title="Видео" loading="lazy" '
        f'allow="{_VIDEO_IFRAME_ALLOW}" allowfullscreen></iframe></div>'
    )


def _video_plugin(md: mistune.Markdown) -> None:
    """Регистрирует block-плагин :::video в расширенном рендере (→ ARC-0052).

    Args:
        md: Объект рендера mistune (контракт плагина: единственный аргумент).
    """
    md.block.register("video", _VIDEO_PATTERN, _parse_video, before="paragraph")
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("video", _render_video)


# Реестр кастомных плагинов расширенного уровня (→ ARC-0054): каждая кастомная
# конструкция — один плагин. Расширение — запись в карту; рельс подключён в
# _build_renderer(). Первый плагин — video (раунд В). Базовый уровень кастомные
# плагины сознательно не наследует: комментарии — только встроенный набор.
_PLUGINS: dict[str, Callable[[mistune.Markdown], None]] = {"video": _video_plugin}


def _build_renderer() -> mistune.Markdown:
    """Собирает расширенный рендер и подключает реестр кастомных плагинов.

    Отдельная функция: подключение плагинов изолировано и накрыто юнит-тестом
    рельса (→ ARC-0050).

    Returns:
        Готовый расширенный рендер.
    """
    renderer = mistune.create_markdown(escape=True, renderer=_BootstrapRenderer())
    for plugin in _PLUGINS.values():
        renderer.use(plugin)
    return renderer


_renderer = _build_renderer()

_basic_renderer = mistune.create_markdown(escape=True, renderer=_BasicRenderer(), plugins=["strikethrough"])

# Базовый уровень: только одобренный набор (→ ARC-0054). Атрибуты — только то,
# что реально выдаёт рендер: href у ссылок (target не нужен — нет переписывания),
# class у цитаты (Bootstrap-стиль).
_BASIC_TAGS = frozenset({"a", "blockquote", "br", "code", "del", "em", "li", "ol", "p", "pre", "strong", "ul"})
_BASIC_ATTRIBUTES: dict[str, set[str]] = {"a": {"href"}, "blockquote": {"class"}}


def render_markdown(source: str, *, basic: bool = False) -> str:
    """Рендерит сырой Markdown в безопасный HTML.

    Единственная точка конвертации Markdown: расширенный уровень — посты
    (умолчание), базовый — комментарии (→ ARC-0054). Порядок обязателен:
    сначала рендер, потом санитизация. Расширенный уровень: карта атрибутов
    строится явно из дефолтной; rel не в карте: nh3 проставляет его сам
    (link_rel по умолчанию) — наличие rel в карте при link_rel запрещено.
    Теги div/iframe добавлены под плагин :::video (→ ARC-0052): путь к iframe
    один — src собирается плагином из проверенных компонентов.

    :param source: сырой Markdown (строка из БД).
    :param basic: базовый уровень (комментарии); расширенный — по умолчанию.
    :return: HTML для вывода в шаблоне (вставляется с фильтром |safe).
    """
    if not source:
        return ""
    if basic:
        return nh3.clean(_basic_renderer(source), tags=_BASIC_TAGS, attributes=_BASIC_ATTRIBUTES)
    tags = set(nh3.ALLOWED_TAGS) | {"div", "iframe"}
    attributes = deepcopy(nh3.ALLOWED_ATTRIBUTES)
    attributes["blockquote"] = {"class"}
    attributes["a"] = {"href", "target"}
    attributes["img"] = {"src", "alt", "class"}
    attributes["div"] = {"class"}
    attributes["iframe"] = {"src", "title", "loading", "allow", "allowfullscreen"}
    return nh3.clean(_renderer(source), tags=tags, attributes=attributes)


def render_markdown_basic(source: str) -> str:
    """Рендерит сырой Markdown базового уровня (комментарии).

    Обёртка над render_markdown(basic=True) и точка регистрации Jinja-фильтра
    «markdown_basic»: в шаблонах два явных фильтра — уровень виден в шаблоне.

    :param source: сырой Markdown (строка из БД).
    :return: HTML для вывода в шаблоне (вставляется с фильтром |safe).
    """
    return render_markdown(source, basic=True)
