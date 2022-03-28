from flask import Blueprint
from app.blueprints.api import bp as api_bp

bp = Blueprint("main", __name__, url_prefix="/")
bp.register_blueprint(api_bp)

from . import routes
