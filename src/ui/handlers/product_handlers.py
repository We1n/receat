"""
Унифицированный обработчик продуктов для EatBot
Обрабатывает все действия, связанные с продуктами, используя новую архитектуру роутера
"""
import logging
from typing import Dict, Any, Optional, List
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from src.ui.keyboards.factory import KeyboardFactory, CallbackDataBuilder
from src.ui.ui_service import ui_service
from src.ui.messages_main import Messages as RawMessages
from src.services.product_service import ProductService
from src.config.states import PRODUCT_ADD

# Правильная типизация Messages
Messages: Dict[str, Any] = RawMessages

logger = logging.getLogger(__name__)

class ProductHandler:
    """Унифицированный обработчик всех действий с продуктами"""
    
    def __init__(self):
        self.product_service = ProductService()
        self.logger = logging.getLogger(__name__)
    
    async def handle_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, params: Dict[str, Any]) -> None:
        """
        Обрабатывает действия с продуктами
        
        Args:
            update: Объект Update от Telegram
            context: Контекст выполнения
            action: Действие (menu, list, view, add, search, delete_confirm, add_confirm, edit, etc.)
            params: Параметры действия
        """
        self.logger.info(f"Обработка действия продуктов: {action}")
        
        if action == "menu":
            await self._show_product_menu(update, context)
        elif action == "list":
            await self._show_product_list(update, context, params)
        elif action == "view":
            await self._show_product_view(update, context, params)
        elif action == "add":
            await self._start_product_add(update, context)
        elif action == "add_confirm":
            await self._handle_add_confirm(update, context)
        elif action == "search":
            await self._start_product_search(update, context)
        elif action == "search_results":
            await self._show_search_results(update, context, params)
        elif action == "delete_confirm":
            await self._confirm_product_delete(update, context, params)
        elif action == "delete":
            await self._delete_product(update, context, params)
        elif action == "edit":
            await self._start_product_edit(update, context, params)
        elif action == "edit_confirm":
            await self._handle_edit_confirm(update, context, params)
        elif action == "edit_name":
            await self._handle_edit_name(update, context, params)
        elif action == "edit_category":
            await self._handle_edit_category(update, context, params)
        elif action == "edit_nutrition":
            await self._handle_edit_nutrition(update, context, params)
        else:
            self.logger.warning(f"Неизвестное действие продуктов: {action}")
            await self._show_product_menu(update, context)
    
    async def _show_product_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает унифицированное меню продуктов"""
        products_text = Messages.get("PRODUCTS", {}).get("menu", "🍏 Меню продуктов")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=products_text,
            reply_markup=KeyboardFactory.get("product_menu")
        )
        self.logger.info("Показано меню продуктов")
    
    async def _show_product_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Показывает список продуктов с унифицированной пагинацией"""
        page = int(params.get("page", 1))
        page_size = 5
        
        all_products = self.product_service.get_all_products()
        
        if not all_products:
            text = "🍏 *Мои продукты*\n\nУ вас пока нет сохраненных продуктов.\n\n💡 Добавьте свой первый продукт!"
            reply_markup = KeyboardFactory.get("navigation")
        else:
            # Унифицированная пагинация
            total_pages = (len(all_products) + page_size - 1) // page_size
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_products = all_products[start_idx:end_idx]
            
            text = f"🍏 *Мои продукты* (страница {page}/{total_pages})\n\nВыберите продукт для просмотра:"
            
            # Используем унифицированную клавиатуру с пагинацией
            keyboard = []
            for product in page_products:
                product_id = product.get('id')
                product_name = product.get('name', 'Без названия')
                display_name = product_name[:30] + "..." if len(product_name) > 30 else product_name
                keyboard.append([
                    InlineKeyboardButton(
                        display_name, 
                        callback_data=CallbackDataBuilder.build("products", "view", id=product_id)
                    )
                ])
            
            # Добавляем пагинацию и навигацию
            if total_pages > 1:
                keyboard.append([
                    InlineKeyboardButton(
                        "◀️", 
                        callback_data=CallbackDataBuilder.build("products", "list", page=page-1)
                    ) if page > 1 else InlineKeyboardButton(" ", callback_data="no_action"),
                    InlineKeyboardButton(f"{page}/{total_pages}", callback_data="no_action"),
                    InlineKeyboardButton(
                        "▶️", 
                        callback_data=CallbackDataBuilder.build("products", "list", page=page+1)
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
        self.logger.info(f"Показан список продуктов (страница {page})")
    
    async def _show_product_view(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Показывает детальный вид продукта с унифицированной клавиатурой"""
        product_id = params.get("id")
        if not product_id:
            await self._show_error(update, context, "ID продукта не указан")
            return
        
        product = self.product_service.get_product_by_id(product_id)
        if not product:
            await self._show_error(update, context, "Продукт не найден")
            return
        
        # Формируем унифицированный текст продукта
        name = product.get('name', 'Без названия')
        category = product.get('category', 'Не указана')
        nutrition = product.get('nutrition', {})
        
        text = f"🍏 *{name}*\n\n"
        text += f"*Категория:* {category}\n\n"
        
        if nutrition:
            text += "*Пищевая ценность (на 100г):*\n"
            calories = nutrition.get('calories', 0)
            protein = nutrition.get('protein', 0)
            fat = nutrition.get('fat', 0)
            carbs = nutrition.get('carbs', 0)
            
            text += f"• Калории: {calories} ккал\n"
            text += f"• Белки: {protein}г\n"
            text += f"• Жиры: {fat}г\n"
            text += f"• Углеводы: {carbs}г\n"
        
        # Унифицированная клавиатура с действиями
        keyboard = [
            [
                InlineKeyboardButton(
                    "✏️ Редактировать", 
                    callback_data=CallbackDataBuilder.build("products", "edit", id=product_id)
                ),
                InlineKeyboardButton(
                    "🗑️ Удалить", 
                    callback_data=CallbackDataBuilder.build("products", "delete_confirm", id=product_id)
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
        self.logger.info(f"Показан продукт: {product_id}")
    
    async def _start_product_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Начинает процесс добавления продукта"""
        if context.user_data is None:
            context.user_data = {}
        
        context.user_data['product_data'] = {}
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="🍏 *Добавление нового продукта*\n\nВведите название продукта:",
            reply_markup=KeyboardFactory.get("navigation")
        )
        
        # Устанавливаем состояние для text_message_handler
        context.user_data['state'] = PRODUCT_ADD
        
        self.logger.info("Начато добавление продукта")
    
    async def _handle_add_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка подтверждения добавления продукта"""
        if context.user_data is None:
            context.user_data = {}
        
        product_data = context.user_data.get('product_data', {})
        name = product_data.get('name', '')
        
        try:
            self.product_service.add_product(name, product_data)
            
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=f"✅ Продукт «{name}» успешно добавлен!",
                reply_markup=KeyboardFactory.get("navigation")
            )
            
            # Очищаем данные
            context.user_data.pop('product_data', None)
            context.user_data['state'] = None
            
            self.logger.info(f"Продукт успешно добавлен: {name}")
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления продукта: {e}")
            await self._show_error(update, context, f"Ошибка при добавлении продукта: {str(e)}")
    
    async def _start_product_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Начинает поиск продуктов"""
        search_text = Messages.get("PRODUCTS", {}).get("search", "🔍 Поиск продуктов")
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"{search_text}\n\nВведите название продукта для поиска:",
            reply_markup=KeyboardFactory.get("navigation")
        )
        
        # Устанавливаем состояние поиска
        if context.user_data is None:
            context.user_data = {}
        context.user_data['state'] = 'product_search'
        
        self.logger.info("Начат поиск продуктов")
    
    async def _show_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Показывает результаты поиска с унифицированной пагинацией"""
        query = params.get("query", "")
        page = int(params.get("page", 1))
        page_size = 5
        
        try:
            from src.services.product_search_service import ProductSearchService
            product_search_service = ProductSearchService(product_service=self.product_service)
            products, total = await product_search_service.search_products(query=query, page=page, per_page=page_size)
            
            if not products:
                text = f"🍏 По запросу '{query}' ничего не найдено.\n\n💡 Попробуйте:\n• Другие названия\n• Проверить написание\n• Более простые запросы"
                reply_markup = KeyboardFactory.get("navigation")
            else:
                text = f"🍏 *Результаты поиска:* '{query}'\n\nНайдено продуктов: {total}\nВыберите продукт для просмотра:"
                
                keyboard = []
                for product in products:
                    product_id = product.get('id')
                    product_name = product.get('name', 'Без названия')
                    if product_id:
                        keyboard.append([
                            InlineKeyboardButton(
                                product_name, 
                                callback_data=CallbackDataBuilder.build("products", "view", id=product_id)
                            )
                        ])
                
                # Добавляем пагинацию если нужно
                total_pages = (total + page_size - 1) // page_size
                if total_pages > 1:
                    keyboard.append([
                        InlineKeyboardButton(
                            "◀️", 
                            callback_data=CallbackDataBuilder.build("products", "search_results", page=page-1, query=query)
                        ) if page > 1 else InlineKeyboardButton(" ", callback_data="no_action"),
                        InlineKeyboardButton(f"{page}/{total_pages}", callback_data="no_action"),
                        InlineKeyboardButton(
                            "▶️", 
                            callback_data=CallbackDataBuilder.build("products", "search_results", page=page+1, query=query)
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
            self.logger.error(f"Ошибка поиска продуктов: {e}")
            await self._show_error(update, context, "Произошла ошибка при поиске продуктов")
    
    async def _confirm_product_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Подтверждение удаления продукта с унифицированной клавиатурой"""
        product_id = params.get("id")
        if not product_id:
            await self._show_error(update, context, "ID продукта не указан")
            return
        
        product = self.product_service.get_product_by_id(product_id)
        if not product:
            await self._show_error(update, context, "Продукт не найден")
            return
        
        product_name = product.get('name', 'Без названия')
        delete_text = Messages.get("PRODUCTS", {}).get("delete_confirm", "🗑️ Подтверждение удаления")
        
        text = f"{delete_text}\n\nВы действительно хотите удалить продукт «{product_name}»?\n\n⚠️ Это действие необратимо!"
        
        # Используем унифицированную клавиатуру подтверждения
        reply_markup = KeyboardFactory.get_confirmation_keyboard(
            action="delete",
            entity_id=product_id,
            section="products"
        )
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=reply_markup
        )
        self.logger.info(f"Запрошено подтверждение удаления продукта: {product_id}")
    
    async def _delete_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Удаление продукта"""
        product_id = params.get("id")
        if not product_id:
            await self._show_error(update, context, "ID продукта не указан")
            return
        
        product = self.product_service.get_product_by_id(product_id)
        if not product:
            await self._show_error(update, context, "Продукт не найден")
            return
        
        product_name = product.get('name', 'Без названия')
        
        try:
            self.product_service.delete_product(product_id)
            
            delete_success_text = Messages.get("PRODUCTS", {}).get("delete_success", "✅ Продукт удален!")
            text = f"{delete_success_text}\n\nПродукт «{product_name}» успешно удален."
            
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=text,
                reply_markup=KeyboardFactory.get("navigation")
            )
            
            self.logger.info(f"Продукт успешно удален: {product_id}")
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления продукта: {e}")
            await self._show_error(update, context, f"Ошибка при удалении продукта: {str(e)}")
    
    async def _start_product_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Начинает редактирование продукта"""
        product_id = params.get("id")
        if not product_id:
            await self._show_error(update, context, "ID продукта не указан")
            return
        
        product = self.product_service.get_product_by_id(product_id)
        if not product:
            await self._show_error(update, context, "Продукт не найден")
            return
        
        # Сохраняем данные для редактирования
        if context.user_data is None:
            context.user_data = {}
        context.user_data['editing_product'] = product
        context.user_data['editing_product_id'] = product_id
        
        text = f"✏️ *Редактирование продукта*\n\nПродукт: {product.get('name', 'Без названия')}\n\nВыберите, что хотите изменить:"
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "📝 Название", 
                    callback_data=CallbackDataBuilder.build("products", "edit_name", id=product_id)
                ),
                InlineKeyboardButton(
                    "🏷️ Категория", 
                    callback_data=CallbackDataBuilder.build("products", "edit_category", id=product_id)
                )
            ],
            [
                InlineKeyboardButton(
                    "🥗 Пищевая ценность", 
                    callback_data=CallbackDataBuilder.build("products", "edit_nutrition", id=product_id)
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
        self.logger.info(f"Начато редактирование продукта: {product_id}")
    
    async def _handle_edit_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Обработка подтверждения редактирования продукта"""
        if context.user_data is None:
            context.user_data = {}
        
        editing_product = context.user_data.get('editing_product')
        editing_product_id = context.user_data.get('editing_product_id')
        
        if not editing_product or not editing_product_id:
            await self._show_error(update, context, "Данные для редактирования не найдены")
            return
        
        # Получаем обновленные данные
        updated_data = context.user_data.get('updated_product_data', {})
        
        try:
            # Обновляем продукт
            if updated_data:
                # Обновляем только измененные поля
                for key, value in updated_data.items():
                    if value is not None:
                        editing_product[key] = value
                
                # Сохраняем обновленный продукт
                self.product_service.update_product(editing_product_id, editing_product)
                
                product_name = editing_product.get('name', 'Без названия')
                text = f"✅ Продукт «{product_name}» успешно обновлен!"
                
                self.logger.info(f"Продукт успешно обновлен: {editing_product_id}")
            else:
                text = "ℹ️ Изменения не были внесены"
            
            # Очищаем данные редактирования
            context.user_data.pop('editing_product', None)
            context.user_data.pop('editing_product_id', None)
            context.user_data.pop('updated_product_data', None)
            
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=text,
                reply_markup=KeyboardFactory.get("navigation")
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления продукта: {e}")
            await self._show_error(update, context, f"Ошибка при обновлении продукта: {str(e)}")
    
    async def _handle_edit_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Обработка редактирования названия продукта"""
        product_id = params.get("id")
        if not product_id:
            await self._show_error(update, context, "ID продукта не указан")
            return
        
        # Устанавливаем состояние редактирования названия
        if context.user_data is None:
            context.user_data = {}
        context.user_data['editing_field'] = 'name'
        context.user_data['editing_product_id'] = product_id
        context.user_data['state'] = 'editing_product_name'
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="📝 Введите новое название продукта:\n\n💡 **Советы:**\n• Используйте понятные названия\n• Минимум 3 символа\n• Избегайте специальных символов",
            reply_markup=KeyboardFactory.get("product_edit_field")
        )
        
        self.logger.info(f"Начато редактирование названия продукта: {product_id}")
    
    async def _handle_edit_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Обработка редактирования категории продукта"""
        product_id = params.get("id")
        if not product_id:
            await self._show_error(update, context, "ID продукта не указан")
            return
        
        # Устанавливаем состояние редактирования категории
        if context.user_data is None:
            context.user_data = {}
        context.user_data['editing_field'] = 'category'
        context.user_data['editing_product_id'] = product_id
        context.user_data['state'] = 'editing_product_category'
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="🏷️ Введите новую категорию продукта:\n\n💡 **Примеры категорий:**\n• Фрукты\n• Овощи\n• Мясо\n• Рыба\n• Молочные продукты\n• Крупы\n• Орехи",
            reply_markup=KeyboardFactory.get("product_edit_field")
        )
        
        self.logger.info(f"Начато редактирование категории продукта: {product_id}")
    
    async def _handle_edit_nutrition(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Обработка редактирования пищевой ценности продукта"""
        product_id = params.get("id")
        if not product_id:
            await self._show_error(update, context, "ID продукта не указан")
            return
        
        # Устанавливаем состояние редактирования пищевой ценности
        if context.user_data is None:
            context.user_data = {}
        context.user_data['editing_field'] = 'nutrition'
        context.user_data['editing_product_id'] = product_id
        context.user_data['state'] = 'editing_product_nutrition'
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="🥗 Введите пищевую ценность (на 100г):\n\n💡 **Формат:**\nКалории: 100\nБелки: 5\nЖиры: 2\nУглеводы: 15\n\n**Пример:**\nКалории: 89\nБелки: 0.9\nЖиры: 0.2\nУглеводы: 23",
            reply_markup=KeyboardFactory.get("product_edit_field")
        )
        
        self.logger.info(f"Начато редактирование пищевой ценности продукта: {product_id}")
    
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

# Глобальный экземпляр унифицированного обработчика продуктов
product_handler = ProductHandler() 