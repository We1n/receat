"""
Навигационная система для бота
"""
import logging
from typing import List, Dict, Any, Optional
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from src.ui.keyboards.factory import CallbackDataBuilder

logger = logging.getLogger(__name__)

# Константы для секций
SECTION_MAIN = "main"
SECTION_RECIPES = "recipes"
SECTION_PRODUCTS = "products"
SECTION_COLLABORATIVE = "collaborative"

# Константы для действий
ACTION_MENU = "menu"
ACTION_SEARCH = "search"
ACTION_ADD = "add"
ACTION_LIST = "list"
ACTION_VIEW = "view"
ACTION_EDIT = "edit"
ACTION_DELETE = "delete"
ACTION_CALCULATE = "calculate"
ACTION_ANALYZE = "analyze"
ACTION_BACK = "back"

class NavigationItem:
    """Элемент навигации"""
    
    def __init__(self, title: str, icon: str, callback_data: str, description: str = ""):
        self.title = title
        self.icon = icon
        self.callback_data = callback_data
        self.description = description

class NavigationStack:
    """Стек навигации для отслеживания пути пользователя"""
    
    def __init__(self):
        self.stack: List[Dict[str, Any]] = []
    
    def push(self, section: str, action: str, params: Optional[Dict[str, Any]] = None):
        """Добавить элемент в стек"""
        self.stack.append({
            'section': section,
            'action': action,
            'params': params or {}
        })
        logger.debug(f"Navigation stack push: {section}:{action}")
    
    def pop(self) -> Optional[Dict[str, Any]]:
        """Извлечь элемент из стека"""
        if self.stack:
            item = self.stack.pop()
            logger.debug(f"Navigation stack pop: {item['section']}:{item['action']}")
            return item
        return None
    
    def peek(self) -> Optional[Dict[str, Any]]:
        """Посмотреть на верхний элемент стека"""
        return self.stack[-1] if self.stack else None
    
    def clear(self):
        """Очистить стек"""
        self.stack.clear()
        logger.debug("Navigation stack cleared")
    
    def get_path(self) -> List[Dict[str, Any]]:
        """Получить весь путь навигации"""
        return self.stack.copy()

class NavigationManager:
    """Менеджер навигации"""
    
    def __init__(self):
        self.stacks: Dict[int, NavigationStack] = {}
    
    def get_stack(self, user_id: int) -> NavigationStack:
        """Получить стек навигации для пользователя"""
        if user_id not in self.stacks:
            self.stacks[user_id] = NavigationStack()
        return self.stacks[user_id]
    
    def navigate_to(self, user_id: int, section: str, action: str, params: Optional[Dict[str, Any]] = None):
        """Перейти к новому разделу"""
        stack = self.get_stack(user_id)
        stack.push(section, action, params)
    
    def go_back(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Вернуться назад"""
        stack = self.get_stack(user_id)
        return stack.pop()
    
    def get_current_location(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить текущее местоположение пользователя"""
        stack = self.get_stack(user_id)
        return stack.peek()

# Создаем глобальный экземпляр менеджера навигации
navigation_manager = NavigationManager()

class NavigationBuilder:
    """Строитель навигационных меню"""
    
    @staticmethod
    def build_menu(items: List[NavigationItem], columns: int = 2) -> InlineKeyboardMarkup:
        """Построить меню из элементов навигации"""
        keyboard = []
        
        # Группируем элементы по колонкам
        for i in range(0, len(items), columns):
            row = []
            for j in range(columns):
                if i + j < len(items):
                    item = items[i + j]
                    row.append(InlineKeyboardButton(
                        f"{item.icon} {item.title}", 
                        callback_data=item.callback_data
                    ))
            if row:
                keyboard.append(row)
        
        # Добавляем кнопку "Назад"
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=CallbackDataBuilder.build("nav", "back"))])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_list_menu(items: List[NavigationItem], page: int = 1, per_page: int = 5) -> InlineKeyboardMarkup:
        """Построить меню списка с пагинацией"""
        keyboard = []
        
        # Элементы списка
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_items = items[start_idx:end_idx]
        
        for item in page_items:
            keyboard.append([InlineKeyboardButton(
                f"{item.icon} {item.title}", 
                callback_data=item.callback_data
            )])
        
        # Пагинация
        total_pages = (len(items) + per_page - 1) // per_page
        if total_pages > 1:
            pagination_row = []
            if page > 1:
                pagination_row.append(InlineKeyboardButton(
                    "⬅️", 
                    callback_data=CallbackDataBuilder.build("nav", "list", page=page-1)
                ))
            pagination_row.append(InlineKeyboardButton(
                f"{page}/{total_pages}", 
                callback_data="no_action"
            ))
            if page < total_pages:
                pagination_row.append(InlineKeyboardButton(
                    "➡️", 
                    callback_data=CallbackDataBuilder.build("nav", "list", page=page+1)
                ))
            keyboard.append(pagination_row)
        
        # Навигационные кнопки
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=CallbackDataBuilder.build("nav", "back"))])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_detail_menu(item: NavigationItem, actions: List[Dict[str, str]]) -> InlineKeyboardMarkup:
        """Построить меню детального просмотра"""
        keyboard = []
        
        # Действия с элементом
        for action in actions:
            keyboard.append([InlineKeyboardButton(
                action["text"], 
                callback_data=action["callback_data"]
            )])
        
        # Навигационные кнопки
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=CallbackDataBuilder.build("nav", "back"))])
        
        return InlineKeyboardMarkup(keyboard)

