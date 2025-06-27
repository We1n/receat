"""
Обработчики для работы с продуктами (адаптация под telegram.ext)
"""
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
)
from src.services.product_service import ProductService
from src.ui.keyboards import KeyboardFactory
from src.ui.messages_main import Messages
from src.ui.ui_service import ui_service
from telegram.error import BadRequest
from src.validators.input_handler import InputHandler
from src.validators.schemas import ProductDTO, ProductSearchDTO, ProductCalculatorDTO
from src.config.states import PRODUCT_SEARCH, NUTRIENT_CALCULATOR
import os, json

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
(
    WAITING_FOR_ADD,
    WAITING_FOR_EDIT,
    WAITING_FOR_CALCULATOR,
) = range(3)

# Добавляю состояние для поиска продукта
SEARCH_PRODUCT = 100

product_service = ProductService()
input_handler = InputHandler()

# Регистрация обработчиков
def register_product_handlers(application):
    application.add_handler(CommandHandler("products", show_products_menu))
    application.add_handler(CallbackQueryHandler(show_products_menu, pattern="^products$"))
    application.add_handler(CallbackQueryHandler(show_product_search_menu, pattern="^product_search$"))
    application.add_handler(CallbackQueryHandler(show_product_add_menu, pattern="^product_add$"))
    application.add_handler(CallbackQueryHandler(show_product_categories_menu, pattern="^product_categories$"))
    application.add_handler(CallbackQueryHandler(show_product_calculator_menu, pattern="^product_calculator$"))
    application.add_handler(CallbackQueryHandler(product_category_view, pattern="^product_category_"))
    application.add_handler(CallbackQueryHandler(product_edit_menu, pattern="^product_edit_"))
    application.add_handler(CallbackQueryHandler(product_delete_confirm, pattern="^product_delete_"))
    application.add_handler(CallbackQueryHandler(product_delete, pattern="^product_delete_confirm_"))
    application.add_handler(CallbackQueryHandler(product_calculator_add, pattern="^product_calculator_add_"))
    application.add_handler(CallbackQueryHandler(product_nutrients_view, pattern="^product_nutrients_"))
    
    # ConversationHandler для добавления продуктов
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(show_product_add_menu, pattern="^product_add$")],
        states={
            WAITING_FOR_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_add)],
            WAITING_FOR_EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_edit)],
            WAITING_FOR_CALCULATOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_calculator)],
        },
        fallbacks=[CallbackQueryHandler(show_products_menu, pattern="^products$")],
        per_message=False
    )
    application.add_handler(conv_handler)

# Меню продуктов
async def show_products_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=Messages["PRODUCTS"]["menu"],
        reply_markup=KeyboardFactory.get("products_menu")
    )
    logger.info("Показано меню продуктов")

# Меню поиска продуктов
async def show_product_search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=Messages["PRODUCTS"]["search"],
        reply_markup=KeyboardFactory.get("back")
    )
    
    if context.user_data is not None:
        context.user_data["state"] = PRODUCT_SEARCH
    logger.info("Пользователь открыл меню поиска продуктов")

# Меню добавления продукта
async def show_product_add_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=Messages["PRODUCTS"]["add"],
        reply_markup=KeyboardFactory.get("back")
    )
    
    if context.user_data is not None:
        context.user_data["state"] = WAITING_FOR_ADD
    logger.info("Пользователь открыл меню добавления продукта")

# Меню категорий продуктов
async def show_product_categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    
    categories = product_service.get_categories()
    if not categories:
        text = "📋 *Категории продуктов*\n\nКатегории не найдены."
        keyboard = KeyboardFactory.get("back")
    else:
        text = "📋 *Категории продуктов*\n\nВыберите категорию:"
        keyboard = []
        
        # Группируем категории по 2 в ряд
        for i in range(0, len(categories), 2):
            row = []
            row.append(InlineKeyboardButton(categories[i], callback_data=f"product_category_{categories[i]}"))
            
            # Добавляем вторую категорию в ряд, если она есть
            if i + 1 < len(categories):
                row.append(InlineKeyboardButton(categories[i + 1], callback_data=f"product_category_{categories[i + 1]}"))
            
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="products")])
        keyboard = InlineKeyboardMarkup(keyboard)
    
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=text,
        reply_markup=keyboard
    )
    logger.info("Показано меню категорий продуктов")

