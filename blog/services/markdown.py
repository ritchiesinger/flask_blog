"""Рендер сырого Markdown из БД в безопасный HTML."""

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

        Ссылка вида /uploads/<имя> (сгенерированные имена: 32 hex + расширение)
        оборачивается: ссылка на детальную версию, внутри img на миниатюру
        thumbs/<имя> с классом img-fluid. GIF проносится без переписывания
        (анимация и миниатюры по дизайну не живут). Чужие URL — без изменений.
        text приходит уже экранированным (escape=True mistune): повторное
        экранирование сломало бы альт-текст; rel всем ссылкам проставляет
        nh3 (link_rel по умолчанию), финальная санитизация — nh3.

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
    движок рендерит как обычно, nh3 снимает теги вне набора (заголовки,
    таблицы, списки задач) — текст сохраняется, разметка исчезает.
    Исключение — картинки: img в базовом наборе отсутствует, а молча
    прятать их нельзя, поэтому рендерится сам синтаксис («что написал,
    то и увидишь»); переписывание миниатюр из _BootstrapRenderer не
    применяется — это поверхность постов.
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


# Реестр кастомных плагинов расширенного уровня (→ ARC-0054): каждая кастомная
# конструкция — один плагин (один план mistune, один тест на санитизацию, одна
# карточка шпаргалки). Расширение — запись в карту; рельс подключён: плагин
# применяется к рендеру при сборке. Базовый уровень кастомные плагины
# сознательно не наследует: комментарии — только встроенный набор.
_PLUGINS: dict[str, Callable[[mistune.Markdown], None]] = {}


def _build_renderer() -> mistune.Markdown:
    """Собирает расширенный рендер и подключает реестр кастомных плагинов.

    Отдельная функция вместо инлайн-цикла: пока реестр пуст, цикл не
    выполняется ни разу — юнит-тест рельса строит рендер с подменённым
    реестром и проверяет подключение плагина (→ ARC-0050).

    Returns:
        Готовый расширенный рендер.
    """
    renderer = mistune.create_markdown(escape=True, renderer=_BootstrapRenderer())
    for plugin in _PLUGINS.values():
        renderer.use(plugin)
    return renderer


_renderer = _build_renderer()

_basic_renderer = mistune.create_markdown(escape=True, renderer=_BasicRenderer(), plugins=["strikethrough"])

# Базовый уровень: только одобренный набор (→ ARC-0054). Заголовки/таблицы/
# списки задач nh3 снимает с сохранением текста. Атрибуты — только то, что
# реально выдаёт рендер: href у ссылок (target не нужен — нет переписывания),
# class у цитаты (Bootstrap-стиль).
_BASIC_TAGS = frozenset({"a", "blockquote", "br", "code", "del", "em", "li", "ol", "p", "pre", "strong", "ul"})
_BASIC_ATTRIBUTES: dict[str, set[str]] = {"a": {"href"}, "blockquote": {"class"}}


def render_markdown(source: str, *, basic: bool = False) -> str:
    """Рендерит сырой Markdown в безопасный HTML.

    Единственная точка конвертации Markdown: расширенный уровень — посты
    (умолчание), базовый — комментарии (→ ARC-0054). Порядок обязателен:
    сначала рендер, потом санитизация — nh3 чистит и то, что mistune мог
    пропустить в атрибутах. Расширенный уровень: карта атрибутов строится
    явно из дефолтной (классы blockquote и img-fluid, target у ссылок);
    rel не в карте: nh3 проставляет его сам (link_rel по умолчанию) —
    наличие rel в карте при link_rel запрещено. Базовый уровень: отдельные
    список тегов _BASIC_TAGS и карта атрибутов _BASIC_ATTRIBUTES.

    :param source: сырой Markdown (строка из БД).
    :param basic: базовый уровень (комментарии); расширенный — по умолчанию.
    :return: HTML для вывода в шаблоне (вставляется с фильтром |safe).
    """
    if not source:
        return ""
    if basic:
        return nh3.clean(_basic_renderer(source), tags=_BASIC_TAGS, attributes=_BASIC_ATTRIBUTES)
    attributes = deepcopy(nh3.ALLOWED_ATTRIBUTES)
    attributes["blockquote"] = {"class"}
    attributes["a"] = {"href", "target"}
    attributes["img"] = {"src", "alt", "class"}
    return nh3.clean(_renderer(source), attributes=attributes)


def render_markdown_basic(source: str) -> str:
    """Рендерит сырой Markdown базового уровня (комментарии).

    Обёртка над render_markdown(basic=True) и точка регистрации Jinja-фильтра
    «markdown_basic»: в шаблонах два явных фильтра, а не один с аргументом —
    уровень виден в шаблоне и не может быть потерян при правке.

    :param source: сырой Markdown (строка из БД).
    :return: HTML для вывода в шаблоне (вставляется с фильтром |safe).
    """
    return render_markdown(source, basic=True)
