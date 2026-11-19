"""Общие хелперы постраничной навигации для WEB- и API-слоёв."""

from flask import request

from blog.constants import MAX_PER_PAGE


def page_from_args(key: str = "page") -> int:
    """Номер страницы из query-параметра; мусор и значения меньше 1 → страница 1.

    Args:
        key: Имя query-параметра; по умолчанию — page.

    Returns:
        Номер страницы, начиная с 1.
    """
    try:
        page = int(request.args.get(key, ""))
    except ValueError:
        return 1
    return page if page >= 1 else 1


def tab_from_args(allowed: tuple[str, ...], default: str, name: str = "tab") -> str:
    """Возвращает параметр вкладки из query-строки с санитизацией.

    Args:
        allowed: Допустимые значения вкладки.
        default: Значение при отсутствии, мусоре или пустой строке.
        name: Имя query-параметра; по умолчанию "tab".

    Returns:
        Корректное значение вкладки.
    """
    value = request.args.get(name, "").strip()
    return value if value in allowed else default


def per_page_from_args(default: int) -> int:
    """Размер страницы из query-параметра.

    Мусор и значения меньше 1 → переданный default,
    значения больше MAX_PER_PAGE → срезаются до лимита.

    Args:
        default: Размер страницы по умолчанию для конкретной сущности.

    Returns:
        Санитизированный размер страницы.
    """
    try:
        per_page = int(request.args.get("per_page", ""))
    except ValueError:
        return default
    if per_page < 1:
        return default
    return min(per_page, MAX_PER_PAGE)
