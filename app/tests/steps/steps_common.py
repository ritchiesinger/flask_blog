"""Общие шаги."""

from dataclasses import dataclass
from typing import Any, List

from allure import step


@dataclass
class Check:
    """Проверка. Синтаксический сахар."""
    def __init__(self, param_name, expect_value, actual_value):
        self.param_name = param_name
        self.expect_value = expect_value
        self.actual_value = actual_value

    def check(self):
        """Провести проверку."""
        expect_equal(self.param_name, self.expect_value, self.actual_value)


def expect_equal(param_name: str, expect_value: Any, actual_value: Any):
    """Шаг проверки какоего-либо значения."""
    step_name = f"{param_name}. Ожидалось: {expect_value}, Факт: {actual_value}"
    if len(step_name) > 100:
        step_name = f"{param_name} соответствует ожидаемому значению"
    with step(step_name):
        assert expect_value == actual_value


def verifier(step_name: str = "Проверки", checklist: List[Check] = None):
    """Шаг для группировки нескольких проверок."""
    checklist = checklist or []
    with step(step_name):
        for check in checklist:
            check.check()
