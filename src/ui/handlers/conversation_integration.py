"""
Интеграция ConversationHandler с роутером
Управляет точками входа и выхода для диалогов
"""
import time
import logging
import asyncio
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes

from src.ui.handlers.navigation_handler import NavigationManager
from src.ui.messages.message_factory import MessageFactory
from src.ui.ui_service import ui_service

logger = logging.getLogger(__name__)

class ConversationIntegration:
    """Интеграция ConversationHandler с роутером"""
    
    CONVERSATION_TYPES = {
        'recipe_creation': 'recipe_creation_conversation_handler',
        'product_addition': 'product_addition_conversation_handler',
        'recipe_edit': 'recipe_edit_conversation_handler',
        'product_edit': 'product_edit_conversation_handler'
    }
    
    @staticmethod
    async def start_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               conversation_type: str) -> None:
        """Запуск диалога с сохранением точки возврата"""
        
        if conversation_type not in ConversationIntegration.CONVERSATION_TYPES:
            raise ValueError(f"Unknown conversation type: {conversation_type}")
        
        # Сохраняем текущее состояние как точку возврата
        if context.user_data is None:
            context.user_data = {}
        
        current_screen = context.user_data.get('current_screen')
        if current_screen:
            context.user_data['conversation_return_point'] = {
                'section': current_screen.section,
                'action': current_screen.action,
                'params': current_screen.params,
                'message_text': current_screen.message_text,
                'keyboard_type': current_screen.keyboard_type,
                'timestamp': time.time()
            }
        
        # Устанавливаем флаги диалога
        if context.user_data is None:
            context.user_data = {}
        context.user_data['in_conversation'] = True
        context.user_data['conversation_type'] = conversation_type
        context.user_data['conversation_start_time'] = time.time()
        
        # Логируем начало диалога
        logger.info(f"Starting conversation: {conversation_type}")
        
        # Запускаем соответствующий ConversationHandler
        handler_name = ConversationIntegration.CONVERSATION_TYPES[conversation_type]
        
        # Импортируем обработчики диалогов
        try:
            from src.ui.handlers.conversation_handlers import (
                create_recipe_conversation_handler
            )
            
            if conversation_type == 'recipe_creation':
                # Создаем и запускаем ConversationHandler для рецептов
                conv_handler = create_recipe_conversation_handler()
                # Здесь нужно будет интегрировать с существующим ConversationHandler
                logger.info("Recipe creation conversation started")
            elif conversation_type == 'product_addition':
                logger.info("Product addition conversation started")
            else:
                logger.warning(f"Conversation type {conversation_type} not implemented yet")
                await ConversationIntegration.end_conversation(update, context, success=False)
        except ImportError as e:
            logger.error(f"Failed to import conversation handlers: {e}")
            await ConversationIntegration.end_conversation(update, context, success=False)
    
    @staticmethod
    async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              success: bool = True, result_data: Optional[Dict[str, Any]] = None) -> None:
        """Завершение диалога с возвратом к предыдущему экрану"""
        
        if context.user_data is None:
            context.user_data = {}
        
        conversation_type = context.user_data.get('conversation_type', 'unknown')
        start_time = context.user_data.get('conversation_start_time', 0)
        duration = time.time() - start_time
        
        # Логируем завершение диалога
        logger.info(f"Ending conversation: {conversation_type}, success: {success}, duration: {duration:.2f}s")
        
        # Очищаем флаги диалога
        context.user_data.pop('in_conversation', None)
        context.user_data.pop('conversation_type', None)
        context.user_data.pop('conversation_start_time', None)
        
        # Получаем точку возврата
        return_point = context.user_data.pop('conversation_return_point', None)
        
        if return_point and success:
            # Показываем сообщение об успехе
            if result_data:
                success_message = ConversationIntegration._get_success_message(conversation_type, result_data)
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text=success_message,
                    reply_markup=None
                )
                await asyncio.sleep(2)  # Показываем сообщение 2 секунды
            
            # Возвращаемся к предыдущему экрану
            await NavigationManager.navigate_to(
                update, context,
                return_point['section'],
                return_point['action'],
                return_point['params'],
                return_point['message_text'],
                return_point['keyboard_type']
            )
        else:
            # Показываем сообщение об отмене
            cancel_message = ConversationIntegration._get_cancel_message(conversation_type)
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=cancel_message,
                reply_markup=None
            )
            await asyncio.sleep(2)
            
            # Возвращаемся в главное меню
            await NavigationManager.go_to_main_menu(update, context)
    
    @staticmethod
    def _get_success_message(conversation_type: str, result_data: Dict[str, Any]) -> str:
        """Получает сообщение об успешном завершении диалога"""
        if conversation_type == 'recipe_creation':
            recipe_name = result_data.get('name', 'Рецепт')
            return MessageFactory.format_success(f"Рецепт '{recipe_name}' успешно создан!")
        elif conversation_type == 'product_addition':
            product_name = result_data.get('name', 'Продукт')
            return MessageFactory.format_success(f"Продукт '{product_name}' успешно добавлен!")
        else:
            return MessageFactory.format_success("Операция выполнена успешно!")
    
    @staticmethod
    def _get_cancel_message(conversation_type: str) -> str:
        """Получает сообщение об отмене диалога"""
        if conversation_type == 'recipe_creation':
            return MessageFactory.format_error("Создание рецепта отменено")
        elif conversation_type == 'product_addition':
            return MessageFactory.format_error("Добавление продукта отменено")
        else:
            return MessageFactory.format_error("Операция отменена")
    
    @staticmethod
    def is_in_conversation(context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Проверяет, находится ли пользователь в диалоге"""
        return context.user_data.get('in_conversation', False) if context.user_data else False
    
    @staticmethod
    def get_conversation_type(context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Получает тип текущего диалога"""
        return context.user_data.get('conversation_type') if context.user_data else None
    
    @staticmethod
    def get_conversation_duration(context: ContextTypes.DEFAULT_TYPE) -> float:
        """Получает продолжительность текущего диалога"""
        if not ConversationIntegration.is_in_conversation(context):
            return 0.0
        
        if context.user_data is None:
            return 0.0
        
        start_time = context.user_data.get('conversation_start_time', 0)
        return time.time() - start_time 