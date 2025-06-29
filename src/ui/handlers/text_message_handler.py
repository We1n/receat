"""
Унифицированный обработчик текстовых сообщений для EatBot
Обрабатывает текстовые сообщения в различных состояниях (ConversationHandler)
"""
import logging
from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from src.ui.ui_service import ui_service
from src.ui.messages_main import Messages as RawMessages
from src.services.recipe_service import RecipeService
from src.validators.input_handler import input_handler, handle_input_errors
from src.validators.schemas import ValidationErrorResponse
from src.config.states import PRODUCT_ADD, PRODUCT_SEARCH, RECIPE_SEARCH, RECIPE_ADD
from src.ui.keyboards.factory import KeyboardFactory

# Правильная типизация Messages
Messages: Dict[str, Any] = RawMessages

logger = logging.getLogger(__name__)

# Инициализация сервисов
recipe_service = RecipeService()

@handle_input_errors
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Унифицированный обработчик текстовых сообщений"""
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
        await handle_product_search(update, context, text)
        return
    elif state == RECIPE_SEARCH:
        await handle_recipe_search(update, context, text)
        return
    elif state == RECIPE_ADD:
        await handle_recipe_add(update, context, text)
        return
    elif state == "editing_recipe_name":
        await handle_recipe_edit_name(update, context, text)
        return
    elif state == "editing_recipe_ingredients":
        await handle_recipe_edit_ingredients(update, context, text)
        return
    elif state == "editing_recipe_instructions":
        await handle_recipe_edit_instructions(update, context, text)
        return
    elif state == "editing_product_name":
        await handle_product_edit_name(update, context, text)
        return
    elif state == "editing_product_category":
        await handle_product_edit_category(update, context, text)
        return
    elif state == "editing_product_nutrition":
        await handle_product_edit_nutrition(update, context, text)
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

async def handle_product_search(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Унифицированная обработка поиска продуктов"""
    user_id = update.effective_user.id if update.effective_user else None
    logger.info(f"[Поиск продуктов] Пользователь {user_id} ищет: {text}")
    
    try:
        from src.services.product_service import ProductService
        product_service = ProductService()
        
        # Простой поиск по названию продукта
        all_products = product_service.get_all_products()
        
        if not all_products:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="🍏 У вас пока нет добавленных продуктов.\n\n💡 Добавьте свой первый продукт!",
                reply_markup=KeyboardFactory.get("navigation")
            )
            return
        
        # Фильтруем продукты по запросу
        query = text.lower().strip()
        matching_products = []
        
        for product in all_products:
            product_name = product.get('name', '').lower()
            if query in product_name:
                matching_products.append(product)
        
        if not matching_products:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=f"🍏 По запросу '{text}' ничего не найдено.\n\n💡 Попробуйте:\n• Другие названия\n• Проверить написание\n• Более простые запросы",
                reply_markup=KeyboardFactory.get("navigation")
            )
            return
        
        # Сохраняем поисковый запрос для пагинации
        if context.user_data is None:
            context.user_data = {}
        context.user_data['product_search_query'] = text
        
        # Используем унифицированную клавиатуру для результатов поиска
        from src.ui.keyboards.factory import KeyboardFactory, CallbackDataBuilder
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = []
        for product in matching_products[:5]:  # Показываем первые 5 результатов
            product_id = product.get('id')
            product_name = product.get('name', 'Без названия')
            if product_id:
                keyboard.append([
                    InlineKeyboardButton(
                        product_name, 
                        callback_data=CallbackDataBuilder.build("products", "view", id=product_id)
                    )
                ])
        
        # Добавляем навигационные кнопки
        keyboard.extend(KeyboardFactory._get_navigation_row())
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"🍏 *Результаты поиска:* '{text}'\n\nНайдено продуктов: {len(matching_products)}\nВыберите продукт для просмотра:",
            reply_markup=reply_markup
        )
        logger.info(f"[Поиск продуктов] Найдено {len(matching_products)} продуктов для пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"[Поиск продуктов] Ошибка: {e}", exc_info=True)
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Произошла ошибка при поиске продуктов. Попробуйте позже или обратитесь в поддержку.",
            reply_markup=KeyboardFactory.get("navigation")
        )
    finally:
        if isinstance(context.user_data, dict):
            context.user_data["state"] = None

