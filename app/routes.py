"""Пути (Views/Routes) сервиса."""

from flask import g, request, session
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth

from app import app, db
from app.models import User, Role, UserRoles
from app.helpers import Errors, Response

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth('Bearer')
multi_auth = MultiAuth(basic_auth, token_auth)


@app.route('/')
def index():
    return "Hello, World!"


@app.route('/api/registration', methods=['POST'])
def user_registration():
    body = request.json
    login = body.get('login')
    password = body.get('password')
    email = body.get('email')
    if login is None or password is None or email is None:
        return Errors.REQUIRED_ARGS_MISSING.get()
    elif User.query.filter_by(login=login).first() is not None:
        return Errors.LOGIN_ALREADY_EXIST.get()
    elif User.query.filter_by(email=email).first() is not None:
        return Errors.EMAIL_ALREADY_EXIST.get()
    else:
        user = User(login=login, email=email)
        user.hash_password(password)
        db.session.add(user)
        db.session.commit()
    return Response(data={"login": user.login, "id": user.id, "email": user.email}).get()


@app.route('/api/token')
@basic_auth.login_required
def get_auth_token():
    return Response(data={"user_roles": g.user.to_dict()["roles"]}).get()


@app.route("/api/user", methods=["GET", "PUT", "PATCH"])
@multi_auth.login_required()
def me_requests():
    user = g.user
    if request.method == "GET":
        return Response(data=user.to_dict()).get()
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


@app.route("/api/admin/users/<int:user_id>", methods=["GET", "DELETE", "PUT", "PATCH"])
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


@app.route("/api/admin/users/", methods=["GET"])
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


@app.route("/api/admin/role", methods=["POST"])
@multi_auth.login_required(role="admin")
def add_new_role_request():
    body = request.json
    if request.method == "POST":
        name = body.get('name')
        description = body.get('description')
        if name is None:
            return Errors.REQUIRED_ARGS_MISSING.get()
        if Role.query.filter_by(name=name).first() is not None:
            return Errors.ROLE_ALREADY_EXIST.get()
        role = Role(name=name, description=description)
        db.session.add(role)
        db.session.commit()
        return Response(data={"name": role.name, "id": role.id}).get()


@app.route("/api/admin/role/<int:role_id>", methods=["GET", "DELETE", "PUT", "PATCH"])
@multi_auth.login_required(role="admin")
def roles_requests(role_id):
    """CRUD ролей."""
    if role_id is None:
        return Errors.REQUIRED_ARGS_MISSING.get()
    role: Role = Role.query.filter_by(id=role_id).first()
    if role is None:
        return Errors.ROLE_NOT_FOUND.get()
    if request.method == "GET":
        return Response(data=role.to_dict()).get()
    elif request.method == "DELETE":
        db.session.delete(role)
        db.session.commit()
        return Errors.EMPTY_SUCCESS.get()
    elif request.method == "PUT":
        name = request.json.get('name')
        description = request.json.get('description')
        if name is None or description is None:
            return Errors.REQUIRED_ARGS_MISSING.get()
        if Role.query.filter_by(name=name).first() is not None:
            return Errors.ROLE_ALREADY_EXIST.get()
        role.name = name
        role.description = description
        db.session.commit()
        return Errors.EMPTY_SUCCESS.get()
    elif request.method == "PATCH":
        name = request.json.get('name')
        description = request.json.get('description')
        if name is None and description is None:
            return Errors.REQUIRED_ARG_MISSING.get()
        if Role.query.filter_by(name=name).first() is not None:
            return Errors.ROLE_ALREADY_EXIST.get()
        role.name = name if name is not None else role.name
        role.description = description if description is not None else role.description
        db.session.commit()
        return Response(data=role.to_dict()).get()


@app.route("/api/admin/role_assignment", methods=["POST", "DELETE"])
@multi_auth.login_required(role="admin")
def role_assignment_requests():
    body = request.json
    if request.method == "POST":
        role_id = body.get('role_id')
        user_id = body.get('user_id')
        if role_id is None or user_id is None:
            return Errors.REQUIRED_ARGS_MISSING.get()
        if UserRoles.query.filter_by(role_id=role_id, user_id=user_id).first() is not None:
            return Errors.ROLE_ALREADY_ASSIGN.get()
        user_role = UserRoles(user_id=user_id, role_id=role_id)
        db.session.add(user_role)
        db.session.commit()
        return Errors.EMPTY_SUCCESS.get()
    elif request.method == "DELETE":
        user_id = body.get("user_id")
        role_id = body.get("role_id")
        if role_id is None or user_id is None:
            return Errors.REQUIRED_ARGS_MISSING.get()
        user_role = UserRoles.query.filter_by(role_id=role_id, user_id=user_id).first()
        if user_role is None:
            return Errors.ROLE_ASSINGMENT_NOT_FOUND.get()
        db.session.delete(user_role)
        db.session.commit()
        return Errors.EMPTY_SUCCESS.get()


@basic_auth.verify_password
def verify_password(login, password):
    user = User.query.filter_by(login=login).first()
    if not user or not user.verify_password(password):
        return False
    session["user_roles"] = user.to_dict()["roles"]
    g.user = user
    return user


@token_auth.verify_token
def verify_token(token):
    user = User.verify_token(token)
    if not user:
        return False
    session["user_roles"] = user.to_dict()["roles"]
    g.user = user
    return user


@basic_auth.get_user_roles
def get_user_roles(_):
    return g.user.to_dict()["roles"]
