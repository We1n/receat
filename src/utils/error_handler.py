"""
Обработчик ошибок для обработчиков
"""
import logging
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Optional, Callable, Any
from src.monitoring.alerting import log_critical_error

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
    async def handle_validation_error(update: Update, error_message: str) -> None:
        """
        Обработка ошибок валидации
        
        Args:
            update: Обновление от Telegram
            error_message: Сообщение об ошибке
        """
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="retry")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=f"❌ Ошибка валидации:\n\n{error_message}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif update.message:
            await update.message.reply_text(
                text=f"❌ Ошибка валидации:\n\n{error_message}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    @staticmethod
    async def handle_permission_error(update: Update) -> None:
        """
        Обработка ошибок доступа
        
        Args:
            update: Обновление от Telegram
        """
        keyboard = [
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text="❌ У вас нет прав для выполнения этого действия",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif update.message:
            await update.message.reply_text(
                text="❌ У вас нет прав для выполнения этого действия",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    @staticmethod
    async def handle_not_found_error(update: Update, item_type: str) -> None:
        """
        Обработка ошибок "не найдено"
        
        Args:
            update: Обновление от Telegram
            item_type: Тип элемента (рецепт, список и т.д.)
        """
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="retry")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=f"❌ {item_type} не найден",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif update.message:
            await update.message.reply_text(
                text=f"❌ {item_type} не найден",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

class ValidationError(Exception):
    """Ошибка валидации данных"""
    pass

class NotFoundError(Exception):
    """Ошибка: объект не найден"""
    pass 