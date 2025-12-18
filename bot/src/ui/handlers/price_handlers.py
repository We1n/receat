"""
Обработчики для работы с ценами на продукты
"""
import logging
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters, CommandHandler

from src.ui.keyboards.factory import KeyboardFactory, CallbackDataBuilder
from src.ui.ui_service import ui_service
from src.services.price_service import PriceService
from src.utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

# Состояния для добавления цены
PRICE_PRODUCT, PRICE_STORE, PRICE_VALUE = range(3)

class PriceHandler:
    """Обработчик для работы с ценами"""
    
    def __init__(self):
        self.price_service = PriceService()
        self.logger = logging.getLogger(__name__)
    
    async def handle_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, params: Dict[str, Any]) -> None:
        """Обработка действий с ценами"""
        self.logger.info(f"Обработка действия цен: {action}")
        
        if action == "set":
            await self.start_price_add(update, context)
        elif action == "view":
            product_name = params.get("product")
            if product_name:
                await self.show_product_price(update, context, product_name)
            else:
                await self.show_price_menu(update, context)
        elif action == "list":
            await self.show_all_prices(update, context)
        else:
            await self.show_price_menu(update, context)
    
    async def show_price_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает меню работы с ценами"""
        text = (
            "💰 *Управление ценами*\n\n"
            "Выберите действие:\n"
            "• /setprice - Установить цену\n"
            "• /price <продукт> - Посмотреть цену\n"
            "• /prices - Список всех цен"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Установить цену", callback_data=CallbackDataBuilder.build("prices", "set")),
                InlineKeyboardButton("👁️ Посмотреть цену", callback_data=CallbackDataBuilder.build("prices", "view"))
            ],
            [
                InlineKeyboardButton("📋 Список цен", callback_data=CallbackDataBuilder.build("prices", "list"))
            ],
            KeyboardFactory._get_navigation_row()[0]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def start_price_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало диалога добавления цены"""
        query = update.callback_query
        if query:
            await query.answer()
        
        if context.user_data is None:
            context.user_data = {}
        
        context.user_data['price_data'] = {}
        
        text = (
            "💰 *Установка цены на продукт*\n\n"
            "Введите название продукта:"
        )
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=KeyboardFactory.get("navigation"),
            parse_mode="Markdown"
        )
        
        self.logger.info("Начато добавление цены")
        return PRICE_PRODUCT
    
    async def handle_price_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода названия продукта"""
        if not update.message or not update.message.text:
            await self._show_error(update, context, "Пожалуйста, введите название продукта")
            return PRICE_PRODUCT
        
        product_name = update.message.text.strip()
        
        if len(product_name) < 2:
            await self._show_error(update, context, "Название продукта слишком короткое. Попробуйте ещё раз:")
            return PRICE_PRODUCT
        
        if context.user_data is None:
            context.user_data = {}
        
        context.user_data.setdefault('price_data', {})['product_name'] = product_name
        
        # Показываем список магазинов для выбора
        stores = self.price_service.get_stores()
        if not stores:
            await self._show_error(update, context, "Магазины не настроены. Обратитесь к администратору.")
            return ConversationHandler.END
        
        keyboard = []
        for store in stores:
            keyboard.append([
                InlineKeyboardButton(
                    f"🏪 {store['name']}",
                    callback_data=CallbackDataBuilder.build("prices", "select_store", {"store_id": store['id']})
                )
            ])
        
        keyboard.append(KeyboardFactory._get_navigation_row()[0])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            f"✅ Продукт: *{product_name}*\n\n"
            "Выберите магазин:"
        )
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        self.logger.info(f"Выбран продукт для цены: {product_name}")
        return PRICE_STORE
    
    async def handle_price_store(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора магазина"""
        query = update.callback_query
        if not query:
            return PRICE_STORE
        
        await query.answer()
        
        if context.user_data is None:
            context.user_data = {}
        
        # Парсим callback_data
        from src.ui.handlers.main_callback_router import CallbackDataParser
        callback_data = query.data
        if not callback_data:
            await self._show_error(update, context, "Ошибка выбора магазина")
            return PRICE_STORE
        
        section, action, params = CallbackDataParser.parse(callback_data)
        
        # Проверяем, что это правильный callback
        if section != "prices" or action != "select_store":
            # Если это не наш callback, пропускаем его
            return PRICE_STORE
        
        store_id = params.get("store_id")
        if not store_id:
            await self._show_error(update, context, "Магазин не выбран")
            return PRICE_STORE
        
        store_info = self.price_service.get_store_info(store_id)
        if not store_info:
            await self._show_error(update, context, "Магазин не найден")
            return PRICE_STORE
        
        context.user_data.setdefault('price_data', {})['store_id'] = store_id
        context.user_data['price_data']['store_name'] = store_info.get('name', store_id)
        
        product_name = context.user_data['price_data'].get('product_name', '')
        
        text = (
            f"✅ Продукт: *{product_name}*\n"
            f"🏪 Магазин: *{store_info['name']}*\n\n"
            "Введите цену (только число, например: 50.5):"
        )
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=KeyboardFactory.get("navigation"),
            parse_mode="Markdown"
        )
        
        self.logger.info(f"Выбран магазин: {store_info['name']}")
        return PRICE_VALUE
    
    async def handle_price_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода цены"""
        if not update.message or not update.message.text:
            await self._show_error(update, context, "Пожалуйста, введите цену")
            return PRICE_VALUE
        
        try:
            price = float(update.message.text.strip().replace(',', '.'))
            if price <= 0:
                raise ValueError("Цена должна быть положительным числом")
        except ValueError as e:
            await self._show_error(update, context, f"Неверный формат цены. Введите число (например: 50.5):\n{str(e)}")
            return PRICE_VALUE
        
        if context.user_data is None:
            context.user_data = {}
        
        price_data = context.user_data.get('price_data', {})
        product_name = price_data.get('product_name')
        store_id = price_data.get('store_id')
        store_name = price_data.get('store_name', '')
        
        if not product_name or not store_id:
            await self._show_error(update, context, "Ошибка: данные не сохранены. Начните заново.")
            return ConversationHandler.END
        
        # Устанавливаем цену
        self.price_service.set_price(product_name, price, store_id)
        
        # Получаем информацию о лучшей цене
        best_price_info = self.price_service.get_best_price(product_name)
        
        text = (
            f"✅ *Цена установлена!*\n\n"
            f"🍏 Продукт: *{product_name}*\n"
            f"🏪 Магазин: *{store_name}*\n"
            f"💰 Цена: *{price:.2f} ₽*\n\n"
        )
        
        if best_price_info and best_price_info.get('price') == price:
            text += f"🎯 *Это лучшая цена!*"
        elif best_price_info:
            text += (
                f"💡 Лучшая цена: *{best_price_info['price']:.2f} ₽* "
                f"в *{best_price_info.get('store_name', 'другом магазине')}*"
            )
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=KeyboardFactory.get("navigation"),
            parse_mode="Markdown"
        )
        
        # Очищаем данные
        context.user_data.pop('price_data', None)
        context.user_data['state'] = None
        
        self.logger.info(f"Цена установлена: {product_name} - {price} ₽ в {store_name}")
        return ConversationHandler.END
    
    async def show_product_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE, product_name: str) -> None:
        """Показывает цену продукта"""
        price_info = self.price_service.get_price(product_name)
        
        if not price_info:
            text = f"❌ Цена на *{product_name}* не найдена.\n\nИспользуйте /setprice для установки цены."
        else:
            best_price = price_info.get('price')
            store_name = price_info.get('store_name', 'неизвестный магазин')
            
            text = (
                f"💰 *Цена на {product_name}*\n\n"
                f"🎯 Лучшая цена: *{best_price:.2f} ₽*\n"
                f"🏪 Магазин: *{store_name}*\n\n"
            )
            
            # Показываем все цены по магазинам
            all_prices = self.price_service.get_all_store_prices(product_name)
            if len(all_prices) > 1:
                text += "*Все цены:*\n"
                for store_id, store_price_data in all_prices.items():
                    store_name_item = store_price_data.get('store_name', store_id)
                    price_item = store_price_data.get('price')
                    if price_item is not None:
                        marker = "🎯" if store_id == price_info.get('store_id') else "  "
                        text += f"{marker} {store_name_item}: {price_item:.2f} ₽\n"
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=KeyboardFactory.get("navigation"),
            parse_mode="Markdown"
        )
    
    async def show_all_prices(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает список всех цен"""
        all_prices = self.price_service.get_all_prices()
        
        if not all_prices:
            text = "📋 *Список цен пуст*\n\nИспользуйте /setprice для добавления цен."
        else:
            text = "📋 *Все цены:*\n\n"
            count = 0
            for product_name, price_data in list(all_prices.items())[:20]:  # Ограничиваем 20 продуктами
                best_price = price_data.get('best_price')
                best_store = price_data.get('best_store')
                if best_price is not None and best_store:
                    store_info = self.price_service.get_store_info(best_store)
                    store_name = store_info.get('name', best_store) if store_info else best_store
                    text += f"• *{product_name}*: {best_price:.2f} ₽ ({store_name})\n"
                    count += 1
            
            if len(all_prices) > 20:
                text += f"\n... и ещё {len(all_prices) - 20} продуктов"
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=KeyboardFactory.get("navigation"),
            parse_mode="Markdown"
        )
    
    async def _show_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error_message: str) -> None:
        """Показывает сообщение об ошибке"""
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"❌ {error_message}",
            reply_markup=KeyboardFactory.get("navigation")
        )
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена диалога"""
        query = update.callback_query
        if query:
            await query.answer()
        
        if context.user_data is None:
            context.user_data = {}
        
        context.user_data.pop('price_data', None)
        context.user_data['state'] = None
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Установка цены отменена",
            reply_markup=KeyboardFactory.get("navigation")
        )
        
        self.logger.info("Установка цены отменена")
        return ConversationHandler.END

# Глобальный экземпляр
price_handler = PriceHandler()

def create_price_conversation_handler() -> ConversationHandler:
    """Создает ConversationHandler для установки цены"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                price_handler.start_price_add,
                pattern=CallbackDataBuilder.build("prices", "set")
            ),
            CommandHandler("setprice", price_handler.start_price_add)
        ],
        states={
            PRICE_PRODUCT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    price_handler.handle_price_product
                )
            ],
            PRICE_STORE: [
                CallbackQueryHandler(
                    price_handler.handle_price_store
                )
            ],
            PRICE_VALUE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    price_handler.handle_price_value
                )
            ],
        },
        fallbacks=[
            CallbackQueryHandler(
                price_handler.cancel_conversation,
                pattern=CallbackDataBuilder.build("nav", "back")
            ),
            CallbackQueryHandler(
                price_handler.cancel_conversation,
                pattern=CallbackDataBuilder.build("nav", "main_menu")
            ),
            CommandHandler("cancel", price_handler.cancel_conversation)
        ],
        allow_reentry=True
    )

# Команды для работы с ценами
@ErrorHandler.handle_errors
async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /price <продукт> - показать цену продукта"""
    if not update.message or not update.effective_user:
        return
    
    args = context.args
    if args:
        product_name = " ".join(args)
        await price_handler.show_product_price(update, context, product_name)
    else:
        await price_handler.show_price_menu(update, context)

@ErrorHandler.handle_errors
async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /prices - показать все цены"""
    if not update.message:
        return
    await price_handler.show_all_prices(update, context)

