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
        elif keyboard_type == "dynamic_inline":
            return KeyboardFactory._dynamic_inline(kwargs.get("buttons", []))
        elif keyboard_type == "dynamic_reply":
            return KeyboardFactory._dynamic_reply(kwargs.get("buttons", []))
        elif keyboard_type == "back":
            return KeyboardFactory._back()
        elif keyboard_type == "navigation":
            return KeyboardFactory._navigation_buttons(kwargs.get("show_main_menu", True))
        elif keyboard_type == "recipe_edit":
            return KeyboardFactory._get_recipe_edit_keyboard(kwargs)
        elif keyboard_type == "recipe_edit_confirm":
            return KeyboardFactory._get_recipe_edit_confirm_keyboard(kwargs)
        elif keyboard_type == "recipe_edit_field":
            return KeyboardFactory._get_recipe_edit_field_keyboard(kwargs)
        elif keyboard_type == "product_menu":
            return KeyboardFactory._product_menu()
        elif keyboard_type == "product_edit":
            return KeyboardFactory._get_product_edit_keyboard(kwargs)
        elif keyboard_type == "product_edit_confirm":
            return KeyboardFactory._get_product_edit_confirm_keyboard(kwargs)
        elif keyboard_type == "product_edit_field":
            return KeyboardFactory._get_product_edit_field_keyboard(kwargs)
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
        """Унифицированное меню рецептов с навигационными кнопками"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "📋 Мои рецепты", 
                    callback_data=CallbackDataBuilder.build("recipes", "list")
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ Добавить рецепт", 
                    callback_data=CallbackDataBuilder.build("recipes", "add")
                )
            ],
            [
                InlineKeyboardButton(
                    "🔍 Поиск рецептов", 
                    callback_data=CallbackDataBuilder.build("recipes", "search")
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

    @staticmethod
    def get_recipe_list_keyboard(recipes: List[Dict[str, Any]], current_page: int, total_pages: int) -> InlineKeyboardMarkup:
        """
        Унифицированная клавиатура для списка рецептов
        
        Args:
            recipes: Список рецептов для отображения
            current_page: Текущая страница
            total_pages: Общее количество страниц
        """
        keyboard = []
        
        # Кнопки рецептов
        for recipe in recipes:
            recipe_id = recipe.get('id')
            recipe_name = recipe.get('name', 'Без названия')
            display_name = recipe_name[:30] + "..." if len(recipe_name) > 30 else recipe_name
            
            if recipe_id:
                keyboard.append([
                    InlineKeyboardButton(
                        display_name, 
                        callback_data=CallbackDataBuilder.build("recipes", "view", id=recipe_id)
                    )
                ])
        
        # Пагинация
        if total_pages > 1:
            pagination_row = []
            
            if current_page > 1:
                pagination_row.append(
                    InlineKeyboardButton(
                        "◀️", 
                        callback_data=CallbackDataBuilder.build("recipes", "list", page=current_page-1)
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
                        callback_data=CallbackDataBuilder.build("recipes", "list", page=current_page+1)
                    )
                )
            
            keyboard.append(pagination_row)
        
        # Навигационные кнопки
        keyboard.extend(KeyboardFactory._get_navigation_row())
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_recipe_view_keyboard(recipe_id: str) -> InlineKeyboardMarkup:
        """
        Унифицированная клавиатура для просмотра рецепта
        
        Args:
            recipe_id: ID рецепта
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "✏️ Редактировать", 
                    callback_data=CallbackDataBuilder.build("recipes", "edit", id=recipe_id)
                ),
                InlineKeyboardButton(
                    "🗑️ Удалить", 
                    callback_data=CallbackDataBuilder.build("recipes", "delete_confirm", id=recipe_id)
                )
            ]
        ]
        
        keyboard.extend(KeyboardFactory._get_navigation_row())
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_recipe_search_keyboard() -> InlineKeyboardMarkup:
        """Унифицированная клавиатура для поиска рецептов"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔍 По названию", 
                    callback_data=CallbackDataBuilder.build("recipes", "search_by_name")
                )
            ],
            [
                InlineKeyboardButton(
                    "🥗 По ингредиентам", 
                    callback_data=CallbackDataBuilder.build("recipes", "search_by_ingredients")
                )
            ]
        ]
        
        keyboard.extend(KeyboardFactory._get_navigation_row())
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _get_recipe_edit_keyboard(params: dict) -> InlineKeyboardMarkup:
        """Клавиатура для редактирования рецепта"""
        recipe_id = params.get("id")
        keyboard = [
            [
                InlineKeyboardButton(
                    "📝 Название", 
                    callback_data=CallbackDataBuilder.build("recipes", "edit_name", id=recipe_id)
                ),
                InlineKeyboardButton(
                    "🥗 Ингредиенты", 
                    callback_data=CallbackDataBuilder.build("recipes", "edit_ingredients", id=recipe_id)
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 Инструкции", 
                    callback_data=CallbackDataBuilder.build("recipes", "edit_instructions", id=recipe_id)
                )
            ]
        ]
        keyboard.extend(KeyboardFactory._get_navigation_row())
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _get_recipe_edit_confirm_keyboard(params: dict) -> InlineKeyboardMarkup:
        """Клавиатура для подтверждения редактирования"""
        recipe_id = params.get("id")
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Сохранить", 
                    callback_data=CallbackDataBuilder.build("recipes", "edit_confirm", id=recipe_id)
                ),
                InlineKeyboardButton(
                    "❌ Отмена", 
                    callback_data=CallbackDataBuilder.build("recipes", "view", id=recipe_id)
                )
            ]
        ]
        keyboard.extend(KeyboardFactory._get_navigation_row())
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _get_recipe_edit_field_keyboard(params: dict) -> InlineKeyboardMarkup:
        """Клавиатура для редактирования конкретного поля"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Готово", 
                    callback_data=CallbackDataBuilder.build("recipes", "edit_confirm")
                ),
                InlineKeyboardButton(
                    "❌ Отмена", 
                    callback_data=CallbackDataBuilder.build("nav", "back")
                )
            ]
        ]
        keyboard.extend(KeyboardFactory._get_navigation_row())
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _product_menu() -> InlineKeyboardMarkup:
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
            ]
        ]
        
        # Добавляем навигационные кнопки
        keyboard.extend(KeyboardFactory._get_navigation_row())
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _get_product_edit_keyboard(params: dict) -> InlineKeyboardMarkup:
        """Клавиатура для редактирования продукта"""
        product_id = params.get("id")
        keyboard = [
            [
                InlineKeyboardButton(
                    "📝 Название", 
                    callback_data=CallbackDataBuilder.build("products", "edit_name", id=product_id)
                ),
                InlineKeyboardButton(
                    "🏷️ Категория", 
                    callback_data=CallbackDataBuilder.build("products", "edit_category", id=product_id)
                )
            ],
            [
                InlineKeyboardButton(
                    "🥗 Пищевая ценность", 
                    callback_data=CallbackDataBuilder.build("products", "edit_nutrition", id=product_id)
                )
            ]
        ]
        keyboard.extend(KeyboardFactory._get_navigation_row())
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _get_product_edit_confirm_keyboard(params: dict) -> InlineKeyboardMarkup:
        """Клавиатура для подтверждения редактирования продукта"""
        product_id = params.get("id")
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Сохранить", 
                    callback_data=CallbackDataBuilder.build("products", "edit_confirm", id=product_id)
                ),
                InlineKeyboardButton(
                    "❌ Отмена", 
                    callback_data=CallbackDataBuilder.build("products", "view", id=product_id)
                )
            ]
        ]
        keyboard.extend(KeyboardFactory._get_navigation_row())
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _get_product_edit_field_keyboard(params: dict) -> InlineKeyboardMarkup:
        """Клавиатура для редактирования конкретного поля продукта"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Готово", 
                    callback_data=CallbackDataBuilder.build("products", "edit_confirm")
                ),
                InlineKeyboardButton(
                    "❌ Отмена", 
                    callback_data=CallbackDataBuilder.build("nav", "back")
                )
            ]
        ]
        keyboard.extend(KeyboardFactory._get_navigation_row())
        return InlineKeyboardMarkup(keyboard)

# Пример использования:
# KeyboardFactory.get("main_menu")
# KeyboardFactory.get("recipe_menu")
# KeyboardFactory.get("dynamic_inline", buttons=[[{"text": "A", "callback_data": "a"}]])
# KeyboardFactory.get("dynamic_reply", buttons=[["A", "B"]]) 