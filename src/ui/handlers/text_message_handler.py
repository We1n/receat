"""
Обработчик текстовых сообщений для EatBot
Обрабатывает только текстовые сообщения в различных состояниях (ConversationHandler)
"""
import logging
from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from src.ui.ui_service import ui_service
from src.ui.messages_main import Messages as RawMessages
from src.services.nutrient_analysis import NutrientAnalysisService
from src.services.recipe_service import RecipeService
from src.validators.input_handler import input_handler, handle_input_errors
from src.validators.schemas import ValidationErrorResponse
from src.config.states import PRODUCT_ADD, PRODUCT_SEARCH, RECIPE_SEARCH, NUTRIENT_CALCULATOR
from src.utils.recipe_utils import calculate_nutrients_from_text

# Правильная типизация Messages
Messages: Dict[str, Any] = RawMessages

logger = logging.getLogger(__name__)

# Инициализация сервисов
nutrient_analyzer = NutrientAnalysisService()
recipe_service = RecipeService()

@handle_input_errors
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик текстовых сообщений"""
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

    # Обработка в зависимости от состояния
    if state == PRODUCT_ADD:
        await handle_product_add(update, context, text)
        return
    elif state == PRODUCT_SEARCH:
        pass
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
    """Обработка поиска рецептов по ингредиенту"""
    user_id = update.effective_user.id if update.effective_user else None
    logger.info(f"[Поиск рецептов] Пользователь {user_id} ищет: {text}")
    
    try:
        from src.services.recipe_search_service import RecipeSearchService
        recipe_search_service = RecipeSearchService(recipe_service=recipe_service)
        recipes, total = await recipe_search_service.search_recipes(query=text, page=1, per_page=5)
        
        if not recipes:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=f"🔍 По запросу '{text}' ничего не найдено.\n\nПопробуйте другие ингредиенты или проверьте написание.",
                reply_markup=None
            )
            return
        
        # Сохраняем поисковый запрос для пагинации
        if context.user_data is None:
            context.user_data = {}
        context.user_data['recipe_search_query'] = text
        
        # Формируем список рецептов
        from src.ui.keyboards.factory import KeyboardFactory, CallbackDataBuilder
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = []
        for recipe in recipes:
            recipe_id = recipe.get('id')
            recipe_name = recipe.get('name', 'Без названия')
            if recipe_id:
                keyboard.append([
                    InlineKeyboardButton(
                        recipe_name, 
                        callback_data=CallbackDataBuilder.build("recipes", "view", id=recipe_id)
                    )
                ])
        
        # Добавляем пагинацию если нужно
        total_pages = (total + 4) // 5
        if total_pages > 1:
            keyboard.append([
                InlineKeyboardButton(
                    "⬅️ Назад", 
                    callback_data=CallbackDataBuilder.build("recipes", "search_page", page=1)
                ),
                InlineKeyboardButton(
                    "Вперёд ➡️", 
                    callback_data=CallbackDataBuilder.build("recipes", "search_page", page=2)
                )
            ])
        
        # Добавляем навигационные кнопки
        keyboard.append([
            InlineKeyboardButton(
                "◀️ Назад", 
                callback_data=CallbackDataBuilder.build("nav", "back")
            ),
            InlineKeyboardButton(
                "🏠 Главное меню", 
                callback_data=CallbackDataBuilder.build("nav", "main_menu")
            )
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"🔍 Найдено рецептов: {total}.\nВыберите рецепт для просмотра:",
            reply_markup=reply_markup
        )
        logger.info(f"[Поиск рецептов] Найдено {total} рецептов для пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"[Поиск рецептов] Ошибка: {e}", exc_info=True)
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Произошла ошибка при поиске рецептов. Попробуйте позже или обратитесь в поддержку.",
            reply_markup=None
        )
    finally:
        if isinstance(context.user_data, dict):
            context.user_data["state"] = None

async def handle_nutrient_calculator(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка калькулятора БЖУ через унифицированный сервис"""
    user_id = update.effective_user.id if update.effective_user else None
    logger.info(f"[Калькулятор БЖУ] Пользователь {user_id} отправил: {text}")
    try:
        result = calculate_nutrients_from_text(text)
        # Преобразование результата в текст для отправки пользователю
        if not result.get('success'):
            result_text = result.get('error', 'Ошибка расчёта.')
        else:
            lines = []
            if result.get('info'):
                lines.extend(result['info'])
            lines.extend(result['results_by_product'])
            if result.get('not_found'):
                lines.append('❗ Не найдены продукты: ' + ', '.join(result['not_found']))
            total = result['total']
            lines.append(f"\nИтого: {total['calories']:.1f} ккал, Б:{total['protein']:.1f} Ж:{total['fat']:.1f} У:{total['carbs']:.1f}")
            result_text = '\n'.join(lines)
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=result_text,
            reply_markup=None,
            parse_mode="Markdown"
        )
        logger.info(f"[Калькулятор БЖУ] Расчет выполнен для пользователя {user_id}")
    except Exception as e:
        logger.error(f"[Калькулятор БЖУ] Ошибка расчета: {e}")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Произошла ошибка при расчете БЖУ. Попробуйте еще раз или обратитесь в поддержку.",
            reply_markup=None
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

def register_text_message_handlers(application):
    """Регистрация обработчиков текстовых сообщений"""
    # Обработчик текстовых сообщений (должен быть одним из последних)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Обработчики текстовых сообщений зарегистрированы") 