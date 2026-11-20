"""Гвард регистрации CLI-команд в фабрике приложения."""

import click
from flask import Flask

from blog import cli, create_app


def test_all_cli_commands_registered_in_factory():
    """Каждая команда blog/cli.py зарегистрирована в app.cli фабрики.

    invoke_cli зовёт click-команду напрямую и регистрацию обходит: без гварда невидимая живому Flask команда не
    падала в тестах (→ ARC-0041).
    """
    expected = {
        obj.name for obj in vars(cli).values()
        if isinstance(obj, click.Command)
    }
    app: Flask = create_app()
    registered = set(app.cli.commands)
    missing = expected - registered
    assert not missing, f"Команды не зарегистрированы в фабрике: {sorted(missing)}"
