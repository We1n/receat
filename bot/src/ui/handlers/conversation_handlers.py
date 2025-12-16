"""
ConversationHandler для EatBot
Интегрирован с новой архитектурой роутера и использует стандартизированный формат callback_data
"""
import logging
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters

from src.ui.keyboards.factory import KeyboardFactory, CallbackDataBuilder
from src.ui.ui_service import ui_service
from src.ui.messages_main import Messages as RawMessages
from src.services.recipe_service import RecipeService
from src.validators.input_handler import input_handler

# Правильная типизация Messages
Messages: Dict[str, Any] = RawMessages

logger = logging.getLogger(__name__)

# Состояния для добавления рецепта
RECIPE_NAME, RECIPE_INGREDIENTS, RECIPE_INSTRUCTIONS, RECIPE_CONFIRM = range(4)

class RecipeConversationHandler:
    """Обработчик диалога добавления рецепта с новой архитектурой"""
    
    def __init__(self):
        self.recipe_service = RecipeService()
        self.logger = logging.getLogger(__name__)
    
    async def start_recipe_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало диалога добавления рецепта"""
        query = update.callback_query
        if query:
            await query.answer()
        
        if context.user_data is None:
            context.user_data = {}
        
        context.user_data['recipe_data'] = {'ingredients': [], 'tags': []}
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=Messages["CONVERSATION"]["recipe_add_start"],
            reply_markup=KeyboardFactory.get("navigation")
        )
        
        self.logger.info("Начато добавление рецепта")
        return RECIPE_NAME
    
    async def handle_recipe_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода названия рецепта"""
        if not update.message or not update.message.text:
            await self._show_error(update, context, "Пожалуйста, введите название рецепта")
            return RECIPE_NAME
        
        text = update.message.text.strip()
        
        # Валидация
        if len(text) < 3:
            await self._show_error(update, context, "Название должно содержать минимум 3 символа. Попробуйте ещё раз:")
            return RECIPE_NAME
        
        if context.user_data is None:
            context.user_data = {}
        
        context.user_data.setdefault('recipe_data', {})['name'] = text
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=Messages["CONVERSATION"]["recipe_name_saved"].format(name=text),
            reply_markup=KeyboardFactory.get("navigation"),
            parse_mode="Markdown"
        )
        
        self.logger.info(f"Сохранено название рецепта: {text}")
        return RECIPE_INGREDIENTS
    
    async def handle_recipe_ingredients(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода ингредиентов"""
        if not update.message or not update.message.text:
            await self._show_error(update, context, "Пожалуйста, введите ингредиенты")
            return RECIPE_INGREDIENTS
        
        text = update.message.text.strip()
        
        if context.user_data is None:
            context.user_data = {}
        
        # Парсим ингредиенты
        ingredients = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('•'):
                # Убираем маркеры списка
                line = line.lstrip('•-*').strip()
                if line:
                    ingredients.append(line)
        
        if not ingredients:
            await self._show_error(update, context, "Не найдено ни одного ингредиента. Попробуйте ещё раз:")
            return RECIPE_INGREDIENTS
        
        context.user_data.setdefault('recipe_data', {})['ingredients'] = ingredients
        
        ingredients_text = "\n".join([f"• {ingredient}" for ingredient in ingredients])
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=Messages["CONVERSATION"]["recipe_ingredients_saved"].format(ingredients_list=ingredients_text),
            reply_markup=KeyboardFactory.get("navigation"),
            parse_mode="Markdown"
        )
        
        self.logger.info(f"Сохранены ингредиенты рецепта: {len(ingredients)} шт.")
        return RECIPE_INSTRUCTIONS
    
    async def handle_recipe_instructions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода инструкций"""
        if not update.message or not update.message.text:
            await self._show_error(update, context, "Пожалуйста, введите инструкции")
            return RECIPE_INSTRUCTIONS
        
        text = update.message.text.strip()
        
        if context.user_data is None:
            context.user_data = {}
        
        context.user_data.setdefault('recipe_data', {})['instructions'] = text
        
        # Показываем предварительный просмотр
        recipe_data = context.user_data.get('recipe_data', {})
        name = recipe_data.get('name', 'Без названия')
        ingredients = recipe_data.get('ingredients', [])
        instructions = recipe_data.get('instructions', '')
        
        ingredients_text = "\n".join([f"• {ingredient}" for ingredient in ingredients])
        
        preview_text = Messages["CONVERSATION"]["recipe_preview"].format(
            name=name,
            ingredients_list=ingredients_text,
            instructions=instructions
        )
        
        # Используем новую клавиатуру подтверждения
        reply_markup = KeyboardFactory.get_recipe_confirm_keyboard()
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=preview_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        self.logger.info("Сохранены инструкции рецепта")
        return RECIPE_CONFIRM
    
    async def handle_recipe_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка подтверждения добавления рецепта"""
        query = update.callback_query
        if not query:
            return RECIPE_CONFIRM
        
        await query.answer()
        callback_data = query.data
        
        if context.user_data is None:
            context.user_data = {}
        
        # Парсим callback_data
        from src.ui.handlers.main_callback_router import CallbackDataParser
        if callback_data:
            section, action, params = CallbackDataParser.parse(callback_data)
        else:
            section, action, params = "nav", "back", {}
        
        if action == "add_confirm":
            # Подтверждаем добавление
            recipe_data = context.user_data.get('recipe_data', {})
            name = recipe_data.get('name', '')
            
            try:
                self.recipe_service.add_recipe(name, recipe_data)
                
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text=Messages["CONVERSATION"]["recipe_added"].format(name=name),
                    reply_markup=KeyboardFactory.get("navigation")
                )
                
                # Очищаем данные
                context.user_data.pop('recipe_data', None)
                context.user_data['state'] = None
                
                self.logger.info(f"Рецепт успешно добавлен: {name}")
                return ConversationHandler.END
                
            except Exception as e:
                await self._show_error(update, context, f"Ошибка при добавлении рецепта: {e}")
                return RECIPE_CONFIRM
        
        elif section == "nav" and action == "back":
            # Отмена - возвращаемся к инструкциям
            await self._show_error(update, context, Messages["CONVERSATION"]["recipe_cancelled"])
            context.user_data.pop('recipe_data', None)
            context.user_data['state'] = None
            return ConversationHandler.END
        
        return RECIPE_CONFIRM
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена диалога"""
        query = update.callback_query
        if query:
            await query.answer()
        
        if context.user_data is None:
            context.user_data = {}
        
        # Очищаем данные
        context.user_data.pop('recipe_data', None)
        context.user_data['state'] = None
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=Messages["CONVERSATION"]["recipe_cancelled"],
            reply_markup=KeyboardFactory.get("navigation")
        )
        
        self.logger.info("Добавление рецепта отменено")
        return ConversationHandler.END
    
    async def _show_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error_message: str) -> None:
        """Показывает сообщение об ошибке"""
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"❌ {error_message}",
            reply_markup=KeyboardFactory.get("navigation")
        )

# Глобальный экземпляр
recipe_conversation_handler = RecipeConversationHandler()

def create_recipe_conversation_handler() -> ConversationHandler:
    """Создает ConversationHandler для добавления рецепта"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                recipe_conversation_handler.start_recipe_add, 
                pattern=CallbackDataBuilder.build("recipes", "add")
            )
        ],
        states={
            RECIPE_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, 
                    recipe_conversation_handler.handle_recipe_name
                )
            ],
            RECIPE_INGREDIENTS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, 
                    recipe_conversation_handler.handle_recipe_ingredients
                )
            ],
            RECIPE_INSTRUCTIONS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, 
                    recipe_conversation_handler.handle_recipe_instructions
                )
            ],
            RECIPE_CONFIRM: [
                CallbackQueryHandler(recipe_conversation_handler.handle_recipe_confirm)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(
                recipe_conversation_handler.cancel_conversation,
                pattern=CallbackDataBuilder.build("nav", "back")
            ),
            CallbackQueryHandler(
                recipe_conversation_handler.cancel_conversation,
                pattern=CallbackDataBuilder.build("nav", "main_menu")
            )
        ],
        allow_reentry=True
    ) 