"""
🧭 Менеджер навигации

Этот модуль предоставляет функциональность для:
- Навигации по интерфейсу бота (меню, разделы, кнопки)
- Навигации по результатам поиска (пагинация, сортировка, фильтрация)

✅ Подсказки:
- Используйте `NavigationManager` для управления навигацией
- Для возврата назад используйте `ACTION_BACK`
- Все ошибки логируются через `logger`

❌ Ограничения:
- Максимальный размер истории навигации: 10 элементов
- Размер страницы результатов: 5 элементов
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Deque, Any, Tuple
from collections import deque
from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
import logging

logger = logging.getLogger(__name__)

# --- Навигационные константы (замена отсутствующего src.ui.constants) ---
SECTION_RECIPES = "recipes"
SECTION_PRODUCTS = "products"
SECTION_CATEGORIES = "categories"
SECTION_NUTRIENTS = "nutrients"
SECTION_COLLABORATIVE = "collaborative"

ACTION_VIEW = "view"
ACTION_ADD = "add"
ACTION_EDIT = "edit"
ACTION_DELETE = "delete"
ACTION_SEARCH = "search"
ACTION_LIST = "list"
ACTION_ANALYZE = "analyze"
ACTION_CALCULATE = "calculate"
ACTION_INVITE = "invite"
ACTION_JOIN = "join"

# Константы для навигации
RECIPES = "recipes"
PRODUCTS = "products"
CATEGORIES = "categories"
NUTRIENTS = "nutrients"
COLLABORATIVE = "collaborative"

class SortOrder(Enum):
    """📊 Порядок сортировки результатов"""
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    TIME_ASC = "time_asc"
    TIME_DESC = "time_desc"
    DIFFICULTY_ASC = "difficulty_asc"
    DIFFICULTY_DESC = "difficulty_desc"
    MATCH_PERCENTAGE_DESC = "match_percentage_desc"

@dataclass
class SearchResult:
    """🔍 Класс для представления результата поиска"""
    recipe: Dict[str, Any]
    match_percentage: float
    exact_matches: List[str]
    fuzzy_matches: List[str]
    missing_ingredients: List[Dict[str, Any]]

class NavigationSection:
    """Секции навигации"""
    RECIPES = "recipes"
    PRODUCTS = "products"
    CATEGORIES = "categories"
    NUTRIENTS = "nutrients"
    COLLABORATIVE = "collaborative"

class NavigationItem:
    """Элемент навигации"""
    def __init__(self, title: str, callback_data: str, icon: str = "", description: str = ""):
        self.title = title
        self.callback_data = callback_data
        self.icon = icon
        self.description = description

class SearchResultsNavigator:
    """🧭 Класс для навигации по результатам поиска"""
    
    def __init__(self, results: List[Dict[str, Any]], page_size: int = 5) -> None:
        """
        Инициализация навигатора
        
        Args:
            results: Список результатов поиска
            page_size: Размер страницы
        
        ✅ Подсказка: Размер страницы по умолчанию: 5 элементов
        """
        self.results = results
        self.page_size = page_size
        self.current_page = 0
        self.sort_order = SortOrder.MATCH_PERCENTAGE_DESC
        self.total_pages = (len(results) + page_size - 1) // page_size
    
    def get_current_page(self) -> List[Dict[str, Any]]:
        """
        Получение текущей страницы результатов
        
        Returns:
            List[Dict]: Список результатов на текущей странице
        
        ✅ Подсказка: Используйте для отображения текущей страницы
        """
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.results))
        return self.results[start_idx:end_idx]
    
    def next_page(self) -> bool:
        """
        Переход к следующей странице
        
        Returns:
            bool: True если переход успешен, False если достигнут конец
        
        ✅ Подсказка: Проверяйте возвращаемое значение для обработки конца списка
        """
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            return True
        return False
    
    def prev_page(self) -> bool:
        """
        Переход к предыдущей странице
        
        Returns:
            bool: True если переход успешен, False если достигнуто начало
        
        ✅ Подсказка: Проверяйте возвращаемое значение для обработки начала списка
        """
        if self.current_page > 0:
            self.current_page -= 1
            return True
        return False
    
    def go_to_page(self, page: int) -> bool:
        """
        Переход к указанной странице
        
        Args:
            page: Номер страницы
            
        Returns:
            bool: True если переход успешен, False если страница не существует
        
        ✅ Подсказка: Проверяйте возвращаемое значение для обработки несуществующей страницы
        """
        if 0 <= page < self.total_pages:
            self.current_page = page
            return True
        return False
    
    def sort_results(self, sort_order: SortOrder) -> None:
        """
        Сортировка результатов
        
        Args:
            sort_order: Порядок сортировки
        
        ✅ Подсказка: Используйте `SortOrder` для выбора порядка сортировки
        """
        self.sort_order = sort_order
        
        if sort_order == SortOrder.NAME_ASC:
            self.results.sort(key=lambda x: x["recipe"]["name"].lower())
        elif sort_order == SortOrder.NAME_DESC:
            self.results.sort(key=lambda x: x["recipe"]["name"].lower(), reverse=True)
        elif sort_order == SortOrder.TIME_ASC:
            self.results.sort(key=lambda x: x["recipe"].get("cooking_time", 0))
        elif sort_order == SortOrder.TIME_DESC:
            self.results.sort(key=lambda x: x["recipe"].get("cooking_time", 0), reverse=True)
        elif sort_order == SortOrder.DIFFICULTY_ASC:
            self.results.sort(key=lambda x: x["recipe"].get("difficulty", "").lower())
        elif sort_order == SortOrder.DIFFICULTY_DESC:
            self.results.sort(key=lambda x: x["recipe"].get("difficulty", "").lower(), reverse=True)
        elif sort_order == SortOrder.MATCH_PERCENTAGE_DESC:
            self.results.sort(key=lambda x: x.get("match_percentage", 0), reverse=True)
    
    def filter_results(self, criteria: Dict[str, Any]) -> None:
        """
        Фильтрация результатов
        
        Args:
            criteria: Словарь с критериями фильтрации:
                - min_match_percentage: float - минимальный процент совпадения
                - max_cooking_time: int - максимальное время приготовления
                - difficulty: str - сложность
                - tags: List[str] - список тегов
        
        ✅ Подсказка: Используйте для фильтрации результатов по заданным критериям
        """
        filtered_results = self.results.copy()
        
        if "min_match_percentage" in criteria:
            filtered_results = [
                r for r in filtered_results
                if r.get("match_percentage", 0) >= criteria["min_match_percentage"]
            ]
        
        if "max_cooking_time" in criteria:
            filtered_results = [
                r for r in filtered_results
                if r["recipe"].get("cooking_time", 0) <= criteria["max_cooking_time"]
            ]
        
        if "difficulty" in criteria:
            filtered_results = [
                r for r in filtered_results
                if r["recipe"].get("difficulty", "").lower() == criteria["difficulty"].lower()
            ]
        
        if "tags" in criteria:
            filtered_results = [
                r for r in filtered_results
                if all(tag.lower() in [t.lower() for t in r["recipe"].get("tags", [])]
                      for tag in criteria["tags"])
            ]
        
        self.results = filtered_results
        self.total_pages = (len(self.results) + self.page_size - 1) // self.page_size
        self.current_page = min(self.current_page, self.total_pages - 1)
    
    def get_navigation_info(self) -> Dict[str, Any]:
        """
        Получение информации о навигации
        
        Returns:
            Dict[str, Any]: Информация о текущей странице, общем количестве страниц и т.д.
        
        ✅ Подсказка: Используйте для отображения информации о навигации
        """
        return {
            "current_page": self.current_page + 1,
            "total_pages": self.total_pages,
            "total_results": len(self.results),
            "sort_order": self.sort_order.value
        }

class NavigationManager:
    """Менеджер навигации"""
    
    def __init__(self):
        self.sections = {
            NavigationSection.RECIPES: [
                NavigationItem("Поиск", f"{SECTION_RECIPES}:{ACTION_SEARCH}", "🔍", "Поиск рецептов"),
                NavigationItem("Добавить", f"{SECTION_RECIPES}:{ACTION_ADD}", "➕", "Добавить рецепт"),
                NavigationItem("Мои рецепты", f"{SECTION_RECIPES}:{ACTION_LIST}", "📋", "Список рецептов"),
                NavigationItem("Категории", f"{SECTION_RECIPES}:{SECTION_CATEGORIES}", "🗂️", "Управление категориями"),
                NavigationItem("Анализ", f"{SECTION_RECIPES}:{ACTION_ANALYZE}", "🧮", "Анализ БЖУ")
            ],
            NavigationSection.PRODUCTS: [
                NavigationItem("Поиск", f"{SECTION_PRODUCTS}:{ACTION_SEARCH}", "🔍", "Поиск продуктов"),
                NavigationItem("Добавить", f"{SECTION_PRODUCTS}:{ACTION_ADD}", "➕", "Добавить продукт"),
                NavigationItem("Категории", f"{SECTION_PRODUCTS}:{SECTION_CATEGORIES}", "🗂️", "Категории продуктов"),
                NavigationItem("Калькулятор", f"{SECTION_PRODUCTS}:{ACTION_CALCULATE}", "🧮", "Калькулятор БЖУ"),
                NavigationItem("История", f"{SECTION_PRODUCTS}:{ACTION_LIST}", "📊", "История продуктов")
            ],
            NavigationSection.CATEGORIES: [
                NavigationItem("Просмотр", f"{SECTION_CATEGORIES}:{ACTION_VIEW}", "👁", "Просмотр категорий"),
                NavigationItem("Добавить", f"{SECTION_CATEGORIES}:{ACTION_ADD}", "➕", "Добавить категорию"),
                NavigationItem("Редактировать", f"{SECTION_CATEGORIES}:{ACTION_EDIT}", "✏️", "Редактировать категорию"),
                NavigationItem("Удалить", f"{SECTION_CATEGORIES}:{ACTION_DELETE}", "🗑️", "Удалить категорию")
            ],
            NavigationSection.NUTRIENTS: [
                NavigationItem("Калькулятор", f"{SECTION_NUTRIENTS}:{ACTION_CALCULATE}", "🧮", "Калькулятор БЖУ"),
                NavigationItem("Анализ рецепта", f"{SECTION_NUTRIENTS}:{ACTION_ANALYZE}", "📊", "Анализ рецепта")
            ],
        }
    
    def get_section_items(self, section: str) -> list:
        """Получить элементы секции"""
        return self.sections.get(section, [])
    
    def get_item_by_callback(self, callback_data: str) -> Optional[NavigationItem]:
        """Получить элемент по callback_data"""
        for section_items in self.sections.values():
            for item in section_items:
                if item.callback_data == callback_data:
                    return item
        return None
    
    def get_main_menu_items(self) -> list:
        """Получить элементы главного меню"""
        return [
            NavigationItem("Рецепты", f"{SECTION_RECIPES}:{ACTION_VIEW}", "📚", "Управление рецептами"),
            NavigationItem("Продукты", f"{SECTION_PRODUCTS}:{ACTION_VIEW}", "🍏", "Управление продуктами"),
            NavigationItem("Категории", f"{SECTION_CATEGORIES}:{ACTION_VIEW}", "🗂️", "Управление категориями"),
            NavigationItem("Нутриенты", f"{SECTION_NUTRIENTS}:{ACTION_VIEW}", "🧮", "Калькулятор БЖУ"),
            NavigationItem("Совместная работа", f"{SECTION_COLLABORATIVE}:{ACTION_VIEW}", "👥", "Совместная работа")
        ]

def create_section_keyboard(section: str, navigation_manager: NavigationManager) -> InlineKeyboardMarkup:
    """Создать клавиатуру для секции"""
    items = navigation_manager.get_section_items(section)
    keyboard = []
    
    # Группируем элементы по 2 в ряд
    for i in range(0, len(items), 2):
        row = []
        row.append(InlineKeyboardButton(f"{items[i].icon} {items[i].title}", callback_data=items[i].callback_data))
        
        # Добавляем второй элемент в ряд, если он есть
        if i + 1 < len(items):
            row.append(InlineKeyboardButton(f"{items[i+1].icon} {items[i+1].title}", callback_data=items[i+1].callback_data))
        
        keyboard.append(row)
    
    # Добавляем кнопку "Назад"
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    
    return InlineKeyboardMarkup(keyboard)

def create_main_menu_keyboard(navigation_manager: NavigationManager) -> InlineKeyboardMarkup:
    """Создать клавиатуру главного меню"""
    items = navigation_manager.get_main_menu_items()
    keyboard = []
    
    # Группируем элементы по 2 в ряд
    for i in range(0, len(items), 2):
        row = []
        row.append(InlineKeyboardButton(f"{items[i].icon} {items[i].title}", callback_data=items[i].callback_data))
        
        # Добавляем второй элемент в ряд, если он есть
        if i + 1 < len(items):
            row.append(InlineKeyboardButton(f"{items[i+1].icon} {items[i+1].title}", callback_data=items[i+1].callback_data))
        
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

def create_dynamic_keyboard(items: list, back_button: bool = True) -> InlineKeyboardMarkup:
    """Создать динамическую клавиатуру"""
    keyboard = []
    
    for item in items:
        if isinstance(item, list):
            # Если это уже список кнопок, добавляем как есть
            keyboard.append([InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"]) for btn in item])
        else:
            # Если это одиночная кнопка, добавляем в отдельный ряд
            keyboard.append([InlineKeyboardButton(item["text"], callback_data=item["callback_data"])])
    
    if back_button:
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    
    return InlineKeyboardMarkup(keyboard)

def create_back_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру с кнопкой "Назад" """
    keyboard = [
        [InlineKeyboardButton("◀️ Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_section_specific_keyboard(section: str, navigation_manager: NavigationManager) -> InlineKeyboardMarkup:
    """Создать специфичную клавиатуру для секции"""
    if section == NavigationSection.RECIPES:
        keyboard = [
            [
                InlineKeyboardButton("🔍 Поиск", callback_data=f"{SECTION_RECIPES}:{ACTION_SEARCH}"),
                InlineKeyboardButton("➕ Добавить", callback_data=f"{SECTION_RECIPES}:{ACTION_ADD}")
            ],
            [
                InlineKeyboardButton("📋 Мои рецепты", callback_data=f"{SECTION_RECIPES}:{ACTION_LIST}"),
                InlineKeyboardButton("🗂️ Категории", callback_data=f"{SECTION_RECIPES}:{SECTION_CATEGORIES}")
            ],
            [InlineKeyboardButton("🧮 Анализ", callback_data=f"{SECTION_RECIPES}:{ACTION_ANALYZE}")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back")]
        ]
    elif section == NavigationSection.PRODUCTS:
        keyboard = [
            [
                InlineKeyboardButton("🔍 Поиск", callback_data=f"{SECTION_PRODUCTS}:{ACTION_SEARCH}"),
                InlineKeyboardButton("➕ Добавить", callback_data=f"{SECTION_PRODUCTS}:{ACTION_ADD}")
            ],
            [
                InlineKeyboardButton("🗂️ Категории", callback_data=f"{SECTION_PRODUCTS}:{SECTION_CATEGORIES}"),
                InlineKeyboardButton("🧮 Калькулятор", callback_data=f"{SECTION_PRODUCTS}:{ACTION_CALCULATE}")
            ],
            [
                InlineKeyboardButton("📊 История", callback_data=f"{SECTION_PRODUCTS}:{ACTION_LIST}"),
                InlineKeyboardButton("◀️ Назад", callback_data="back")
            ]
        ]
    elif section == NavigationSection.CATEGORIES:
        keyboard = [
            [
                InlineKeyboardButton("👁 Просмотр", callback_data=f"{SECTION_CATEGORIES}:{ACTION_VIEW}"),
                InlineKeyboardButton("➕ Добавить", callback_data=f"{SECTION_CATEGORIES}:{ACTION_ADD}")
            ],
            [
                InlineKeyboardButton("✏️ Редактировать", callback_data=f"{SECTION_CATEGORIES}:{ACTION_EDIT}"),
                InlineKeyboardButton("🗑️ Удалить", callback_data=f"{SECTION_CATEGORIES}:{ACTION_DELETE}")
            ],
            [InlineKeyboardButton("◀️ Назад", callback_data="back")]
        ]
    elif section == NavigationSection.NUTRIENTS:
        keyboard = [
            [
                InlineKeyboardButton("🧮 Калькулятор", callback_data=f"{SECTION_NUTRIENTS}:{ACTION_CALCULATE}"),
                InlineKeyboardButton("📊 Анализ рецепта", callback_data=f"{SECTION_NUTRIENTS}:{ACTION_ANALYZE}")
            ],
            [InlineKeyboardButton("◀️ Назад", callback_data="back")]
        ]
    elif section == NavigationSection.COLLABORATIVE:
        keyboard = [
            # Здесь были пункты 'Пригласить', 'Мои коллаборации', 'Присоединиться' — удалены как неиспользуемые
        ]
    else:
        # Возвращаем стандартную клавиатуру секции
        return create_section_keyboard(section, navigation_manager)
    
    return InlineKeyboardMarkup(keyboard) 