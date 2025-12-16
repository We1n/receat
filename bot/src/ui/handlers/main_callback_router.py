"""
Единый роутер колбэков для EatBot
Обрабатывает все нажатия на inline-кнопки с использованием стандартизированного формата callback_data
"""
import logging
from typing import Dict, Any, Optional, Tuple
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class CallbackDataParser:
    """Парсер для стандартизированного формата callback_data"""
    
    @staticmethod
    def parse(callback_data: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Парсит callback_data в формате section:action:param1=value1:param2=value2
        
        Args:
            callback_data: Строка callback_data
            
        Returns:
            Tuple[section, action, params]
        """
        if not callback_data or callback_data == "no_action":
            return "nav", "no_action", {}
        
        parts = callback_data.split(":")
        
        if len(parts) < 2:
            logger.warning(f"Invalid callback_data format: {callback_data}")
            return "nav", "error", {"original_data": callback_data}
        
        section = parts[0]
        action = parts[1]
        params = {}
        
        # Парсим параметры
        for part in parts[2:]:
            if "=" in part:
                key, value = part.split("=", 1)
                params[key] = value
            else:
                # Если нет =, считаем это значением без ключа
                params["value"] = part
        
        return section, action, params

class MainCallbackRouter:
    """Единый роутер для всех колбэков"""
    
    def __init__(self):
        self.handlers: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_handler(self, section: str, handler):
        """Регистрирует обработчик для определенного раздела"""
        self.handlers[section] = handler
        self.logger.info(f"Зарегистрирован обработчик для раздела: {section}")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Основной обработчик всех колбэков
        
        Args:
            update: Объект Update от Telegram
            context: Контекст выполнения
        """
        query = update.callback_query
        if not query:
            return
        
        callback_data = query.data
        self.logger.info(f"Получен колбэк: {callback_data}")
        
        # Проверяем на None
        if callback_data is None:
            self.logger.warning("Получен колбэк с пустыми данными")
            return
        
        # Парсим callback_data
        section, action, params = CallbackDataParser.parse(callback_data)
        
        self.logger.info(f"Парсинг: section={section}, action={action}, params={params}")
        
        # Отвечаем на колбэк (убираем "часики")
        try:
            await query.answer()
        except Exception as e:
            self.logger.warning(f"Ошибка при ответе на колбэк: {e}")
        
        # Находим и вызываем соответствующий обработчик
        if section in self.handlers:
            try:
                await self.handlers[section].handle_action(update, context, action, params)
            except Exception as e:
                self.logger.error(f"Ошибка в обработчике {section}: {e}", exc_info=True)
                await self._handle_error(update, context, f"Ошибка обработки: {e}")
        else:
            self.logger.warning(f"Не найден обработчик для раздела: {section}")
            await self._handle_error(update, context, f"Неизвестный раздел: {section}")
    
    async def _handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error_message: str) -> None:
        """Обработка ошибок в колбэках"""
        try:
            from src.ui.ui_service import ui_service
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=f"❌ Произошла ошибка: {error_message}",
                reply_markup=None
            )
        except Exception as e:
            self.logger.error(f"Ошибка при отправке сообщения об ошибке: {e}")

# Глобальный экземпляр роутера
callback_router = MainCallbackRouter()

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальная функция-обработчик для регистрации в Application"""
    await callback_router.handle_callback(update, context) 