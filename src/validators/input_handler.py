"""
Унифицированный обработчик пользовательского ввода

Этот модуль реализует единую систему обработки всех данных, вводимых пользователем,
в соответствии с планом рефакторинга унификации обработки пользовательского ввода.
"""

import logging
from typing import Dict, Any, Optional, Union, Callable, Type
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from pydantic import ValidationError, BaseModel

from .schemas import (
    RecipeDTO, UserProfileDTO, UserMealDTO, CategoryDTO,
    SearchQueryDTO, FilterDTO, ProductDTO, ProductSearchDTO, ProductCalculatorDTO,
    NutrientSearchDTO, NutrientCalculatorDTO,
    ValidationErrorResponse, create_error_response
)

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ
# ============================================================================

class ValidationResult:
    """Результат валидации данных"""
    
    def __init__(self, is_valid: bool, data: Any, error_message: Optional[str] = None):
        self.is_valid = is_valid
        self.data = data
        self.error_message = error_message

# ============================================================================
# ОСНОВНОЙ КЛАСС
# ============================================================================

logger = logging.getLogger(__name__)

class InputHandler:
    """
    Унифицированный обработчик пользовательского ввода
    
    Обеспечивает:
    - Валидацию входящих данных
    - Стандартизированную обработку ошибок
    - Единый интерфейс для всех обработчиков
    """
    
    def __init__(self):
        """Инициализация обработчика ввода"""
        self.logger = logging.getLogger(__name__)
        
        self.validators = {
            'recipe': RecipeDTO,
            'user_profile': UserProfileDTO,
            'user_meal': UserMealDTO,
            'category': CategoryDTO,
            'search_query': SearchQueryDTO,
            'filter': FilterDTO,
            'product': ProductDTO,
            'product_search': ProductSearchDTO,
            'product_calculator': ProductCalculatorDTO,
            'nutrient_search': NutrientSearchDTO,
            'nutrient_calculator': NutrientCalculatorDTO,
        }
        
        # Маппинг парсеров для разных типов данных
        self.parser_mapping = {
            "product_add": self.parse_product_input,
            "product_edit": self.parse_product_input,
            "product_search": self.parse_product_search_input,
            "product_calculator": self.parse_product_calculator_input,
            "nutrient_search": self.parse_nutrient_search_input,
            "nutrient_calculator": self.parse_nutrient_calculator_input,
        }
    
    def validate_input(
        self,
        data: Dict[str, Any],
        schema_name: str,
        user_message: str = "Ошибка валидации данных"
    ) -> Union[Any, ValidationErrorResponse]:
        """
        Валидация входящих данных по схеме
        
        Args:
            data: Данные для валидации
            schema_name: Название схемы валидации
            user_message: Сообщение для пользователя при ошибке
            
        Returns:
            Валидированный объект или ответ с ошибками
        """
        try:
            if schema_name not in self.validators:
                logger.error(f"Неизвестная схема валидации: {schema_name}")
                return ValidationErrorResponse(
                    success=False,
                    message="Внутренняя ошибка валидации",
                    data=None,
                    errors={"schema": f"Неизвестная схема: {schema_name}"}
                )
            
            schema = self.validators[schema_name]
            validated_data = schema(**data)
            logger.info(f"Данные успешно валидированы по схеме: {schema_name}")
            return validated_data
            
        except ValidationError as e:
            logger.warning(f"Ошибка валидации данных: {e}")
            return create_error_response(e, user_message)
        except Exception as e:
            logger.error(f"Неожиданная ошибка при валидации: {e}")
            return ValidationErrorResponse(
                success=False,
                message="Внутренняя ошибка валидации",
                data=None,
                errors={"internal": "Неожиданная ошибка при обработке данных"}
            )
    
    def extract_user_data(self, update: Update) -> Dict[str, Any]:
        """
        Извлечение данных пользователя из Telegram Update
        
        Args:
            update: Объект Update от Telegram
            
        Returns:
            Словарь с данными пользователя
        """
        user_data = {}
        
        if update.effective_user:
            user = update.effective_user
            user_data.update({
                'user_id': user.id,
                'username': user.username or f"user_{user.id}",
                'first_name': user.first_name,
                'last_name': user.last_name
            })
        
        if update.message and update.message.text:
            user_data['text'] = update.message.text
            
        if update.callback_query and update.callback_query.data:
            user_data['callback_data'] = update.callback_query.data
            
        return user_data
    
    def parse_callback_data(self, callback_data: str) -> Dict[str, Any]:
        """
        Парсинг callback данных
        
        Args:
            callback_data: Строка callback данных
            
        Returns:
            Словарь с распарсенными данными
        """
        try:
            # Простой парсинг в формате "action:param1:param2"
            parts = callback_data.split(':')
            if len(parts) < 1:
                return {'action': 'unknown'}
            
            result = {'action': parts[0]}
            
            # Парсинг параметров
            for i, part in enumerate(parts[1:], 1):
                if '=' in part:
                    key, value = part.split('=', 1)
                    result[key] = value
                else:
                    result[f'param_{i}'] = part
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка парсинга callback данных: {e}")
            return {'action': 'error', 'error': str(e)}
    
    def parse_product_input(self, text: str) -> Dict[str, Any]:
        """
        Парсинг ввода продукта из текста
        
        Args:
            text: Текст с данными продукта
            
        Returns:
            Словарь с данными продукта
        """
        try:
            product_data: Dict[str, Any] = {}
            nutrients: Dict[str, float] = {}
            lines = text.split('\n')
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == "название":
                        product_data["name"] = value
                    elif key == "категория":
                        product_data["category"] = value
                    elif key == "калории":
                        nutrients["calories"] = float(value.replace("ккал", "").replace("г", ""))
                    elif key == "белки":
                        nutrients["protein"] = float(value.replace("г", ""))
                    elif key == "жиры":
                        nutrients["fat"] = float(value.replace("г", ""))
                    elif key == "углеводы":
                        nutrients["carbs"] = float(value.replace("г", ""))
                    elif key == "клетчатка":
                        nutrients["fiber"] = float(value.replace("г", ""))
                    elif key == "сахар":
                        nutrients["sugar"] = float(value.replace("г", ""))
                    elif key == "натрий":
                        nutrients["sodium"] = float(value.replace("мг", ""))
                    elif key == "холестерин":
                        nutrients["cholesterol"] = float(value.replace("мг", ""))
            
            if nutrients:
                product_data["nutrients"] = nutrients
            
            return product_data
            
        except Exception as e:
            logger.error(f"Ошибка парсинга данных продукта: {e}")
            return {}
    
    def parse_product_search_input(self, text: str) -> Dict[str, Any]:
        """
        Парсинг поискового запроса продуктов
        
        Args:
            text: Поисковый запрос
            
        Returns:
            Словарь с данными поиска
        """
        try:
            return {
                "query": text.strip()
            }
        except Exception as e:
            logger.error(f"Ошибка парсинга поискового запроса: {e}")
            return {"query": ""}
    
    def parse_product_calculator_input(self, text: str) -> Dict[str, Any]:
        """
        Парсинг ввода для калькулятора продуктов
        
        Args:
            text: Количество в граммах
            
        Returns:
            Словарь с данными калькулятора
        """
        try:
            amount = float(text.strip())
            return {
                "amount": amount
            }
        except ValueError:
            logger.error(f"Некорректное количество в калькуляторе: {text}")
            return {"amount": 0}
        except Exception as e:
            logger.error(f"Ошибка парсинга данных калькулятора: {e}")
            return {"amount": 0}
    
    def parse_nutrient_search_input(self, text: str) -> Dict[str, Any]:
        """
        Парсинг поискового запроса нутриентов
        
        Args:
            text: Поисковый запрос
            
        Returns:
            Словарь с данными поиска
        """
        try:
            return {
                "query": text.strip()
            }
        except Exception as e:
            logger.error(f"Ошибка парсинга поискового запроса нутриентов: {e}")
            return {"query": ""}
    
    def parse_nutrient_calculator_input(self, text: str) -> Dict[str, Any]:
        """
        Парсинг ввода для калькулятора нутриентов
        
        Args:
            text: Количество в граммах
            
        Returns:
            Словарь с данными калькулятора
        """
        try:
            amount = float(text.strip())
            return {
                "amount": amount
            }
        except ValueError:
            logger.error(f"Некорректное количество в калькуляторе нутриентов: {text}")
            return {"amount": 0}
        except Exception as e:
            logger.error(f"Ошибка парсинга данных калькулятора нутриентов: {e}")
            return {"amount": 0}
    
    def sanitize_text(self, text: str) -> str:
        """
        Очистка текста от потенциально опасных символов
        
        Args:
            text: Исходный текст
            
        Returns:
            Очищенный текст
        """
        if not text:
            return ""
        
        # Удаление HTML тегов
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # Ограничение длины
        if len(text) > 5000:
            text = text[:5000]
        
        # Удаление лишних пробелов
        text = ' '.join(text.split())
        
        return text.strip()
    
    def validate_telegram_input(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        required_fields: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Валидация входящих данных Telegram
        
        Args:
            update: Объект Update
            context: Контекст бота
            required_fields: Список обязательных полей
            
        Returns:
            Словарь с валидированными данными
        """
        user_data = self.extract_user_data(update)
        
        # Проверка обязательных полей
        if required_fields:
            missing_fields = [field for field in required_fields if field not in user_data]
            if missing_fields:
                logger.warning(f"Отсутствуют обязательные поля: {missing_fields}")
                return {
                    'valid': False,
                    'errors': {field: f"Поле {field} обязательно" for field in missing_fields}
                }
        
        # Очистка текста
        if 'text' in user_data:
            user_data['text'] = self.sanitize_text(user_data['text'])
        
        return {
            'valid': True,
            'data': user_data
        }

    async def validate_text_input(
        self,
        update: Update,
        schema_class: Type[BaseModel],
        parser_type: str,
        context: ContextTypes.DEFAULT_TYPE
    ) -> ValidationResult:
        """
        Валидация текстового ввода с парсингом
        
        Args:
            update: Объект Update от Telegram
            schema_class: Класс схемы Pydantic для валидации
            parser_type: Тип парсера для извлечения данных
            context: Контекст бота
            
        Returns:
            ValidationResult с результатом валидации
        """
        try:
            # Извлечение текста из сообщения
            if not update.message or not update.message.text:
                return ValidationResult(
                    is_valid=False,
                    data=None,
                    error_message="Сообщение не содержит текста"
                )
            
            text = update.message.text.strip()
            if not text:
                return ValidationResult(
                    is_valid=False,
                    data=None,
                    error_message="Текст сообщения пуст"
                )
            
            # Парсинг данных
            if parser_type in self.parser_mapping:
                parsed_data = self.parser_mapping[parser_type](text)
            else:
                # Простой парсинг как fallback
                parsed_data = {"text": text}
            
            # Валидация через Pydantic
            try:
                validated_data = schema_class(**parsed_data)
                return ValidationResult(
                    is_valid=True,
                    data=validated_data,
                    error_message=None
                )
            except ValidationError as e:
                # Форматирование ошибок валидации
                error_details = []
                for error in e.errors():
                    field = error['loc'][0] if error['loc'] else 'unknown'
                    message = error['msg']
                    error_details.append(f"• {field}: {message}")
                
                error_message = "❌ Ошибка валидации данных:\n" + "\n".join(error_details)
                return ValidationResult(
                    is_valid=False,
                    data=None,
                    error_message=error_message
                )
                
        except Exception as e:
            logger.error(f"Ошибка валидации текстового ввода: {e}")
            return ValidationResult(
                is_valid=False,
                data=None,
                error_message=f"Внутренняя ошибка: {str(e)}"
            )
    
    async def handle_validation_error(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        error_message: str,
        keyboard_type: str = "back"
    ):
        """
        Обработка ошибок валидации с отправкой сообщения пользователю
        
        Args:
            update: Объект Update
            context: Контекст бота
            error_message: Сообщение об ошибке
            keyboard_type: Тип клавиатуры для ответа
        """
        try:
            from src.ui.keyboards import KeyboardFactory
            from src.ui.ui_service import ui_service
            
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=error_message,
                reply_markup=KeyboardFactory.get(keyboard_type)
            )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения об ошибке: {e}")
            if update.message:
                await update.message.reply_text(error_message)

def validate_input_decorator(schema_name: str, user_message: str = "Ошибка валидации данных"):
    """
    Декоратор для автоматической валидации входящих данных
    
    Args:
        schema_name: Название схемы валидации
        user_message: Сообщение для пользователя при ошибке
        
    Returns:
        Декоратор функции
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            handler = InputHandler()
            
            # Извлечение данных из update
            user_data = handler.extract_user_data(update)
            
            # Валидация данных
            validation_result = handler.validate_input(user_data, schema_name, user_message)
            
            if isinstance(validation_result, ValidationErrorResponse):
                # Ошибка валидации - отправляем сообщение пользователю
                error_message = f"❌ {validation_result.message}\n\n"
                if validation_result.errors:
                    error_message += "🔍 Детали ошибок:\n"
                    for field, error in validation_result.errors.items():
                        error_message += f"• {field}: {error}\n"
                
                if update.message:
                    await update.message.reply_text(error_message)
                return
            
            # Данные валидны - передаем в функцию
            return await func(update, context, validation_result, *args, **kwargs)
        
        return wrapper
    return decorator

def handle_input_errors(func: Callable):
    """
    Декоратор для обработки ошибок ввода
    
    Args:
        func: Функция для декорирования
        
    Returns:
        Декоратор функции
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Ошибка валидации в {func.__name__}: {e}")
            error_response = create_error_response(e, "Ошибка в данных")
            error_message = f"❌ {error_response.message}\n\n"
            if error_response.errors:
                error_message += "🔍 Исправьте следующие ошибки:\n"
                for field, error in error_response.errors.items():
                    error_message += f"• {field}: {error}\n"
            
            if update.message:
                await update.message.reply_text(error_message)
        except Exception as e:
            logger.error(f"Неожиданная ошибка в {func.__name__}: {e}")
            if update.message:
                await update.message.reply_text(
                    "❌ Произошла внутренняя ошибка. Попробуйте позже или обратитесь в поддержку."
                )
    
    return wrapper

# Глобальный экземпляр обработчика
input_handler = InputHandler() 