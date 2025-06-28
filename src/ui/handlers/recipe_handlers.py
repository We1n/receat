"""
Обработчик рецептов для EatBot
Обрабатывает все действия, связанные с рецептами, используя новую архитектуру роутера
"""
import logging
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from src.ui.keyboards.factory import KeyboardFactory, CallbackDataBuilder
from src.ui.ui_service import ui_service
from src.ui.messages_main import Messages as RawMessages
from src.services.recipe_service import RecipeService
from src.config.states import RECIPE_ADD

# Правильная типизация Messages
Messages: Dict[str, Any] = RawMessages

logger = logging.getLogger(__name__)

# Состояния для добавления рецепта
RECIPE_NAME, RECIPE_INGREDIENTS, RECIPE_INSTRUCTIONS, RECIPE_CONFIRM = range(4)

class RecipeHandler:
    """Обработчик всех действий с рецептами"""
    
    def __init__(self):
        self.recipe_service = RecipeService()
        self.logger = logging.getLogger(__name__)
    
    async def handle_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, params: Dict[str, Any]) -> None:
        """
        Обрабатывает действия с рецептами
        
        Args:
            update: Объект Update от Telegram
            context: Контекст выполнения
            action: Действие (menu, list, view, add, search, delete_confirm, add_confirm, etc.)
            params: Параметры действия
        """
        self.logger.info(f"Обработка действия рецептов: {action}")
        
        if action == "menu":
            await self._show_recipe_menu(update, context)
        elif action == "list":
            await self._show_recipe_list(update, context, params)
        elif action == "view":
            await self._show_recipe_view(update, context, params)
        elif action == "add":
            await self._start_recipe_add(update, context)
        elif action == "add_confirm":
            await self._handle_add_confirm(update, context)
        elif action == "search":
            await self._start_recipe_search(update, context)
        elif action == "delete_confirm":
            await self._confirm_recipe_delete(update, context, params)
        elif action == "delete":
            await self._delete_recipe(update, context, params)
        else:
            self.logger.warning(f"Неизвестное действие рецептов: {action}")
            await self._show_recipe_menu(update, context)
    
    async def _show_recipe_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает меню рецептов"""
        recipes_text = Messages.get("RECIPES", {}).get("menu", "📚 Меню рецептов")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=recipes_text,
            reply_markup=KeyboardFactory.get("recipe_menu")
        )
        self.logger.info("Показано меню рецептов")
    
    async def _show_recipe_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Показывает список рецептов с пагинацией"""
        page = int(params.get("page", 1))
        page_size = 5
        
        all_recipes = self.recipe_service.get_all_recipes()
        
        if not all_recipes:
            text = "📋 *Мои рецепты*\n\nУ вас пока нет сохраненных рецептов."
            reply_markup = KeyboardFactory.get("navigation")
        else:
            # Пагинация
            total_pages = (len(all_recipes) + page_size - 1) // page_size
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_recipes = all_recipes[start_idx:end_idx]
            
            text = f"📋 *Мои рецепты* (страница {page}/{total_pages})\n\nВыберите рецепт для просмотра:"
            
            keyboard = []
            for recipe in page_recipes:
                recipe_id = recipe.get('id')
                recipe_name = recipe.get('name', 'Без названия')
                display_name = recipe_name[:30] + "..." if len(recipe_name) > 30 else recipe_name
                keyboard.append([
                    InlineKeyboardButton(
                        display_name, 
                        callback_data=CallbackDataBuilder.build("recipes", "view", id=recipe_id)
                    )
                ])
            
            # Добавляем пагинацию если нужно
            if total_pages > 1:
                keyboard.append([
                    InlineKeyboardButton(
                        "◀️", 
                        callback_data=CallbackDataBuilder.build("recipes", "list", page=page-1)
                    ) if page > 1 else InlineKeyboardButton(" ", callback_data="no_action"),
                    InlineKeyboardButton(f"{page}/{total_pages}", callback_data="no_action"),
                    InlineKeyboardButton(
                        "▶️", 
                        callback_data=CallbackDataBuilder.build("recipes", "list", page=page+1)
                    ) if page < total_pages else InlineKeyboardButton(" ", callback_data="no_action")
                ])
            
            # Добавляем навигационные кнопки
            keyboard.extend(KeyboardFactory._get_navigation_row())
            
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=reply_markup
        )
        self.logger.info(f"Показан список рецептов (страница {page})")
    
    async def _show_recipe_view(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Показывает детальный вид рецепта"""
        recipe_id = params.get("id")
        if not recipe_id:
            await self._show_error(update, context, "ID рецепта не указан")
            return
        
        recipe = self.recipe_service.get_recipe_by_id(recipe_id)
        if not recipe:
            await self._show_error(update, context, "Рецепт не найден")
            return
        
        # Формируем текст рецепта
        name = recipe.get('name', 'Без названия')
        ingredients = recipe.get('ingredients', [])
        instructions = recipe.get('instructions', 'Инструкции не указаны')
        
        text = f"📖 *{name}*\n\n"
        
        if ingredients:
            text += "*Ингредиенты:*\n"
            for ingredient in ingredients:
                if isinstance(ingredient, dict):
                    amount = ingredient.get('amount', '')
                    unit = ingredient.get('unit', '')
                    name_ing = ingredient.get('name', '')
                    text += f"• {name_ing} {amount} {unit}\n"
                else:
                    text += f"• {ingredient}\n"
            text += "\n"
        
        text += f"*Инструкции:*\n{instructions}"
        
        # Клавиатура с действиями
        keyboard = [
            [
                InlineKeyboardButton(
                    "✏️ Редактировать", 
                    callback_data=CallbackDataBuilder.build("recipes", "edit", id=recipe_id)
                ),
                InlineKeyboardButton(
                    "🗑️ Удалить", 
                    callback_data=CallbackDataBuilder.build("recipes", "delete_confirm", id=recipe_id)
                )
            ]
        ]
        
        # Добавляем навигационные кнопки
        keyboard.extend(KeyboardFactory._get_navigation_row())
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=reply_markup
        )
        self.logger.info(f"Показан рецепт: {recipe_id}")
    
    async def _start_recipe_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Начинает процесс добавления рецепта"""
        if context.user_data is None:
            context.user_data = {}
        
        context.user_data['recipe_data'] = {'ingredients': [], 'tags': []}
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="➕ *Добавление рецепта*\n\nВведите название рецепта:",
            reply_markup=KeyboardFactory.get("navigation")
        )
        
        # Устанавливаем состояние
        context.user_data['state'] = RECIPE_NAME
        
        self.logger.info("Начато добавление рецепта")
    
    async def _handle_add_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает подтверждение добавления рецепта"""
        if context.user_data is None:
            context.user_data = {}
        
        recipe_data = context.user_data.get('recipe_data', {})
        name = recipe_data.get('name', '')
        
        try:
            self.recipe_service.add_recipe(name, recipe_data)
            
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=f"✅ Рецепт «{name}» успешно добавлен!",
                reply_markup=KeyboardFactory.get("navigation")
            )
            
            # Очищаем данные
            context.user_data.pop('recipe_data', None)
            context.user_data['state'] = None
            
            self.logger.info(f"Рецепт успешно добавлен: {name}")
            
        except Exception as e:
            await self._show_error(update, context, f"Ошибка при добавлении рецепта: {e}")
    
    async def _start_recipe_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Начинает поиск рецептов"""
        search_text = Messages.get("RECIPES", {}).get("search", "🔍 Поиск рецептов")
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"{search_text}\n\nВведите название или ингредиенты:",
            reply_markup=KeyboardFactory.get("navigation")
        )
        
        # Устанавливаем состояние поиска
        if context.user_data is None:
            context.user_data = {}
        context.user_data['state'] = 'recipe_search'
        
        self.logger.info("Начат поиск рецептов")
    
    async def _confirm_recipe_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Запрашивает подтверждение удаления рецепта"""
        recipe_id = params.get("id")
        if not recipe_id:
            await self._show_error(update, context, "ID рецепта не указан")
            return
        
        recipe = self.recipe_service.get_recipe_by_id(recipe_id)
        if not recipe:
            await self._show_error(update, context, "Рецепт не найден")
            return
        
        name = recipe.get('name', 'Без названия')
        
        text = f"🗑️ *Подтверждение удаления*\n\nВы действительно хотите удалить рецепт «{name}»?"
        
        reply_markup = KeyboardFactory.get_confirmation_keyboard("delete", recipe_id, "recipes")
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=reply_markup
        )
        self.logger.info(f"Запрошено подтверждение удаления рецепта: {recipe_id}")
    
    async def _delete_recipe(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Удаляет рецепт"""
        recipe_id = params.get("id")
        if not recipe_id:
            await self._show_error(update, context, "ID рецепта не указан")
            return
        
        try:
            self.recipe_service.delete_recipe(recipe_id)
            
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="✅ Рецепт успешно удален!",
                reply_markup=KeyboardFactory.get("navigation")
            )
            self.logger.info(f"Рецепт удален: {recipe_id}")
        except Exception as e:
            await self._show_error(update, context, f"Ошибка при удалении: {e}")
    
    async def _show_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error_message: str) -> None:
        """Показывает сообщение об ошибке"""
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"❌ {error_message}",
            reply_markup=KeyboardFactory.get("navigation")
        )

# Глобальный экземпляр обработчика рецептов
recipe_handler = RecipeHandler() 