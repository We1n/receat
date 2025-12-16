"""
Обработчик ошибок для обработчиков
"""
import logging
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Optional, Callable, Any
from src.monitoring.alerting import log_critical_error
from src.ui.keyboards.factory import CallbackDataBuilder

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Класс для обработки ошибок"""
    
    @classmethod
    def handle_errors(cls, func: Callable) -> Callable:
        """
        Декоратор для обработки ошибок
        
        Args:
            func: Функция для обработки
            
        Returns:
            Callable: Обернутая функция
        """
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"❌ Ошибка в {func.__name__}: {str(e)}", exc_info=True)
                log_critical_error(f"Ошибка в {func.__name__}", e)
                
                # Получаем update из аргументов
                update = next((arg for arg in args if isinstance(arg, Update)), None)
                if not update:
                    return
                
                # Формируем сообщение об ошибке
                error_message = "❌ Произошла ошибка:\n\n"
                
                # Добавляем специфичные сообщения для разных типов ошибок
                if isinstance(e, ValueError):
                    error_message += "• Неверный формат данных\n"
                elif isinstance(e, KeyError):
                    error_message += "• Отсутствуют необходимые данные\n"
                elif isinstance(e, TypeError):
                    error_message += "• Неверный тип данных\n"
                else:
                    error_message += "• Внутренняя ошибка сервера\n"
                
                error_message += "\nПожалуйста, попробуйте позже или обратитесь в поддержку."
                
                # Создаем клавиатуру
                keyboard = [
                    [InlineKeyboardButton("🔄 Попробовать снова", callback_data="retry")],
                    [InlineKeyboardButton("❓ Помощь", callback_data="help")]
                ]
                
                # Отправляем сообщение об ошибке
                if update.callback_query:
                    await update.callback_query.edit_message_text(
                        text=error_message,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                elif update.message:
                    await update.message.reply_text(
                        text=error_message,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                
                # Логируем ошибку
                logger.error(f"Ошибка в {func.__name__}: {str(e)}", exc_info=True)
                
                # Возвращаем None вместо выброса исключения
                return None
        
        return wrapper
    
    @staticmethod
    async def handle_validation_error(
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE, 
        error_message: str,
        keyboard_type: str = "back"
    ) -> None:
        """
        Обработка ошибок валидации
        
        Args:
            update: Обновление от Telegram
            context: Контекст обработчика
            error_message: Сообщение об ошибке
            keyboard_type: Тип клавиатуры для возврата
        """
        try:
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data=CallbackDataBuilder.build("nav", "retry"))],
                [InlineKeyboardButton("❓ Помощь", callback_data=CallbackDataBuilder.build("nav", "help"))]
            ]
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=f"❌ {error_message}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            elif update.message:
                await update.message.reply_text(
                    text=f"❌ {error_message}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            
            logger.warning(f"Validation error handled: {error_message}")
            
        except Exception as e:
            logger.error(f"Error in handle_validation_error: {e}")
    
    @staticmethod
    async def handle_system_error(
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE, 
        error_message: str,
        keyboard_type: str = "back"
    ) -> None:
        """
        Обработка системных ошибок
        
        Args:
            update: Обновление от Telegram
            context: Контекст обработчика
            error_message: Сообщение об ошибке
            keyboard_type: Тип клавиатуры для возврата
        """
        try:
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data=CallbackDataBuilder.build("nav", "retry"))],
                [InlineKeyboardButton("❓ Помощь", callback_data=CallbackDataBuilder.build("nav", "help"))]
            ]
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=f"💥 Системная ошибка: {error_message}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            elif update.message:
                await update.message.reply_text(
                    text=f"💥 Системная ошибка: {error_message}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            
            logger.error(f"System error handled: {error_message}")
            
        except Exception as e:
            logger.error(f"Error in handle_system_error: {e}")
    
    @staticmethod
    async def handle_network_error(
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE, 
        error_message: str,
        keyboard_type: str = "back"
    ) -> None:
        """
        Обработка сетевых ошибок
        
        Args:
            update: Обновление от Telegram
            context: Контекст обработчика
            error_message: Сообщение об ошибке
            keyboard_type: Тип клавиатуры для возврата
        """
        try:
            keyboard = [
                [InlineKeyboardButton("❓ Помощь", callback_data=CallbackDataBuilder.build("nav", "help"))]
            ]
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=f"🌐 Сетевая ошибка: {error_message}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            elif update.message:
                await update.message.reply_text(
                    text=f"🌐 Сетевая ошибка: {error_message}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            
            logger.error(f"Network error handled: {error_message}")
            
        except Exception as e:
            logger.error(f"Error in handle_network_error: {e}")
    
    @staticmethod
    async def handle_permission_error(
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE, 
        error_message: str,
        keyboard_type: str = "back"
    ) -> None:
        """
        Обработка ошибок доступа
        
        Args:
            update: Обновление от Telegram
            context: Контекст обработчика
            error_message: Сообщение об ошибке
            keyboard_type: Тип клавиатуры для возврата
        """
        try:
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data=CallbackDataBuilder.build("nav", "retry"))],
                [InlineKeyboardButton("❓ Помощь", callback_data=CallbackDataBuilder.build("nav", "help"))]
            ]
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=f"🔒 Ошибка доступа: {error_message}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            elif update.message:
                await update.message.reply_text(
                    text=f"🔒 Ошибка доступа: {error_message}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            
            logger.warning(f"Permission error handled: {error_message}")
            
        except Exception as e:
            logger.error(f"Error in handle_permission_error: {e}")

class ValidationError(Exception):
    """Ошибка валидации данных"""
    pass

class NotFoundError(Exception):
    """Ошибка: объект не найден"""
    pass 