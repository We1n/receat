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
from src.services.nutrient_analysis import NutrientAnalysisService
from src.services.recipe_service import RecipeService
from src.validators.input_handler import input_handler, handle_input_errors
from src.validators.schemas import RecipeDTO, UserProfileDTO, ValidationErrorResponse, IngredientDTO
from src.config.states import RECIPE_ADD, PRODUCT_ADD, PRODUCT_SEARCH, RECIPE_SEARCH, NUTRIENT_CALCULATOR
from src.services.pfc_calculator import calculate_from_text
from src.ui.handlers.product_handlers import handle_product_search as real_product_search
import time
import asyncio
import re
from telegram.error import BadRequest
from src.ui.handlers.recipe_actions_handler import (
    recipe_name_handler,
    recipe_ingredients_handler,
    recipe_instructions_handler,
    recipe_confirm_handler,
    recipe_view_callback
)

logger = logging.getLogger(__name__)

# Инициализация сервисов
nutrient_analyzer = NutrientAnalysisService()
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

def log_any_callback(update: Update):
    query = getattr(update, 'callback_query', None)
    if query and hasattr(query, 'data'):
        logger.info(f"[UNIVERSAL CALLBACK LOG] callback_query.data: {query.data}")

# Callback-меню
async def products_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.critical(f"[UNIVERSAL CALLBACK LOG] callback_query.data: {update.callback_query.data if hasattr(update, 'callback_query') and update.callback_query else None}")
    log_any_callback(update)
    query = update.callback_query
    if not query:
        return
    await query.answer()
    
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=Messages["PRODUCTS"]["menu"],
        reply_markup=KeyboardFactory.get("products_menu")
    )
    logger.info("Показано меню продуктов")

async def recipes_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.critical(f"[UNIVERSAL CALLBACK LOG] callback_query.data: {update.callback_query.data if hasattr(update, 'callback_query') and update.callback_query else None}")
    log_any_callback(update)
    query = update.callback_query
    if not query:
        return
    await query.answer()
    
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=Messages["RECIPES"]["menu"],
        reply_markup=KeyboardFactory.get("recipe_menu")
    )
    logger.info("Показано меню рецептов")

async def back_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.critical(f"[UNIVERSAL CALLBACK LOG] callback_query.data: {update.callback_query.data if hasattr(update, 'callback_query') and update.callback_query else None}")
    """Обработчик кнопки 'Назад' - возврат в главное меню"""
    await ui_service.show_main_menu(update, context)
    logger.info("Возврат в главное меню")

async def main_products_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.critical(f"[UNIVERSAL CALLBACK LOG] callback_query.data: {update.callback_query.data if hasattr(update, 'callback_query') and update.callback_query else None}")
    """Обработчик кнопки 'Продукты' в главном меню"""
    query = update.callback_query
    if not query:
        return
    await query.answer()
    
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=Messages["PRODUCTS"]["menu"],
        reply_markup=KeyboardFactory.get("products_menu")
    )
    logger.info("Переход в меню продуктов")

async def main_recipes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.critical(f"[UNIVERSAL CALLBACK LOG] callback_query.data: {update.callback_query.data if hasattr(update, 'callback_query') and update.callback_query else None}")
    """Обработчик кнопки 'Рецепты' в главном меню"""
    query = update.callback_query
    if not query:
        return
    await query.answer()
    
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=Messages["RECIPES"]["menu"],
        reply_markup=KeyboardFactory.get("recipe_menu")
    )
    logger.info("Переход в меню рецептов")

async def recipe_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.critical(f"[UNIVERSAL CALLBACK LOG] callback_query.data: {update.callback_query.data if hasattr(update, 'callback_query') and update.callback_query else None}")
    query = update.callback_query
    if not query:
        return
    await query.answer()
    if context.user_data is None:
        context.user_data = {}
    context.user_data['recipe_data'] = {'ingredients': [], 'tags': []}
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text="➕ *Добавление рецепта*\n\nВведите название рецепта:",
        reply_markup=None
    )
    logger.info("[Добавление рецепта] Запрошено название рецепта")
    return RECIPE_NAME

