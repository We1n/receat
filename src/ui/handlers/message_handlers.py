"""
Обработчики сообщений для бота (адаптация под telegram.ext, полный функционал)
"""
import logging
from typing import cast, List, Dict, Any
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, MessageHandler, CallbackQueryHandler, filters, ConversationHandler
)
from src.ui.messages_main import Messages
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

logger = logging.getLogger(__name__)

# Инициализация сервисов
nutrient_analyzer = NutrientAnalysisService()
recipe_service = RecipeService()

# Состояния для добавления рецепта
RECIPE_NAME, RECIPE_CATEGORY, RECIPE_INGREDIENTS, RECIPE_INGREDIENT_AMOUNT, RECIPE_INGREDIENT_UNIT, RECIPE_MORE_INGREDIENTS, RECIPE_INSTRUCTIONS, RECIPE_TIME, RECIPE_DIFFICULTY, RECIPE_PORTIONS, RECIPE_CONFIRM = range(11)

def log_any_callback(update: Update):
    query = getattr(update, 'callback_query', None)
    if query and hasattr(query, 'data'):
        logger.info(f"[UNIVERSAL CALLBACK LOG] callback_query.data: {query.data}")

# Callback-меню
async def products_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    log_any_callback(update)
    """Обработчик кнопки 'Назад' - возврат в главное меню"""
    await ui_service.show_main_menu(update, context)
    logger.info("Возврат в главное меню")

async def main_products_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_any_callback(update)
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
    log_any_callback(update)
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
    """Начало добавления рецепта"""
    query = update.callback_query
    if not query:
        return
    await query.answer()
    if context.user_data is None:
        context.user_data = {}
    # Инициализируем данные рецепта
    context.user_data['recipe_data'] = {
        'ingredients': [],
        'tags': []
    }
    context.user_data['recipe_step_history'] = []
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text="➕ *Добавление рецепта*\n\nВведите название рецепта:"
    )
    logger.info("Начато добавление рецепта")
    return RECIPE_NAME