# Меню калькулятора продуктов
async def show_product_calculator_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=(
            "🧮 *Калькулятор БЖУ*\n\n"
            "Введите продукт и вес, либо список ингредиентов (каждый с новой строкой).\n\n"
            "_Пример:_\n"
            "100 г овсяные хлопья\n"
            "1 яблоко\n"
            "200 мл молоко\n"
            "1 ч.л. мёд"
        ),
        reply_markup=KeyboardFactory.get("back")
    )
    if context.user_data is not None:
        context.user_data["state"] = NUTRIENT_CALCULATOR
    logger.info("Показано меню универсального калькулятора БЖУ")

# Просмотр продуктов по категории
async def product_category_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not getattr(query, 'data', None):
        return
    await query.answer()
    category_data = query.data
    if not category_data or not isinstance(category_data, str):
        return
    category = category_data.replace("product_category_", "")
    products = await product_service.get_products_by_category(category)
    
    if not products:
        text = f"📋 *Продукты в категории '{category}'*\n\nПродукты не найдены."
        keyboard = KeyboardFactory.get("back")
    else:
        text = f"📋 *Продукты в категории '{category}'*\n\n"
        keyboard = []
        
        # Группируем продукты по 2 в ряд
        for i in range(0, len(products), 2):
            row = []
            row.append(InlineKeyboardButton(products[i]['name'], callback_data=f"product_edit_{products[i]['id']}"))
            
            # Добавляем второй продукт в ряд, если он есть
            if i + 1 < len(products):
                row.append(InlineKeyboardButton(products[i + 1]['name'], callback_data=f"product_edit_{products[i + 1]['id']}"))
            
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="product_categories")])
        keyboard = InlineKeyboardMarkup(keyboard)
    
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=text,
        reply_markup=keyboard
    )
    logger.info(f"Показаны продукты категории: {category}")

# Меню редактирования продукта
async def product_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not getattr(query, 'data', None):
        return
    logger.info(f"product_edit_menu вызван, query.data: {query.data}")
    await query.answer()
    product_data = query.data
    if not product_data or not isinstance(product_data, str):
        return
    product_id = int(product_data.replace("product_edit_", ""))
    if context.user_data is not None:
        context.user_data["product_id"] = product_id
    product = await product_service.get_product(product_id)
    
    if not product:
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=Messages["ERRORS"]["not_found"],
            reply_markup=KeyboardFactory.get("products_menu")
        )
        logger.error(f"Продукт не найден для редактирования: {product_id}")
        return
    
    text = f"✏️ *Редактирование продукта*\n\n"
    text += f"Название: {product['name']}\n"
    text += f"Категория: {product.get('category', 'Не указана')}\n"
    text += f"Калории: {product.get('nutrients', {}).get('calories', 0)} ккал\n"
    text += f"Белки: {product.get('nutrients', {}).get('protein', 0)}г\n"
    text += f"Жиры: {product.get('nutrients', {}).get('fat', 0)}г\n"
    text += f"Углеводы: {product.get('nutrients', {}).get('carbs', 0)}г"
    
    keyboard = [
        [
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"product_edit_start_{product_id}"),
            InlineKeyboardButton("🗑 Удалить", callback_data=f"product_delete_{product_id}")
        ],
        [
            InlineKeyboardButton("🧮 Калькулятор", callback_data=f"product_calculator_add_{product_id}"),
            InlineKeyboardButton("📊 Нутриенты", callback_data=f"product_nutrients_{product_id}")
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="products")]
    ]
    
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    logger.info(f"Показано меню редактирования продукта {product_id}")

