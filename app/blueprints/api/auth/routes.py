from flask import g, session

from . import bp as auth_bp, basic_auth, token_auth
from app.helpers import Response
from app.models import User


@auth_bp.route('/token')
@basic_auth.login_required
def get_auth_token():
    return Response(data={"user_roles": g.user.to_dict()["roles"]}).get()


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
