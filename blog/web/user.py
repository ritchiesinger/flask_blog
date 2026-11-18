"""WEB-роуты профиля пользователя."""

from flask import Blueprint, render_template

from blog.constants import POSTS_PER_PAGE
from blog.pagination import page_from_args
from blog.services import user_service
from blog.web.errors import web_errors

bp = Blueprint("user", __name__)


@bp.get("/user/<username>")
@web_errors
def profile(username: str):
    """Профиль пользователя: аватар, логин и две независимые ленты.

    Посты листаются параметром page, комментарии — comment_page.
    Неизвестный логин — NotFoundError → фирменная 404-страница.
    """
    profile_user, posts, comments = user_service.get_profile(
        username=username,
        page=page_from_args(),
        comment_page=page_from_args(key="comment_page"),
        per_page=POSTS_PER_PAGE,
    )
    return render_template(
        "blog/profile.html",
        profile_user=profile_user,
        posts=posts,
        comments=comments,
    )
