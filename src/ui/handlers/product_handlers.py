"""
Обработчики для работы с продуктами (LEGACY - обновлено в product_handlers_new.py)
"""
import logging
from typing import Dict, Any, List
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
)

from src.ui.keyboards.factory import KeyboardFactory
from src.ui.ui_service import ui_service
from src.ui.messages_main import Messages
from src.services.product_service import ProductService
from src.validators.input_handler import input_handler, handle_input_errors
from src.validators.schemas import ProductDTO, ValidationErrorResponse

logger = logging.getLogger(__name__)

# Инициализация сервиса
product_service = ProductService()

# Состояния для добавления продукта
PRODUCT_NAME, PRODUCT_CALORIES, PRODUCT_PROTEIN, PRODUCT_FAT, PRODUCT_CARBS, PRODUCT_CONFIRM = range(6)

# LEGACY: Все обработчики колбэков удалены
# Теперь все колбэки обрабатываются через единый роутер в main_callback_router.py
# Новые обработчики находятся в product_handlers_new.py

def show_products_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню продуктов (LEGACY - больше не используется)"""
    logger.warning("show_products_menu is deprecated. Use product_handlers_new.py instead.")
    pass

def show_product_search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню поиска продуктов (LEGACY - больше не используется)"""
    logger.warning("show_product_search_menu is deprecated. Use product_handlers_new.py instead.")
    pass

def show_product_add_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню добавления продукта (LEGACY - больше не используется)"""
    logger.warning("show_product_add_menu is deprecated. Use product_handlers_new.py instead.")
    pass

def show_product_calculator_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню калькулятора продуктов (LEGACY - больше не используется)"""
    logger.warning("show_product_calculator_menu is deprecated. Use product_handlers_new.py instead.")
    pass

def product_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню редактирования продукта (LEGACY - больше не используется)"""
    logger.warning("product_edit_menu is deprecated. Use product_handlers_new.py instead.")
    pass

def product_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение удаления продукта (LEGACY - больше не используется)"""
    logger.warning("product_delete_confirm is deprecated. Use product_handlers_new.py instead.")
    pass

def product_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление продукта (LEGACY - больше не используется)"""
    logger.warning("product_delete is deprecated. Use product_handlers_new.py instead.")
    pass

def product_calculator_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавление продукта в калькулятор (LEGACY - больше не используется)"""
    logger.warning("product_calculator_add is deprecated. Use product_handlers_new.py instead.")
    pass

def product_nutrients_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр нутриентов продукта (LEGACY - больше не используется)"""
    logger.warning("product_nutrients_view is deprecated. Use product_handlers_new.py instead.")
    pass

def register_product_handlers(application: Application):
    """Регистрация обработчиков продуктов (LEGACY - больше не используется)"""
    logger.warning("register_product_handlers is deprecated. Use product_handlers_new.py instead.")
    
    # LEGACY: Все CallbackQueryHandler удалены
    # Теперь все колбэки обрабатываются через единый роутер в main_callback_router.py
    
    # ConversationHandler для добавления продукта (если нужен)
    # conv_handler = ConversationHandler(
    #     entry_points=[CallbackQueryHandler(show_product_add_menu, pattern="^product_add$")],
    #     states={
    #         PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_name)],
    #         PRODUCT_CALORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_calories)],
    #         PRODUCT_PROTEIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_protein)],
    #         PRODUCT_FAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_fat)],
    #         PRODUCT_CARBS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_carbs)],
    #         PRODUCT_CONFIRM: [CallbackQueryHandler(handle_product_confirm)]
    #     },
    #     fallbacks=[CallbackQueryHandler(show_products_menu, pattern="^products$")],
    #     allow_reentry=True
    # )
    # application.add_handler(conv_handler)
    
    logger.info("LEGACY: register_product_handlers completed (deprecated)") 