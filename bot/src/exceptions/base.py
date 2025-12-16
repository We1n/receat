"""
Базовые классы исключений для приложения (рефакторинг: фабрика исключений)
"""
from typing import Optional, List, Dict, Any, Type
from datetime import datetime

class AppError(Exception):
    """Базовый класс для всех исключений приложения"""
    def __init__(
        self,
        message: str,
        error_code: str,
        user_message: Optional[str] = None,
        recovery_steps: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.user_message = user_message or message
        self.recovery_steps = recovery_steps or []
        self.context = context or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)

class EatBotException(AppError):
    """Базовое исключение для EatBot"""
    pass

# --- Фабрика для однотипных исключений ---
def exception_factory(name: str, error_code: str, recovery_steps: Optional[List[str]] = None, base: Type[Exception] = EatBotException):
    def __init__(self, message, user_message=None, context=None):
        base.__init__(
            self,
            message=message,
            error_code=error_code,
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )
    return type(name, (base,), {"__init__": __init__})

# --- Уникальные/часто используемые исключения ---
ValidationError = exception_factory(
    "ValidationError",
    error_code="VALIDATION_ERROR",
    recovery_steps=[
        "Проверьте правильность введенных данных",
        "Используйте только разрешенные символы",
        "Если проблема повторяется, обратитесь в поддержку"
    ]
)
StateError = exception_factory(
    "StateError",
    error_code="STATE_ERROR",
    recovery_steps=[
        "Вернитесь в главное меню",
        "Начните операцию заново",
        "Если проблема повторяется, обратитесь в поддержку"
    ]
)
NetworkError = exception_factory(
    "NetworkError",
    error_code="NETWORK_ERROR",
    recovery_steps=[
        "Проверьте подключение к интернету",
        "Попробуйте повторить операцию позже",
        "Если проблема повторяется, обратитесь в поддержку"
    ]
)
NotFoundError = exception_factory(
    "NotFoundError",
    error_code="NOT_FOUND_ERROR",
    recovery_steps=[
        "Проверьте правильность запроса",
        "Если проблема повторяется, обратитесь в поддержку"
    ]
)
CacheError = exception_factory(
    "CacheError",
    error_code="CACHE_ERROR",
    recovery_steps=[
        "Попробуйте повторить операцию позже",
        "Если проблема повторяется, обратитесь в поддержку"
    ]
)
DuplicateError = exception_factory(
    "DuplicateError",
    error_code="DUPLICATE_ERROR",
    recovery_steps=[
        "Проверьте, не существует ли уже такая запись",
        "Если проблема повторяется, обратитесь в поддержку"
    ]
)
PermissionError = exception_factory(
    "PermissionError",
    error_code="PERMISSION_ERROR",
    recovery_steps=[
        "Проверьте свои права доступа",
        "Если проблема повторяется, обратитесь в поддержку"
    ]
)
# --- Пример для других ошибок (можно расширять по необходимости) ---
ConfigurationError = exception_factory("ConfigurationError", "CONFIG_ERROR")
AuthenticationError = exception_factory("AuthenticationError", "AUTH_ERROR")
AuthorizationError = exception_factory("AuthorizationError", "AUTHZ_ERROR")
TimeoutError = exception_factory("TimeoutError", "TIMEOUT_ERROR")
ResourceNotFoundError = exception_factory("ResourceNotFoundError", "RESOURCE_NOT_FOUND")
ResourceExistsError = exception_factory("ResourceExistsError", "RESOURCE_EXISTS")
InvalidInputError = exception_factory("InvalidInputError", "INVALID_INPUT")
InvalidStateError = exception_factory("InvalidStateError", "INVALID_STATE")
InvalidOperationError = exception_factory("InvalidOperationError", "INVALID_OPERATION")
InvalidResponseError = exception_factory("InvalidResponseError", "INVALID_RESPONSE")
InvalidRequestError = exception_factory("InvalidRequestError", "INVALID_REQUEST")
InvalidTokenError = exception_factory("InvalidTokenError", "INVALID_TOKEN")
InvalidCredentialsError = exception_factory("InvalidCredentialsError", "INVALID_CREDENTIALS")
InvalidSessionError = exception_factory("InvalidSessionError", "INVALID_SESSION")
InvalidCacheError = exception_factory("InvalidCacheError", "INVALID_CACHE")
InvalidLogError = exception_factory("InvalidLogError", "INVALID_LOG")
InvalidMetricError = exception_factory("InvalidMetricError", "INVALID_METRIC")
InvalidMonitorError = exception_factory("InvalidMonitorError", "INVALID_MONITOR")
InvalidConfigError = exception_factory("InvalidConfigError", "INVALID_CONFIG")
InvalidEnvError = exception_factory("InvalidEnvError", "INVALID_ENV")
InvalidPathError = exception_factory("InvalidPathError", "INVALID_PATH")
InvalidFileError = exception_factory("InvalidFileError", "INVALID_FILE")
InvalidDirectoryError = exception_factory("InvalidDirectoryError", "INVALID_DIRECTORY")
InvalidPermissionError = exception_factory("InvalidPermissionError", "INVALID_PERMISSION")
InvalidUserError = exception_factory("InvalidUserError", "INVALID_USER")
InvalidGroupError = exception_factory("InvalidGroupError", "INVALID_GROUP")
InvalidRoleError = exception_factory("InvalidRoleError", "INVALID_ROLE")
InvalidAccessError = exception_factory("InvalidAccessError", "INVALID_ACCESS")
InvalidSecurityError = exception_factory("InvalidSecurityError", "INVALID_SECURITY")
InvalidPerformanceError = exception_factory("InvalidPerformanceError", "INVALID_PERFORMANCE")
InvalidScalabilityError = exception_factory("InvalidScalabilityError", "INVALID_SCALABILITY")
InvalidMonitoringError = exception_factory("InvalidMonitoringError", "INVALID_MONITORING")
InvalidDeploymentError = exception_factory("InvalidDeploymentError", "INVALID_DEPLOYMENT")
InvalidSupportError = exception_factory("InvalidSupportError", "INVALID_SUPPORT")
# --- Специализированные ошибки для рецептов ---
RecipeError = exception_factory("RecipeError", "RECIPE_ERROR")
RecipeNotFoundError = exception_factory("RecipeNotFoundError", "RECIPE_NOT_FOUND")

# --- Документация по использованию фабрики ---
"""
Пример использования:
    raise ValidationError("Некорректные данные")
    raise NotFoundError("Объект не найден", user_message="Не найдено", context={"id": 123})
""" 