async def recipe_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.critical(f"[UNIVERSAL CALLBACK LOG] callback_query.data: {update.callback_query.data if hasattr(update, 'callback_query') and update.callback_query else None}")
    """Показать интерактивный список рецептов пользователя"""
    query = update.callback_query
    if not query:
        return
    await query.answer()
    all_recipes = recipe_service.get_all_recipes()
    if not all_recipes:
        text = "📋 *Мои рецепты*\n\nУ вас пока нет сохраненных рецептов."
        reply_markup = KeyboardFactory.get("back")
    else:
        text = "📋 *Мои рецепты*\n\nВыберите рецепт для просмотра:"
        keyboard = []
        for recipe in all_recipes:
            recipe_id = recipe.get('id')
            recipe_name = recipe.get('name', 'Без названия')
            display_name = recipe_name[:30] + "..." if len(recipe_name) > 30 else recipe_name
            keyboard.append([InlineKeyboardButton(display_name, callback_data=f"recipe_view_{recipe_id}")])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=text,
        reply_markup=reply_markup
    )
    logger.info("Показан интерактивный список рецептов")

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
        await real_product_search(update, context)
        return
    elif state == RECIPE_SEARCH:
        await handle_recipe_search(update, context, text)
        return
    elif state == NUTRIENT_CALCULATOR:
        await handle_nutrient_calculator(update, context, text)
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
        product_service = getattr(getattr(context, 'application', None), 'product_service', None)
        if product_service:
            product_service.add_product(
                name=name,
                nutrients={
                    'calories': float(data.get('калории', 0)),
                    'protein': float(data.get('белки', 0)),
                    'fat': float(data.get('жиры', 0)),
                    'carbs': float(data.get('углеводы', 0))
                },
                unit='г',
                description='',
                emoji='🍏'
            )
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"""✅ *Продукт успешно добавлен!*

*Название:* {name}
*Калории:* {data.get('калории', 0)} ккал
*Белки:* {data.get('белки', 0)} г
*Жиры:* {data.get('жиры', 0)} г
*Углеводы:* {data.get('углеводы', 0)} г

Что делать дальше?""",
            reply_markup=KeyboardFactory.get("products_menu"),
            parse_mode="Markdown"
        )
    except Exception as e:
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"❌ Ошибка добавления продукта: {e}\n\nПроверьте формат ввода и попробуйте снова.",
            reply_markup=KeyboardFactory.get("back")
        )
    if isinstance(context.user_data, dict):
        context.user_data["state"] = None

