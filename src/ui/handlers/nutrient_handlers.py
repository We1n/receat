"""
Обработчики для работы с нутриентами (LEGACY - обновлено в новой архитектуре)
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
from src.services.nutrient_analysis import NutrientAnalysisService
from src.validators.input_handler import input_handler, handle_input_errors
from src.validators.schemas import NutrientCalculatorDTO, ValidationErrorResponse

logger = logging.getLogger(__name__)

# Инициализация сервиса
nutrient_analyzer = NutrientAnalysisService()

# LEGACY: Все обработчики колбэков удалены
# Теперь все колбэки обрабатываются через единый роутер в main_callback_router.py

def show_nutrient_calculator_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню калькулятора нутриентов (LEGACY - больше не используется)"""
    logger.warning("show_nutrient_calculator_menu is deprecated. Use new architecture instead.")
    pass

def handle_nutrient_calculation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка расчета нутриентов (LEGACY - больше не используется)"""
    logger.warning("handle_nutrient_calculation is deprecated. Use new architecture instead.")
    pass

def show_nutrient_analysis_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню анализа нутриентов (LEGACY - больше не используется)"""
    logger.warning("show_nutrient_analysis_menu is deprecated. Use new architecture instead.")
    pass

def handle_nutrient_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка анализа нутриентов (LEGACY - больше не используется)"""
    logger.warning("handle_nutrient_analysis is deprecated. Use new architecture instead.")
    pass

def register_nutrient_handlers(application: Application):
    """Регистрация обработчиков нутриентов (LEGACY - больше не используется)"""
    logger.warning("register_nutrient_handlers is deprecated. Use new architecture instead.")
    
    # LEGACY: Все CallbackQueryHandler удалены
    # Теперь все колбэки обрабатываются через единый роутер в main_callback_router.py
    
    logger.info("LEGACY: register_nutrient_handlers completed (deprecated)") 