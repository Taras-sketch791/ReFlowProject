class RobokassaError(Exception):
    """Базовое исключение для модуля."""

class InvalidSignature(RobokassaError):
    """Подпись не совпадает."""

class APIError(RobokassaError):
    """Ошибка при обращении к API."""

class ValidationError(RobokassaError):
    """Неверные параметры платежа."""
