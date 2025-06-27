from .base import (
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

class MealPlannerError(Exception):
    pass

class MealPlanGenerationError(Exception):
    pass

class UserPreferencesError(Exception):
    pass 