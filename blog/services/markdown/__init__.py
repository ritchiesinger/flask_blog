"""Рендер сырого Markdown из БД в безопасный HTML (пакет, раскладка раунда С).

До раунда С это был монолит markdown.py; плагины разнесены по модулям:
core — рендеры двух уровней и nh3-карты, video — плагин раунда В,
blocks — плагины раунда С (img/gallery/carousel/broken). Внешние контракты
сохранены: render_markdown и render_markdown_basic доступны как
blog.services.markdown.render_markdown(.basic) — Jinja-фильтры в фабрике
и существующие тесты работают без изменений.
"""

from copy import deepcopy

import nh3

from .blocks import carousel_plugin, gallery_plugin, img_plugin
from .core import _BASIC_ATTRIBUTES, _BASIC_TAGS, build_basic_renderer, build_extended_renderer
from .video import video_plugin

# Реестр кастомных плагинов расширенного уровня (→ ARC-0054): каждая кастомная
# конструкция — один плагин, реестр собирается из модулей пакета. Рельс
# подключается в build_extended_renderer (→ ARC-0050). Базовый уровень
# кастомные плагины сознательно не наследует: комментарии — только встроенный
# набор (→ ARC-0054).
_PLUGINS: tuple = (video_plugin, img_plugin, gallery_plugin, carousel_plugin)

_extended_renderer = build_extended_renderer(_PLUGINS)
_basic_renderer = build_basic_renderer()


def render_markdown(source: str, *, basic: bool = False) -> str:
    """Рендерит сырой Markdown в безопасный HTML.

    Единственная точка конвертации Markdown: расширенный уровень — посты
    (умолчание), базовый — комментарии (→ ARC-0054). Порядок обязателен:
    сначала рендер, потом санитизация. Расширенный уровень: карта атрибутов
    строится явно из дефолтной; rel не в карте: nh3 проставляет его сам
    (link_rel по умолчанию) — наличие rel в карте при link_rel запрещено.
    Теги div/iframe — под плагин :::video (→ ARC-0052) и контейнеры раунда С:
    div снимает nh3 с любой разметки плагинов, путь к iframe один — src
    собирается плагином из проверенных компонентов. data-bs-ride добавлен под
    :::carousel: переключение слайдов Bootstrap-скриптом; кнопок-стрелок нет —
    они бы потребовали button и data-bs-target в карту.

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
    attributes["div"] = {"class", "data-bs-ride"}
    attributes["iframe"] = {"src", "title", "loading", "allow", "allowfullscreen"}
    return nh3.clean(_extended_renderer(source), tags=tags, attributes=attributes)


def render_markdown_basic(source: str) -> str:
    """Рендерит сырой Markdown базового уровня (комментарии).

    Обёртка над render_markdown(basic=True) и точка регистрации Jinja-фильтра
    «markdown_basic»: в шаблонах два явных фильтра — уровень виден в шаблоне.

    :param source: сырой Markdown (строка из БД).
    :return: HTML для вывода в шаблоне (вставляется с фильтром |safe).
    """
    return render_markdown(source, basic=True)