# Подтверждение удаления продукта
async def product_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not getattr(query, 'data', None):
        return
    logger.info(f"[DEBUG] product_delete_confirm callback_data: {getattr(query, 'data', None)}")
    await query.answer()
    delete_data = query.data
    if not delete_data or not isinstance(delete_data, str):
        return
    if not delete_data.startswith("product_delete_"):
        logger.error(f"Некорректный формат callback_data для удаления продукта: {delete_data}")
        return
    product_id = int(delete_data.replace("product_delete_", ""))
    product = await product_service.get_product(product_id)
    if not product:
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=Messages["ERRORS"]["not_found"],
            reply_markup=KeyboardFactory.get("products_menu")
        )
        logger.error(f"Продукт не найден для удаления: {product_id}")
        return
    text = f"🗑 *Удаление продукта*\n\n"
    text += f"Вы уверены, что хотите удалить продукт {product['name']}?\n"
    text += "Это действие нельзя отменить."
    reply_markup = KeyboardFactory.get_confirmation_keyboard("product_delete_confirm", product_id)
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=text,
        reply_markup=reply_markup
    )
    logger.info(f"Запрошено подтверждение удаления продукта {product_id}")

# Удаление продукта
async def product_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("[DEBUG] Вход в product_delete")
    query = update.callback_query
    if not query or not getattr(query, 'data', None):
        logger.error("Нет query или data в product_delete")
        return
    logger.info(f"[DEBUG] product_delete callback_data: {getattr(query, 'data', None)}")
    logger.info(f"[DEBUG] product_delete products_file: {getattr(product_service, 'products_file', None)}")
    file_path = getattr(product_service, 'products_file', None)
    if file_path:
        try:
            can_write = os.access(str(file_path), os.W_OK)
            logger.info(f"[DEBUG] product_delete file write access: {can_write}")
        except Exception as e:
            logger.error(f"[DEBUG] Ошибка проверки прав на запись: {e}")
        try:
            with open(file_path, encoding="utf-8") as f:
                before = f.read()
            logger.info(f"[DEBUG] product_delete file before: {before}")
        except Exception as e:
            logger.error(f"[DEBUG] Ошибка чтения файла до удаления: {e}")
    await query.answer()
    delete_data = query.data
    if not delete_data or not delete_data.startswith("product_delete_confirm_"):
        logger.error(f"Некорректный формат callback_data для product_delete: {delete_data}")
        return
    product_id = int(delete_data.replace("product_delete_confirm_", ""))
    logger.info(f"[Удаление продукта] Попытка удалить продукт с ID: {product_id}")
    try:
        logger.info(f"[Удаление продукта] Продукты до удаления: {[p['id'] for p in getattr(product_service, 'data', {}).get('products', [])]}")
        deleted = await product_service.delete_product(product_id)
        logger.info(f"[Удаление продукта] Результат удаления: {deleted}")
        logger.info(f"[Удаление продукта] Продукты после удаления: {[p['id'] for p in getattr(product_service, 'data', {}).get('products', [])]}")
        if hasattr(product_service, 'invalidate_cache'):
            try:
                await product_service.invalidate_cache()
                logger.info("[DEBUG] product_delete cache invalidated")
            except Exception as e:
                logger.error(f"[DEBUG] Ошибка сброса кэша: {e}")
        if file_path:
            try:
                with open(file_path, encoding="utf-8") as f:
                    after = f.read()
                logger.info(f"[DEBUG] product_delete file after: {after}")
            except Exception as e:
                logger.error(f"[DEBUG] Ошибка чтения файла после удаления: {e}")
        if deleted:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=Messages["SUCCESS"]["deleted"],
                reply_markup=KeyboardFactory.get("products_menu")
            )
            logger.info(f"Продукт удалён: {product_id}")
        else:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=Messages["ERRORS"]["not_found"],
                reply_markup=KeyboardFactory.get("products_menu")
            )
            logger.error(f"Ошибка удаления продукта: {product_id}")
    except Exception as e:
        logger.exception(f"Исключение при удалении продукта {product_id}: {e}")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"❌ Произошла ошибка при удалении продукта: {e}",
            reply_markup=KeyboardFactory.get("products_menu")
        )
    logger.info("[DEBUG] Выход из product_delete")

