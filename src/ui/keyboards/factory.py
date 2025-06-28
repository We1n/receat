"""
Фабрика клавиатур для EatBot
Позволяет генерировать все типы клавиатур по типу и параметрам.
Использует стандартизированный формат callback_data: section:action:params
"""
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger("src.ui.keyboards.factory")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
if not logger.hasHandlers():
    logger.addHandler(handler)

class CallbackDataBuilder:
    """Строитель для создания стандартизированных callback_data"""
    
    @staticmethod
    def build(section: str, action: str, **params) -> str:
        """
        Создает callback_data в формате section:action:param1=value1:param2=value2
        
        Args:
            section: Раздел (main, recipes, products, nav)
            action: Действие (menu, list, view, add, search, back, main_menu)
            **params: Дополнительные параметры (id, page, etc.)
        """
        parts = [section, action]
        
        for key, value in params.items():
            if value is not None:
                parts.append(f"{key}={value}")
        
        callback_data = ":".join(parts)
        
        # Проверяем ограничение Telegram (64 байта)
        if len(callback_data.encode('utf-8')) > 64:
            logger.warning(f"Callback data too long ({len(callback_data)} chars): {callback_data}")
            # Обрезаем до безопасной длины
            callback_data = callback_data[:60] + "..."
        
        return callback_data

