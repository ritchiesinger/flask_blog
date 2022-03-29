"""API сервиса."""

# pylint: disable=cyclic-import  # Это неправда

from flask import Blueprint
from app.blueprints.api.auth import bp as auth_bp
from app.blueprints.api.admin import bp as admin_bp

bp = Blueprint("api", __name__, url_prefix="/api")
bp.register_blueprint(auth_bp)
bp.register_blueprint(admin_bp)

from . import routes  # pylint: disable=wrong-import-position  # Особенность Flask
