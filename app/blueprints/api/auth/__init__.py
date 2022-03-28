from flask import Blueprint
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth('Bearer')
multi_auth = MultiAuth(basic_auth, token_auth)

bp = Blueprint("auth", __name__)

from . import routes
