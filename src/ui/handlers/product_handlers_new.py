"""
Обработчик продуктов для EatBot
Обрабатывает все действия, связанные с продуктами, используя новую архитектуру роутера
"""
import logging
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from src.ui.keyboards.factory import KeyboardFactory, CallbackDataBuilder
from src.ui.ui_service import ui_service
from src.ui.messages_main import Messages as RawMessages
from src.services.product_service import ProductService

# Правильная типизация Messages
Messages: Dict[str, Any] = RawMessages

logger = logging.getLogger(__name__)

class ProductHandler:
    """Обработчик всех действий с продуктами"""
    
    def __init__(self):
        self.product_service = ProductService()
        self.logger = logging.getLogger(__name__)
    
    async def handle_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, params: Dict[str, Any]) -> None:
        """
        Обрабатывает действия с продуктами
        
        Args:
            update: Объект Update от Telegram
            context: Контекст выполнения
            action: Действие (menu, list, view, add, search, calculator, delete_confirm, etc.)
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
        elif action == "search":
            await self._start_product_search(update, context)
        elif action == "calculator":
            await self._start_calculator(update, context)
        elif action == "delete_confirm":
            await self._confirm_product_delete(update, context, params)
        elif action == "delete":
            await self._delete_product(update, context, params)
        else:
            self.logger.warning(f"Неизвестное действие продуктов: {action}")
            await self._show_product_menu(update, context)
    
    async def _show_product_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает меню продуктов"""
        products_text = Messages.get("PRODUCTS", {}).get("menu", "🍏 Меню продуктов")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=products_text,
            reply_markup=KeyboardFactory.get("products_menu")
        )
        self.logger.info("Показано меню продуктов")
    
    async def _show_product_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Показывает список продуктов с пагинацией"""
        page = int(params.get("page", 1))
        page_size = 5
        
        all_products = self.product_service.get_all_products()
        
        if not all_products:
            text = "📋 *Мои продукты*\n\nУ вас пока нет сохраненных продуктов."
            reply_markup = KeyboardFactory.get("navigation")
        else:
            # Пагинация
            total_pages = (len(all_products) + page_size - 1) // page_size
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_products = all_products[start_idx:end_idx]
            
            text = f"📋 *Мои продукты* (страница {page}/{total_pages})\n\nВыберите продукт для просмотра:"
            
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
            
            # Добавляем пагинацию если нужно
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
            
            # Добавляем навигационные кнопки
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
        """Показывает детальный вид продукта"""
        product_id = params.get("id")
        if not product_id:
            await self._show_error(update, context, "ID продукта не указан")
            return
        
        product = self.product_service.get_product_by_id(product_id)
        if not product:
            await self._show_error(update, context, "Продукт не найден")
            return
        
        # Формируем текст продукта
        name = product.get('name', 'Без названия')
        calories = product.get('calories', 0)
        protein = product.get('protein', 0)
        fat = product.get('fat', 0)
        carbs = product.get('carbs', 0)
        
        text = f"🍏 *{name}*\n\n"
        text += f"*Пищевая ценность на 100г:*\n"
        text += f"• Калории: {calories} ккал\n"
        text += f"• Белки: {protein}г\n"
        text += f"• Жиры: {fat}г\n"
        text += f"• Углеводы: {carbs}г"
        
        # Клавиатура с действиями
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
        
        # Добавляем навигационные кнопки
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
        add_text = Messages.get("PRODUCTS", {}).get("add", "➕ Добавление продукта")
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"{add_text}\n\nВведите информацию о продукте в формате:\n\n**Название:** [название продукта]\n**Калории:** [количество на 100г]\n**Белки:** [граммы на 100г]\n**Жиры:** [граммы на 100г]\n**Углеводы:** [граммы на 100г]",
            reply_markup=KeyboardFactory.get("navigation")
        )
        
        # Устанавливаем состояние добавления
        if context.user_data is None:
            context.user_data = {}
        context.user_data['state'] = 'product_add'
        
        self.logger.info("Начато добавление продукта")
    
    async def _start_product_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Начинает поиск продуктов"""
        search_text = Messages.get("PRODUCTS", {}).get("search", "🔍 Поиск продукта")
        
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
    
    async def _start_calculator(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Начинает калькулятор БЖУ"""
        calculator_text = Messages.get("PRODUCTS", {}).get("calculator", "🧮 Калькулятор БЖУ")
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"{calculator_text}\n\nВведите продукты и их количество:\n\n**Формат:**\n[название продукта] [количество]г\n\n💡 **Пример:**\nяблоко 150г\nкуриная грудка 200г\nовсянка 50г",
            reply_markup=KeyboardFactory.get("navigation")
        )
        
        # Устанавливаем состояние калькулятора
        if context.user_data is None:
            context.user_data = {}
        context.user_data['state'] = 'product_calculator'
        
        self.logger.info("Начат калькулятор БЖУ")
    
    async def _confirm_product_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Запрашивает подтверждение удаления продукта"""
        product_id = params.get("id")
        if not product_id:
            await self._show_error(update, context, "ID продукта не указан")
            return
        
        product = self.product_service.get_product_by_id(product_id)
        if not product:
            await self._show_error(update, context, "Продукт не найден")
            return
        
        name = product.get('name', 'Без названия')
        
        text = f"🗑️ *Подтверждение удаления*\n\nВы действительно хотите удалить продукт «{name}»?"
        
        reply_markup = KeyboardFactory.get_confirmation_keyboard("delete", product_id, "products")
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=reply_markup
        )
        self.logger.info(f"Запрошено подтверждение удаления продукта: {product_id}")
    
    async def _delete_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Удаляет продукт"""
        product_id = params.get("id")
        if not product_id:
            await self._show_error(update, context, "ID продукта не указан")
            return
        
        try:
            self.product_service.delete_product(product_id)
            
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="✅ Продукт успешно удален!",
                reply_markup=KeyboardFactory.get("navigation")
            )
            self.logger.info(f"Продукт удален: {product_id}")
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

# Глобальный экземпляр обработчика продуктов
product_handler = ProductHandler() 