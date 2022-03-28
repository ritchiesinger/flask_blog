from . import bp as main_bp


@main_bp.route('/')
def index():
    return "Hello, Flask Application!"
