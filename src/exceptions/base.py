"""
Базовые классы исключений для приложения
"""

from typing import Optional, List, Dict, Any
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
        """
        Инициализация исключения
        
        Args:
            message: Внутреннее сообщение об ошибке
            error_code: Код ошибки
            user_message: Сообщение для пользователя
            recovery_steps: Шаги по восстановлению
            context: Дополнительный контекст ошибки
        """
        self.message = message
        self.error_code = error_code
        self.user_message = user_message or message
        self.recovery_steps = recovery_steps or []
        self.context = context or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)

class EatBotException(AppError):
    """Базовое исключение для EatBot"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "EATBOT_ERROR",
        user_message: Optional[str] = None,
        recovery_steps: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class ValidationError(EatBotException):
    """Исключение для ошибок валидации"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте правильность введенных данных",
            "Используйте только разрешенные символы",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class StateError(EatBotException):
    """Ошибки состояния бота"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Вернитесь в главное меню",
            "Начните операцию заново",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="STATE_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class NetworkError(EatBotException):
    """Ошибки сети"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте подключение к интернету",
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class NotFoundError(EatBotException):
    """Исключение для случаев, когда объект не найден"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте правильность запроса",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="NOT_FOUND_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class CacheError(EatBotException):
    """Ошибка работы с кэшем"""
    
    def __init__(
        self,
        message: str = "Ошибка при работе с кэшем",
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class DuplicateError(EatBotException):
    """Ошибка: попытка создать дублирующуюся запись"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте, не существует ли уже такая запись",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="DUPLICATE_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class PermissionError(EatBotException):
    """Исключение для ошибок доступа"""
    
    def __init__(
        self,
        message: str = "Недостаточно прав для выполнения операции",
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте свои права доступа",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="PERMISSION_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class ConfigurationError(EatBotException):
    """Исключение для ошибок конфигурации"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте настройки приложения",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class AuthenticationError(EatBotException):
    """Ошибка аутентификации"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте свои учетные данные",
            "Попробуйте войти заново",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class AuthorizationError(EatBotException):
    """Ошибка авторизации"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте свои права доступа",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class TimeoutError(EatBotException):
    """Ошибка таймаута"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class ResourceNotFoundError(EatBotException):
    """Ошибка отсутствия ресурса"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте правильность запроса",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class ResourceExistsError(EatBotException):
    """Ошибка существования ресурса"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте, не существует ли уже такой ресурс",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="RESOURCE_EXISTS_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidInputError(EatBotException):
    """Ошибка неверного ввода"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте правильность введенных данных",
            "Используйте только разрешенные символы",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_INPUT_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidStateError(EatBotException):
    """Ошибка неверного состояния"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Вернитесь в главное меню",
            "Начните операцию заново",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_STATE_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidOperationError(EatBotException):
    """Ошибка неверной операции"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте правильность операции",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_OPERATION_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidResponseError(EatBotException):
    """Ошибка неверного ответа"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_RESPONSE_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidRequestError(EatBotException):
    """Ошибка неверного запроса"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте правильность запроса",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_REQUEST_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidTokenError(EatBotException):
    """Ошибка неверного токена"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте войти заново",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_TOKEN_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidCredentialsError(EatBotException):
    """Ошибка неверных учетных данных"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте свои учетные данные",
            "Попробуйте войти заново",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_CREDENTIALS_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidSessionError(EatBotException):
    """Ошибка неверной сессии"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте войти заново",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_SESSION_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidCacheError(EatBotException):
    """Ошибка неверного кэша"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_CACHE_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidLogError(EatBotException):
    """Ошибка неверного лога"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_LOG_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidMetricError(EatBotException):
    """Ошибка неверной метрики"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_METRIC_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidMonitorError(EatBotException):
    """Ошибка неверного монитора"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_MONITOR_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidConfigError(EatBotException):
    """Ошибка неверной конфигурации"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте настройки приложения",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_CONFIG_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidEnvError(EatBotException):
    """Ошибка неверного окружения"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте настройки окружения",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_ENV_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidPathError(EatBotException):
    """Ошибка неверного пути"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте правильность пути",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_PATH_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidFileError(EatBotException):
    """Ошибка неверного файла"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте правильность файла",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_FILE_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidDirectoryError(EatBotException):
    """Ошибка неверной директории"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте правильность директории",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_DIRECTORY_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidPermissionError(EatBotException):
    """Ошибка неверного разрешения"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте свои права доступа",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_PERMISSION_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidUserError(EatBotException):
    """Ошибка неверного пользователя"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте свои учетные данные",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_USER_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidGroupError(EatBotException):
    """Ошибка неверной группы"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте свои права доступа",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_GROUP_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidRoleError(EatBotException):
    """Ошибка неверной роли"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте свои права доступа",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_ROLE_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidAccessError(EatBotException):
    """Ошибка неверного доступа"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте свои права доступа",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_ACCESS_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidSecurityError(EatBotException):
    """Ошибка неверной безопасности"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте свои права доступа",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_SECURITY_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidPerformanceError(EatBotException):
    """Ошибка неверной производительности"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_PERFORMANCE_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidScalabilityError(EatBotException):
    """Ошибка неверной масштабируемости"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_SCALABILITY_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidMonitoringError(EatBotException):
    """Ошибка неверного мониторинга"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_MONITORING_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidDeploymentError(EatBotException):
    """Ошибка неверного развертывания"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_DEPLOYMENT_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class InvalidSupportError(EatBotException):
    """Ошибка неверной поддержки"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="INVALID_SUPPORT_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class RecipeError(EatBotException):
    """Ошибка при работе с рецептами"""
    
    def __init__(
        self,
        message: str = "Ошибка при работе с рецептами",
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Попробуйте повторить операцию позже",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="RECIPE_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        )

class RecipeNotFoundError(RecipeError):
    """Ошибка при отсутствии рецепта"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        recovery_steps = [
            "Проверьте правильность запроса",
            "Если проблема повторяется, обратитесь в поддержку"
        ]
        super().__init__(
            message=message,
            error_code="RECIPE_NOT_FOUND_ERROR",
            user_message=user_message,
            recovery_steps=recovery_steps,
            context=context
        ) 