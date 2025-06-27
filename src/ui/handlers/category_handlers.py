from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CommandHandler,
    ConversationHandler,
)
from functools import partial
import logging

from src.monitoring.profiler import Profiler
from src.utils.error_handler import ErrorHandler, ValidationError, NotFoundError
from src.ui.keyboards import KeyboardFactory
from src.ui.ui_service import ui_service
from src.config.states import States
from src.services.data_service import DataService
from src.services.category_service import CategoryService
from src.validators.input_handler import input_handler, handle_input_errors
from src.validators.schemas import CategoryDTO, ValidationErrorResponse

logger = logging.getLogger(__name__)
profiler = Profiler()


class CategoryHandlers:
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.category_service = CategoryService()

    async def _send_category_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Отправляет сообщение с меню управления категориями."""
        categories_data = await self.category_service.get_categories()
        category_names = [cat["name"] for cat in categories_data]
        keyboard = KeyboardFactory.get(
            "category_management_menu", categories=category_names
        )

        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="🗂️ **Управление категориями рецептов**\n\n"
            "Выберите категорию для просмотра или воспользуйтесь кнопками управления.",
            reply_markup=keyboard
        )

    @profiler.profile
    async def show_category_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отображает меню управления категориями. Точка входа в диалог."""
        query = update.callback_query
        if not query or not query.message:
            return ConversationHandler.END
        await query.answer()
        await self._send_category_menu(update, context)
        return States.CHOOSING_ACTION

    @profiler.profile
    async def prompt_add_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info(f"[prompt_add_category] state={context.user_data.get('state') if context.user_data else None}, user_data={context.user_data}")
        query = update.callback_query
        if not query:
            return ConversationHandler.END

        await query.answer()
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="📝 Введите название для новой категории:"
        )
        return States.AWAITING_CATEGORY_NAME

    @profiler.profile
    @handle_input_errors
    async def save_new_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сохраняет новую категорию с валидацией"""
        if not update.message or not update.message.text:
            return States.AWAITING_CATEGORY_NAME
        
        category_name = update.message.text.strip()
        # Валидация через CategoryDTO
        validation = input_handler.validate_input({"name": category_name}, 'category')
        if isinstance(validation, ValidationErrorResponse):
            error_message = f"❌ Ошибка валидации категории:\n\n"
            for field, error in validation.errors.items():
                error_message += f"• {field}: {error}\n"
            await update.message.reply_text(error_message)
            return States.AWAITING_CATEGORY_NAME
        try:
            await self.category_service.add_category(category_name)
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=f"✅ Категория '{category_name}' успешно создана!"
            )
        except ValidationError as e:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=f"❌ Ошибка валидации: {e}"
            )
            return States.AWAITING_CATEGORY_NAME
        except Exception as e:
            logger.error(f"Ошибка создания категории: {e}")
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="❌ Произошла ошибка при создании категории. Попробуйте еще раз."
            )
            return States.AWAITING_CATEGORY_NAME

        # Возвращаемся в меню категорий
        await self._send_category_menu(update, context)
        return States.CHOOSING_ACTION

    @profiler.profile
    async def prompt_edit_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info(f"[prompt_edit_category] state={context.user_data.get('state') if context.user_data else None}, user_data={context.user_data}")
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        await query.answer()

        categories_data = await self.category_service.get_categories()
        category_names = [cat["name"] for cat in categories_data]

        if not category_names:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="📭 Нет категорий для редактирования.",
                reply_markup=KeyboardFactory.get("back")
            )
            return States.CHOOSING_ACTION

        keyboard = await self._get_category_selection_keyboard(category_names, "edit_category")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="✏️ Выберите категорию для редактирования:",
            reply_markup=keyboard
        )
        return States.AWAITING_CATEGORY_TO_EDIT

    async def _get_category_selection_keyboard(self, category_names, action_prefix):
        """Создает клавиатуру для выбора категории с кнопками в ряд"""
        keyboard = []
        
        # Группируем категории по 2 в ряд
        for i in range(0, len(category_names), 2):
            row = []
            row.append(InlineKeyboardButton(
                category_names[i], 
                callback_data=f"{action_prefix}|{category_names[i]}"
            ))
            
            # Добавляем вторую категорию в ряд, если она есть
            if i + 1 < len(category_names):
                row.append(InlineKeyboardButton(
                    category_names[i + 1], 
                    callback_data=f"{action_prefix}|{category_names[i + 1]}"
                ))
            
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_category_menu")])
        return InlineKeyboardMarkup(keyboard)

    @profiler.profile
    async def prompt_new_category_name(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        logger.info(f"[prompt_new_category_name] state={context.user_data.get('state') if context.user_data else None}, user_data={context.user_data}, query.data={update.callback_query.data if update.callback_query else None}")
        query = update.callback_query
        if not query or not query.data or not context.user_data: 
            return ConversationHandler.END
        
        category_to_edit = query.data.split('|', 1)[1]
        context.user_data['category_to_edit'] = category_to_edit
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"✏️ Введите новое имя для категории '{category_to_edit}':"
        )
        return States.AWAITING_NEW_CATEGORY_NAME

    @profiler.profile
    @handle_input_errors
    async def save_updated_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сохраняет обновленное имя категории с валидацией"""
        if not update.message or not update.message.text or not context.user_data:
             return States.AWAITING_NEW_CATEGORY_NAME
        
        old_name = context.user_data.get('category_to_edit')
        new_name = update.message.text.strip()
        # Валидация через CategoryDTO
        validation = input_handler.validate_input({"name": new_name}, 'category')
        if isinstance(validation, ValidationErrorResponse):
            error_message = f"❌ Ошибка валидации категории:\n\n"
            for field, error in validation.errors.items():
                error_message += f"• {field}: {error}\n"
            await update.message.reply_text(error_message)
            return States.AWAITING_NEW_CATEGORY_NAME
        try:
            category = await self.category_service.get_category_by_name(old_name)
            if category:
                await self.category_service.update_category(category['id'], {'name': new_name})
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text=f"✅ Категория '{old_name}' переименована в '{new_name}'."
                )
            else:
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text=f"❌ Не удалось найти категорию '{old_name}'."
                )
        except (ValidationError, NotFoundError) as e:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=f"❌ Ошибка: {e}"
            )

        context.user_data.pop('category_to_edit', None)
        # Возврат в меню
        await self._send_category_menu(update, context)
        return States.CHOOSING_ACTION

    @profiler.profile
    async def prompt_delete_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info(f"[prompt_delete_category] state={context.user_data.get('state') if context.user_data else None}, user_data={context.user_data}")
        query = update.callback_query
        if not query: 
            return ConversationHandler.END
        await query.answer()

        categories_data = await self.category_service.get_categories()
        category_names = [cat['name'] for cat in categories_data]

        if not category_names:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text="📭 Нет категорий для удаления.",
                reply_markup=KeyboardFactory.get("back")
            )
            return States.CHOOSING_ACTION

        keyboard = await self._get_category_selection_keyboard(category_names, "delete_category")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="🗑️ Выберите категорию, которую хотите удалить:",
            reply_markup=keyboard
        )
        return States.AWAITING_CATEGORY_TO_DELETE

    @profiler.profile
    async def confirm_delete_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info(f"[confirm_delete_category] state={context.user_data.get('state') if context.user_data else None}, user_data={context.user_data}, query.data={update.callback_query.data if update.callback_query else None}")
        query = update.callback_query
        if not query or not query.data or not context.user_data: 
            return ConversationHandler.END
        
        category_to_delete = query.data.split('|', 1)[1]
        # Получаем ID категории по имени (или если уже ID, приводим к int)
        category_service = getattr(self, 'category_service', None)
        if category_service:
            category_obj = await category_service.get_category_by_name(category_to_delete)
            category_id = category_obj['id'] if category_obj else category_to_delete
        else:
            category_id = category_to_delete
        context.user_data['category_to_delete'] = category_id

        keyboard = KeyboardFactory.get_confirmation_keyboard("category_delete_confirm", int(category_id))
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"❓ Вы уверены, что хотите удалить категорию '{category_to_delete}'? "
                 f"Это действие необратимо.",
            reply_markup=keyboard
        )
        return States.CONFIRMING_DELETE_CATEGORY

    @profiler.profile
    async def execute_delete_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удаляет категорию."""
        query = update.callback_query
        if not query or not context.user_data: 
            return ConversationHandler.END
        
        await query.answer()  # Немедленный ответ на callback
        category_name = context.user_data.get('category_to_delete')
        
        try:
            category = await self.category_service.get_category_by_name(category_name)
            if category:
                await self.category_service.delete_category(category['id'])
                # Получаем обновлённый список категорий для меню
                categories_data = await self.category_service.get_categories()
                category_names = [cat["name"] for cat in categories_data]
                keyboard = KeyboardFactory.get(
                    "category_management_menu", categories=category_names
                )
                success_text = f"✅ Категория '{category_name}' успешно удалена."
                menu_text = "🗂️ **Управление категориями рецептов**\n\nВыберите категорию для просмотра или воспользуйтесь кнопками управления."
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text=f"{success_text}\n\n{menu_text}",
                    reply_markup=keyboard
                )
            else:
                await ui_service._send_or_edit_message(
                    update=update,
                    context=context,
                    text=f"❌ Не удалось найти категорию '{category_name}'."
                )
        except (ValidationError, NotFoundError) as e:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=f"❌ Ошибка: {e}"
            )

        if context.user_data:
            context.user_data.pop('category_to_delete', None)
        # Не вызываем _send_category_menu повторно
        return States.CHOOSING_ACTION

    @profiler.profile
    async def back_to_recipes_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Возвращает пользователя в меню рецептов."""
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        await query.answer()
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="📚 Меню рецептов",
            reply_markup=KeyboardFactory.get("recipe_menu")
        )
        return ConversationHandler.END
    
    @profiler.profile
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отменяет текущий диалог."""
        if update.callback_query:
            await update.callback_query.answer()
        
        # Очищаем данные категорий из user_data
        if context.user_data:
            context.user_data.pop('category_to_edit', None)
            context.user_data.pop('category_to_delete', None)
        
        if update.effective_chat:
             await ui_service._send_or_edit_message(
                 update=update,
                 context=context,
                 text="❌ Действие отменено."
             )
        
        # Попытка вернуться в меню рецептов, если это возможно
        if update.callback_query:
            return await self.back_to_recipes_menu(update, context)
        
        return ConversationHandler.END

    def register_handlers(self, application):
        """Регистрация обработчиков категорий через ConversationHandler"""
        conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.show_category_menu, pattern="^recipe_categories$"),
                CommandHandler("categories", self.show_category_menu),
            ],
            states={
                States.CHOOSING_ACTION: [
                    CallbackQueryHandler(self.prompt_add_category, pattern="^category_add$"),
                    CallbackQueryHandler(self.prompt_edit_category, pattern="^category_edit$"),
                    CallbackQueryHandler(self.prompt_delete_category, pattern="^category_delete$"),
                    CallbackQueryHandler(self.back_to_recipes_menu, pattern="^back_to_recipes$"),
                    CallbackQueryHandler(self.show_category_menu, pattern="^back_to_category_menu$"),
                ],
                States.AWAITING_CATEGORY_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_new_category)
                ],
                States.AWAITING_CATEGORY_TO_EDIT: [
                    CallbackQueryHandler(self.prompt_new_category_name, pattern=r"^edit_category\|")
                ],
                States.AWAITING_NEW_CATEGORY_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_updated_category)
                ],
                States.AWAITING_CATEGORY_TO_DELETE: [
                    CallbackQueryHandler(self.confirm_delete_category, pattern=r"^delete_category\|")
                ],
                States.CONFIRMING_DELETE_CATEGORY: [
                    CallbackQueryHandler(self.execute_delete_category, pattern="^recipe_delete_confirm_yes$"),
                    CallbackQueryHandler(self.show_category_menu, pattern="^recipe_delete_confirm_no$"),
                ]
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CallbackQueryHandler(self.back_to_recipes_menu, pattern="^back_to_recipes$")
            ],
            map_to_parent={
                # Возврат в главное меню (если нужно)
                ConversationHandler.END: States.MAIN_MENU,
            },
            per_message=False  # Исправляем предупреждение
        )
        application.add_handler(conv_handler)


def setup_category_handlers(application: Application, data_service: DataService):
    """
    Настройка обработчиков для работы с категориями
    
    Args:
        application: Приложение Telegram
        data_service: Сервис для работы с данными
    """
    category_handlers = CategoryHandlers(data_service)
    
    # Регистрация обработчиков
    category_handlers.register_handlers(application)