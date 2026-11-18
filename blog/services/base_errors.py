"""Базовые общие классы ошибок."""

class ServiceError(Exception):
    """Базовый класс для всех ошибок бизнес-логики."""
    status_code = 500  # по умолчанию — серверная ошибка


class NotFoundError(ServiceError):
    """Запрашиваемая сущность не найдена."""
    status_code = 404


class ForbiddenError(ServiceError):
    """Доступ к ресурсу запрещён текущему пользователю."""
    status_code = 403


class BadRequestError(ServiceError):
    """Запрос некорректен или не прошёл валидацию."""
    status_code = 400


class ConflictError(ServiceError):
    """Конфликт с существующей сущностью, например занятый логин."""
    status_code = 409
