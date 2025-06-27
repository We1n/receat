"""
Обработчики для работы с нутриентами (адаптация под telegram.ext, полный функционал)
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
)
from src.ui.keyboards import KeyboardFactory
from src.ui.ui_service import ui_service
from src.validators.input_handler import InputHandler
from src.validators.schemas import NutrientSearchDTO, NutrientCalculatorDTO
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
(
    WAITING_FOR_SEARCH,
    WAITING_FOR_AMOUNT,
    WAITING_FOR_PERIOD,
    WAITING_FOR_PRODUCT,
    WAITING_FOR_QUANTITY
) = range(5)

# Инициализация обработчика ввода
input_handler = InputHandler()

# Регистрация обработчиков

def register_nutrient_handlers(application):
    application.add_handler(CommandHandler("nutrients", show_nutrients_menu))
    application.add_handler(ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_nutrient_search, pattern="^nutrient_search$"),
            CallbackQueryHandler(show_nutrient_reference, pattern="^nutrient_reference$")
        ],
        states={
            WAITING_FOR_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_nutrient_search)],
            WAITING_FOR_PRODUCT: [CallbackQueryHandler(process_product_selection, pattern="^product_.*")],
            WAITING_FOR_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_quantity)],
        },
        fallbacks=[CallbackQueryHandler(show_nutrients_menu, pattern="^back$")],
        allow_reentry=True,
        per_message=False
    ))

# Меню нутриентов
async def show_nutrients_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text="🍎 *Меню нутриентов*\n\nВыберите действие:",
        reply_markup=KeyboardFactory.get("nutrient_menu")
    )
    logger.info("Показано меню нутриентов")

# Поиск нутриентов
async def start_nutrient_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        logger.error("Нет callback_query в start_nutrient_search")
        return
    await query.answer()
    
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text="🔍 *Поиск нутриентов*\n\nВведите название нутриента или его часть.\nНапример: белок, витамин C, железо",
        reply_markup=KeyboardFactory.get("back")
    )
    
    if context.user_data is not None:
        context.user_data["state"] = WAITING_FOR_SEARCH
    logger.info("Пользователь начал поиск нутриентов")

async def process_nutrient_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик поиска нутриентов с валидацией через InputHandler"""
    try:
        # Валидация входящих данных через InputHandler
        validation_result = await input_handler.validate_text_input(
            update, 
            NutrientSearchDTO, 
            "nutrient_search",
            context
        )
        
        if not validation_result.is_valid:
            return
        
        search_data = validation_result.data
        query = search_data.query
        
        if not query:
            text = (
                "❌ *Нутриенты не найдены*\n\n"
                "Пожалуйста, введите название нутриента или его часть."
            )
        else:
            text = "🔍 *Результаты поиска:*\n\n"
            # TODO: интеграция с сервисом поиска нутриентов
            text += f"Поиск по запросу: '{query}'\n\n"
            text += "🔧 Функция поиска нутриентов находится в разработке."
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=KeyboardFactory.get("back")
        )
        logger.info(f"Результаты поиска нутриентов отправлены для запроса: {query}")
        
    except Exception as e:
        await input_handler.handle_validation_error(
            update, 
            context, 
            f"Ошибка при поиске нутриентов: {str(e)}",
            "back"
        )
        logger.exception("Ошибка при поиске нутриентов")

async def show_nutrient_reference(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        logger.error("Нет callback_query в show_nutrient_reference")
        return
    await query.answer()
    
    try:
        nutrients_path = Path('data/nutrients.json')
        faq_path = Path('data/nutrition_faq.md')
        nutrients = []
        faq = ''
        if nutrients_path.exists():
            with open(nutrients_path, encoding='utf-8') as f:
                nutrients = json.load(f)
        if faq_path.exists():
            with open(faq_path, encoding='utf-8') as f:
                faq = f.read()
        text = '📚 *Справочник по нутриентам*\n\n'
        if nutrients:
            text += 'Основные нутриенты:\n'
            for n in nutrients:
                text += f"• {n.get('name', 'Без названия')} — {n.get('description', '')}\n"
            text += '\n'
        if faq:
            text += '❓ *FAQ по питанию*\n' + faq[:2000]  # Ограничение на размер сообщения
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text
        )
        logger.info("Пользователь открыл справочник по нутриентам")
    except Exception as e:
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"❌ Ошибка при загрузке справочника: {e}"
        )
        logger.error(f"Ошибка при загрузке справочника по нутриентам: {e}")

async def process_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not hasattr(query, 'data') or not query.data:
        logger.error("Нет данных в callback_query для process_product_selection")
        return
    await query.answer()
    product_id = int(query.data.split("_")[1])
    if context.user_data is not None:
        context.user_data["product_id"] = product_id
    
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text="🧮 *Калькулятор нутриентов*\n\nВведите количество в граммах:",
        reply_markup=KeyboardFactory.get("back")
    )
    
    if context.user_data is not None:
        context.user_data["state"] = WAITING_FOR_QUANTITY
    logger.info(f"Пользователь выбрал продукт: {product_id}")

async def process_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода количества с валидацией через InputHandler"""
    try:
        # Валидация входящих данных через InputHandler
        validation_result = await input_handler.validate_text_input(
            update, 
            NutrientCalculatorDTO, 
            "nutrient_calculator",
            context
        )
        
        if not validation_result.is_valid:
            return
        
        calculator_data = validation_result.data
        amount = calculator_data.amount
        product_id = context.user_data.get("product_id") if context.user_data else None
        
        if not product_id:
            await input_handler.handle_validation_error(
                update, 
                context, 
                "ID продукта не найден в калькуляторе нутриентов",
                "back"
            )
            return
        
        # TODO: получить продукт по product_id и рассчитать нутриенты
        text = f"🧮 *Результаты расчета нутриентов*\n\n"
        text += f"Продукт ID: {product_id}\n"
        text += f"Количество: {amount} г\n\n"
        text += "🔧 Функция расчета нутриентов находится в разработке."
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=KeyboardFactory.get("back")
        )
        logger.info(f"Пользователь ввел количество: {amount} для продукта {product_id}")
        
        if context.user_data is not None:
            context.user_data.clear()
            
    except Exception as e:
        await input_handler.handle_validation_error(
            update, 
            context, 
            f"Ошибка при вводе количества: {str(e)}",
            "back"
        )
        logger.exception("Ошибка при вводе количества") 