async def handle_recipe_search(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка поиска рецептов по ингредиенту"""
    from src.services.recipe_search_service import RecipeSearchService
    from src.ui.keyboards.factory import KeyboardFactory
    logger.info(f"[Поиск рецептов] Пользователь {update.effective_user.id if update.effective_user else 'N/A'} ищет по ингредиенту: {text}")
    user_id = update.effective_user.id if update.effective_user else None
    query = text.strip()
    if not query or len(query) < 2:
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Пожалуйста, введите корректное название ингредиента (минимум 2 символа).",
            reply_markup=KeyboardFactory.get("back")
        )
        logger.warning(f"[Поиск рецептов] Пользователь {user_id} ввёл некорректный запрос: '{text}'")
        return
    try:
        # Параметры пагинации
        page = 1
        per_page = 5
        # Сохраняем поисковый запрос и страницу
        if not isinstance(context.user_data, dict):
            context.user_data = {}
        context.user_data['recipe_search_query'] = query
        context.user_data['recipe_search_page'] = page
        # Поиск рецептов
        recipe_search_service = RecipeSearchService(recipe_service=recipe_service)
        logger.info("Вызов recipe_search_service.search_recipes...")
        recipes, total = await recipe_search_service.search_recipes(query=query, page=page, per_page=per_page)
        logger.info(f"Результат поиска: {len(recipes)} рецептов, всего найдено: {total}")
        total_pages = (total + per_page - 1) // per_page
        if not recipes:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=f"❌ Ничего не найдено по запросу: {query}",
                reply_markup=KeyboardFactory.get("back")
            )
            logger.info(f"[Поиск рецептов] Нет результатов для запроса: {query}")
            if isinstance(context.user_data, dict):
                context.user_data["state"] = None
            return
        # Формируем клавиатуру с результатами
        keyboard = []
        for recipe in recipes:
            recipe_id = recipe.get('id')
            recipe_name = recipe.get('name', 'Без названия')
            if recipe_id:
                keyboard.append([InlineKeyboardButton(recipe_name, callback_data=f"recipe_view_{recipe_id}")])

        # Добавляем пагинацию
        if total_pages > 1:
            pagination_row = []
            if page > 1:
                pagination_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"recipe_search_page_{page-1}"))
            if page < total_pages:
                pagination_row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"recipe_search_page_{page+1}"))
            if pagination_row:
                keyboard.append(pagination_row)

        keyboard.append([InlineKeyboardButton("◀️ В меню", callback_data="back")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"🔍 Найдено рецептов: {total} (стр. {page}/{total_pages}).\nВыберите рецепт для просмотра:",
            reply_markup=reply_markup
        )
        logger.info(f"[Поиск рецептов] Найдено {total} рецептов по запросу: {query}")
        # Оставляем состояние для дальнейшей пагинации
    except Exception as e:
        logger.error(f"[Поиск рецептов] Ошибка поиска: {e}", exc_info=True)
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Произошла ошибка при поиске. Попробуйте позже.",
            reply_markup=KeyboardFactory.get("back")
        )
        if isinstance(context.user_data, dict):
            context.user_data["state"] = None

async def handle_nutrient_calculator(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка калькулятора БЖУ через унифицированный сервис"""
    user_id = update.effective_user.id if update.effective_user else None
    logger.info(f"[Калькулятор БЖУ] Пользователь {user_id} отправил: {text}")
    try:
        result_text = await calculate_from_text(text)
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=result_text,
            reply_markup=KeyboardFactory.get("back"),
            parse_mode="Markdown"
        )
        logger.info(f"[Калькулятор БЖУ] Расчет выполнен для пользователя {user_id}")
    except Exception as e:
        logger.error(f"[Калькулятор БЖУ] Ошибка расчета: {e}")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Произошла ошибка при расчете БЖУ. Попробуйте еще раз или обратитесь в поддержку.",
            reply_markup=KeyboardFactory.get("back")
        )
    finally:
        if isinstance(context.user_data, dict):
            context.user_data["state"] = None

