"""Тестовый Flask-клиент с автоматической фиксацией HTTP-трафика в отчёт Allure.

AllureClient переопределяет метод ``open``: перед отправкой запроса и после
получения ответа он добавляет в Allure аттачи с запросом и ответом. Тело
запроса берётся из аргументов вызова, а не из ``response.request`` — повторное
чтение тела из уже вычитанного werkzeug-потока вызывает ``ClientDisconnected``.

Обработка редиректов: при ``follow_redirects=True`` werkzeug рекурсивно
вызывает ``open`` второй раз, передавая ``EnvironBuilder`` вместо пути.
Внутренний вызов не аттачится (иначе в отчёт попадает repr билдера и
дубликат ответа) — в отчёте остаётся одна пара «запрос/ответ» на каждый
логический вызов, с финальным ответом.

Тип аттача выбирается по содержимому: JSON-запросы и ответы с
``content_type: application/json`` аттачатся как JSON, остальное (формы,
HTML) — как TEXT.

Секреты (заголовки авторизации, cookies, пароли в телах) маскируются
перед записью в отчёт.
"""

import json
from typing import Any
from urllib.parse import urlencode

import allure
from flask.testing import FlaskClient
from werkzeug.test import EnvironBuilder, TestResponse

#: Заголовки, значения которых маскируются в аттаче запроса.
SENSITIVE_HEADERS = {"authorization", "cookie"}

#: Поля JSON-тела, значения которых маскируются в аттаче запроса.
SENSITIVE_FIELDS = {"password"}


def _mask[T](data: T) -> T:
    """Рекурсивно маскирует значения из SENSITIVE_FIELDS в структурах данных.

    Обходит словари и списки произвольной вложенности и заменяет значения
    защищённых полей на ``"***"``. Прочие типы возвращаются без изменений.

    :param data: словарь, список или скалярное значение.
    :return: копия структуры с замаскированными секретами.
    """
    if isinstance(data, dict):
        return {k: "***" if k in SENSITIVE_FIELDS else _mask(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_mask(item) for item in data]
    return data


def _request_text_from_kwargs(args: tuple, kwargs: dict) -> str:
    """Собирает текстовое представление запроса из аргументов ``FlaskClient.open``.

    Тело читается из ``kwargs`` (``json`` или ``data``) до отправки запроса,
    поэтому поток ввода остаётся нетронутым. Заголовки и поля тела, входящие
    в SENSITIVE_HEADERS / SENSITIVE_FIELDS, маскируются.

    :param args: позиционные аргументы ``open`` (первый — путь запроса).
    :param kwargs: именованные аргументы ``open`` (method, headers, json, data).
    :return: строка вида «метод, путь, заголовки, тело».
    """
    method = kwargs.get("method", "GET")
    path = args[0] if args else kwargs.get("path", "")
    lines = [f"{method} {path}"]
    for key, value in (kwargs.get("headers") or {}).items():
        lines.append(f"{key}: {'***' if key.lower() in SENSITIVE_HEADERS else value}")
    body = ""
    if "json" in kwargs:
        body = json.dumps(_mask(kwargs["json"]), ensure_ascii=False, indent=2)
    elif kwargs.get("data") is not None:
        data = kwargs["data"]
        if isinstance(data, dict):
            body = urlencode(_mask(data))
        elif isinstance(data, bytes):
            body = data.decode(errors="replace")
        else:
            body = str(data)
    if body:
        lines.append("")
        lines.append(body)
    return "\n".join(lines)


def _response_text(response: TestResponse) -> str:
    """Собирает текстовое представление ответа: статус, заголовки, тело.

    JSON-ответы форматируются с отступами; остальное (HTML и прочее)
    декодируется как текст.

    :param response: ответ тестового клиента.
    :return: строка вида «статус, заголовки, тело».
    """
    response_body = response.get_data(as_text=False)
    try:
        response_body = json.dumps(json.loads(response_body), ensure_ascii=False, indent=2)
    except ValueError:
        response_body = response_body.decode(errors="replace")
    response_text = response.status + "\n"
    response_text += "\n".join(f"{k}: {v}" for k, v in response.headers.items())
    response_text += f"\n\n{response_body}"
    return response_text


class AllureClient(FlaskClient):
    """Flask-клиент, который пишет в Allure аттачи запроса и ответа.

    Подключается через ``app.test_client_class = AllureClient`` до создания
    клиента. Все вызовы ``get``/``post``/``delete`` и т. д. идут через
    переопределённый ``open``, поэтому аттачи появляются автоматически,
    без изменений в самих тестах.

    Внутренние редиректные вызовы (второй ``open`` внутри одного вызова
    при ``follow_redirects=True``) не аттачатся: их аргументом является
    ``EnvironBuilder``, а ответ совпадает с финальным.
    """

    #: Писать ли аттачи в отчёт. Отключается точечно на клиенте:
    #: ``setup_app_client.attach_traffic = False``.
    attach_traffic: bool = True

    def open(self, *args: Any, **kwargs: Any) -> TestResponse:
        """Отправляет запрос и добавляет его с ответом в Allure.

        Аттач запроса создаётся до отправки, поэтому он попадёт в отчёт
        даже при ошибке на стороне сервера. Тип аттача — JSON для
        JSON-запросов, TEXT для остального.
        """
        is_redirect_call = bool(args) and isinstance(args[0], EnvironBuilder)
        if self.attach_traffic and not is_redirect_call:
            has_json = "json" in kwargs
            allure.attach(
                _request_text_from_kwargs(args, kwargs),
                name="HTTP запрос",
                attachment_type=allure.attachment_type.JSON if has_json else allure.attachment_type.TEXT,
            )
        response = super().open(*args, **kwargs)

        if self.attach_traffic and not is_redirect_call:
            is_json = (response.content_type or "").startswith("application/json")
            allure.attach(
                _response_text(response),
                name="HTTP ответ",
                attachment_type=allure.attachment_type.JSON if is_json else allure.attachment_type.TEXT,
            )
        return response