async def handle_recipe_search(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Унифицированная обработка поиска рецептов"""
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
                text=f"🔍 По запросу '{text}' ничего не найдено.\n\n💡 Попробуйте:\n• Другие ингредиенты\n• Проверить написание\n• Более простые запросы",
                reply_markup=None
            )
            return
        
        # Сохраняем поисковый запрос для пагинации
        if context.user_data is None:
            context.user_data = {}
        context.user_data['recipe_search_query'] = text
        
        # Используем унифицированную клавиатуру для результатов поиска
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
                    "◀️", 
                    callback_data=CallbackDataBuilder.build("recipes", "search_results", page=1, query=text)
                ),
                InlineKeyboardButton(f"1/{total_pages}", callback_data="no_action"),
                InlineKeyboardButton(
                    "▶️", 
                    callback_data=CallbackDataBuilder.build("recipes", "search_results", page=2, query=text)
                )
            ])
        
        # Добавляем навигационные кнопки
        keyboard.extend(KeyboardFactory._get_navigation_row())
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"🔍 *Результаты поиска:* '{text}'\n\nНайдено рецептов: {total}\nВыберите рецепт для просмотра:",
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

async def handle_recipe_add(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка добавления рецепта через ConversationHandler"""
    # Этот метод будет вызываться из ConversationHandler
    # Здесь можно добавить дополнительную логику если нужно
    logger.info(f"[Добавление рецепта] Получен текст: {text}")
    
    # Передаем управление в ConversationHandler
    from src.ui.handlers.conversation_handlers import RecipeConversationHandler
    conversation_handler = RecipeConversationHandler()
    
    # Определяем текущий этап добавления рецепта
    if context.user_data is None:
        context.user_data = {}
    recipe_data = context.user_data.get('recipe_data', {})
    
    if 'name' not in recipe_data:
        # Этап ввода названия
        return await conversation_handler.handle_recipe_name(update, context)
    elif 'ingredients' not in recipe_data or not recipe_data['ingredients']:
        # Этап ввода ингредиентов
        return await conversation_handler.handle_recipe_ingredients(update, context)
    elif 'instructions' not in recipe_data:
        # Этап ввода инструкций
        return await conversation_handler.handle_recipe_instructions(update, context)
    else:
        # Все данные введены, показываем подтверждение
        return await conversation_handler.handle_recipe_confirm(update, context)

async def handle_general_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка обычных сообщений"""
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=f"💬 Получено сообщение: {text}\n\nИспользуйте меню для навигации."
    )

async def handle_recipe_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка редактирования названия рецепта"""
    user_id = update.effective_user.id if update.effective_user else None
    logger.info(f"[Редактирование рецепта] Пользователь {user_id} редактирует название: {text}")
    
    try:
        if context.user_data is None:
            context.user_data = {}
        
        recipe_id = context.user_data.get('editing_recipe_id')
        if not recipe_id:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Ошибка: ID рецепта не найден",
                reply_markup=KeyboardFactory.get("navigation")
            )
            return
        
        # Валидация названия
        if len(text.strip()) < 3:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Название должно содержать минимум 3 символа",
                reply_markup=KeyboardFactory.get("recipe_edit_field")
            )
            return
        
        # Сохраняем обновленное название
        if 'updated_recipe_data' not in context.user_data:
            context.user_data['updated_recipe_data'] = {}
        context.user_data['updated_recipe_data']['name'] = text.strip()
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"✅ Название обновлено на: «{text.strip()}»\n\nТеперь вы можете продолжить редактирование или сохранить изменения.",
            reply_markup=KeyboardFactory.get("recipe_edit_confirm", id=recipe_id)
        )
        
        # Сбрасываем состояние
        context.user_data['state'] = None
        
    except Exception as e:
        logger.error(f"[Редактирование рецепта] Ошибка: {e}", exc_info=True)
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Произошла ошибка при редактировании названия",
            reply_markup=KeyboardFactory.get("navigation")
        )

