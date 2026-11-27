"""Плагины раунда С: :::img, :::gallery, :::carousel (→ ARC-0057)."""

import re
from collections.abc import Callable
from html import escape

import mistune

from blog.services import uploads_service

# Все три конструкции — block-плагины по образцу video (эталон footnotes):
# md.block.register(name, regex, parse, before="paragraph"), parse возвращает m.end().
# Регэкспы переживают конвейер чата: hex-коды вместо сырых спецсимволов
# (0x5B/0x5D — скобки, 0x0A — перенос, 0x09 — таб). Продолжение урока ARC-0049.
# Alt: пустые скобки легитимны (декоративная картинка, решение 5). Классы — через
# запятую после пути, разделитель токенов — пробел.
_IMG_PATTERN = (
    r"^:::img\x5B(?P<alt>[^\x5D\x0A]*)\x5D"
    r"\x28(?P<path>[^\x29\x0A]+?)(?:,\s*(?P<classes>[^\x29\x0A]+))?\x29[ \x09]*(?:[\x0A]|$)"
)
_IMG_RE = re.compile(_IMG_PATTERN)

# Контейнер: от открывающей строки до :::end или конца файла. Содержимое — сырой
# текст блока, разбор построчный в рендере (мини-парсер решения 3): регэксп не
# пытается валидировать строки внутри — это работа рендера с правилом деградации
# «мусор убивает весь блок» (решение 3). Конец контейнера привязан к
# предшествующему переносу строки: ^ без MULTILINE матчится только в начале
# строки-данных, а :::end внутри тела — в середине. Токен-паттерн «:::endless»
# не закрывает: после :::end требуется перенос/EOL.
_GALLERY_PATTERN = (
    r"^:::gallery[ \x09]*[\x0A]"
    r"(?P<body_gallery>(?:[\x0A]|.)*?)"
    r"(?:\Z|:::end[ \x09]*(?:[\x0A]|$))"
)
_CAROUSEL_PATTERN = _GALLERY_PATTERN.replace("gallery", "carousel")

# Whitelist классов (решение 2): img-fluid всегда, далее — whitelist. Любой
# неизвестный токен → деградация строки в стандартную markdown-картинку.
_SIZE_CLASSES = {"w-25", "w-50", "w-75", "w-100"}
_FLOAT_CLASSES = {"float-start", "float-end"}
_ALLOWED_CLASSES = _SIZE_CLASSES | _FLOAT_CLASSES | {"rounded"}

# --- Разбор ---

def _parse_img(block, m: re.Match[str], state) -> int:
    """Разбор :::img[alt](path, classes): токен img, поля упакованы разделителем.

    Args:
        block: Блочный парсер mistune.
        m: Совпадение регэкспа _IMG_PATTERN.
        state: Состояние блочного разбора.

    Returns:
        Конец совпадения (m.end()) — канон mistune для block-плагинов.
    """
    state.append_token({
        "type": "img",
        "raw": "\x1F".join((m.group("alt"), m.group("path"), m.group("classes") or "")),
    })
    return m.end()


def _make_container_parser(kind: str) -> Callable[[object, re.Match[str], object], int]:
    r"""Фабрика парсеров контейнеров: gallery и carousel различаются только типом токена.

    Закрытость определяется по хвосту совпадения: regex потребил :::end —
    токен контейнера; дошло до \\Z — открытый контейнер, токен broken со всем
    остатком поста (решение 2: хвост без :::end — весь остаток текстом).
    Хвост срезается и от хвостовых пробелов/табов: регэксп разрешает их после
    :::end — закрытый блок с «:::end   » обязан классифицироваться как закрытый
    (урок прогона п. 29).

    Args:
        kind: Имя конструкции (gallery или carousel).

    Returns:
        Функция разбора для md.block.register.
    """
    def parse(block, m: re.Match[str], state) -> int:
        if m.group(0).rstrip(" \x09\n").endswith(":::end"):
            state.append_token({"type": kind, "raw": m.group(f"body_{kind}")})
        else:
            state.append_token({"type": "broken", "raw": m.group(0)})
        return m.end()
    return parse


