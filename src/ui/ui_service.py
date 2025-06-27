"""
Централизованный сервис для управления пользовательским интерфейсом бота.

Этот модуль инкапсулирует логику отправки и редактирования сообщений,
обеспечивая консистентное поведение UI во всем боте.
"""

import logging
from typing import Optional
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from src.ui.keyboards import KeyboardFactory
from src.ui.messages_main import Messages

logger = logging.getLogger(__name__)


class UIService:
    """Сервис для централизованного управления UI бота."""
    
    def __init__(self):
        """Инициализация UIService."""
        self.logger = logging.getLogger(__name__)
    
    async def _send_or_edit_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        parse_mode: str = "Markdown"
    ) -> None:
        """
        Внутренний метод для отправки или редактирования сообщения.
        
        Определяет, нужно ли отправить новое сообщение или отредактировать существующее,
        основываясь на наличии callback_query в update.
        
        Args:
            update: Объект Update от Telegram
            context: Контекст обработчика
            text: Текст сообщения
            reply_markup: Клавиатура (опционально)
            parse_mode: Режим парсинга (по умолчанию Markdown)
        """
        try:
            if update.callback_query and update.callback_query.message:
                # Редактируем существующее сообщение
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                await update.callback_query.answer()
                self.logger.debug("Сообщение отредактировано")
            else:
                # Отправляем новое сообщение
                if update.message:
                    await update.message.reply_text(
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
                    self.logger.debug("Новое сообщение отправлено")
                else:
                    self.logger.warning("Не удалось определить способ отправки сообщения")
                    
        except BadRequest as e:
            if "Message is not modified" in str(e):
                # Сообщение не изменилось - это нормально
                if update.callback_query:
                    await update.callback_query.answer()
                self.logger.debug("Сообщение не изменилось")
            else:
                # Другая ошибка - логируем и пытаемся отправить новое сообщение
                self.logger.warning(f"Ошибка редактирования сообщения: {e}")
                if update.effective_chat:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
                    self.logger.debug("Отправлено новое сообщение после ошибки редактирования")
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при отправке/редактировании сообщения: {e}")
            raise
    
    async def show_main_menu(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Отображает главное меню бота.
        
        Формирует текст с приветствием пользователя и отображает главное меню
        с помощью _send_or_edit_message.
        
        Args:
            update: Объект Update от Telegram
            context: Контекст обработчика
        """
        # Получаем имя пользователя
        user_name = update.effective_user.first_name if update.effective_user else "пользователь"
        
        # Формируем текст главного меню
        menu_text = Messages["MAIN"]["menu"].format(first_name=user_name)
        
        # Получаем клавиатуру главного меню
        keyboard = KeyboardFactory.get("main_menu")
        
        # Отображаем меню
        await self._send_or_edit_message(
            update=update,
            context=context,
            text=menu_text,
            reply_markup=keyboard
        )
        
        self.logger.info(f"Главное меню отображено для пользователя {update.effective_user.id if update.effective_user else 'unknown'}")


# Создаем глобальный экземпляр для использования в обработчиках
ui_service = UIService() 