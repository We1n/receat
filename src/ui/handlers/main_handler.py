"""
Обработчик главного меню для EatBot
Обрабатывает переходы между основными разделами
"""
import logging
from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes

from src.ui.keyboards.factory import KeyboardFactory
from src.ui.ui_service import ui_service
from src.ui.messages_main import Messages as RawMessages

# Правильная типизация Messages
Messages: Dict[str, Any] = RawMessages

logger = logging.getLogger(__name__)

class MainHandler:
    """Обработчик главного меню и основных разделов"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def handle_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, params: Dict[str, Any]) -> None:
        """
        Обрабатывает действия главного меню
        
        Args:
            update: Объект Update от Telegram
            context: Контекст выполнения
            action: Действие (menu, recipes, products, collaborative, nutrients)
            params: Параметры действия
        """
        self.logger.info(f"Обработка действия главного меню: {action}")
        
        if action == "menu":
            await self._show_main_menu(update, context)
        elif action == "recipes":
            await self._show_recipes_menu(update, context)
        elif action == "products":
            await self._show_products_menu(update, context)
        elif action == "collaborative":
            await self._show_collaborative_menu(update, context)
        elif action == "nutrients":
            await self._show_nutrients_menu(update, context)
        else:
            self.logger.warning(f"Неизвестное действие главного меню: {action}")
            await self._show_main_menu(update, context)
    
    async def _show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает главное меню"""
        await ui_service.show_main_menu(update, context)
        self.logger.info("Показано главное меню")
    
    async def _show_recipes_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает меню рецептов"""
        recipes_text = Messages.get("RECIPES", {}).get("menu", "📚 Меню рецептов")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=recipes_text,
            reply_markup=KeyboardFactory.get("recipe_menu")
        )
        self.logger.info("Переход в меню рецептов")
    
    async def _show_products_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает меню продуктов"""
        products_text = Messages.get("PRODUCTS", {}).get("menu", "🍏 Меню продуктов")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=products_text,
            reply_markup=KeyboardFactory.get("products_menu")
        )
        self.logger.info("Переход в меню продуктов")
    
    async def _show_collaborative_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает меню совместной работы"""
        collaborative_text = Messages.get("COLLABORATIVE", {}).get("menu", "🤝 Совместная работа")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=collaborative_text,
            reply_markup=KeyboardFactory.get("collaborative_menu")
        )
        self.logger.info("Переход в меню совместной работы")
    
    async def _show_nutrients_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает меню нутриентов"""
        nutrients_text = Messages.get("NUTRIENTS", {}).get("menu", "🧬 Нутриенты")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=nutrients_text,
            reply_markup=KeyboardFactory.get("nutrient_menu")
        )
        self.logger.info("Переход в меню нутриентов")

# Глобальный экземпляр обработчика главного меню
main_handler = MainHandler() 