# --- Рендер ---

def _validate_classes(raw: str | None) -> list[str] | None:
    """Валидирует классы по whitelist (решение 2).

    Args:
        raw: Строка классов из синтаксиса (может быть пустой).

    Returns:
        Список разрешённых токенов; None — есть неизвестный токен (деградация).
    """
    if not raw:
        return []
    tokens = raw.split()
    if all(token in _ALLOWED_CLASSES for token in tokens):
        return tokens
    return None


def _parse_lines(raw: str) -> list[tuple[str, str, str | None]] | None:
    """Разбирает тело контейнера построчно на :::img.

    Пустые строки пропускаются. Мусор внутри — None: «мусор убивает весь
    блок» (решение 3), деградация всего контейнера.

    Args:
        raw: Тело контейнера из токена.

    Returns:
        Список (alt, path, classes) или None при мусорной строке.
    """
    parsed: list[tuple[str, str, str | None]] = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        match = _IMG_RE.match(line)
        if match is None:
            return None
        parsed.append((match.group("alt"), match.group("path"), match.group("classes")))
    return parsed


def _broken_html(raw: str) -> str:
    """Экранирует сырой текст деградировавшего блока (решение 3).

    <pre>, а не абзац: переносы строк внутри блока сохраняются. Осознанное
    уточнение решения 3 — блок многострочный.

    Args:
        raw: Сырой текст блока (без экранирования).

    Returns:
        HTML с экранированным текстом.
    """
    return f"<pre>{escape(raw, quote=True)}</pre>\n"


def _render_broken(renderer, text: str) -> str:
    """Рендерит токен broken (открытый контейнер): экранированный остаток поста.

    Args:
        renderer: Активный рендер mistune (не используется).
        text: Сырой остаток поста от открывающей строки.

    Returns:
        HTML с экранированным текстом.
    """
    return _broken_html(text)


def _render_img(renderer, text: str) -> str:
    r"""Рендерит :::img: img с whitelist-классами или деградация в markdown-картинку.

    Деградация (решение 2): неизвестный класс — строка рендерится стандартной
    markdown-картинкой через renderer.image (переписывание миниатюр для
    /uploads сохраняется). img-fluid всегда (решение 2). Для /uploads/<имя> —
    миниатюра со ссылкой на детальную (→ ARC-0044), GIF — оригинал без ссылки.
    Лимит синтаксиса: запятая внутри пути трактуется как разделитель классов —
    валидация не пройдёт, путь продеградирует усечённым.

    Args:
        renderer: Активный рендер mistune (для деградации).
        text: Поля токена через \\x1F (alt, path, classes).

    Returns:
        HTML картинки.
    """
    alt, path, raw_classes = text.split("\x1F")
    classes = _validate_classes(raw_classes)
    if classes is None:
        return renderer.image(escape(alt, quote=True), path)
    class_str = "img-fluid" + (" " + " ".join(classes) if classes else "")
    match = uploads_service.UPLOAD_RE.fullmatch(path)
    if match is None or path.endswith(".gif"):
        return f'<img src="{escape(path, quote=True)}" alt="{escape(alt, quote=True)}" class="{class_str}">'
    name = match.group(1)
    return (
        f'<a href="/uploads/{escape(name, quote=True)}" target="_blank">'
        f'<img src="/uploads/thumbs/{escape(name, quote=True)}" alt="{escape(alt, quote=True)}" class="{class_str}">'
        f'</a>'
    )


