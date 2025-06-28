"""
Обработчики для совместной работы (LEGACY - обновлено в новой архитектуре)
"""
import logging
from typing import Dict, Any, List
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
)

from src.ui.keyboards.factory import KeyboardFactory
from src.ui.ui_service import ui_service
from src.ui.messages_main import Messages
from src.services.data_service import DataService
from src.validators.input_handler import input_handler, handle_input_errors
from src.validators.schemas import ValidationErrorResponse

logger = logging.getLogger(__name__)

# LEGACY: Все обработчики колбэков удалены
# Теперь все колбэки обрабатываются через единый роутер в main_callback_router.py

def show_collaborative_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню совместной работы (LEGACY - больше не используется)"""
    logger.warning("show_collaborative_menu is deprecated. Use new architecture instead.")
    pass

def handle_share_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка шаринга рецепта (LEGACY - больше не используется)"""
    logger.warning("handle_share_recipe is deprecated. Use new architecture instead.")
    pass

def handle_share_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка шаринга продукта (LEGACY - больше не используется)"""
    logger.warning("handle_share_product is deprecated. Use new architecture instead.")
    pass

def handle_share_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка шаринга меню (LEGACY - больше не используется)"""
    logger.warning("handle_share_menu is deprecated. Use new architecture instead.")
    pass

def setup_collaborative_handlers(application: Application, data_service: DataService, callback_handler):
    """Настройка обработчиков совместной работы (LEGACY - больше не используется)"""
    logger.warning("setup_collaborative_handlers is deprecated. Use new architecture instead.")
    
    # LEGACY: Все CallbackQueryHandler удалены
    # Теперь все колбэки обрабатываются через единый роутер в main_callback_router.py
    
    logger.info("LEGACY: setup_collaborative_handlers completed (deprecated)")
