"""Block-плагин :::video (раунд В, п. 28; → ARC-0052, RuTube → ARC-0056)."""

import re
from html import escape as html_escape

import mistune

# Block-плагин mistune 3.4.0 по образцу встроенного footnotes (эталон с диска):
# md.block.register(name, regex, parse, before=...), parse возвращает m.end(),
# рендер — md.renderer.register(type, func) только для HTML-рендера.
# Уровень — только расширенный: в комментариях :::video остаётся текстом абзаца.
# Регэкспы переживают конвейер чата: YouTube/VK/RuTube — без обратных слешей
# (точка и знак вопроса в символьных классах), в _VIDEO_PATTERN — hex-коды
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
# RuTube (→ ARC-0056): embed из «Код вставки плеера» — rutube.ru/play/embed/<32 hex>,
# у приватных роликов «по ссылке» в адресе живёт ключ ?p=KEY (без него плеер не
# отвечает) — embed-адрес проносится вербатимом, как VK-сниппет.
_RUTUBE_EMBED_RE = re.compile(
    r"https?://rutube[.]ru/play/embed/(?P<id>[0-9A-Fa-f]{32})(?:/[?&]p=(?P<key>[0-9A-Za-z_-]+))?"
)
# Публичная страница rutube.ru/video/<32 hex>/ и приватная /video/private/<32 hex>/?p=KEY:
# пересобираются в play/embed/<id> с переносом ключа — hash у RuTube нет, пересборка
# безопасна (в отличие от VK, у которого hash привязан к точному виду адреса).
_RUTUBE_PAGE_RE = re.compile(
    r"https?://rutube[.]ru/video(?:/private)?/(?P<id>[0-9A-Fa-f]{32})/?"
    r"(?:[?&]p=(?P<key>[0-9A-Za-z_-]+))?"
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
        url: Ссылка на YouTube, VK или RuTube из синтаксиса :::video.

    Returns:
        Готовый embed-адрес из проверенных компонентов; None — домен не распознан.
    """
    match = _YOUTUBE_RE.search(url)
    if match:
        return f"https://www.youtube.com/embed/{match.group('id')}"
    rutube_embed = _RUTUBE_EMBED_RE.search(url)
    if rutube_embed:
        # Embed-адрес RuTube проносится как есть: он целиком прошёл whitelist-регэксп,
        # у приватных роликов в нём живёт ключ ?p=KEY — пересборка может его потерять
        # (→ ARC-0056).
        return rutube_embed.group(0)
    rutube_page = _RUTUBE_PAGE_RE.search(url)
    if rutube_page:
        key = rutube_page.group("key")
        key_suffix = f"/?p={key}" if key else ""
        return f"https://rutube.ru/play/embed/{rutube_page.group('id')}{key_suffix}"
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

        safe = html_escape(text, quote=True)
        return f'<p><a href="{safe}">{safe}</a></p>'
    return (
        '<div class="video-embed">'
        f'<iframe src="{html_escape(embed, quote=True)}" title="Видео" loading="lazy" '
        f'allow="{_VIDEO_IFRAME_ALLOW}" allowfullscreen></iframe></div>'
    )


def video_plugin(md: mistune.Markdown) -> None:
    """Регистрирует block-плагин :::video в расширенном рендере (→ ARC-0052).

    Имя без подчёркивания: модуль плагина публичный, реестр собирается
    в __init__.py пакета (→ раскладка пакета, раунд С).

    Args:
        md: Объект рендера mistune (контракт плагина: единственный аргумент).
    """
    md.block.register("video", _VIDEO_PATTERN, _parse_video, before="paragraph")
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("video", _render_video)
