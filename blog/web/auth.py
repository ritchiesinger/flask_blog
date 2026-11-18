"""WEB-роуты аутентификации: вход, выход и регистрация пользователя."""

from urllib.parse import urlsplit

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from blog.services import auth_service
from blog.services.base_errors import ServiceError

bp = Blueprint("auth", __name__)


def _safe_next_url() -> str | None:
    """Возвращает безопасный параметр next из запроса или None.

    Пропускает только относительные пути внутри сайта: без схемы
    и хоста, начиная с "/" и не начинаясь с "//". Это закрывает
    open redirect: "/login?next=https://evil.site" и вариант
    "//evil.site" оба отвергаются.
    """
    next_url = request.args.get("next")
    if not next_url:
        return None
    split = urlsplit(next_url)
    if split.scheme or split.netloc:
        return None
    if not next_url.startswith("/") or next_url.startswith("//"):
        return None
    return next_url


@bp.route("/login", methods=("GET", "POST"))
def login() -> str | Response:
    """Страница авторизации."""
    if current_user.is_authenticated:
        return redirect(url_for("blog.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = auth_service.authenticate(username, password)

        if user:
            login_user(user)
            return redirect(_safe_next_url() or url_for("blog.index"))

        flash("Неверный логин или пароль", "danger")

    return render_template("auth/login.html")


@bp.route("/logout")
def logout() -> Response:
    """Выход. Сброс авторизации."""
    logout_user()
    flash("Вы вышли из системы", "info")
    return redirect(url_for("blog.index"))


@bp.route("/register", methods=("GET", "POST"))
def register() -> str | Response:
    """Регистрация нового пользователя."""
    if current_user.is_authenticated:
        return redirect(url_for("blog.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        try:
            auth_service.register_user(username, password)
        except ServiceError as e:
            flash(str(e), "danger")
            return render_template("auth/register.html", username=username)

        flash(f'Аккаунт "{username}" успешно создан. Теперь можно войти.', "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")
