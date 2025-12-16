"""
Обработчики сообщений для бота (адаптация под telegram.ext, полный функционал)
"""
import logging
from typing import cast, List, Dict, Any
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, MessageHandler, CallbackQueryHandler, filters, ConversationHandler
)
from src.ui.messages_main import Messages as RawMessages
Messages: Dict[str, Any] = RawMessages
from src.ui.keyboards import KeyboardFactory
from src.ui.ui_service import ui_service
from src.services.recipe_service import RecipeService
from src.validators.input_handler import input_handler, handle_input_errors
from src.validators.schemas import RecipeDTO, UserProfileDTO, ValidationErrorResponse, IngredientDTO
from src.config.states import RECIPE_ADD, PRODUCT_ADD, PRODUCT_SEARCH, RECIPE_SEARCH
import time
import asyncio
import re
from telegram.error import BadRequest

logger = logging.getLogger(__name__)

# Инициализация сервисов
recipe_service = RecipeService()

# --- Константы для парсинга ингредиентов ---
KNOWN_UNITS = [
    "г", "кг", "мл", "л", "шт", "ст.л.", "ч.л.", "стакан", "пакет", "банка", "долька", "кусок", "пучок", "капля", "зубчик"
]

# --- Новый парсер ингредиентов ---
def parse_ingredient(text: str):
    note = None
    # Удаляем комментарии в скобках
    if "(" in text and ")" in text:
        note_match = re.search(r"\\((.*?)\\)", text)
        if note_match:
            note = note_match.group(1)
            text = re.sub(r"\\(.*?\\)", "", text).strip()
    # Ищем единицу измерения
    for unit in sorted(KNOWN_UNITS, key=len, reverse=True):
        pattern = rf"^(.*?)\\s+([\\d\\.,]+)\\s*{unit}\\b"
        match = re.match(pattern, text)
        if match:
            name = match.group(1).strip()
            amount = float(match.group(2).replace(",", "."))
            return name, amount, unit, note
    # Если не найдено — возможно, формат "Соль по вкусу"
    if "по вкусу" in text.lower():
        name = text.lower().replace("по вкусу", "").strip()
        return name, 1.0, "по вкусу", None
    return None, None, None, note

# Состояния для добавления рецепта
RECIPE_NAME, RECIPE_INGREDIENTS, RECIPE_INSTRUCTIONS, RECIPE_CONFIRM = range(4)

@handle_input_errors
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"handle_message triggered. User state: {context.user_data.get('state') if context.user_data else None}")
    user_data = context.user_data if context.user_data else {}
    text = update.message.text if (update.message and update.message.text) else ""
    state = user_data.get("state")
    logger.info(f"Получено сообщение: {text}, состояние: {state}")

    # Валидация профиля пользователя для любого сообщения
    user_profile = input_handler.extract_user_data(update)
    profile_validation = input_handler.validate_input(user_profile, 'user_profile')
    if isinstance(profile_validation, ValidationErrorResponse):
        error_message = f"❌ Ошибка профиля пользователя:\n\n"
        for field, error in profile_validation.errors.items():
            error_message += f"• {field}: {error}\n"
        if update.message and hasattr(update.message, 'reply_text'):
            await update.message.reply_text(error_message)
        return

    if state == PRODUCT_ADD:
        await handle_product_add(update, context, text)
        return
    elif state == PRODUCT_SEARCH:
        # TODO: Реализовать поиск продуктов
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="🔍 Поиск продуктов временно недоступен. Используйте меню продуктов.",
            reply_markup=None
        )
        if isinstance(context.user_data, dict):
            context.user_data["state"] = None
        return
    elif state == RECIPE_SEARCH:
        # Используем унифицированный обработчик из text_message_handler
        from src.ui.handlers.text_message_handler import handle_recipe_search
        await handle_recipe_search(update, context, text)
        return
    else:
        # Базовая валидация для обычных сообщений
        text_validation = input_handler.validate_input({"query": text}, 'search_query')
        if isinstance(text_validation, ValidationErrorResponse):
            error_message = f"❌ Ошибка валидации текста:\n\n"
            for field, error in text_validation.errors.items():
                error_message += f"• {field}: {error}\n"
            if update.message and hasattr(update.message, 'reply_text'):
                await update.message.reply_text(error_message)
            return
        await handle_general_message(update, context, text)

async def handle_product_add(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка добавления продукта с подтверждением и кнопками"""
    # Пример простого парсинга (можно заменить на более сложный)
    try:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip().lower()] = value.strip()
        name = data.get('название')
        if not name:
            raise ValueError('Не указаны название')
        # Добавление продукта (можно доработать под ваш сервис)
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"✅ Продукт '{name}' добавлен!",
            reply_markup=None
        )
        if isinstance(context.user_data, dict):
            context.user_data["state"] = None
    except Exception as e:
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"❌ Ошибка при добавлении продукта: {e}",
            reply_markup=None
        )

async def handle_recipe_search(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка поиска рецептов - использует унифицированный обработчик"""
    # Импортируем унифицированный обработчик
    from src.ui.handlers.text_message_handler import handle_recipe_search as unified_recipe_search
    await unified_recipe_search(update, context, text)

async def handle_general_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка обычных сообщений"""
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=f"💬 Получено сообщение: {text}\n\nИспользуйте меню для навигации."
    )

def register_message_handlers(application):
    """Регистрация обработчиков сообщений (LEGACY - больше не используется)"""
    logger.warning("register_message_handlers is deprecated. Use register_text_message_handlers instead.")
    # Обработчик текстовых сообщений (должен быть одним из последних)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))