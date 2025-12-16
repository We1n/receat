"""
Модуль клавиатур для Telegram бота.

Доступные клавиатуры:
- main_menu — главное меню (InlineKeyboard)
- recipe_menu — меню рецептов (InlineKeyboard)
- products_menu — меню продуктов (InlineKeyboard)
- collaborative_menu — меню совместной работы (InlineKeyboard)
- dynamic_inline — динамическая inline клавиатура
- dynamic_reply — динамическая reply клавиатура
- confirm — клавиатура подтверждения
- back — клавиатура с кнопкой "Назад"

Использование:
    from src.ui.keyboards import KeyboardFactory
    
    keyboard = KeyboardFactory.get("main_menu")
    keyboard = KeyboardFactory.get("recipe_menu")
    keyboard = KeyboardFactory.get("dynamic_inline", buttons=[[{"text": "A", "callback_data": "a"}]])
"""

from .factory import KeyboardFactory

__all__ = ['KeyboardFactory']

def main_menu():
    """Главное меню: обёртка для NavigationManager"""
    from src.ui.navigation import NavigationManager
    return NavigationManager().get_main_menu() 