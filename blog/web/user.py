"""WEB-роуты профиля пользователя."""

from flask import Blueprint, render_template

from blog.constants import PROFILE_TAB_POSTS, PROFILE_TABS
from blog.pagination import page_from_args, tab_from_args
from blog.services import user_service
from blog.web.errors import web_errors

bp = Blueprint("user", __name__)


@bp.get("/user/<username>")
@web_errors
def profile(username: str):
    """Профиль пользователя: аватар, логин и лента активной вкладки.

    Вкладка — параметр tab (posts/comments, мусор → posts), страница ленты —
    page. Санитизация обоих — через pagination.py. Рендерится только активная
    лента: неактивная не запрашивается вовсе. Неизвестный логин — NotFoundError
    → фирменная 404-страница.
    """
    tab = tab_from_args(allowed=PROFILE_TABS, default=PROFILE_TAB_POSTS)
    profile_user, pagination = user_service.get_profile(username=username, tab=tab, page=page_from_args())
    return render_template(
        "blog/profile.html",
        profile_user=profile_user,
        tab=tab,
        pagination=pagination,
    )
