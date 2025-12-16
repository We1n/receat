"""
Унифицированный обработчик рецептов для EatBot
Обрабатывает все действия, связанные с рецептами, используя новую архитектуру роутера
"""
import logging
from typing import Dict, Any, Optional, List
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
    """Унифицированный обработчик всех действий с рецептами"""
    
    def __init__(self):
        self.recipe_service = RecipeService()
        self.logger = logging.getLogger(__name__)
    
    async def handle_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, params: Dict[str, Any]) -> None:
        """
        Обрабатывает действия с рецептами
        
        Args:
            update: Объект Update от Telegram
            context: Контекст выполнения
            action: Действие (menu, list, view, add, search, delete_confirm, add_confirm, edit, etc.)
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
        elif action == "search_results":
            await self._show_search_results(update, context, params)
        elif action == "delete_confirm":
            await self._confirm_recipe_delete(update, context, params)
        elif action == "delete":
            await self._delete_recipe(update, context, params)
        elif action == "edit":
            await self._start_recipe_edit(update, context, params)
        elif action == "edit_confirm":
            await self._handle_edit_confirm(update, context, params)
        elif action == "edit_name":
            await self._handle_edit_name(update, context, params)
        elif action == "edit_ingredients":
            await self._handle_edit_ingredients(update, context, params)
        elif action == "edit_instructions":
            await self._handle_edit_instructions(update, context, params)
        else:
            self.logger.warning(f"Неизвестное действие рецептов: {action}")
            await self._show_recipe_menu(update, context)
    
    async def _show_recipe_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает унифицированное меню рецептов"""
        recipes_text = Messages.get("RECIPES", {}).get("menu", "📚 Меню рецептов")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=recipes_text,
            reply_markup=KeyboardFactory.get("recipe_menu")
        )
        self.logger.info("Показано меню рецептов")
    
    async def _show_recipe_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Показывает список рецептов с унифицированной пагинацией"""
        page = int(params.get("page", 1))
        page_size = 5
        
        all_recipes = self.recipe_service.get_all_recipes()
        
        if not all_recipes:
            text = "📋 *Мои рецепты*\n\nУ вас пока нет сохраненных рецептов.\n\n💡 Добавьте свой первый рецепт!"
            reply_markup = KeyboardFactory.get("navigation")
        else:
            # Унифицированная пагинация
            total_pages = (len(all_recipes) + page_size - 1) // page_size
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_recipes = all_recipes[start_idx:end_idx]
            
            text = f"📋 *Мои рецепты* (страница {page}/{total_pages})\n\nВыберите рецепт для просмотра:"
            
            # Используем унифицированную клавиатуру с пагинацией
            reply_markup = KeyboardFactory.get_pagination_keyboard(
                section="recipes",
                action="list",
                current_page=page,
                total_pages=total_pages
            )
            
            # Добавляем кнопки рецептов
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
            
            # Добавляем пагинацию и навигацию
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
        """Показывает детальный вид рецепта с унифицированной клавиатурой"""
        recipe_id = params.get("id")
        if not recipe_id:
            await self._show_error(update, context, "ID рецепта не указан")
            return
        
        recipe = self.recipe_service.get_recipe_by_id(recipe_id)
        if not recipe:
            await self._show_error(update, context, "Рецепт не найден")
            return
        
        # Формируем унифицированный текст рецепта
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
        
        # Унифицированная клавиатура с действиями
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
        """Начинает процесс добавления рецепта с ConversationHandler"""
        if context.user_data is None:
            context.user_data = {}
        
        context.user_data['recipe_data'] = {'ingredients': [], 'tags': []}
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=Messages["CONVERSATION"]["recipe_add_start"],
            reply_markup=KeyboardFactory.get("navigation")
        )
        
        # Устанавливаем состояние для ConversationHandler
        context.user_data['state'] = RECIPE_ADD
        
        self.logger.info("Начато добавление рецепта")
    
    async def _handle_add_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка подтверждения добавления рецепта"""
        if context.user_data is None:
            context.user_data = {}
        
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
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления рецепта: {e}")
            await self._show_error(update, context, f"Ошибка при добавлении рецепта: {str(e)}")
    
    async def _start_recipe_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Начинает поиск рецептов"""
        search_text = Messages.get("RECIPES", {}).get("search", "🔍 Поиск рецептов")
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"{search_text}\n\nВведите название или ингредиенты для поиска:",
            reply_markup=KeyboardFactory.get("navigation")
        )
        
        # Устанавливаем состояние поиска
        if context.user_data is None:
            context.user_data = {}
        context.user_data['state'] = 'recipe_search'
        
        self.logger.info("Начат поиск рецептов")
    
    async def _show_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Показывает результаты поиска с унифицированной пагинацией"""
        query = params.get("query", "")
        page = int(params.get("page", 1))
        page_size = 5
        
        try:
            from src.services.recipe_search_service import RecipeSearchService
            recipe_search_service = RecipeSearchService(recipe_service=self.recipe_service)
            recipes, total = await recipe_search_service.search_recipes(query=query, page=page, per_page=page_size)
            
            if not recipes:
                text = f"🔍 По запросу '{query}' ничего не найдено.\n\n💡 Попробуйте:\n• Другие ингредиенты\n• Проверить написание\n• Более простые запросы"
                reply_markup = KeyboardFactory.get("navigation")
            else:
                text = f"🔍 *Результаты поиска:* '{query}'\n\nНайдено рецептов: {total}\nВыберите рецепт для просмотра:"
                
                keyboard = []
                for recipe in recipes:
                    recipe_id = recipe.get('id')
                    recipe_name = recipe.get('name', 'Без названия')
                    if recipe_id:
                        keyboard.append([
                            InlineKeyboardButton(
                                recipe_name, 
                                callback_data=CallbackDataBuilder.build("recipes", "view", id=recipe_id)
                            )
                        ])
                
                # Добавляем пагинацию если нужно
                total_pages = (total + page_size - 1) // page_size
                if total_pages > 1:
                    keyboard.append([
                        InlineKeyboardButton(
                            "◀️", 
                            callback_data=CallbackDataBuilder.build("recipes", "search_results", page=page-1, query=query)
                        ) if page > 1 else InlineKeyboardButton(" ", callback_data="no_action"),
                        InlineKeyboardButton(f"{page}/{total_pages}", callback_data="no_action"),
                        InlineKeyboardButton(
                            "▶️", 
                            callback_data=CallbackDataBuilder.build("recipes", "search_results", page=page+1, query=query)
                        ) if page < total_pages else InlineKeyboardButton(" ", callback_data="no_action")
                    ])
                
                keyboard.extend(KeyboardFactory._get_navigation_row())
                reply_markup = InlineKeyboardMarkup(keyboard)
            
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=text,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска рецептов: {e}")
            await self._show_error(update, context, "Произошла ошибка при поиске рецептов")
    
    async def _confirm_recipe_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Подтверждение удаления рецепта с унифицированной клавиатурой"""
        recipe_id = params.get("id")
        if not recipe_id:
            await self._show_error(update, context, "ID рецепта не указан")
            return
        
        recipe = self.recipe_service.get_recipe_by_id(recipe_id)
        if not recipe:
            await self._show_error(update, context, "Рецепт не найден")
            return
        
        recipe_name = recipe.get('name', 'Без названия')
        delete_text = Messages.get("RECIPES", {}).get("delete_confirm", "🗑️ Подтверждение удаления")
        
        text = f"{delete_text}\n\nВы действительно хотите удалить рецепт «{recipe_name}»?\n\n⚠️ Это действие необратимо!"
        
        # Используем унифицированную клавиатуру подтверждения
        reply_markup = KeyboardFactory.get_confirmation_keyboard(
            action="delete",
            entity_id=recipe_id,
            section="recipes"
        )
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=reply_markup
        )
        self.logger.info(f"Запрошено подтверждение удаления рецепта: {recipe_id}")
    
    async def _delete_recipe(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Удаление рецепта"""
        recipe_id = params.get("id")
        if not recipe_id:
            await self._show_error(update, context, "ID рецепта не указан")
            return
        
        recipe = self.recipe_service.get_recipe_by_id(recipe_id)
        if not recipe:
            await self._show_error(update, context, "Рецепт не найден")
            return
        
        recipe_name = recipe.get('name', 'Без названия')
        
        try:
            self.recipe_service.delete_recipe(recipe_id)
            
            delete_success_text = Messages.get("RECIPES", {}).get("delete_success", "✅ Рецепт удален!")
            text = f"{delete_success_text}\n\nРецепт «{recipe_name}» успешно удален."
            
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=text,
                reply_markup=KeyboardFactory.get("navigation")
            )
            
            self.logger.info(f"Рецепт успешно удален: {recipe_id}")
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления рецепта: {e}")
            await self._show_error(update, context, f"Ошибка при удалении рецепта: {str(e)}")
    
    async def _start_recipe_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Начинает редактирование рецепта"""
        recipe_id = params.get("id")
        if not recipe_id:
            await self._show_error(update, context, "ID рецепта не указан")
            return
        
        recipe = self.recipe_service.get_recipe_by_id(recipe_id)
        if not recipe:
            await self._show_error(update, context, "Рецепт не найден")
            return
        
        # Сохраняем данные для редактирования
        if context.user_data is None:
            context.user_data = {}
        context.user_data['editing_recipe'] = recipe
        context.user_data['editing_recipe_id'] = recipe_id
        
        text = f"✏️ *Редактирование рецепта*\n\nРецепт: {recipe.get('name', 'Без названия')}\n\nВыберите, что хотите изменить:"
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "📝 Название", 
                    callback_data=CallbackDataBuilder.build("recipes", "edit_name", id=recipe_id)
                ),
                InlineKeyboardButton(
                    "🥗 Ингредиенты", 
                    callback_data=CallbackDataBuilder.build("recipes", "edit_ingredients", id=recipe_id)
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 Инструкции", 
                    callback_data=CallbackDataBuilder.build("recipes", "edit_instructions", id=recipe_id)
                )
            ]
        ]
        
        keyboard.extend(KeyboardFactory._get_navigation_row())
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=reply_markup
        )
        self.logger.info(f"Начато редактирование рецепта: {recipe_id}")
    
    async def _handle_edit_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Обработка подтверждения редактирования рецепта"""
        if context.user_data is None:
            context.user_data = {}
        
        editing_recipe = context.user_data.get('editing_recipe')
        editing_recipe_id = context.user_data.get('editing_recipe_id')
        
        if not editing_recipe or not editing_recipe_id:
            await self._show_error(update, context, "Данные для редактирования не найдены")
            return
        
        # Получаем обновленные данные
        updated_data = context.user_data.get('updated_recipe_data', {})
        
        try:
            # Обновляем рецепт
            if updated_data:
                # Обновляем только измененные поля
                for key, value in updated_data.items():
                    if value is not None:
                        editing_recipe[key] = value
                
                # Сохраняем обновленный рецепт
                self.recipe_service.update_recipe(editing_recipe_id, editing_recipe)
                
                recipe_name = editing_recipe.get('name', 'Без названия')
                text = f"✅ Рецепт «{recipe_name}» успешно обновлен!"
                
                self.logger.info(f"Рецепт успешно обновлен: {editing_recipe_id}")
            else:
                text = "ℹ️ Изменения не были внесены"
            
            # Очищаем данные редактирования
            context.user_data.pop('editing_recipe', None)
            context.user_data.pop('editing_recipe_id', None)
            context.user_data.pop('updated_recipe_data', None)
            
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=text,
                reply_markup=KeyboardFactory.get("navigation")
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления рецепта: {e}")
            await self._show_error(update, context, f"Ошибка при обновлении рецепта: {str(e)}")
    
    async def _handle_edit_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Обработка редактирования названия рецепта"""
        recipe_id = params.get("id")
        if not recipe_id:
            await self._show_error(update, context, "ID рецепта не указан")
            return
        
        # Устанавливаем состояние редактирования названия
        if context.user_data is None:
            context.user_data = {}
        context.user_data['editing_field'] = 'name'
        context.user_data['editing_recipe_id'] = recipe_id
        context.user_data['state'] = 'editing_recipe_name'  # Устанавливаем состояние для text_message_handler
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="📝 Введите новое название рецепта:\n\n💡 **Советы:**\n• Используйте понятные названия\n• Минимум 3 символа\n• Избегайте специальных символов",
            reply_markup=KeyboardFactory.get("recipe_edit_field")
        )
        
        self.logger.info(f"Начато редактирование названия рецепта: {recipe_id}")
    
    async def _handle_edit_ingredients(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Обработка редактирования ингредиентов рецепта"""
        recipe_id = params.get("id")
        if not recipe_id:
            await self._show_error(update, context, "ID рецепта не указан")
            return
        
        # Устанавливаем состояние редактирования ингредиентов
        if context.user_data is None:
            context.user_data = {}
        context.user_data['editing_field'] = 'ingredients'
        context.user_data['editing_recipe_id'] = recipe_id
        context.user_data['state'] = 'editing_recipe_ingredients'  # Устанавливаем состояние для text_message_handler
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="🥗 Введите новые ингредиенты:\n\n💡 **Формат:**\n• По одному ингредиенту на строку\n• Можно указать количество и единицы\n\n**Пример:**\n• Мука 200г\n• Яйца 2шт\n• Сахар 100г",
            reply_markup=KeyboardFactory.get("recipe_edit_field")
        )
        
        self.logger.info(f"Начато редактирование ингредиентов рецепта: {recipe_id}")
    
    async def _handle_edit_instructions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Обработка редактирования инструкций рецепта"""
        recipe_id = params.get("id")
        if not recipe_id:
            await self._show_error(update, context, "ID рецепта не указан")
            return
        
        # Устанавливаем состояние редактирования инструкций
        if context.user_data is None:
            context.user_data = {}
        context.user_data['editing_field'] = 'instructions'
        context.user_data['editing_recipe_id'] = recipe_id
        context.user_data['state'] = 'editing_recipe_instructions'  # Устанавливаем состояние для text_message_handler
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="📋 Введите новые инструкции:\n\n💡 **Советы:**\n• Опишите процесс пошагово\n• Укажите время приготовления\n• Добавьте важные нюансы",
            reply_markup=KeyboardFactory.get("recipe_edit_field")
        )
        
        self.logger.info(f"Начато редактирование инструкций рецепта: {recipe_id}")
    
    async def _show_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error_message: str) -> None:
        """Показывает унифицированное сообщение об ошибке"""
        error_text = Messages.get("ERRORS", {}).get("not_found", "❌ Ошибка")
        text = f"{error_text}\n\n{error_message}"
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=KeyboardFactory.get("navigation")
        )
        self.logger.warning(f"Показана ошибка: {error_message}")

# Глобальный экземпляр унифицированного обработчика рецептов
recipe_handler = RecipeHandler() 