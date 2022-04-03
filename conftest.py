"""Настройки и фикстуры pytest."""

pytest_plugins = [
    "app.tests.steps.preconditions.preconditions_common",
    "app.tests.steps.preconditions.preconditions_users",
]
