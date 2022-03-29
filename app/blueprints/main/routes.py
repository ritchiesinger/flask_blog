"""Марщруты основного (корневого) приложения."""

from . import bp as main_bp


@main_bp.route('/')
def index():
    """Маршрут тестового запроса."""
    return "Hello, Flask Application!"
