"""Ядро рендера: рендеры двух уровней и карты санитизации nh3 (→ ARC-0054)."""

from html import escape, unescape

import mistune

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


# Базовый уровень: только одобренный набор (→ ARC-0054). Атрибуты — только то,
# что реально выдаёт рендер: href у ссылок (target не нужен — нет переписывания),
# class у цитаты (Bootstrap-стиль).
_BASIC_TAGS = frozenset({"a", "blockquote", "br", "code", "del", "em", "li", "ol", "p", "pre", "strong", "ul"})
_BASIC_ATTRIBUTES: dict[str, set[str]] = {"a": {"href"}, "blockquote": {"class"}}


def build_extended_renderer(plugins) -> mistune.Markdown:
    """Собирает расширенный рендер и подключает реестр кастомных плагинов.

    Плагины передаются снаружи: реестр собирается в __init__.py пакета
    из модулей-плагинов (→ раскладка пакета, раунд С). Изолированная
    сборка накрыта юнит-тестом рельса (→ ARC-0050).

    Args:
        plugins: Итерируемое количество плагинов (объекты вида plugin(md)).

    Returns:
        Готовый расширенный рендер.
    """
    renderer = mistune.create_markdown(escape=True, renderer=_BootstrapRenderer())
    for plugin in plugins:
        renderer.use(plugin)
    return renderer


def build_basic_renderer() -> mistune.Markdown:
    """Собирает базовый рендер (комментарии).

    Кастомные плагины сознательно не подключаются: комментарии — только
    встроенный набор (→ ARC-0054).

    Returns:
        Готовый базовый рендер.
    """
    return mistune.create_markdown(escape=True, renderer=_BasicRenderer(), plugins=["strikethrough"])
