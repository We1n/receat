import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.ui.keyboards.factory import KeyboardFactory
from src.ui.ui_service import ui_service
from src.config.states import States
from src.services.category_service import CategoryService
from src.services.data_service import DataService
from typing import Optional
from src.validators.input_handler import input_handler, handle_input_errors
from src.validators.schemas import ValidationErrorResponse

logger = logging.getLogger(__name__)

class CallbackHandler:
    """
    Универсальный обработчик callback-запросов для категорий и совместной работы.
    Соответствует правилам проекта: логирование, обработка ошибок, подсказки, возврат назад, эмодзи, Markdown.
    """
    def __init__(self, data_service: Optional[DataService] = None, category_service: Optional[CategoryService] = None):
        self.data_service = data_service or DataService()
        self.category_service = category_service or CategoryService()

    @handle_input_errors
    async def handle_category_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> States:
        query = update.callback_query
        if not query or not hasattr(query, "data") or not query.data:
            logger.error("[Callback] Нет данных callback_query для категорий")
            if update.message:
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text="❌ Ошибка: нет данных для обработки категории.",
                    reply_markup=KeyboardFactory.get("back")
                )
            return States.MAIN_MENU
        try:
            await query.answer()
            data = query.data
            logger.info(f"[Callback] Категории: {data}")

            # Централизованная валидация callback данных
            callback_data = input_handler.parse_callback_data(data)
            validation = input_handler.validate_input(callback_data, 'search_query')
            if isinstance(validation, ValidationErrorResponse):
                error_message = f"❌ Ошибка валидации callback:\n\n"
                for field, error in validation.errors.items():
                    error_message += f"• {field}: {error}\n"
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text=error_message,
                    reply_markup=KeyboardFactory.get("back")
                )
                return States.MAIN_MENU

            # Пример: category:main или category:<id>
            if data == "category:main":
                categories = await self.category_service.get_categories()
                text = "📁 *Категории рецептов*\n\nВыберите категорию:"
                buttons = [[{"text": cat["name"], "callback_data": f"category_{cat['id']}"}] for cat in categories]
                buttons.append([{"text": "◀️ Назад", "callback_data": "back"}])
                reply_markup = KeyboardFactory.get("dynamic_inline", buttons=buttons)
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text=text,
                    reply_markup=reply_markup
                )
                return States.MAIN_MENU
            elif isinstance(data, str) and data.startswith("category_"):
                cat_id = int(data.split("_")[1])
                category = await self.category_service.get_category(cat_id)
                text = f"📁 *{category['name']}*\n\nОписание: {category.get('description', '—')}"
                buttons = [
                    [{"text": "✏️ Редактировать", "callback_data": f"edit_category|{cat_id}"}],
                    [{"text": "🗑 Удалить", "callback_data": f"delete_category|{cat_id}"}],
                    [{"text": "◀️ Назад", "callback_data": "category:main"}]
                ]
                reply_markup = KeyboardFactory.get("dynamic_inline", buttons=buttons)
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text=text,
                    reply_markup=reply_markup
                )
                return States.MAIN_MENU
            else:
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text="❌ Неизвестная категория. Попробуйте снова.",
                    reply_markup=KeyboardFactory.get("back")
                )
                logger.warning(f"[Callback] Неизвестная категория: {data}")
                return States.MAIN_MENU
        except Exception as e:
            logger.error(f"Ошибка в handle_category_callback: {e}", exc_info=True)
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Произошла ошибка при обработке категории. Попробуйте еще раз или вернитесь назад.",
                reply_markup=KeyboardFactory.get("back")
            )
            return States.MAIN_MENU

    @handle_input_errors
    async def handle_collaborative_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> States:
        query = update.callback_query
        if not query or not hasattr(query, "data") or not query.data:
            logger.error("[Callback] Нет данных callback_query для collaborative")
            if update.message:
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text="❌ Ошибка: нет данных для обработки совместной работы.",
                    reply_markup=KeyboardFactory.get("back")
                )
            return States.MAIN_MENU
        try:
            await query.answer()
            data = query.data
            logger.info(f"[Callback] Совместная работа: {data}")

            # Централизованная валидация callback данных
            callback_data = input_handler.parse_callback_data(data)
            validation = input_handler.validate_input(callback_data, 'search_query')
            if isinstance(validation, ValidationErrorResponse):
                error_message = f"❌ Ошибка валидации callback:\n\n"
                for field, error in validation.errors.items():
                    error_message += f"• {field}: {error}\n"
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text=error_message,
                    reply_markup=KeyboardFactory.get("back")
                )
                return States.MAIN_MENU

            # Пример: collaborative:main
            if data == "collaborative:main":
                text = "🤝 *Совместная работа*\n\nВыберите действие:"
                buttons = [
                    [{"text": "➕ Пригласить", "callback_data": "collaborative_invite"}],
                    [{"text": "📋 Мои коллаборации", "callback_data": "collaborative_list"}],
                    [{"text": "◀️ Назад", "callback_data": "back"}]
                ]
                reply_markup = KeyboardFactory.get("dynamic_inline", buttons=buttons)
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text=text,
                    reply_markup=reply_markup
                )
                return States.MAIN_MENU
            else:
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text="❌ Неизвестная команда совместной работы. Попробуйте снова.",
                    reply_markup=KeyboardFactory.get("back")
                )
                logger.warning(f"[Callback] Неизвестная collaborative: {data}")
                return States.MAIN_MENU
        except Exception as e:
            logger.error(f"Ошибка в handle_collaborative_callback: {e}", exc_info=True)
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Произошла ошибка при обработке совместной работы. Попробуйте еще раз или вернитесь назад.",
                reply_markup=KeyboardFactory.get("back")
            )
            return States.MAIN_MENU 