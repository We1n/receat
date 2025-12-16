"""
Обработчики команд бота
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from src.monitoring.profiler import Profiler
from src.utils.error_handler import ErrorHandler
from src.config.states import States
from src.ui.keyboards import KeyboardFactory
from src.ui.ui_service import ui_service
import logging

logger = logging.getLogger(__name__)
profiler = Profiler(output_dir="profiles/commands")

class CommandHandlers:
    """Обработчики команд"""
    
    def __init__(self):
        """Инициализация обработчиков команд"""
        pass
    
    @profiler.profile(save_to_file=True)
    @ErrorHandler.handle_errors
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        if not update.message or not update.effective_user:
            return
            
        # Используем UIService для отображения главного меню
        await ui_service.show_main_menu(update, context)
        
        logger.info(f"Пользователь {update.effective_user.id} запустил бота")
    
    @profiler.profile(save_to_file=True)
    @ErrorHandler.handle_errors
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help"""
        help_text = (
            "🤖 *EatBot - Помощник по здоровому питанию*\n\n"
            "📚 *Доступные команды:*\n"
            "/start - Запустить бота\n"
            "/help - Показать эту справку\n"
            "/recipes - Меню рецептов\n"
            "/products - Меню продуктов\n"
            "/collaborative - Совместная работа\n\n"
            "💡 *Советы:*\n"
            "• Используйте меню для навигации\n"
            "• Добавляйте свои рецепты и продукты\n"
            "• Создавайте категории для удобства\n\n"
            "❓ *Нужна помощь?*\n"
            "Обратитесь к администратору бота."
        )
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=help_text
        )
        logger.info("Показана справка пользователю")
    
    @profiler.profile(save_to_file=True)
    @ErrorHandler.handle_errors
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /menu"""
        if not update.message:
            return
            
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="🏠 Главное меню",
            reply_markup=KeyboardFactory.get("main_menu")
        )
    
    @profiler.profile(save_to_file=True)
    @ErrorHandler.handle_errors
    async def recipes_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /recipes"""
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="📚 *Меню рецептов*\n\nВыберите действие:",
            reply_markup=KeyboardFactory.get("recipe_menu")
        )
        logger.info("Показано меню рецептов")
    
    @profiler.profile(save_to_file=True)
    @ErrorHandler.handle_errors
    async def products_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /products"""
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="🍏 *Меню продуктов*\n\nВыберите действие:",
            reply_markup=KeyboardFactory.get("products_menu")
        )
        logger.info("Показано меню продуктов")
    
    @profiler.profile(save_to_file=True)
    @ErrorHandler.handle_errors
    async def collaborative_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /collaborative"""
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="👥 *Совместная работа*\n\nВыберите действие:",
            reply_markup=KeyboardFactory.get("collaborative_menu")
        )
        logger.info("Показано меню совместной работы")
    
    @profiler.profile(save_to_file=True)
    @ErrorHandler.handle_errors
    async def handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> States:
        """Обработчик команды /cancel"""
        if not update.effective_user or not update.message:
            return States.MAIN_MENU
            
        user = update.effective_user
        logger.info(f"Пользователь {user.id} отменил текущее действие")
        
        # Очищаем контекст
        if context.user_data:
            context.user_data.clear()
        
        # Отправляем сообщение об отмене
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text="❌ Действие отменено\n\n🏠 Возвращаемся в главное меню...",
            reply_markup=KeyboardFactory.get("main_menu")
        )
        
        return States.MAIN_MENU
    
    def register_handlers(self, application):
        """Регистрация обработчиков команд"""
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("menu", self.menu_command))
        application.add_handler(CommandHandler("recipes", self.recipes_command))
        application.add_handler(CommandHandler("products", self.products_command))
        application.add_handler(CommandHandler("collaborative", self.collaborative_command))
        application.add_handler(CommandHandler("cancel", self.handle_cancel)) 