from flask import g, request

from . import bp as api_bp
from app.blueprints.api.auth import multi_auth
from app.helpers import Response, Errors
from app.models import User
from app import db


@api_bp.route('/')
def index():
    return "Hello, API Blueprint!"


@api_bp.route('/registration', methods=['POST'])
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


@api_bp.route("/user", methods=["GET", "PUT", "PATCH"])
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
