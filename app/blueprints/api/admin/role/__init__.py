from flask import Blueprint

bp = Blueprint("role", __name__)

from . import routes