class KeyboardFactory:
    """
    Универсальная фабрика клавиатур для бота.
    Используйте get(type, **kwargs) для получения нужной клавиатуры.
    """
    @staticmethod
    def get(keyboard_type: str, **kwargs) -> Any:
        if keyboard_type == "main_menu":
            return KeyboardFactory._main_menu()
        elif keyboard_type == "recipe_menu":
            return KeyboardFactory._recipe_menu()
        elif keyboard_type == "products_menu":
            return KeyboardFactory._products_menu()
        elif keyboard_type == "collaborative_menu":
            return KeyboardFactory._collaborative_menu()
        elif keyboard_type == "nutrient_menu":
            return KeyboardFactory._nutrient_menu()
        elif keyboard_type == "dynamic_inline":
            return KeyboardFactory._dynamic_inline(kwargs.get("buttons", []))
        elif keyboard_type == "dynamic_reply":
            return KeyboardFactory._dynamic_reply(kwargs.get("buttons", []))
        elif keyboard_type == "back":
            return KeyboardFactory._back()
        elif keyboard_type == "navigation":
            return KeyboardFactory._navigation_buttons(kwargs.get("show_main_menu", True))
        else:
            raise ValueError(f"Неизвестный тип клавиатуры: {keyboard_type}")

    @staticmethod
    def _main_menu() -> InlineKeyboardMarkup:
        """Главное меню с новым форматом callback_data"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "📚 Рецепты", 
                    callback_data=CallbackDataBuilder.build("main", "recipes")
                ),
                InlineKeyboardButton(
                    "🍏 Продукты", 
                    callback_data=CallbackDataBuilder.build("main", "products")
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _recipe_menu() -> InlineKeyboardMarkup:
        """Меню рецептов с навигационными кнопками"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔍 Поиск", 
                    callback_data=CallbackDataBuilder.build("recipes", "search")
                ),
                InlineKeyboardButton(
                    "➕ Добавить", 
                    callback_data=CallbackDataBuilder.build("recipes", "add")
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 Мои рецепты", 
                    callback_data=CallbackDataBuilder.build("recipes", "list")
                )
            ],
            [
                InlineKeyboardButton(
                    "🧮 Калькулятор БЖУ", 
                    callback_data=CallbackDataBuilder.build("products", "calculator")
                )
            ]
        ]
        
        # Добавляем навигационные кнопки
        keyboard.extend(KeyboardFactory._get_navigation_row())
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _products_menu() -> InlineKeyboardMarkup:
        """Меню продуктов с навигационными кнопками"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔍 Поиск", 
                    callback_data=CallbackDataBuilder.build("products", "search")
                ),
                InlineKeyboardButton(
                    "➕ Добавить", 
                    callback_data=CallbackDataBuilder.build("products", "add")
                )
            ],
            [
                InlineKeyboardButton(
                    "🧮 Калькулятор БЖУ", 
                    callback_data=CallbackDataBuilder.build("products", "calculator")
                )
            ]
        ]
        
        # Добавляем навигационные кнопки
        keyboard.extend(KeyboardFactory._get_navigation_row())
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _collaborative_menu() -> InlineKeyboardMarkup:
        """Меню совместной работы с навигационными кнопками"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "➕ Пригласить", 
                    callback_data=CallbackDataBuilder.build("collaborative", "invite")
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 Мои коллаборации", 
                    callback_data=CallbackDataBuilder.build("collaborative", "list")
                )
            ]
        ]
        
        # Добавляем навигационные кнопки
        keyboard.extend(KeyboardFactory._get_navigation_row())
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _nutrient_menu() -> InlineKeyboardMarkup:
        """Меню нутриентов с навигационными кнопками"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔍 Поиск нутриентов", 
                    callback_data=CallbackDataBuilder.build("nutrients", "search")
                ),
                InlineKeyboardButton(
                    "📚 Справочник", 
                    callback_data=CallbackDataBuilder.build("nutrients", "reference")
                )
            ],
            [
                InlineKeyboardButton(
                    "🧮 Калькулятор БЖУ", 
                    callback_data=CallbackDataBuilder.build("nutrients", "calculator")
                ),
                InlineKeyboardButton(
                    "📊 Анализ рациона", 
                    callback_data=CallbackDataBuilder.build("nutrients", "analysis")
                )
            ]
        ]
        
        # Добавляем навигационные кнопки
        keyboard.extend(KeyboardFactory._get_navigation_row())
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _dynamic_inline(buttons: list) -> InlineKeyboardMarkup:
        """
        Генерирует InlineKeyboardMarkup из списка списков кнопок.
        Пример buttons:
        [
            [
                {"text": "Кнопка 1", "callback_data": "cb1"},
                {"text": "Кнопка 2", "callback_data": "cb2"}
            ],
            [
                {"text": "Назад", "callback_data": "back"}
            ]
        ]
        """
        keyboard = []
        for row in buttons:
            keyboard.append([InlineKeyboardButton(**btn) for btn in row])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _dynamic_reply(buttons: list) -> ReplyKeyboardMarkup:
        """
        Генерирует ReplyKeyboardMarkup из списка списков кнопок.
        Пример buttons:
        [
            ["Кнопка 1", "Кнопка 2"],
            ["Назад"]
        ]
        """
        keyboard = [[KeyboardButton(text) for text in row] for row in buttons]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def _back() -> InlineKeyboardMarkup:
        """Простая кнопка 'Назад'"""
        keyboard = [
            [InlineKeyboardButton(
                "◀️ Назад", 
                callback_data=CallbackDataBuilder.build("nav", "back")
            )]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _navigation_buttons(show_main_menu: bool = True) -> InlineKeyboardMarkup:
        """Унифицированные кнопки навигации"""
        keyboard = [
            [InlineKeyboardButton(
                "◀️ Назад", 
                callback_data=CallbackDataBuilder.build("nav", "back")
            )]
        ]
        
        if show_main_menu:
            keyboard.append([
                InlineKeyboardButton(
                    "🏠 Главное меню", 
                    callback_data=CallbackDataBuilder.build("nav", "main_menu")
                )
            ])
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _get_navigation_row() -> List[List[InlineKeyboardButton]]:
        """Возвращает строку с навигационными кнопками"""
        return [
            [
                InlineKeyboardButton(
                    "◀️ Назад", 
                    callback_data=CallbackDataBuilder.build("nav", "back")
                ),
                InlineKeyboardButton(
                    "🏠 Главное меню", 
                    callback_data=CallbackDataBuilder.build("nav", "main_menu")
                )
            ]
        ]

    @staticmethod
    def get_confirmation_keyboard(action: str, entity_id: str, section: str = "recipes") -> InlineKeyboardMarkup:
        """
        Универсальная клавиатура подтверждения для любых сущностей.
        
        Args:
            action: Действие (delete, edit, etc.)
            entity_id: ID сущности
            section: Раздел (recipes, products, etc.)
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Подтвердить", 
                    callback_data=CallbackDataBuilder.build(section, f"{action}_confirm", id=entity_id)
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Отмена", 
                    callback_data=CallbackDataBuilder.build("nav", "back")
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_recipe_confirm_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура подтверждения добавления рецепта"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Подтвердить", 
                    callback_data=CallbackDataBuilder.build("recipes", "add_confirm")
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Отменить", 
                    callback_data=CallbackDataBuilder.build("nav", "back")
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_pagination_keyboard(section: str, action: str, current_page: int, total_pages: int, **params) -> InlineKeyboardMarkup:
        """
        Клавиатура с пагинацией
        
        Args:
            section: Раздел (recipes, products, etc.)
            action: Действие (list, search, etc.)
            current_page: Текущая страница
            total_pages: Общее количество страниц
            **params: Дополнительные параметры (search_query, filters, etc.)
        """
        keyboard = []
        
        # Кнопки пагинации
        pagination_row = []
        
        if current_page > 1:
            pagination_row.append(
                InlineKeyboardButton(
                    "◀️", 
                    callback_data=CallbackDataBuilder.build(section, action, page=current_page-1, **params)
                )
            )
        
        pagination_row.append(
            InlineKeyboardButton(
                f"{current_page}/{total_pages}", 
                callback_data="no_action"
            )
        )
        
        if current_page < total_pages:
            pagination_row.append(
                InlineKeyboardButton(
                    "▶️", 
                    callback_data=CallbackDataBuilder.build(section, action, page=current_page+1, **params)
                )
            )
        
        if pagination_row:
            keyboard.append(pagination_row)
        
        # Навигационные кнопки
        keyboard.extend(KeyboardFactory._get_navigation_row())
        
        return InlineKeyboardMarkup(keyboard)

# Пример использования:
# KeyboardFactory.get("main_menu")
# KeyboardFactory.get("recipe_menu")
# KeyboardFactory.get("dynamic_inline", buttons=[[{"text": "A", "callback_data": "a"}]])
# KeyboardFactory.get("dynamic_reply", buttons=[["A", "B"]]) 