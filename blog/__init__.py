"""Фабрика приложения: конфигурация, расширения, роуты и CLI-команды."""

import click
from flask import Flask, render_template

# Модуль с колбэками загрузки пользователя: декораторы регистрируют их на login_manager и jwt при импорте.
import blog.loaders  # noqa: F401 (импорт ради регистрации)
from blog.extensions import db, jwt, login_manager, migrate
from blog.services.markdown import render_markdown


def create_app(test_config: dict | None = None) -> Flask:
    """Создаёт и настраивает экземпляр приложения Flask.

    Инициализирует расширения, регистрирует обработчик ошибок 500,
    блюпринты web- и API-роутов и CLI-команды. Колбэки загрузки
    пользователя (Flask-Login и flask-jwt-extended) регистрируются
    при импорте blog.loaders.

    Args:
        test_config: Словарь с конфигурацией для тестов; если задан,
            применяется поверх базовой конфигурации из blog.config.Config.

    Returns:
        Готовое к запуску приложение.
    """
    app = Flask(__name__)
    app.config.from_object("blog.config.Config")
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)  # включает команду flask db
    login_manager.init_app(app)
    app.jinja_env.filters["markdown"] = render_markdown
    jwt.init_app(app)

    @app.errorhandler(500)
    def internal_error(e: Exception) -> tuple[str, int]:
        """Обрабатывает необработанные исключения сервера.

        Логирует исключение с трейсбеком и отдаёт страницу 500.

        Args:
            e: Перехваченное исключение.

        Returns:
            (Страница ошибки errors/500.html, 500).
        """
        app.logger.exception(e)
        return render_template("errors/500.html"), 500

    @app.errorhandler(404)
    def not_found(error: Exception) -> tuple[str, int]:
        """Отдаёт фирменную страницу 404.

        Ловит и несуществующие URL (роутинг), и NotFoundError от роутов
        (спрятанная админ-поверхность): после abort(404) в web_errors
        обе ветки рендерятся одинаково.

        Args:
            error: Перехваченная ошибка роутинга или NotFoundError.

        Returns:
            (Страница ошибки errors/404.html, 404).
        """
        return render_template("errors/404.html"), 404

    from blog.api.admin import bp as api_admin_bp
    from blog.api.auth import bp as api_auth_bp
    from blog.api.comments import bp as api_comments_bp
    from blog.api.posts import bp as api_posts_bp
    from blog.web.admin import bp as web_admin_bp
    from blog.web.auth import bp as web_auth_bp
    from blog.web.blog import bp as web_blog_bp
    from blog.web.uploads import bp as web_upload_bp

    app.register_blueprint(api_auth_bp)
    app.register_blueprint(api_posts_bp)
    app.register_blueprint(api_comments_bp)
    app.register_blueprint(api_admin_bp)
    app.register_blueprint(web_admin_bp)
    app.register_blueprint(web_auth_bp)
    app.register_blueprint(web_blog_bp)
    app.register_blueprint(web_upload_bp)

    @app.cli.command("init-db")
    def init_db() -> None:
        """Инициализирует базу данных: создаёт все таблицы."""
        db.create_all()
        click.echo("База инициализирована.")

    from blog.cli import clean_uploads, create_admin, make_admin

    app.cli.add_command(create_admin)  # noqa Особенность Click - декораторы click намеренно типизированы так.
    app.cli.add_command(make_admin)  # noqa Особенность Click - декораторы click намеренно типизированы так.
    app.cli.add_command(clean_uploads)  # noqa Особенность Click - декораторы click намеренно типизированы так.

    return app
