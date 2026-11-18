"""Помощники CLI-тестов: запуск команды с аттачем команды и вывода консоли в Allure."""

from click import Command
from click.testing import CliRunner, Result
from flask import Flask
from glamor import attach, attachment_type

MASK = "***"


def invoke_cli(app: Flask, command: Command, args: list[str], *, hidden: tuple[int, ...] = ()) -> Result:
    """Запускает CLI-команду в контексте приложения и аттачит команду с выводом в отчёт.

    Args:
        app: тестовое приложение.
        command: click-команда (её .name идёт в отображение команды).
        args: аргументы команды, как для CliRunner.invoke.
        hidden: индексы аргументов, маскируемых в аттаче команды (пароли), чтобы секрет не попадал в отчёт.

    Returns:
        Result: результат invoke для последующих ассертов.
    """
    shown = " ".join(MASK if i in hidden else arg for i, arg in enumerate(args))
    attach(name="Команда", body=f"flask {command.name} {shown}", attachment_type=attachment_type.TEXT)
    with app.app_context():  # контекст нужен, чтобы with_appcontext работал с тестовым приложением
        result = CliRunner().invoke(command, args)
    attach(name="Вывод консоли", body=result.output, attachment_type=attachment_type.TEXT)
    return result
