"""Методы API по работе с пользователями."""

# pylint: disable=cyclic-import  # Это неправда

from flask import Blueprint

bp = Blueprint("users", __name__, url_prefix="/users")

from . import routes  # pylint: disable=wrong-import-position  # Особенность Flask
