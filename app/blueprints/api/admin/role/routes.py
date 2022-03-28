from flask import request

from . import bp as roles_bp
from app.helpers import Response, Errors
from app.blueprints.api.auth import multi_auth
from app.models import Role, UserRoles
from app import db


@roles_bp.route("/role", methods=["POST"])
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


@roles_bp.route("/role/<int:role_id>", methods=["GET", "DELETE", "PUT", "PATCH"])
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


@roles_bp.route("/role_assignment", methods=["POST", "DELETE"])
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
