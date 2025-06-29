"""
Состояния для FSM (Finite State Machine)
"""
from enum import Enum, auto

class States(Enum):
    """Состояния бота"""
    MAIN_MENU = "main_menu"
    RECIPES_MENU = "recipes_menu"
    PROFILE_MENU = "profile_menu"
    PRODUCTS_MENU = "products_menu"
    COLLABORATIVE_MENU = auto()
    SETTINGS_MENU = "settings_menu"
    
    # Состояния для работы с рецептами
    RECIPE_SEARCH = "recipe_search"
    RECIPE_ADD = "recipe_add"
    RECIPE_EDIT = "recipe_edit"
    RECIPE_VIEW = "recipe_view"
    
    # Состояния для работы с продуктами
    PRODUCT_SEARCH = "product_search"
    PRODUCT_ADD = "product_add"
    PRODUCT_EDIT = "product_edit"
    
    # Состояния для работы с профилем
    PROFILE_EDIT = "profile_edit"
    PROFILE_VIEW = "profile_view"
    
    # Состояния для совместной работы
    COLLABORATIVE_INVITE = "collaborative_invite"
    COLLABORATIVE_ACCEPT = "collaborative_accept"
    
    # Общие состояния
    WAITING_INPUT = "waiting_input"
    CONFIRMATION = "confirmation"
    ERROR = "error"

# Состояния для работы с ценами
WAITING_PRICE = 1001

# Состояния для ConversationHandler и других сценариев
RECIPE_ADD, PRODUCT_ADD, PRODUCT_SEARCH, RECIPE_SEARCH = range(4)

# Можно добавить другие состояния, если нужно 