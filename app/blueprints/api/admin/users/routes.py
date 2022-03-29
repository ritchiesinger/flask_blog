from flask import request, g

from . import bp as users_bp
from app.helpers import Response, Errors
from app.blueprints.api.auth import multi_auth
from app.models import User, db


@users_bp.route("/<int:user_id>", methods=["GET", "DELETE", "PUT", "PATCH"])
@multi_auth.login_required(role="admin")
def users_requests(user_id):
    """Получение информации о любом пользователе и удаление любого пользователя."""
    if user_id is None:
        return Errors.REQUIRED_ARGS_MISSING.get()
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return Errors.USER_NOT_FOUND.get()
    if request.method == "GET":
        return Response(data=user.to_dict()).get()
    elif request.method == "DELETE":
        if user_id == g.user.id:
            return Errors.ADMIN_SELF_DELETE_NOT_ALLOWED.get()
        else:
            db.session.delete(user)
            db.session.commit()
            return Errors.EMPTY_SUCCESS.get()
    elif request.method == "PUT":
        body = request.json
        login = body.get('login')
        email = body.get('email')
        if login is None or email is None:
            return Errors.REQUIRED_ARGS_MISSING.get()
        if User.query.filter_by(login=login).first() is not None:
            return Errors.LOGIN_ALREADY_EXIST.get()
        if User.query.filter_by(email=email).first() is not None:
            return Errors.EMAIL_ALREADY_EXIST.get()
        user.login = login
        user.email = email
        db.session.commit()
        return Errors.EMPTY_SUCCESS.get()
    elif request.method == "PATCH":
        body = request.json
        login = body.get('login')
        email = body.get('email')
        if login is None and email is None:
            return Errors.REQUIRED_ARG_MISSING.get()
        else:
            if User.query.filter_by(login=login).first() is not None:
                return Errors.LOGIN_ALREADY_EXIST.get()
            elif User.query.filter_by(email=email).first() is not None:
                return Errors.EMAIL_ALREADY_EXIST.get()
            else:
                user.login = login if login is not None else user.login
                user.email = email if email is not None else user.email
                db.session.commit()
                return Response(data=user.to_dict()).get()


@users_bp.route("/", methods=["GET"])
@multi_auth.login_required(role="admin")
def admin_search_users():
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