class NavigationMenus:
    """Предопределенные навигационные меню"""
    
    @staticmethod
    def get_main_menu() -> InlineKeyboardMarkup:
        """Главное меню"""
        items = [
            NavigationItem("Рецепты", "🍳", CallbackDataBuilder.build(SECTION_RECIPES, ACTION_MENU)),
            NavigationItem("Продукты", "🥗", CallbackDataBuilder.build(SECTION_PRODUCTS, ACTION_MENU)),
            NavigationItem("Совместная работа", "🤝", CallbackDataBuilder.build(SECTION_COLLABORATIVE, ACTION_MENU))
        ]
        return NavigationBuilder.build_menu(items, 2)
    
    @staticmethod
    def get_recipes_menu() -> InlineKeyboardMarkup:
        """Меню рецептов"""
        keyboard = [
            [InlineKeyboardButton("🔍 Поиск", callback_data=CallbackDataBuilder.build(SECTION_RECIPES, ACTION_SEARCH))],
            [InlineKeyboardButton("➕ Добавить", callback_data=CallbackDataBuilder.build(SECTION_RECIPES, ACTION_ADD))],
            [InlineKeyboardButton("📋 Мои рецепты", callback_data=CallbackDataBuilder.build(SECTION_RECIPES, ACTION_LIST))],
            [InlineKeyboardButton("🧮 Анализ", callback_data=CallbackDataBuilder.build(SECTION_RECIPES, ACTION_ANALYZE))],
            [InlineKeyboardButton("◀️ Назад", callback_data=CallbackDataBuilder.build("nav", "back"))]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_products_menu() -> InlineKeyboardMarkup:
        """Меню продуктов"""
        keyboard = [
            [InlineKeyboardButton("🔍 Поиск", callback_data=CallbackDataBuilder.build(SECTION_PRODUCTS, ACTION_SEARCH))],
            [InlineKeyboardButton("➕ Добавить", callback_data=CallbackDataBuilder.build(SECTION_PRODUCTS, ACTION_ADD))],
            [InlineKeyboardButton("🧮 Калькулятор", callback_data=CallbackDataBuilder.build(SECTION_PRODUCTS, ACTION_CALCULATE))],
            [InlineKeyboardButton("📊 История", callback_data=CallbackDataBuilder.build(SECTION_PRODUCTS, ACTION_LIST))],
            [InlineKeyboardButton("◀️ Назад", callback_data=CallbackDataBuilder.build("nav", "back"))]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_back_button() -> InlineKeyboardMarkup:
        """Кнопка "Назад" """
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data=CallbackDataBuilder.build("nav", "back"))]
        ])
    
    @staticmethod
    def get_main_menu_button() -> InlineKeyboardMarkup:
        """Кнопка "Главное меню" """
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Главное меню", callback_data=CallbackDataBuilder.build("nav", "main_menu"))]
        ]) 