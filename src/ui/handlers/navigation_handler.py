"""
Обработчик навигации для EatBot
Управляет стеком навигации и обрабатывает навигационные действия
"""
import logging
from typing import Dict, Any, Optional, List
from telegram import Update
from telegram.ext import ContextTypes

from src.ui.keyboards import KeyboardFactory
from src.ui.ui_service import ui_service
from src.ui.messages_main import Messages as RawMessages

# Правильная типизация Messages
Messages: Dict[str, Any] = RawMessages

logger = logging.getLogger(__name__)

class NavigationStack:
    """Стек навигации для отслеживания истории переходов"""
    
    def __init__(self):
        self.stack: List[Dict[str, Any]] = []
    
    def push(self, section: str, action: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Добавляет новый элемент в стек"""
        if params is None:
            params = {}
        
        self.stack.append({
            "section": section,
            "action": action,
            "params": params.copy()
        })
        
        # Ограничиваем размер стека (максимум 10 элементов)
        if len(self.stack) > 10:
            self.stack.pop(0)
        
        logger.info(f"Добавлен в стек навигации: {section}:{action}")
    
    def pop(self) -> Optional[Dict[str, Any]]:
        """Извлекает последний элемент из стека"""
        if self.stack:
            item = self.stack.pop()
            logger.info(f"Извлечен из стека: {item['section']}:{item['action']}")
            return item
        return None
    
    def peek(self) -> Optional[Dict[str, Any]]:
        """Возвращает последний элемент без извлечения"""
        return self.stack[-1] if self.stack else None
    
    def clear(self) -> None:
        """Очищает стек"""
        self.stack.clear()
        logger.info("Стек навигации очищен")
    
    def get_stack_info(self) -> str:
        """Возвращает информацию о стеке для отладки"""
        if not self.stack:
            return "Стек пуст"
        
        items = [f"{item['section']}:{item['action']}" for item in self.stack]
        return " -> ".join(items)

class NavigationHandler:
    """Обработчик навигационных действий"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_navigation_stack(self, context: ContextTypes.DEFAULT_TYPE) -> NavigationStack:
        """Получает или создает стек навигации для пользователя"""
        if context.user_data is None:
            context.user_data = {}
        
        if "navigation_stack" not in context.user_data:
            context.user_data["navigation_stack"] = NavigationStack()
        
        return context.user_data["navigation_stack"]
    
    async def handle_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, params: Dict[str, Any]) -> None:
        """
        Обрабатывает навигационные действия
        
        Args:
            update: Объект Update от Telegram
            context: Контекст выполнения
            action: Действие (back, main_menu, no_action, error)
            params: Параметры действия
        """
        self.logger.info(f"Обработка навигационного действия: {action}")
        
        if action == "back":
            await self._handle_back(update, context)
        elif action == "main_menu":
            await self._handle_main_menu(update, context)
        elif action == "no_action":
            # Ничего не делаем (например, для кнопки с номером страницы)
            pass
        elif action == "error":
            await self._handle_error(update, context, params)
        else:
            self.logger.warning(f"Неизвестное навигационное действие: {action}")
            await self._handle_error(update, context, {"message": f"Неизвестное действие: {action}"})
    
    async def _handle_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка кнопки 'Назад'"""
        navigation_stack = self.get_navigation_stack(context)
        
        # Извлекаем предыдущий элемент из стека
        previous_item = navigation_stack.pop()
        
        if previous_item:
            # Вызываем предыдущее действие
            await self._execute_navigation_item(update, context, previous_item)
        else:
            # Если стек пуст, возвращаемся в главное меню
            await self._handle_main_menu(update, context)
    
    async def _handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка кнопки 'Главное меню'"""
        # Очищаем стек навигации
        navigation_stack = self.get_navigation_stack(context)
        navigation_stack.clear()
        
        # Показываем главное меню
        await ui_service.show_main_menu(update, context)
        self.logger.info("Переход в главное меню")
    
    async def _handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Обработка ошибок навигации"""
        error_message = params.get("message", "Произошла ошибка навигации")
        self.logger.error(f"Ошибка навигации: {error_message}")
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=f"❌ {error_message}",
            reply_markup=KeyboardFactory.get("navigation")
        )
    
    async def _execute_navigation_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE, item: Dict[str, Any]) -> None:
        """Выполняет элемент навигации"""
        section = item["section"]
        action = item["action"]
        params = item.get("params", {})
        
        self.logger.info(f"Выполнение навигационного элемента: {section}:{action}")
        
        # Импортируем обработчики по необходимости
        if section == "main":
            await self._handle_main_section(update, context, action, params)
        elif section == "recipes":
            await self._handle_recipes_section(update, context, action, params)
        elif section == "products":
            await self._handle_products_section(update, context, action, params)
        elif section == "collaborative":
            await self._handle_collaborative_section(update, context, action, params)
        else:
            self.logger.warning(f"Неизвестный раздел для навигации: {section}")
            await self._handle_main_menu(update, context)
    
    async def _handle_main_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, params: Dict[str, Any]) -> None:
        """Обработка раздела main"""
        if action == "recipes":
            recipes_text = Messages.get("RECIPES", {}).get("menu", "📚 Меню рецептов")
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=recipes_text,
                reply_markup=KeyboardFactory.get("recipe_menu")
            )
        elif action == "products":
            products_text = Messages.get("PRODUCTS", {}).get("menu", "🍏 Меню продуктов")
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=products_text,
                reply_markup=KeyboardFactory.get("products_menu")
            )
        else:
            await self._handle_main_menu(update, context)
    
    async def _handle_recipes_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, params: Dict[str, Any]) -> None:
        """Обработка раздела recipes"""
        # Здесь будет делегирование в RecipeHandler
        # Пока что просто показываем меню рецептов
        recipes_text = Messages.get("RECIPES", {}).get("menu", "📚 Меню рецептов")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=recipes_text,
            reply_markup=KeyboardFactory.get("recipe_menu")
        )
    
    async def _handle_products_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, params: Dict[str, Any]) -> None:
        """Обработка раздела products"""
        # Здесь будет делегирование в ProductHandler
        # Пока что просто показываем меню продуктов
        products_text = Messages.get("PRODUCTS", {}).get("menu", "🍏 Меню продуктов")
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=products_text,
            reply_markup=KeyboardFactory.get("products_menu")
        )
    
    async def _handle_collaborative_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, params: Dict[str, Any]) -> None:
        """Обработка раздела collaborative"""
        # Здесь будет делегирование в CollaborativeHandler
        # Пока что просто показываем меню коллабораций
        collaborative_messages = Messages.get("COLLABORATIVE", {})
        menu_text = collaborative_messages.get("menu", "🤝 Совместная работа") if isinstance(collaborative_messages, dict) else "🤝 Совместная работа"
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=menu_text,
            reply_markup=KeyboardFactory.get("collaborative_menu")
        )

# Глобальный экземпляр обработчика навигации
navigation_handler = NavigationHandler() 