# Добавление продукта в калькулятор
async def product_calculator_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает добавление продукта в калькулятор и запрашивает количество."""
    query = update.callback_query
    if not query or not getattr(query, 'data', None):
        return ConversationHandler.END
    await query.answer()
    try:
        calc_data = query.data
        if not calc_data or not isinstance(calc_data, str):
            return ConversationHandler.END
        product_id = int(calc_data.split('_')[-1])
        # Сохраняем ID продукта для следующего шага (handle_product_calculator)
        if context.user_data is not None:
            context.user_data["product_id"] = product_id
        product = await product_service.get_product(product_id)
        if not product:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=Messages["ERRORS"]["not_found"],
                reply_markup=KeyboardFactory.get("back")
            )
            return ConversationHandler.END
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"Введите количество для продукта '{product['name']}' в граммах:",
            reply_markup=KeyboardFactory.get("back")
        )
        # Устанавливаем состояние ожидания текстового сообщения от пользователя с количеством
        return WAITING_FOR_CALCULATOR
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка обработки callback'а product_calculator_add: {e}")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова.",
            reply_markup=KeyboardFactory.get("back")
        )
        return ConversationHandler.END

# Добавление продукта
async def handle_product_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик добавления продукта с валидацией через InputHandler"""
    try:
        # Валидация входящих данных через InputHandler
        validation_result = await input_handler.validate_text_input(
            update, 
            ProductDTO, 
            "product_add",
            context
        )
        
        if not validation_result.is_valid:
            return
        
        product_data = validation_result.data
        
        # Добавление продукта через сервис
        product_id = product_service.add_product(
            product_data.name,
            product_data.category,
            product_data.nutrients.dict(),
            unit="г",
            description="",
            emoji=""
        )
        
        if product_id:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=Messages["SUCCESS"]["created"],
                reply_markup=KeyboardFactory.get("products_menu")
            )
            logger.info(f"Продукт добавлен: {product_id}")
        else:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=Messages["ERRORS"]["invalid_input"],
                reply_markup=KeyboardFactory.get("back")
            )
            logger.error("Ошибка добавления продукта")
            
    except Exception as e:
        await input_handler.handle_validation_error(
            update, 
            context, 
            f"Ошибка при добавлении продукта: {str(e)}",
            "products_menu"
        )
        logger.exception("Ошибка при добавлении продукта")
    finally:
        if context.user_data is not None:
            context.user_data["state"] = None

# Редактирование продукта
async def handle_product_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик редактирования продукта с валидацией через InputHandler"""
    try:
        product_id = context.user_data.get("product_id") if context.user_data else None
        if not product_id:
            await input_handler.handle_validation_error(
                update, 
                context, 
                "ID продукта не найден при редактировании",
                "products_menu"
            )
            logger.warning("ID продукта не найден при редактировании")
            return
        
        # Валидация входящих данных через InputHandler
        validation_result = await input_handler.validate_text_input(
            update, 
            ProductDTO, 
            "product_edit",
            context
        )
        
        if not validation_result.is_valid:
            return
        
        product_data = validation_result.data
        
        # Обновление продукта через сервис
        if product_service.update_product(product_id, product_data.dict()):
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=Messages["SUCCESS"]["updated"],
                reply_markup=KeyboardFactory.get("products_menu")
            )
            logger.info(f"Продукт обновлен: {product_id}")
        else:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=Messages["ERRORS"]["not_found"],
                reply_markup=KeyboardFactory.get("products_menu")
            )
            logger.error(f"Ошибка обновления продукта: {product_id}")
            
    except Exception as e:
        await input_handler.handle_validation_error(
            update, 
            context, 
            f"Ошибка при редактировании продукта: {str(e)}",
            "products_menu"
        )
        logger.exception("Ошибка при редактировании продукта")
    finally:
        if context.user_data is not None:
            context.user_data["state"] = None

# Калькулятор продуктов
async def handle_product_calculator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик калькулятора продуктов с валидацией через InputHandler"""
    try:
        # Валидация входящих данных через InputHandler
        validation_result = await input_handler.validate_text_input(
            update, 
            ProductCalculatorDTO, 
            "product_calculator",
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
                "ID продукта не найден в калькуляторе",
                "products_menu"
            )
            return
        
        product = await product_service.get_product(product_id)
        if not product:
            await input_handler.handle_validation_error(
                update, 
                context, 
                "Продукт не найден",
                "products_menu"
            )
            return
        
        # Расчет нутриентов
        nutrients = product.get("nutrients", {})
        calculated_nutrients = {}
        for nutrient, value in nutrients.items():
            calculated_nutrients[nutrient] = (value * amount) / 100
        
        text = f"🧮 *Калькулятор БЖУ*\n\n"
        text += f"Продукт: {product['name']}\n"
        text += f"Количество: {amount}г\n\n"
        text += f"Калории: {calculated_nutrients.get('calories', 0):.1f} ккал\n"
        text += f"Белки: {calculated_nutrients.get('protein', 0):.1f}г\n"
        text += f"Жиры: {calculated_nutrients.get('fat', 0):.1f}г\n"
        text += f"Углеводы: {calculated_nutrients.get('carbs', 0):.1f}г"
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=KeyboardFactory.get("products_menu")
        )
        logger.info(f"Рассчитаны нутриенты для продукта {product_id}: {amount}г")
        
    except Exception as e:
        await input_handler.handle_validation_error(
            update, 
            context, 
            f"Ошибка в калькуляторе продуктов: {str(e)}",
            "products_menu"
        )
        logger.exception("Ошибка в калькуляторе продуктов")
    finally:
        if context.user_data is not None:
            context.user_data["state"] = None

