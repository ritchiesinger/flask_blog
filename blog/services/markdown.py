"""Рендер сырого Markdown из БД в безопасный HTML."""

from copy import deepcopy
from html import escape

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


_renderer = mistune.create_markdown(escape=True, renderer=_BootstrapRenderer())


def render_markdown(source: str) -> str:
    """Рендерит сырой Markdown в безопасный HTML.

    Единственная точка конвертации тела поста (решения арки 2 — в ядре
    проекта). Порядок обязателен: сначала рендер, потом санитизация —
    nh3 чистит и то, что mistune мог пропустить в атрибутах. Карта
    атрибутов строится явно: классы blockquote и img-fluid, target у
    ссылок на детальные версии. rel не в карте: nh3 проставляет его сам
    (link_rel по умолчанию) — наличие rel в карте при link_rel запрещено.

    :param source: сырой Markdown тела поста (строка из БД).
    :return: HTML для вывода в шаблоне (вставляется с фильтром |safe).
    """
    if not source:
        return ""
    attributes = deepcopy(nh3.ALLOWED_ATTRIBUTES)
    attributes["blockquote"] = {"class"}
    attributes["a"] = {"href", "target"}
    attributes["img"] = {"src", "alt", "class"}
    return nh3.clean(_renderer(source), attributes=attributes)
