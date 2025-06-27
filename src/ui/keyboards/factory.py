"""
Фабрика клавиатур для EatBot
Позволяет генерировать все типы клавиатур по типу и параметрам.
"""
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import Optional, List, Dict, Any
import logging

ADD_RECIPE_CALLBACK = "add_recipe"

logger = logging.getLogger("src.ui.keyboards.factory")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
if not logger.hasHandlers():
    logger.addHandler(handler)

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
        else:
            raise ValueError(f"Неизвестный тип клавиатуры: {keyboard_type}")

    @staticmethod
    def _main_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("📚 Рецепты", callback_data="main_recipes"),
                InlineKeyboardButton("🍏 Продукты", callback_data="main_products")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _recipe_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("🔍 Поиск", callback_data="recipe_search"),
                InlineKeyboardButton("➕ Добавить", callback_data=ADD_RECIPE_CALLBACK)
            ],
            [
                InlineKeyboardButton("📋 Мои рецепты", callback_data="recipe_list"),
                InlineKeyboardButton("🗂️ Категории", callback_data="recipe_categories")
            ],
            [InlineKeyboardButton("🧮 Калькулятор БЖУ", callback_data="product_calculator")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _products_menu() -> InlineKeyboardMarkup:
        """Клавиатура для меню продуктов"""
        keyboard = [
            [
                InlineKeyboardButton("🔍 Поиск", callback_data="product_search"), 
                InlineKeyboardButton("➕ Добавить", callback_data="product_add")
            ],
            [
                InlineKeyboardButton("📋 Категории", callback_data="product_categories"), 
                InlineKeyboardButton("🧮 Калькулятор БЖУ", callback_data="product_calculator")
            ],
            [
                InlineKeyboardButton("◀️ Назад", callback_data="back")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _collaborative_menu() -> InlineKeyboardMarkup:
        """Клавиатура для меню совместной работы"""
        keyboard = [
            [InlineKeyboardButton("➕ Пригласить", callback_data="collaborative_invite")],
            [InlineKeyboardButton("📋 Мои коллаборации", callback_data="collaborative_list")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _nutrient_menu() -> InlineKeyboardMarkup:
        """Клавиатура для меню нутриентов"""
        keyboard = [
            [
                InlineKeyboardButton("🔍 Поиск нутриентов", callback_data="nutrient_search"),
                InlineKeyboardButton("📚 Справочник", callback_data="nutrient_reference")
            ],
            [
                InlineKeyboardButton("🧮 Калькулятор БЖУ", callback_data="nutrient_calculator"),
                InlineKeyboardButton("📊 Анализ рациона", callback_data="nutrient_analysis")
            ],
            [InlineKeyboardButton("◀️ Назад", callback_data="back")]
        ]
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
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="back")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_confirmation_keyboard(action_prefix: str, entity_id, back_callback: str = "back") -> InlineKeyboardMarkup:
        """
        Универсальная клавиатура подтверждения для любых сущностей.
        action_prefix: например, 'recipe_delete_confirm'
        entity_id: строка или число (UUID или int)
        back_callback: callback_data для кнопки отмены (по умолчанию 'back')
        """
        callback_data = f"{action_prefix}_{entity_id}"
        logger.info(f"[KEYBOARD] callback_data={callback_data}, длина={len(callback_data)}, type(entity_id)={type(entity_id)}, value={entity_id}")
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить", callback_data=callback_data)],
            [InlineKeyboardButton("❌ Отмена", callback_data=back_callback)]
        ]
        return InlineKeyboardMarkup(keyboard)

# Пример использования:
# KeyboardFactory.get("main_menu")
# KeyboardFactory.get("recipe_menu")
# KeyboardFactory.get("dynamic_inline", buttons=[[{"text": "A", "callback_data": "a"}]])
# KeyboardFactory.get("dynamic_reply", buttons=[["A", "B"]]) 