# Просмотр нутриентов продукта
async def product_nutrients_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not getattr(query, 'data', None):
        return
    await query.answer()
    nutrients_data = query.data
    if not nutrients_data or not isinstance(nutrients_data, str):
        return
    product_id = int(nutrients_data.replace("product_nutrients_", ""))
    product = await product_service.get_product(product_id)
    
    if not product:
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=Messages["ERRORS"]["not_found"],
            reply_markup=KeyboardFactory.get("products_menu")
        )
        logger.error(f"Продукт не найден для просмотра нутриентов: {product_id}")
        return
    
    nutrients = product.get("nutrients", {})
    text = f"📊 *Нутриенты продукта*\n\n"
    text += f"Название: {product['name']}\n\n"
    text += f"Калории: {nutrients.get('calories', 0)} ккал\n"
    text += f"Белки: {nutrients.get('protein', 0)}г\n"
    text += f"Жиры: {nutrients.get('fat', 0)}г\n"
    text += f"Углеводы: {nutrients.get('carbs', 0)}г\n"
    text += f"Клетчатка: {nutrients.get('fiber', 0)}г\n"
    text += f"Сахар: {nutrients.get('sugar', 0)}г\n"
    text += f"Натрий: {nutrients.get('sodium', 0)}мг\n"
    text += f"Холестерин: {nutrients.get('cholesterol', 0)}мг"
    
    await ui_service._send_or_edit_message(
        update=update,
        context=context,
        text=text,
        reply_markup=KeyboardFactory.get("back")
    )
    logger.info(f"Показаны нутриенты продукта {product_id}")

# Поиск продуктов
async def handle_product_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"handle_product_search called. User: {update.effective_user.id if update.effective_user else 'unknown'}")
    """Обработчик поиска продуктов с валидацией через InputHandler"""
    try:
        # Валидация входящих данных через InputHandler
        validation_result = await input_handler.validate_text_input(
            update, 
            ProductSearchDTO, 
            "product_search",
            context
        )
        
        if not validation_result.is_valid:
            return
        
        search_data = validation_result.data
        query = search_data.query
        
        # Поиск продуктов через сервис
        products = product_service.search_products(query)
        
        if not products:
            text = f"🔍 *Поиск продуктов*\n\nПо запросу '{query}' ничего не найдено."
            keyboard = KeyboardFactory.get("back")
        else:
            text = f"🔍 *Результаты поиска*\n\nПо запросу '{query}' найдено {len(products)} продуктов:\n\n"
            keyboard = []
            for product in products[:10]:  # Ограничиваем до 10 результатов
                keyboard.append([{"text": product['name'], "callback_data": f"product_edit_{product['id']}"}])
            keyboard.append([{"text": "◀️ Назад", "callback_data": "products"}])
            keyboard = InlineKeyboardMarkup(keyboard)
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=keyboard
        )
        logger.info(f"Поиск продуктов по запросу '{query}': найдено {len(products)}")
        
    except Exception as e:
        await input_handler.handle_validation_error(
            update, 
            context, 
            f"Ошибка при поиске продуктов: {str(e)}",
            "products_menu"
        )
        logger.exception("Ошибка при поиске продуктов")
    finally:
        if context.user_data is not None:
            context.user_data["state"] = None 