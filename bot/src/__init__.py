# Инициализация пакета src

from .exceptions import (
    EatBotException,
    ValidationError,
    NotFoundError,
    PermissionError,
    ConfigurationError
)

__all__ = [
    'EatBotException',
    'ValidationError',
    'NotFoundError',
    'PermissionError',
    'ConfigurationError'
]
