"""Маршруты связанные с ролями в API."""

# pylint: disable=no-member  # Особенность асбтрактного представления моделей без существующего ещё приложения

from typing import Optional, Tuple

from flask import request

from app.helpers import Response, Errors
from app.blueprints.api.auth import multi_auth
from app.models import Role, UserRoles, db
from . import bp as roles_bp


@roles_bp.route("/role", methods=["POST"])
@multi_auth.login_required(role="admin")
def add_new_role_request() -> Optional[Tuple, Response]:
    """Добавление новой роли."""
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
    return None


@roles_bp.route("/role/<int:role_id>", methods=["PATCH"])
@multi_auth.login_required(role="admin")
def edit_role_requests(role_id: int) -> Optional[Tuple, Response]:
    """Изменение роли."""
    if role_id is None:
        response = Errors.REQUIRED_ARGS_MISSING.get()
    else:
        role: Role = Role.query.filter_by(id=role_id).first()
        if role is None:
            response = Errors.ROLE_NOT_FOUND.get()
        else:
            name = request.json.get('name')
            description = request.json.get('description')
            if name is None and description is None:
                response = Errors.REQUIRED_ARG_MISSING.get()
            elif Role.query.filter_by(name=name).first() is not None:
                response = Errors.ROLE_ALREADY_EXIST.get()
            else:
                role.name = name if name is not None else role.name
                role.description = description if description is not None else role.description
                db.session.commit()
                response = Response(data=role.to_dict()).get()
    return response


@roles_bp.route("/role/<int:role_id>", methods=["GET"])
@multi_auth.login_required(role="admin")
def get_role_requests(role_id: int) -> Optional[Tuple, Response]:
    """Получение данных роли."""
    if role_id is None:
        response = Errors.REQUIRED_ARGS_MISSING.get()
    else:
        role: Role = Role.query.filter_by(id=role_id).first()
        if role is None:
            response = Errors.ROLE_NOT_FOUND.get()
        else:
            response = Response(data=role.to_dict()).get()
    return response


@roles_bp.route("/role/<int:role_id>", methods=["DELETE"])
@multi_auth.login_required(role="admin")
def delete_role_requests(role_id: int) -> Optional[Tuple, Response]:
    """Удаление роли."""
    if role_id is None:
        response = Errors.REQUIRED_ARGS_MISSING.get()
    else:
        role: Role = Role.query.filter_by(id=role_id).first()
        if role is None:
            response = Errors.ROLE_NOT_FOUND.get()
        else:
            db.session.delete(role)
            db.session.commit()
            response = Errors.EMPTY_SUCCESS.get()
    return response


@roles_bp.route("/role_assignment", methods=["POST", "DELETE"])
@multi_auth.login_required(role="admin")
def role_assignment_requests() -> Optional[Tuple, Response]:
    """Назначение и снятие роли у пользователя."""
    body = request.json
    response = None
    if request.method == "POST":
        role_id = body.get('role_id')
        user_id = body.get('user_id')
        if role_id is None or user_id is None:
            response = Errors.REQUIRED_ARGS_MISSING.get()
        elif UserRoles.query.filter_by(role_id=role_id, user_id=user_id).first() is not None:
            response = Errors.ROLE_ALREADY_ASSIGN.get()
        else:
            user_role = UserRoles(user_id=user_id, role_id=role_id)
            db.session.add(user_role)
            db.session.commit()
            response = Errors.EMPTY_SUCCESS.get()
    if request.method == "DELETE":
        user_id = body.get("user_id")
        role_id = body.get("role_id")
        if role_id is None or user_id is None:
            response = Errors.REQUIRED_ARGS_MISSING.get()
        else:
            user_role = UserRoles.query.filter_by(role_id=role_id, user_id=user_id).first()
            if user_role is None:
                response = Errors.ROLE_ASSINGMENT_NOT_FOUND.get()
            else:
                db.session.delete(user_role)
                db.session.commit()
                response = Errors.EMPTY_SUCCESS.get()
    return response
