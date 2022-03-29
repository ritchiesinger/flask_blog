"""Методы API по работе с ролями."""

# pylint: disable=cyclic-import  # Это неправда

from flask import Blueprint

bp = Blueprint("role", __name__)

from . import routes  # pylint: disable=wrong-import-position  # Особенность Flask
