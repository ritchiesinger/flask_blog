"""Рендер сырого Markdown из БД в безопасный HTML."""

from copy import deepcopy

import mistune
import nh3


class _BootstrapRenderer(mistune.HTMLRenderer):
    """Добавляет Bootstrap-классы элементам без дефолтных стилей."""

    def block_quote(self, text: str) -> str:
        return f'<blockquote class="blockquote">\n{text}</blockquote>\n'


_renderer = mistune.create_markdown(escape=True, renderer=_BootstrapRenderer())


def render_markdown(source: str) -> str:
    """Рендерит сырой Markdown в безопасный HTML.

    Единственная точка конвертации тела поста (решения арки 2 — в ядре
    проекта). Порядок обязателен: сначала рендер, потом санитизация —
    nh3 чистит и то, что mistune мог пропустить в атрибутах.

    :param source: сырой Markdown тела поста (строка из БД).
    :return: HTML для вывода в шаблоне (вставляется с фильтром |safe).
    """
    if not source:
        return ""
    attributes = deepcopy(nh3.ALLOWED_ATTRIBUTES)
    attributes["blockquote"] = {"class"}
    return nh3.clean(_renderer(source), attributes=attributes)
