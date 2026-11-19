"""WEB-роуты постов."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from blog.constants import POSTS_PER_PAGE
from blog.pagination import page_from_args
from blog.services import comment_service, post_service
from blog.services.permissions import Action, ensure_allowed
from blog.web.errors import web_errors

bp = Blueprint("blog", __name__)


@bp.get("/")
@web_errors
def index():
    """Главная: список постов с пагинацией (без авторизации)."""
    pagination = post_service.list_posts(page=page_from_args(), per_page=POSTS_PER_PAGE)
    return render_template("blog/index.html", posts=pagination.items, pagination=pagination)


@bp.route("/create", methods=("GET", "POST"))
@login_required
@web_errors
def create():
    """Создание поста: только для авторизованных."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()

        if not title:
            flash("Заголовок обязателен.", "error")
            return render_template("blog/create.html")

        # Бизнес‑логика в одном месте
        post_service.create_post(title=title, body=body, author_id=current_user.id)
        flash("Пост успешно создан!", "success")
        return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:post_id>", methods=("GET",))
@web_errors
def view(post_id: int):
    """Просмотр одного поста (публичная страница); ?page листает комментарии."""
    post = post_service.get_post(post_id)
    pagination = comment_service.list_for_post(post_id, page=page_from_args())
    return render_template("blog/view.html", post=post, pagination=pagination)


@bp.route("/<int:post_id>/update", methods=("GET", "POST"))
@login_required
@web_errors
def update(post_id: int):
    """Редактирование: только автор может менять свой пост."""
    post = post_service.get_post(post_id)
    ensure_allowed(post.author_id, actor=current_user, action=Action.UPDATE, subject="поста")

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()

        if not title:
            flash("Заголовок обязателен.", "error")
            # Возвращаем тот же шаблон с текущим постом, чтобы не потерять контекст
            return render_template("blog/update.html", post=post)

        post_service.update_post(post, title, body)
        flash("Пост обновлён!", "success")
        return redirect(url_for("blog.view", post_id=post.id))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:post_id>/delete", methods=("POST",))
@login_required
@web_errors
def delete(post_id: int):
    """Удаление: только автор. POST‑only для безопасности (защита от GET‑удаления)."""
    post = post_service.get_post(post_id)
    ensure_allowed(post.author_id, actor=current_user, action=Action.DELETE, subject="поста")

    post_service.delete_post(post)
    flash("Пост удалён.", "success")
    return redirect(url_for("blog.index"))


@bp.route("/<int:post_id>/comments", methods=("POST",))
@login_required
@web_errors
def comment_create(post_id: int):
    """Создание комментария: только для авторизованных."""
    post = post_service.get_post(post_id)
    body = request.form.get("body", "").strip()

    if not body:
        flash("Текст комментария не может быть пустым.", "error")
        return render_template(
            "blog/view.html",
            post=post,
            pagination=comment_service.list_for_post(post_id),
        )

    comment_service.create_comment(post_id=post_id, author_id=current_user.id, body=body)
    flash("Комментарий добавлен!", "success")
    return redirect(url_for("blog.view", post_id=post_id))


@bp.route("/comments/<int:comment_id>/update", methods=("GET", "POST"))
@login_required
@web_errors
def comment_update(comment_id: int):
    """Редактирование комментария: только автор комментария."""
    comment = comment_service.get_comment(comment_id)
    ensure_allowed(comment.author_id, actor=current_user, action=Action.UPDATE, subject="комментария")

    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if not body:
            flash("Текст комментария не может быть пустым.", "error")
            return render_template("blog/comment_update.html", comment=comment)
        comment_service.update_comment(comment, body)
        flash("Комментарий обновлён!", "success")
        return redirect(url_for("blog.view", post_id=comment.post_id))

    return render_template("blog/comment_update.html", comment=comment)


@bp.route("/comments/<int:comment_id>/delete", methods=("POST",))
@login_required
@web_errors
def comment_delete(comment_id: int):
    """Удаление комментария: только автор комментария. POST-only."""
    comment = comment_service.get_comment(comment_id)
    ensure_allowed(comment.author_id, actor=current_user, action=Action.DELETE, subject="комментария")

    post_id = comment.post_id
    comment_service.delete_comment(comment)
    flash("Комментарий удалён.", "success")
    return redirect(url_for("blog.view", post_id=post_id))
