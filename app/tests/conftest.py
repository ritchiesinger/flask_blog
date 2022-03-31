from pytest import fixture
from app import create_app
from config import TestingConfig


@fixture()
def app():
    app = create_app(TestingConfig)
    # other setup can go here
    yield app
    # clean up / reset resources here


@fixture()
def client(app):
    return app.test_client()


@fixture()
def runner(app):
    return app.test_cli_runner()