async def handle_recipe_edit_ingredients(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка редактирования ингредиентов рецепта"""
    user_id = update.effective_user.id if update.effective_user else None
    logger.info(f"[Редактирование рецепта] Пользователь {user_id} редактирует ингредиенты")
    
    try:
        if context.user_data is None:
            context.user_data = {}
        
        recipe_id = context.user_data.get('editing_recipe_id')
        if not recipe_id:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Ошибка: ID рецепта не найден",
                reply_markup=KeyboardFactory.get("navigation")
            )
            return
        
        # Парсим ингредиенты
        ingredients = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not ingredients:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Список ингредиентов не может быть пустым",
                reply_markup=KeyboardFactory.get("recipe_edit_field")
            )
            return
        
        # Сохраняем обновленные ингредиенты
        if 'updated_recipe_data' not in context.user_data:
            context.user_data['updated_recipe_data'] = {}
        context.user_data['updated_recipe_data']['ingredients'] = ingredients
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"✅ Ингредиенты обновлены!\n\nДобавлено ингредиентов: {len(ingredients)}\n\nТеперь вы можете продолжить редактирование или сохранить изменения.",
            reply_markup=KeyboardFactory.get("recipe_edit_confirm", id=recipe_id)
        )
        
        # Сбрасываем состояние
        context.user_data['state'] = None
        
    except Exception as e:
        logger.error(f"[Редактирование рецепта] Ошибка: {e}", exc_info=True)
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Произошла ошибка при редактировании ингредиентов",
            reply_markup=KeyboardFactory.get("navigation")
        )

async def handle_recipe_edit_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка редактирования инструкций рецепта"""
    user_id = update.effective_user.id if update.effective_user else None
    logger.info(f"[Редактирование рецепта] Пользователь {user_id} редактирует инструкции")
    
    try:
        if context.user_data is None:
            context.user_data = {}
        
        recipe_id = context.user_data.get('editing_recipe_id')
        if not recipe_id:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Ошибка: ID рецепта не найден",
                reply_markup=KeyboardFactory.get("navigation")
            )
            return
        
        # Валидация инструкций
        if len(text.strip()) < 10:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Инструкции должны содержать минимум 10 символов",
                reply_markup=KeyboardFactory.get("recipe_edit_field")
            )
            return
        
        # Сохраняем обновленные инструкции
        if 'updated_recipe_data' not in context.user_data:
            context.user_data['updated_recipe_data'] = {}
        context.user_data['updated_recipe_data']['instructions'] = text.strip()
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"✅ Инструкции обновлены!\n\nТеперь вы можете продолжить редактирование или сохранить изменения.",
            reply_markup=KeyboardFactory.get("recipe_edit_confirm", id=recipe_id)
        )
        
        # Сбрасываем состояние
        context.user_data['state'] = None
        
    except Exception as e:
        logger.error(f"[Редактирование рецепта] Ошибка: {e}", exc_info=True)
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Произошла ошибка при редактировании инструкций",
            reply_markup=KeyboardFactory.get("navigation")
        )