async def handle_general_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка обычных сообщений"""
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=f"💬 Получено сообщение: {text}\n\nИспользуйте меню для навигации."
    )

# --- Обработчик поиска рецептов по ингредиенту ---
async def recipe_search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.critical(f"[UNIVERSAL CALLBACK LOG] callback_query.data: {update.callback_query.data if hasattr(update, 'callback_query') and update.callback_query else None}")
    query = getattr(update, 'callback_query', None)
    if not query:
        return
    await query.answer()
    try:
        from src.ui.keyboards.factory import KeyboardFactory
        await query.edit_message_text(
            "🔍 Пожалуйста, введите название ингредиента, который у вас есть (например: 'огурец').\n\n" \
            "⏪ Для возврата в меню нажмите 'Назад'",
            reply_markup=KeyboardFactory.get("back")
        )
        logger.info(f"[Поиск рецептов] Пользователь {update.effective_user.id if update.effective_user else 'N/A'} начал поиск по ингредиенту.")
        if not isinstance(context.user_data, dict):
            context.user_data = {}
        context.user_data["state"] = RECIPE_SEARCH
    except Exception as e:
        logger.error(f"[Поиск рецептов] Ошибка при инициализации поиска: {e}")
        await query.edit_message_text(
            f"❌ Произошла ошибка при запуске поиска. Попробуйте позже или обратитесь в поддержку.\n\nОшибка: {e}",
            reply_markup=KeyboardFactory.get("back")
        )

# --- Обработчик пагинации поиска рецептов по ингредиенту ---
async def recipe_search_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from src.services.recipe_search_service import RecipeSearchService
    from src.ui.keyboards.factory import KeyboardFactory
    logger.critical(f"[UNIVERSAL CALLBACK LOG] callback_query.data: {update.callback_query.data if hasattr(update, 'callback_query') and update.callback_query else None}")
    query_obj = getattr(update, 'callback_query', None)
    if not query_obj or not hasattr(query_obj, 'answer') or not hasattr(query_obj, 'data'):
        return
    await query_obj.answer()
    try:
        data = query_obj.data
        if not isinstance(data, str):
            await query_obj.edit_message_text(
                "❌ Ошибка пагинации. Попробуйте начать поиск заново.",
                reply_markup=KeyboardFactory.get("back")
            )
            return
        parts = data.split('_')
        if len(parts) < 4:
            await query_obj.edit_message_text(
                "❌ Ошибка пагинации. Попробуйте начать поиск заново.",
                reply_markup=KeyboardFactory.get("back")
            )
            return
        page = int(parts[-1])
        if not isinstance(context.user_data, dict):
            context.user_data = {}
        search_query = context.user_data.get('recipe_search_query', '')
        if not search_query:
            await query_obj.edit_message_text(
                "❌ Не найден поисковый запрос. Начните поиск заново.",
                reply_markup=KeyboardFactory.get("back")
            )
            return
        per_page = 5
        recipe_search_service = RecipeSearchService(recipe_service=recipe_service)
        recipes, total = await recipe_search_service.search_recipes(query=search_query, page=page, per_page=per_page)
        if not recipes:
            await query_obj.edit_message_text(
                f"❌ Ничего не найдено по запросу: {search_query}",
                reply_markup=KeyboardFactory.get("back")
            )
            return
        keyboard = []
        for recipe in recipes:
            recipe_id = recipe.get('id')
            recipe_name = recipe.get('name', 'Без названия')
            if recipe_id:
                keyboard.append([InlineKeyboardButton(recipe_name, callback_data=f"recipe_view_{recipe_id}")])
        total_pages = (total + per_page - 1) // per_page
        if total_pages > 1:
            pagination_row = []
            if page > 1:
                pagination_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"recipe_search_page_{page-1}"))
            if page < total_pages:
                pagination_row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"recipe_search_page_{page+1}"))
            if pagination_row:
                keyboard.append(pagination_row)
        keyboard.append([InlineKeyboardButton("◀️ В меню", callback_data="back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"🔍 Найдено рецептов: {total} (стр. {page}/{total_pages}).\nВыберите рецепт для просмотра:",
            reply_markup=reply_markup
        )
        context.user_data['recipe_search_page'] = page
    except Exception as e:
        logger.error(f"[Пагинация поиска рецептов] Ошибка: {e}", exc_info=True)
        await query_obj.edit_message_text(
            "❌ Произошла ошибка при пагинации. Попробуйте позже.",
            reply_markup=KeyboardFactory.get("back")
        )

def register_message_handlers(application):
    """Регистрация обработчиков сообщений"""
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(recipe_add_callback, pattern='^add_recipe')],
        states={
            RECIPE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, recipe_name_handler)],
            RECIPE_INGREDIENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recipe_ingredients_handler)],
            RECIPE_INSTRUCTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recipe_instructions_handler)],
            RECIPE_CONFIRM: [CallbackQueryHandler(recipe_confirm_handler, pattern='^confirm_'), CallbackQueryHandler(recipe_cancel_step_handler, pattern='^cancel_recipe')],
        },
        fallbacks=[CallbackQueryHandler(recipe_cancel_step_handler, pattern='^cancel_recipe')],
        allow_reentry=True
    )
    application.add_handler(conv_handler)
    
    # Главное меню и общие
    application.add_handler(CallbackQueryHandler(main_products_callback, pattern="^main_products$"))
    application.add_handler(CallbackQueryHandler(main_recipes_callback, pattern="^main_recipes$"))
    application.add_handler(CallbackQueryHandler(back_button_callback, pattern="^back$"))

    # Меню продуктов
    application.add_handler(CallbackQueryHandler(products_menu_callback, pattern="^products_menu$"))

    # Меню рецептов
    application.add_handler(CallbackQueryHandler(recipes_menu_callback, pattern="^recipes_menu$"))
    application.add_handler(CallbackQueryHandler(recipe_list_callback, pattern='^recipe_list$'))
    
    # Интерактивные рецепты
    application.add_handler(CallbackQueryHandler(recipe_view_callback, pattern='^recipe_view_'))

    # Обработчик текстовых сообщений (должен быть одним из последних)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Добавляем новый обработчик для поиска рецептов
    application.add_handler(CallbackQueryHandler(recipe_search_callback, pattern='^recipe_search$'))

    # --- Обработчик пагинации поиска рецептов по ингредиенту ---
    application.add_handler(CallbackQueryHandler(recipe_search_page_callback, pattern=r'^recipe_search_page_\\d+$'))