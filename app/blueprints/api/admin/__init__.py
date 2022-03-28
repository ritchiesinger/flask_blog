from flask import Blueprint
from app.blueprints.api.admin.users import bp as users_bp
from app.blueprints.api.admin.role import bp as roles_bp

bp = Blueprint("admin", __name__, url_prefix="/admin")
bp.register_blueprint(users_bp)
bp.register_blueprint(roles_bp)
