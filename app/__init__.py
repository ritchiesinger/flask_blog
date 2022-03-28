"""Инициализация приложения."""

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

app = Flask(__name__)

app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
cors = CORS(app)

from app.blueprints.main import bp as main_bp
app.register_blueprint(main_bp)

from app import models