async def recipe_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка названия рецепта"""
    if not update.message or not update.message.text:
        return RECIPE_NAME
    text = update.message.text.strip()
    if len(text) < 3:
        await update.message.reply_text("❌ Название должно содержать минимум 3 символа. Попробуйте еще раз:")
        return RECIPE_NAME
    if context.user_data is None:
        context.user_data = {}
    if 'recipe_data' not in context.user_data or not isinstance(context.user_data['recipe_data'], dict):
        context.user_data['recipe_data'] = {}
    context.user_data['recipe_data']['name'] = text
    
    # Показываем выбор категории
    keyboard = [
        [InlineKeyboardButton("🌅 Завтрак", callback_data="category_завтрак")],
        [InlineKeyboardButton("🌞 Обед", callback_data="category_обед")],
        [InlineKeyboardButton("🌙 Ужин", callback_data="category_ужин")],
        [InlineKeyboardButton("🍎 Перекус", callback_data="category_перекус")],
        [InlineKeyboardButton("🍰 Десерт", callback_data="category_десерт")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ Название: *{text}*\n\nВыберите категорию:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return RECIPE_CATEGORY

async def recipe_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not hasattr(query, 'data') or not query.data:
        return RECIPE_CATEGORY
    await query.answer()
    category = query.data.replace("category_", "")
    if context.user_data is None:
        context.user_data = {}
    if 'recipe_data' not in context.user_data or not isinstance(context.user_data['recipe_data'], dict):
        context.user_data['recipe_data'] = {}
    context.user_data['recipe_data']['category'] = category
    await query.edit_message_text(
        f"✅ Категория: *{category}*\n\nТеперь добавьте ингредиенты в формате `Название Количество Единица`.\nНапример: `Помидоры 2 шт`\n\nВведите первый ингредиент:",
        parse_mode="Markdown"
    )
    return RECIPE_INGREDIENTS

async def recipe_ingredients_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not getattr(update.message, 'text', None):
        return RECIPE_INGREDIENTS
    text = update.message.text
    if not isinstance(text, str):
        return RECIPE_INGREDIENTS
    text = text.strip()
    name, amount, unit = None, None, None
    special_units = ["по вкусу", "щепотка"]
    for sp_unit in special_units:
        if sp_unit in text.lower():
            name = text.lower().replace(sp_unit, "").strip()
            amount = 1.0
            unit = sp_unit
            break
    if name is None:
        match = re.match(r'^(.*?)\s+([\d\.,]+)\s*(.*)', text)
        if match:
            name = match.group(1).strip()
            amount_str = match.group(2).replace(',', '.')
            unit = match.group(3).strip()
            if not unit:
                if update.message:
                    await update.message.reply_text("❌ Не указана единица измерения. Попробуйте еще раз. Например: `Помидоры 2 шт`", parse_mode="Markdown")
                return RECIPE_INGREDIENTS
            try:
                amount = float(amount_str) if amount_str else 1.0
            except ValueError:
                if update.message:
                    await update.message.reply_text("❌ Неверный формат количества. Попробуйте еще раз. Например: `Помидоры 2 шт`", parse_mode="Markdown")
                return RECIPE_INGREDIENTS
        else:
            if update.message:
                await update.message.reply_text("❌ Неверный формат. Укажите название, количество и единицу измерения. Например: `Помидоры 2 шт`", parse_mode="Markdown")
            return RECIPE_INGREDIENTS
    try:
        if name is None or amount is None or unit is None:
            raise ValueError("Не удалось распознать все части ингредиента.")
        ingredient_data = IngredientDTO(name=name, amount=float(amount), unit=unit)
    except ValueError as e:
        if update.message:
            await update.message.reply_text(f"❌ Ошибка валидации: {e}. Попробуйте еще раз.")
        return RECIPE_INGREDIENTS
    current_ingredient = ingredient_data.dict()
    if not isinstance(context.user_data, dict):
        context.user_data = {}
    if 'recipe_data' not in context.user_data or not isinstance(context.user_data['recipe_data'], dict):
        context.user_data['recipe_data'] = {}
    if 'ingredients' not in context.user_data['recipe_data'] or not isinstance(context.user_data['recipe_data']['ingredients'], list):
        context.user_data['recipe_data']['ingredients'] = []
    context.user_data['recipe_data']['ingredients'].append(current_ingredient)
    if 'recipe_step_history' not in context.user_data or not isinstance(context.user_data['recipe_step_history'], list):
        context.user_data['recipe_step_history'] = []
    context.user_data['recipe_step_history'].append(RECIPE_INGREDIENTS)
    ingredient_text = f"{current_ingredient['name']} - {current_ingredient['amount']} {current_ingredient['unit']}"
    ingredients_list = "\n".join([f"• {ing['name']} - {ing['amount']} {ing['unit']}" for ing in context.user_data['recipe_data']['ingredients']])
    keyboard = [
        [InlineKeyboardButton("➕ Добавить ещё", callback_data="more_ingredients")],
        [InlineKeyboardButton("✅ Завершить", callback_data="finish_ingredients")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_step"), InlineKeyboardButton("❌ Отмена", callback_data="cancel_recipe")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(
            f"✅ Добавлен: *{ingredient_text}*\n\n*Все ингредиенты:*\n{ingredients_list}\n\nЧто делаем дальше?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    return RECIPE_MORE_INGREDIENTS

async def recipe_more_ingredients_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = getattr(update, 'callback_query', None)
    if not query or not hasattr(query, 'data') or not query.data:
        return RECIPE_MORE_INGREDIENTS
    await query.answer()
    if query.data == "more_ingredients":
        await query.edit_message_text("Введите следующий ингредиент в формате `Название Количество Единица`:", reply_markup=get_step_keyboard(False, True), parse_mode="Markdown")
        return RECIPE_INGREDIENTS
    else:
        await query.edit_message_text(
            "✅ Ингредиенты добавлены!\n\nТеперь введите инструкции по приготовлению:",
            reply_markup=get_step_keyboard(True, True)
        )
        return RECIPE_INSTRUCTIONS

async def recipe_instructions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка инструкций"""
    if not update.message or not getattr(update.message, 'text', None):
        return RECIPE_INSTRUCTIONS
    text = update.message.text
    if not isinstance(text, str):
        return RECIPE_INSTRUCTIONS
    text = text.strip()
    if len(text) < 10:
        if update.message and hasattr(update.message, 'reply_text'):
            await update.message.reply_text("❌ Инструкции должны содержать минимум 10 символов. Попробуйте еще раз:", reply_markup=get_step_keyboard(True, True))
        return RECIPE_INSTRUCTIONS
    if not isinstance(context.user_data, dict):
        context.user_data = {}
    if 'recipe_data' not in context.user_data or not isinstance(context.user_data['recipe_data'], dict):
        context.user_data['recipe_data'] = {}
    if 'recipe_step_history' not in context.user_data or not isinstance(context.user_data['recipe_step_history'], list):
        context.user_data['recipe_step_history'] = []
    context.user_data['recipe_data']['instructions'] = text
    context.user_data['recipe_step_history'].append(RECIPE_INSTRUCTIONS)
    # Показываем выбор времени приготовления
    keyboard = [
        [InlineKeyboardButton("15 мин", callback_data="time_15"), InlineKeyboardButton("30 мин", callback_data="time_30")],
        [InlineKeyboardButton("45 мин", callback_data="time_45"), InlineKeyboardButton("60 мин", callback_data="time_60")],
        [InlineKeyboardButton("90+ мин", callback_data="time_90")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_step"), InlineKeyboardButton("❌ Отмена", callback_data="cancel_recipe")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(
            f"✅ Инструкции добавлены!\n\nВыберите время приготовления:",
            reply_markup=reply_markup
        )
    return RECIPE_TIME

async def recipe_time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка времени приготовления"""
    query = getattr(update, 'callback_query', None)
    if not query or not hasattr(query, 'data') or not query.data:
        return RECIPE_TIME
    await query.answer()
    if not isinstance(query.data, str) or not query.data.startswith("time_"):
        return RECIPE_TIME
    time_str = query.data.replace("time_", "")
    try:
        cooking_time = int(time_str)
    except ValueError:
        return RECIPE_TIME
    if not isinstance(context.user_data, dict):
        context.user_data = {}
    if 'recipe_data' not in context.user_data or not isinstance(context.user_data['recipe_data'], dict):
        context.user_data['recipe_data'] = {}
    if 'recipe_step_history' not in context.user_data or not isinstance(context.user_data['recipe_step_history'], list):
        context.user_data['recipe_step_history'] = []
    context.user_data['recipe_data']['cooking_time'] = cooking_time
    context.user_data['recipe_step_history'].append(RECIPE_TIME)
    # Показываем выбор сложности
    keyboard = [
        [InlineKeyboardButton("🟢 Легкая", callback_data="difficulty_Легкая")],
        [InlineKeyboardButton("🟡 Средняя", callback_data="difficulty_Средняя")],
        [InlineKeyboardButton("🔴 Сложная", callback_data="difficulty_Сложная")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_step"), InlineKeyboardButton("❌ Отмена", callback_data="cancel_recipe")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"✅ Время: *{cooking_time} минут*\n\nВыберите сложность:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return RECIPE_DIFFICULTY

async def recipe_difficulty_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сложности"""
    query = getattr(update, 'callback_query', None)
    if not query or not hasattr(query, 'data') or not query.data:
        return RECIPE_DIFFICULTY
    await query.answer()
    if not isinstance(query.data, str) or not query.data.startswith("difficulty_"):
        return RECIPE_DIFFICULTY
    difficulty = query.data.replace("difficulty_", "")
    if not isinstance(context.user_data, dict):
        context.user_data = {}
    if 'recipe_data' not in context.user_data or not isinstance(context.user_data['recipe_data'], dict):
        context.user_data['recipe_data'] = {}
    if 'recipe_step_history' not in context.user_data or not isinstance(context.user_data['recipe_step_history'], list):
        context.user_data['recipe_step_history'] = []
    context.user_data['recipe_data']['difficulty'] = difficulty
    context.user_data['recipe_step_history'].append(RECIPE_DIFFICULTY)
    # Показываем выбор количества порций
    keyboard = [
        [InlineKeyboardButton("1", callback_data="portions_1"), InlineKeyboardButton("2", callback_data="portions_2")],
        [InlineKeyboardButton("4", callback_data="portions_4"), InlineKeyboardButton("6", callback_data="portions_6")],
        [InlineKeyboardButton("8+", callback_data="portions_8")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_step"), InlineKeyboardButton("❌ Отмена", callback_data="cancel_recipe")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"✅ Сложность: *{difficulty}*\n\nВыберите количество порций:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return RECIPE_PORTIONS

async def recipe_portions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка количества порций"""
    query = getattr(update, 'callback_query', None)
    if not query or not hasattr(query, 'data') or not query.data:
        return RECIPE_PORTIONS
    await query.answer()
    if not isinstance(query.data, str) or not query.data.startswith("portions_"):
        return RECIPE_PORTIONS
    try:
        portions = int(query.data.replace("portions_", ""))
    except ValueError:
        return RECIPE_PORTIONS
    if not isinstance(context.user_data, dict):
        context.user_data = {}
    if 'recipe_data' not in context.user_data or not isinstance(context.user_data['recipe_data'], dict):
        context.user_data['recipe_data'] = {}
    if 'recipe_step_history' not in context.user_data or not isinstance(context.user_data['recipe_step_history'], list):
        context.user_data['recipe_step_history'] = []
    context.user_data['recipe_data']['portions'] = portions
    context.user_data['recipe_step_history'].append(RECIPE_PORTIONS)
    # Добавляем недостающие поля
    recipe_data = context.user_data['recipe_data']
    recipe_data['nutrients'] = {"calories": 0, "proteins": 0, "fats": 0, "carbs": 0}
    # Показываем итоговый рецепт для подтверждения
    ingredients_text = "\n".join([f"• {ing['name']} - {ing['amount']} {ing['unit']}" for ing in recipe_data.get('ingredients', [])])
    summary_text = f"""📋 *Итоговый рецепт:*
\n🍽️ **Название:** {recipe_data.get('name', '')}\n📂 **Категория:** {recipe_data.get('category', '')}\n⏱️ **Время:** {recipe_data.get('cooking_time', '')} мин\n🎯 **Сложность:** {recipe_data.get('difficulty', '')}\n👥 **Порций:** {recipe_data.get('portions', '')}\n\n🥘 **Ингредиенты:**\n{ingredients_text}\n\n📝 **Инструкции:**\n{recipe_data.get('instructions', '')}\n\nСохранить рецепт?"""
    keyboard = [
        [InlineKeyboardButton("✅ Сохранить", callback_data="confirm_save")],
        [InlineKeyboardButton("❌ Отменить", callback_data="confirm_cancel")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_step")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.edit_message_text(
            summary_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    return RECIPE_CONFIRM

async def recipe_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка подтверждения сохранения"""
    query = getattr(update, 'callback_query', None)
    if not query or not hasattr(query, 'data') or not query.data:
        return ConversationHandler.END
    await query.answer()
    if query.data == "confirm_save":
        try:
            if not isinstance(context.user_data, dict):
                context.user_data = {}
            recipe_data = context.user_data.get('recipe_data', {})
            recipe_id = await recipe_service.create_recipe(recipe_data)
            await query.edit_message_text(
                f"✅ *Рецепт успешно сохранен!*\n\nID: {recipe_id}\n\nВозвращаемся в главное меню...",
                parse_mode="Markdown"
            )
            await ui_service.show_main_menu(update, context)
        except Exception as e:
            logger.error(f"Ошибка сохранения рецепта: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при сохранении рецепта. Попробуйте еще раз."
            )
    else:  # confirm_cancel
        await query.edit_message_text(
            "❌ Добавление рецепта отменено.\n\nВозвращаемся в главное меню..."
        )
        await ui_service.show_main_menu(update, context)
    # Очищаем данные
    if isinstance(context.user_data, dict):
        context.user_data.pop('recipe_data', None)
        context.user_data.pop('recipe_step_history', None)
    return ConversationHandler.END

async def cancel_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена добавления рецепта"""
    if update.message:
        if hasattr(update.message, 'reply_text'):
            await update.message.reply_text("❌ Добавление рецепта отменено. Возвращаемся в главное меню...")
    # Очищаем данные
    if isinstance(context.user_data, dict):
        if 'recipe_data' in context.user_data:
            del context.user_data['recipe_data']
        if STEP_HISTORY_KEY in context.user_data:
            del context.user_data[STEP_HISTORY_KEY]
    await ui_service.show_main_menu(update, context)
    return ConversationHandler.END

async def recipe_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        # Создаем кнопки для каждого рецепта
        keyboard = []
        if isinstance(all_recipes, dict):
            for recipe_id, recipe_name in all_recipes.items():
                display_name = recipe_name[:30] + "..." if len(recipe_name) > 30 else recipe_name
                keyboard.append([InlineKeyboardButton(display_name, callback_data=f"recipe_view_{recipe_id}")])
        elif isinstance(all_recipes, list):
            for i, recipe in enumerate(all_recipes):
                name = recipe.get('name') or recipe.get('title') or f'Рецепт {i+1}'
                recipe_id = recipe.get('id', i)
                display_name = name[:30] + "..." if len(name) > 30 else name
                keyboard.append([InlineKeyboardButton(display_name, callback_data=f"recipe_view_{recipe_id}")])
        
        # Добавляем кнопку "Назад"
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
        reply_markup = InlineKeyboardMarkup(keyboard)

    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=text,
        reply_markup=reply_markup
    )
    logger.info("Показан интерактивный список рецептов")

async def recipe_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_any_callback(update)
    query = getattr(update, 'callback_query', None)
    logger.info(f"[DEBUG] recipe_view_callback: {query.data if query and hasattr(query, 'data') else 'NO QUERY'}")
    if not query or not hasattr(query, 'data') or not query.data:
        return
    await query.answer()
    if not isinstance(query.data, str) or not query.data.startswith("recipe_view_"):
        return
    recipe_id = query.data.replace("recipe_view_", "")
    try:
        recipe = recipe_service.get_recipe_by_id(recipe_id)
        if not recipe:
            await query.edit_message_text(
                "❌ Рецепт не найден.",
                reply_markup=KeyboardFactory.get("back")
            )
            return
        ingredients_text = "\n".join([f"• {ing['name']} - {ing['amount']} {ing['unit']}" for ing in recipe.get('ingredients', [])])
        recipe_text = f"""📋 *{recipe.get('name', 'Без названия')}*
\n📂 **Категория:** {recipe.get('category', 'Не указана')}\n⏱️ **Время:** {recipe.get('cooking_time', 0)} мин\n🎯 **Сложность:** {recipe.get('difficulty', 'Не указана')}\n👥 **Порций:** {recipe.get('portions', 1)}\n\n🥘 **Ингредиенты:**\n{ingredients_text}\n\n📝 **Инструкции:**\n{recipe.get('instructions', 'Не указаны')}\n\n🔢 **БЖУ (на порцию):**\n• Калории: {recipe.get('nutrients', {}).get('calories', 0)} ккал\n• Белки: {recipe.get('nutrients', {}).get('proteins', 0)} г\n• Жиры: {recipe.get('nutrients', {}).get('fats', 0)} г\n• Углеводы: {recipe.get('nutrients', {}).get('carbs', 0)} г"""
        keyboard = [
            [InlineKeyboardButton("⭐ В избранное", callback_data=f"recipe_favorite_{recipe_id}")],
            [InlineKeyboardButton("✏️ Редактировать", callback_data=f"recipe_edit_{recipe_id}")],
            [InlineKeyboardButton("🗑️ Удалить", callback_data=f"recipe_delete_{recipe_id}")],
            [InlineKeyboardButton("◀️ К списку", callback_data="recipe_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            recipe_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка при получении рецепта {recipe_id}: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при загрузке рецепта.",
            reply_markup=KeyboardFactory.get("back")
        )

async def recipe_favorite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = getattr(update, 'callback_query', None)
    if not query or not hasattr(query, 'data') or not query.data:
        return
    await query.answer()
    if not isinstance(query.data, str) or not query.data.startswith("recipe_favorite_"):
        return
    recipe_id = query.data.replace("recipe_favorite_", "")
    await query.edit_message_text("⭐ Функция избранного будет добавлена в следующем обновлении!")
    logger.info(f"Попытка добавить рецепт {recipe_id} в избранное")

async def recipe_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = getattr(update, 'callback_query', None)
    if not query or not hasattr(query, 'data') or not query.data:
        return
    await query.answer()
    if not isinstance(query.data, str) or not query.data.startswith("recipe_edit_"):
        return
    recipe_id = query.data.replace("recipe_edit_", "")
    await query.edit_message_text("✏️ Функция редактирования будет добавлена в следующем обновлении!")
    logger.info(f"Попытка редактировать рецепт {recipe_id}")

async def recipe_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_any_callback(update)
    query = getattr(update, 'callback_query', None)
    logger.info(f"[DEBUG] recipe_delete_callback: {query.data if query and hasattr(query, 'data') else 'NO QUERY'}")
    if not query or not hasattr(query, 'data') or not query.data:
        return
    await query.answer()
    if not isinstance(query.data, str) or not query.data.startswith("recipe_delete_"):
        return
    recipe_id = query.data.replace("recipe_delete_", "")
    reply_markup = KeyboardFactory.get_confirmation_keyboard("recipe_delete_confirm", int(recipe_id))
    await query.edit_message_text(
        "🗑️ *Удаление рецепта*\n\nВы уверены, что хотите удалить этот рецепт?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def recipe_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_any_callback(update)
    query = getattr(update, 'callback_query', None)
    logger.info(f"[DEBUG] recipe_delete_confirm_callback: {query.data if query and hasattr(query, 'data') else 'NO QUERY'}")
    logger.info(f"[UI] Получен запрос на удаление рецепта. query={query}")
    if not query or not hasattr(query, 'data') or not query.data:
        return
    await query.answer()
    if not isinstance(query.data, str) or not query.data.startswith("recipe_delete_confirm_"):
        return
    recipe_id = query.data.replace("recipe_delete_confirm_", "")
    logger.info(f"[UI] Кнопка удаления: получен recipe_id={recipe_id}")
    if not recipe_id.isdigit():
        logger.error(f"[UI] Некорректный формат recipe_id: {recipe_id}")
        await query.edit_message_text(
            "❌ Ошибка: некорректный формат ID рецепта. Удаление невозможно.",
            reply_markup=KeyboardFactory.get("back")
        )
        return
    try:
        recipe = recipe_service.get_recipe_by_id(recipe_id)
        logger.info(f"[UI] Результат поиска по ID: {recipe}")
        if not recipe:
            logger.error(f"[UI] Рецепт с ID {recipe_id} не найден.")
            await query.edit_message_text(
                "❌ Рецепт не найден. Удаление невозможно.",
                reply_markup=KeyboardFactory.get("back")
            )
            return
        recipe_name = recipe.get('name')
        logger.info(f"[UI] Имя рецепта для удаления: {recipe_name}")
        if not recipe_name:
            logger.error(f"[UI] У рецепта с ID {recipe_id} отсутствует имя!")
            await query.edit_message_text(
                "❌ Ошибка: у рецепта отсутствует имя. Удаление невозможно.",
                reply_markup=KeyboardFactory.get("back")
            )
            return
        start_time = time.time()
        deleted = await asyncio.to_thread(recipe_service.delete_recipe, recipe_name)
        duration = time.time() - start_time
        logger.info(f"[UI] Результат удаления: {deleted}, время выполнения: {duration:.4f} сек.")
        if deleted:
            await query.edit_message_text(
                "✅ Рецепт успешно удалён!\n\nВозвращаемся к списку рецептов...",
                reply_markup=KeyboardFactory.get("back")
            )
            logger.info(f"[UI] Рецепт {recipe_id} ('{recipe_name}') удалён")
        else:
            await query.edit_message_text(
                "❌ Не удалось удалить рецепт. Возможно, он уже был удалён.",
                reply_markup=KeyboardFactory.get("back")
            )
            logger.warning(f"[UI] Не удалось удалить рецепт: {recipe_id} ('{recipe_name}')")
    except Exception as e:
        logger.error(f"[UI] Ошибка удаления рецепта {recipe_id}: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Произошла ошибка при удалении рецепта.",
            reply_markup=KeyboardFactory.get("back")
        )

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
        category = data.get('категория')
        calories = float(data.get('калории', 0))
        protein = float(data.get('белки', 0))
        fat = float(data.get('жиры', 0))
        carbs = float(data.get('углеводы', 0))
        if not (name and category):
            raise ValueError('Не указаны название или категория')
        # Добавление продукта (можно доработать под ваш сервис)
        product_service = getattr(getattr(context, 'application', None), 'product_service', None)
        if product_service:
            product_service.add_product(
                name=name,
                category=category,
                nutrients={
                    'calories': calories,
                    'protein': protein,
                    'fat': fat,
                    'carbs': carbs
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
*Категория:* {category}
*Калории:* {calories} ккал
*Белки:* {protein} г
*Жиры:* {fat} г
*Углеводы:* {carbs} г

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

# --- Вспомогательные клавиатуры для шагов ---
def get_step_keyboard(include_back=True, include_cancel=True):
    keyboard = []
    row = []
    if include_back:
        row.append(InlineKeyboardButton("◀️ Назад", callback_data="back_step"))
    if include_cancel:
        row.append(InlineKeyboardButton("❌ Отмена", callback_data="cancel_recipe"))
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard) if keyboard else None

# --- Обработчики шагов с поддержкой "Назад" и "Отмена" ---

# Для хранения истории шагов
STEP_HISTORY_KEY = 'recipe_step_history'

# --- Обработчик кнопки "Назад" ---
async def recipe_back_step_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = getattr(update, 'callback_query', None)
    if not query:
        return ConversationHandler.END
    await query.answer()
    if not isinstance(context.user_data, dict):
        context.user_data = {}
    history = context.user_data.get('recipe_step_history', [])
    if not isinstance(history, list) or not history:
        await query.edit_message_text("Нет истории шагов. Возвращаемся в начало.")
        return ConversationHandler.END
    prev_step = history.pop() if history else None
    context.user_data['recipe_step_history'] = history
    if prev_step == RECIPE_INGREDIENTS:
        await query.edit_message_text("Введите ингредиент в формате `Название Количество Единица`:", reply_markup=get_step_keyboard(False, True), parse_mode="Markdown")
        return RECIPE_INGREDIENTS
    elif prev_step == RECIPE_INSTRUCTIONS:
        await query.edit_message_text("Введите инструкции:", reply_markup=get_step_keyboard(True, True))
        return RECIPE_INSTRUCTIONS
    elif prev_step == RECIPE_TIME:
        # Показываем выбор времени с кнопками
        keyboard = [
            [InlineKeyboardButton("15 мин", callback_data="time_15"), InlineKeyboardButton("30 мин", callback_data="time_30")],
            [InlineKeyboardButton("45 мин", callback_data="time_45"), InlineKeyboardButton("60 мин", callback_data="time_60")],
            [InlineKeyboardButton("90+ мин", callback_data="time_90")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_step"), InlineKeyboardButton("❌ Отмена", callback_data="cancel_recipe")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите время приготовления:", reply_markup=reply_markup)
        return RECIPE_TIME
    elif prev_step == RECIPE_DIFFICULTY:
        # Показываем выбор сложности с кнопками
        keyboard = [
            [InlineKeyboardButton("🟢 Легкая", callback_data="difficulty_Легкая")],
            [InlineKeyboardButton("🟡 Средняя", callback_data="difficulty_Средняя")],
            [InlineKeyboardButton("🔴 Сложная", callback_data="difficulty_Сложная")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_step"), InlineKeyboardButton("❌ Отмена", callback_data="cancel_recipe")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите сложность:", reply_markup=reply_markup)
        return RECIPE_DIFFICULTY
    elif prev_step == RECIPE_PORTIONS:
        # Показываем выбор порций с кнопками
        keyboard = [
            [InlineKeyboardButton("1", callback_data="portions_1"), InlineKeyboardButton("2", callback_data="portions_2")],
            [InlineKeyboardButton("4", callback_data="portions_4"), InlineKeyboardButton("6", callback_data="portions_6")],
            [InlineKeyboardButton("8+", callback_data="portions_8")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_step"), InlineKeyboardButton("❌ Отмена", callback_data="cancel_recipe")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите количество порций:", reply_markup=reply_markup)
        return RECIPE_PORTIONS
    else:
        await query.edit_message_text("❌ Не удалось определить предыдущий шаг. Возвращаемся в главное меню...")
        await ui_service.show_main_menu(update, context)
        return ConversationHandler.END

# --- Обработчик кнопки "Отмена" ---
async def recipe_cancel_step_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    if query:
        await query.answer()
        await query.edit_message_text("❌ Добавление рецепта отменено. Возвращаемся в главное меню...")
    else:
        if update.message and hasattr(update.message, 'reply_text'):
            await update.message.reply_text("❌ Добавление рецепта отменено. Возвращаемся в главное меню...")
    if isinstance(context.user_data, dict):
        if 'recipe_data' in context.user_data:
            del context.user_data['recipe_data']
        if STEP_HISTORY_KEY in context.user_data:
            del context.user_data[STEP_HISTORY_KEY]
    await ui_service.show_main_menu(update, context)
    return ConversationHandler.END

def register_message_handlers(application):
    """Регистрация обработчиков сообщений"""
    # ConversationHandler для добавления рецепта
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(recipe_add_callback, pattern='^add_recipe$')],
        states={
            RECIPE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, recipe_name_handler)],
            RECIPE_CATEGORY: [CallbackQueryHandler(recipe_category_handler, pattern='^category_')],
            RECIPE_INGREDIENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recipe_ingredients_handler), CallbackQueryHandler(recipe_back_step_handler, pattern='^back_step'), CallbackQueryHandler(recipe_cancel_step_handler, pattern='^cancel_recipe')],
            RECIPE_MORE_INGREDIENTS: [CallbackQueryHandler(recipe_more_ingredients_handler, pattern='^(more_ingredients|finish_ingredients)'), CallbackQueryHandler(recipe_back_step_handler, pattern='^back_step'), CallbackQueryHandler(recipe_cancel_step_handler, pattern='^cancel_recipe')],
            RECIPE_INSTRUCTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recipe_instructions_handler), CallbackQueryHandler(recipe_back_step_handler, pattern='^back_step'), CallbackQueryHandler(recipe_cancel_step_handler, pattern='^cancel_recipe')],
            RECIPE_TIME: [CallbackQueryHandler(recipe_time_handler, pattern='^time_'), CallbackQueryHandler(recipe_back_step_handler, pattern='^back_step'), CallbackQueryHandler(recipe_cancel_step_handler, pattern='^cancel_recipe')],
            RECIPE_DIFFICULTY: [CallbackQueryHandler(recipe_difficulty_handler, pattern='^difficulty_'), CallbackQueryHandler(recipe_back_step_handler, pattern='^back_step'), CallbackQueryHandler(recipe_cancel_step_handler, pattern='^cancel_recipe')],
            RECIPE_PORTIONS: [CallbackQueryHandler(recipe_portions_handler, pattern='^portions_'), CallbackQueryHandler(recipe_back_step_handler, pattern='^back_step'), CallbackQueryHandler(recipe_cancel_step_handler, pattern='^cancel_recipe')],
            RECIPE_CONFIRM: [CallbackQueryHandler(recipe_confirm_handler, pattern='^confirm_'), CallbackQueryHandler(recipe_back_step_handler, pattern='^back_step'), CallbackQueryHandler(recipe_cancel_step_handler, pattern='^cancel_recipe')],
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
    application.add_handler(CallbackQueryHandler(recipe_favorite_callback, pattern='^recipe_favorite_'))
    application.add_handler(CallbackQueryHandler(recipe_edit_callback, pattern='^recipe_edit_'))
    application.add_handler(CallbackQueryHandler(recipe_delete_callback, pattern=r'^recipe_delete_\d+$'))
    application.add_handler(CallbackQueryHandler(recipe_delete_confirm_callback, pattern=r'^recipe_delete_confirm_\d+$'))

    # Обработчик текстовых сообщений (должен быть одним из последних)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Добавляем новый обработчик для поиска рецептов
    application.add_handler(CallbackQueryHandler(recipe_search_callback, pattern='^recipe_search$'))

    # --- Обработчик пагинации поиска рецептов по ингредиенту ---
    application.add_handler(CallbackQueryHandler(recipe_search_page_callback, pattern=r'^recipe_search_page_\\d+$'))

# Новый обработчик для кнопки поиска рецептов
async def recipe_search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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