async def handle_product_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка редактирования названия продукта"""
    user_id = update.effective_user.id if update.effective_user else None
    logger.info(f"[Редактирование продукта] Пользователь {user_id} редактирует название: {text}")
    
    try:
        if context.user_data is None:
            context.user_data = {}
        
        product_id = context.user_data.get('editing_product_id')
        if not product_id:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Ошибка: ID продукта не найден",
                reply_markup=KeyboardFactory.get("navigation")
            )
            return
        
        # Валидация названия
        if len(text.strip()) < 3:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Название должно содержать минимум 3 символа",
                reply_markup=KeyboardFactory.get("product_edit_field")
            )
            return
        
        # Сохраняем обновленное название
        if 'updated_product_data' not in context.user_data:
            context.user_data['updated_product_data'] = {}
        context.user_data['updated_product_data']['name'] = text.strip()
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"✅ Название обновлено на: «{text.strip()}»\n\nТеперь вы можете продолжить редактирование или сохранить изменения.",
            reply_markup=KeyboardFactory.get("product_edit_confirm", id=product_id)
        )
        
        # Сбрасываем состояние
        context.user_data['state'] = None
        
    except Exception as e:
        logger.error(f"[Редактирование продукта] Ошибка: {e}", exc_info=True)
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Произошла ошибка при редактировании названия",
            reply_markup=KeyboardFactory.get("navigation")
        )

async def handle_product_edit_category(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка редактирования категории продукта"""
    user_id = update.effective_user.id if update.effective_user else None
    logger.info(f"[Редактирование продукта] Пользователь {user_id} редактирует категорию: {text}")
    
    try:
        if context.user_data is None:
            context.user_data = {}
        
        product_id = context.user_data.get('editing_product_id')
        if not product_id:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Ошибка: ID продукта не найден",
                reply_markup=KeyboardFactory.get("navigation")
            )
            return
        
        # Валидация категории
        if len(text.strip()) < 2:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Категория должна содержать минимум 2 символа",
                reply_markup=KeyboardFactory.get("product_edit_field")
            )
            return
        
        # Сохраняем обновленную категорию
        if 'updated_product_data' not in context.user_data:
            context.user_data['updated_product_data'] = {}
        context.user_data['updated_product_data']['category'] = text.strip()
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"✅ Категория обновлена на: «{text.strip()}»\n\nТеперь вы можете продолжить редактирование или сохранить изменения.",
            reply_markup=KeyboardFactory.get("product_edit_confirm", id=product_id)
        )
        
        # Сбрасываем состояние
        context.user_data['state'] = None
        
    except Exception as e:
        logger.error(f"[Редактирование продукта] Ошибка: {e}", exc_info=True)
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Произошла ошибка при редактировании категории",
            reply_markup=KeyboardFactory.get("navigation")
        )

async def handle_product_edit_nutrition(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка редактирования пищевой ценности продукта"""
    user_id = update.effective_user.id if update.effective_user else None
    logger.info(f"[Редактирование продукта] Пользователь {user_id} редактирует пищевую ценность")
    
    try:
        if context.user_data is None:
            context.user_data = {}
        
        product_id = context.user_data.get('editing_product_id')
        if not product_id:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Ошибка: ID продукта не найден",
                reply_markup=KeyboardFactory.get("navigation")
            )
            return
        
        # Парсим пищевую ценность
        nutrition_data = {}
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            if ':' in line:
                key, value_str = line.split(':', 1)
                key = key.strip().lower()
                try:
                    value = float(value_str.strip())
                    nutrition_data[key] = value
                except ValueError:
                    continue
        
        # Проверяем наличие основных полей
        if not nutrition_data:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Не удалось распознать пищевую ценность. Проверьте формат.",
                reply_markup=KeyboardFactory.get("product_edit_field")
            )
            return
        
        # Сохраняем обновленную пищевую ценность
        if 'updated_product_data' not in context.user_data:
            context.user_data['updated_product_data'] = {}
        context.user_data['updated_product_data']['nutrition'] = nutrition_data
        
        # Формируем текст подтверждения
        nutrition_text = "\n".join([f"• {key.capitalize()}: {value}" for key, value in nutrition_data.items()])
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"✅ Пищевая ценность обновлена!\n\n{nutrition_text}\n\nТеперь вы можете продолжить редактирование или сохранить изменения.",
            reply_markup=KeyboardFactory.get("product_edit_confirm", id=product_id)
        )
        
        # Сбрасываем состояние
        context.user_data['state'] = None
        
    except Exception as e:
        logger.error(f"[Редактирование продукта] Ошибка: {e}", exc_info=True)
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Произошла ошибка при редактировании пищевой ценности",
            reply_markup=KeyboardFactory.get("navigation")
        )

def register_text_message_handlers(application):
    """Регистрация унифицированных обработчиков текстовых сообщений"""
    # Обработчик текстовых сообщений (должен быть одним из последних)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Унифицированные обработчики текстовых сообщений зарегистрированы") 