def _render_gallery(renderer, raw: str) -> str:
    """Рендерит :::gallery: сетка миниатюр со ссылкой на оригинал.

    Классы строк игнорируются — миниатюра со стандартной сеткой классов
    (решение 1: рендер обрабатывает строки сам). GIF — оригинал без ссылки.
    Пустой контейнер — пустая сетка (решение принято в чате).

    Args:
        renderer: Активный рендер mistune (не используется).
        raw: Тело контейнера из токена.

    Returns:
        HTML сетки или экранированный блок при мусорной строке.
    """
    parsed = _parse_lines(raw)
    if parsed is None:
        return _broken_html(f":::gallery\n{raw}")
    items: list[str] = []
    for alt, path, _classes in parsed:
        match = uploads_service.UPLOAD_RE.fullmatch(path)
        if match is not None and not path.endswith(".gif"):
            name = match.group(1)
            href = f"/uploads/{escape(name, quote=True)}"
            src = f"/uploads/thumbs/{escape(name, quote=True)}"
        else:
            href = src = escape(path, quote=True)
        items.append(
            f'<a href="{href}"><img src="{src}" alt="{escape(alt, quote=True)}" '
            'class="img-fluid rounded"></a>'
        )
    return '<div class="gallery-grid">' + "".join(items) + "</div>"


def _render_carousel(renderer, raw: str) -> str:
    """Рендерит :::carousel: Bootstrap-карусель, оригиналы в слайдах (решение 1).

    Непустой alt — подпись слайда (решение 5), пустой — слайд без подписи.
    Классы слайда: d-block w-100 img-fluid всегда + whitelist-токены пользователя;
    неизвестный токен — деградация всего блока (канон «мусор убивает весь блок»,
    тот же whitelist, что у :::img). Стрелки и индикаторы не рендерятся: они
    потребовали бы расширения nh3-карты (button, data-bs-атрибуты) — вопрос
    вынесен пользователю. Для слайдов /uploads/<имя> — оригинал (не миниатюра),
    GIF — оригинал.

    Args:
        renderer: Активный рендер mistune (не используется).
        raw: Тело контейнера из токена.

    Returns:
        HTML карусели или экранированный блок при мусорной строке/классе.
    """
    parsed = _parse_lines(raw)
    if parsed is None:
        return _broken_html(f":::carousel\n{raw}")
    items: list[str] = []
    for index, (alt, path, classes) in enumerate(parsed):
        validated = _validate_classes(classes)
        if validated is None:
            return _broken_html(f":::carousel\n{raw}")
        active = " active" if index == 0 else ""
        tokens = "d-block w-100 img-fluid" + (" " + " ".join(validated) if validated else "")
        match = uploads_service.UPLOAD_RE.fullmatch(path)
        if match is not None and not path.endswith(".gif"):
            src = f"/uploads/{match.group(1)}"
        else:
            src = path
        caption = f'<div class="carousel-caption"><p>{escape(alt, quote=True)}</p></div>' if alt else ""
        items.append(
            f'<div class="carousel-item{active}">'
            f'<img src="{escape(src, quote=True)}" alt="{escape(alt, quote=True)}" class="{tokens}">'
            f"{caption}</div>"
        )
    return (
        '<div class="carousel slide" data-bs-ride="carousel">'
        '<div class="carousel-inner">' + "".join(items) + "</div></div>"
    )


# --- Регистрация ---

def img_plugin(md: mistune.Markdown) -> None:
    """Регистрирует block-плагин :::img в расширенном рендере.

    Args:
        md: Объект рендера mistune (контракт плагина: единственный аргумент).
    """
    md.block.register("img", _IMG_PATTERN, _parse_img, before="paragraph")
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("img", _render_img)


def gallery_plugin(md: mistune.Markdown) -> None:
    """Регистрирует block-плагин :::gallery и токен broken.

    broken регистрируется здесь: токен broken возникает из обоих
    контейнерных парсеров, а плагины подключаются парой через __init__.py.

    Args:
        md: Объект рендера mistune (контракт плагина: единственный аргумент).
    """
    md.block.register("gallery", _GALLERY_PATTERN, _make_container_parser("gallery"), before="paragraph")
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("gallery", _render_gallery)
        md.renderer.register("broken", _render_broken)


def carousel_plugin(md: mistune.Markdown) -> None:
    """Регистрирует block-плагин :::carousel в расширенном рендере.

    Args:
        md: Объект рендера mistune (контракт плагина: единственный аргумент).
    """
    md.block.register("carousel", _CAROUSEL_PATTERN, _make_container_parser("carousel"), before="paragraph")
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("carousel", _render_carousel)
