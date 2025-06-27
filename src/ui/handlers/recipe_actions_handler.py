"""
Обработчики действий с рецептами: атомарные async-функции для ConversationHandler.
"""
from telegram import Update
from telegram.ext import ContextTypes
from src.ui.ui_service import ui_service
from src.ui.keyboards import KeyboardFactory
from src.services.recipe_service import RecipeService
from src.validators.input_handler import input_handler
from src.ui.messages_main import Messages
import logging

logger = logging.getLogger(__name__)
recipe_service = RecipeService()

# --- Шаг 1: Ввод названия рецепта ---
async def recipe_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not isinstance(update.message.text, str):
        return 0
    text = update.message.text.strip()
    if len(text) < 3:
        await update.message.reply_text("❌ Название должно содержать минимум 3 символа. Попробуйте ещё раз:")
        return 0
    if not isinstance(context.user_data, dict):
        context.user_data = {}
    context.user_data.setdefault('recipe_data', {})['name'] = text
    await update.message.reply_text(
        f"✅ Название: *{text}*\n\nТеперь введите все ингредиенты списком, каждый ингредиент — с новой строки.",
        parse_mode="Markdown"
    )
    return 1

# --- Шаг 2: Ввод ингредиентов ---
async def recipe_ingredients_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not isinstance(update.message.text, str):
        return 1
    text = update.message.text.strip()
    if not isinstance(context.user_data, dict):
        context.user_data = {}
    context.user_data.setdefault('recipe_data', {})['ingredients'] = text.split('\n')
    await update.message.reply_text(
        "✅ Ингредиенты сохранены. Теперь введите пошаговую инструкцию приготовления:",
        parse_mode="Markdown"
    )
    return 2

# --- Шаг 3: Ввод инструкции ---
async def recipe_instructions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not isinstance(update.message.text, str):
        return 2
    text = update.message.text.strip()
    if not isinstance(context.user_data, dict):
        context.user_data = {}
    context.user_data.setdefault('recipe_data', {})['instructions'] = text
    await update.message.reply_text(
        "✅ Инструкция сохранена. Подтвердите добавление рецепта или отмените.",
        reply_markup=KeyboardFactory.get("recipe_confirm")
    )
    return 3

# --- Шаг 4: Подтверждение ---
async def recipe_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = getattr(update, 'callback_query', None)
    if not query or not hasattr(query, 'data'):
        return 3
    await query.answer()
    if not isinstance(context.user_data, dict):
        context.user_data = {}
    if query.data == "confirm_recipe":
        data = context.user_data.get('recipe_data', {})
        recipe_service.add_recipe(data.get('name', ''), data)
        await query.edit_message_text("✅ Рецепт успешно добавлен!")
        return -1
    elif query.data == "cancel_recipe":
        await query.edit_message_text("❌ Добавление рецепта отменено.")
        return -1
    return 3

# --- Просмотр рецепта ---
async def recipe_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = getattr(update, 'callback_query', None)
    if not query or not hasattr(query, 'data'):
        return
    await query.answer()
    recipe_id = query.data.replace("recipe_view_", "")
    recipe = recipe_service.get_recipe_by_id(recipe_id)
    if not recipe:
        await query.edit_message_text("❌ Рецепт не найден.")
        return
    text = f"*{recipe['name']}*\n\nИнгредиенты:\n" + "\n".join(recipe.get('ingredients', []))
    text += f"\n\nИнструкция:\n{recipe.get('instructions', '')}"
    await query.edit_message_text(text, parse_mode="Markdown")

# --- Редактирование рецепта ---
async def recipe_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = getattr(update, 'callback_query', None)
    if not query or not hasattr(query, 'data'):
        return
    await query.answer()
    recipe_id = query.data.replace("recipe_edit_", "")
    recipe = recipe_service.get_recipe_by_id(recipe_id)
    if not recipe:
        await query.edit_message_text("❌ Рецепт не найден.")
        return
    await query.edit_message_text("✏️ Функция редактирования будет добавлена в следующем обновлении!")
    logger.info(f"Попытка редактировать рецепт {recipe_id}")

# --- Удаление рецепта ---
async def recipe_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = getattr(update, 'callback_query', None)
    if not query or not hasattr(query, 'data'):
        return
    await query.answer()
    recipe_id = query.data.replace("recipe_delete_confirm_", "")
    recipe = recipe_service.get_recipe_by_id(recipe_id)
    if not recipe:
        await query.edit_message_text("❌ Рецепт не найден. Удаление невозможно.")
        return
    deleted = recipe_service.delete_recipe_by_id(recipe_id)
    if deleted:
        await query.edit_message_text("✅ Рецепт успешно удалён! Возвращаемся к списку рецептов...")
        logger.info(f"Рецепт {recipe_id} удалён")
    else:
        await query.edit_message_text("❌ Не удалось удалить рецепт. Возможно, он уже был удалён.")
        logger.warning(f"Не удалось удалить рецепт: {recipe_id}")

async def recipe_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = getattr(update, 'callback_query', None)
    if not query or not hasattr(query, 'data'):
        return
    await query.answer()
    recipe_id = query.data.replace("recipe_delete_", "").replace("confirm_", "")
    # Здесь можно реализовать подтверждение через отдельную клавиатуру
    await query.edit_message_text(
        text="❗ Вы уверены, что хотите удалить этот рецепт? Это действие необратимо!",
        # reply_markup=KeyboardFactory.get_confirmation_keyboard("recipe_delete_confirm", recipe_id)
        reply_markup=None
    )
    logger.info(f"Пользователь инициировал удаление рецепта {recipe_id}")

# --- Редактирование, удаление, избранное и другие действия можно вынести аналогично --- 