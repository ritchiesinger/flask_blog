"""Маршруты связанные с пользователями в API."""

# pylint: disable=no-member  # Особенность асбтрактного представления моделей без существующего
# ещё приложения

from typing import Optional, Tuple

from flask import request, g

from app.helpers import Response, Errors
from app.blueprints.api.auth import multi_auth
from app.models import User, db
from . import bp as users_bp


@users_bp.route("/<int:user_id>", methods=["PATCH"])
@multi_auth.login_required(role="admin")
def admin_edit_user_requests(user_id: int) -> Optional[Tuple[Response, int]]:
    """Редактирование профиля любого пользователя."""
    if user_id is None:
        response = Errors.REQUIRED_ARGS_MISSING.get()
    else:
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            response = Errors.USER_NOT_FOUND.get()
        else:
            body = request.json
            login = body.get('login')
            email = body.get('email')
            if login is None and email is None:
                response = Errors.REQUIRED_ARG_MISSING.get()
            elif User.query.filter_by(login=login).first() is not None:
                response = Errors.LOGIN_ALREADY_EXIST.get()
            elif User.query.filter_by(email=email).first() is not None:
                response = Errors.EMAIL_ALREADY_EXIST.get()
            else:
                user.login = login if login is not None else user.login
                user.email = email if email is not None else user.email
                db.session.commit()
                response = Response(data=user.to_dict()).get()
    return response


@users_bp.route("/<int:user_id>", methods=["GET"])
@users_bp.route("/", methods=["GET"])
@multi_auth.login_required(role="admin")
def admin_get_user_request(user_id: int = None) -> Optional[Tuple[Response, int]]:
    """Получение информации о любом пользователе."""
    if user_id is None:
        response = Errors.REQUIRED_ARGS_MISSING.get()
    else:
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            response = Errors.USER_NOT_FOUND.get()
        else:
            response = Response(data=user.to_dict()).get()
    return response


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@multi_auth.login_required(role="admin")
def admin_delete_user_request(user_id: int) -> Optional[Tuple[Response, int]]:
    """Удаление любого пользователя."""
    if user_id is None:
        response = Errors.REQUIRED_ARGS_MISSING.get()
    else:
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            response = Errors.USER_NOT_FOUND.get()
        elif user_id == g.user.id:
            response = Errors.ADMIN_SELF_DELETE_NOT_ALLOWED.get()
        else:
            db.session.delete(user)
            db.session.commit()
            response = Errors.EMPTY_SUCCESS.get()
    return response


@users_bp.route("/search", methods=["GET"])
@multi_auth.login_required(role="admin")
def admin_search_users():
    """Поиск пользователй с фильтрацией."""
    login = request.args.get('login')
    email = request.args.get('email')
    page = int(request.args.get('page')) if request.args.get('page') else 1
    per_page = int(request.args.get('per_page')) if request.args.get('per_page') else 10
    users = [
        user.to_dict() for user in User.query.filter(
            User.login.contains(login) if login else True,
            User.email.contains(email) if email else True
        ).all()
    ]
    total_users_found = len(users)
    total_pages = (total_users_found // per_page) + (1 if total_users_found % per_page != 0 else 0)
    page = page if page <= total_pages else total_pages  # если запрашивали несуществующую страницу
    return_batch = users[(page - 1) * per_page: ((page - 1) * per_page) + per_page]
    return_data = {
        "users": return_batch,
        "total_pages": total_pages,
        "page": page,
        "per_page": per_page,
        "total_users_found": total_users_found
    }
    return Response(data=return_data).get()
