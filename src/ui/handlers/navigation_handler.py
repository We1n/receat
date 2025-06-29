"""
Обработчик навигации для EatBot
Управляет стеком навигации и обрабатывает навигационные действия
"""
import logging
import time
from typing import Dict, Any, Optional, List
from telegram import Update
from telegram.ext import ContextTypes

from src.ui.keyboards import KeyboardFactory
from src.ui.ui_service import ui_service
from src.ui.messages.message_factory import MessageFactory

logger = logging.getLogger(__name__)

class NavigationItem:
    """Полная информация о состоянии экрана"""
    def __init__(self, section: str, action: str, params: Dict[str, Any], 
                 message_text: str, keyboard_type: str, return_point: Optional[str] = None):
        self.section = section
        self.action = action
        self.params = params.copy()
        self.message_text = message_text
        self.keyboard_type = keyboard_type
        self.return_point = return_point  # Для ConversationHandler
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует в словарь для сохранения"""
        return {
            "section": self.section,
            "action": self.action,
            "params": self.params,
            "message_text": self.message_text,
            "keyboard_type": self.keyboard_type,
            "return_point": self.return_point,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NavigationItem':
        """Создает из словаря"""
        return cls(
            section=data["section"],
            action=data["action"],
            params=data.get("params", {}),
            message_text=data["message_text"],
            keyboard_type=data["keyboard_type"],
            return_point=data.get("return_point")
        )

class EnhancedNavigationStack:
    """Улучшенный стек навигации с полной информацией"""
    
    def __init__(self, max_size: int = 15):
        self.stack: List[NavigationItem] = []
        self.max_size = max_size
    
    def push_screen(self, item: NavigationItem) -> None:
        """Добавляет экран в стек с полной информацией"""
        self.stack.append(item)
        
        # Ограничиваем размер стека
        if len(self.stack) > self.max_size:
            self.stack.pop(0)
        
        logger.info(f"Добавлен в стек навигации: {item.section}:{item.action}")
    
    def pop(self) -> Optional[NavigationItem]:
        """Извлекает последний элемент из стека"""
        if self.stack:
            item = self.stack.pop()
            logger.info(f"Извлечен из стека: {item.section}:{item.action}")
            return item
        return None
    
    def peek(self) -> Optional[NavigationItem]:
        """Возвращает последний элемент без извлечения"""
        return self.stack[-1] if self.stack else None
    
    def clear(self) -> None:
        """Очищает стек"""
        self.stack.clear()
        logger.info("Стек навигации очищен")
    
    def get_return_point(self) -> Optional[str]:
        """Получает точку возврата для ConversationHandler"""
        return self.stack[-1].return_point if self.stack else None
    
    def get_stack_info(self) -> str:
        """Возвращает информацию о стеке для отладки"""
        if not self.stack:
            return "Стек пуст"
        
        items = [f"{item.section}:{item.action}" for item in self.stack]
        return " -> ".join(items)
    
    def size(self) -> int:
        """Возвращает размер стека"""
        return len(self.stack)

class NavigationManager:
    """Менеджер навигации с полным управлением стеком"""
    
    @classmethod
    async def navigate_to(cls, update: Update, context: ContextTypes.DEFAULT_TYPE,
                         section: str, action: str, params: Dict[str, Any],
                         message_text: str, keyboard_type: str) -> None:
        """Переход на новый экран с автоматическим добавлением в стек"""
        
        # Сохраняем текущее состояние
        cls._save_current_screen(context)
        
        # Создаем новый экран
        new_screen = NavigationItem(section, action, params, message_text, keyboard_type)
        if context.user_data is None:
            context.user_data = {}
        context.user_data['current_screen'] = new_screen
        
        # Показываем экран
        await cls._show_screen(update, context, new_screen)
    
    @classmethod
    async def go_back(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Возврат на предыдущий экран"""
        navigation_stack = cls._get_navigation_stack(context)
        previous_screen = navigation_stack.pop()
        
        if previous_screen:
            if context.user_data is None:
                context.user_data = {}
            context.user_data['current_screen'] = previous_screen
            await cls._show_screen(update, context, previous_screen)
        else:
            await cls.go_to_main_menu(update, context)
    
    @classmethod
    async def go_to_main_menu(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Переход в главное меню"""
        cls._clear_navigation_stack(context)
        
        await cls.navigate_to(
            update, context,
            "main", "menu", {},
            MessageFactory.get_main_menu(),
            "main_menu"
        )
    
    @classmethod
    def _save_current_screen(cls, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Сохраняет текущий экран в стек"""
        if context.user_data is None:
            context.user_data = {}
        
        current_screen = context.user_data.get('current_screen')
        if current_screen:
            navigation_stack = cls._get_navigation_stack(context)
            navigation_stack.push_screen(current_screen)
    
    @classmethod
    def _get_navigation_stack(cls, context: ContextTypes.DEFAULT_TYPE) -> EnhancedNavigationStack:
        """Получает стек навигации"""
        if context.user_data is None:
            context.user_data = {}
        
        if 'navigation_stack' not in context.user_data:
            context.user_data['navigation_stack'] = EnhancedNavigationStack()
        return context.user_data['navigation_stack']
    
    @classmethod
    def _clear_navigation_stack(cls, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Очищает стек навигации"""
        if context.user_data is None:
            context.user_data = {}
        
        navigation_stack = cls._get_navigation_stack(context)
        navigation_stack.clear()
        context.user_data.pop('current_screen', None)
    
    @classmethod
    async def _show_screen(cls, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                          screen: NavigationItem) -> None:
        """Показывает экран"""
        keyboard = KeyboardFactory.get(screen.keyboard_type, **screen.params)
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=screen.message_text,
            reply_markup=keyboard
        )

class NavigationHandler:
    """Обработчик навигационных действий"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_navigation_stack(self, context: ContextTypes.DEFAULT_TYPE) -> EnhancedNavigationStack:
        """Получает или создает стек навигации для пользователя"""
        if context.user_data is None:
            context.user_data = {}
        
        if "navigation_stack" not in context.user_data:
            context.user_data["navigation_stack"] = EnhancedNavigationStack()
        
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
        await NavigationManager.go_back(update, context)
    
    async def _handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка кнопки 'Главное меню'"""
        await NavigationManager.go_to_main_menu(update, context)
    
    async def _handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict[str, Any]) -> None:
        """Обработка ошибок навигации"""
        error_message = params.get("message", "Произошла ошибка навигации")
        self.logger.error(f"Ошибка навигации: {error_message}")
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=MessageFactory.format_error(error_message),
            reply_markup=KeyboardFactory.get("navigation")
        )

# Глобальный экземпляр обработчика навигации
navigation_handler = NavigationHandler() 