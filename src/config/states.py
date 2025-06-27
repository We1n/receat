"""
Состояния для FSM (Finite State Machine)
"""
from enum import Enum, auto

class States(Enum):
    """Состояния бота"""
    MAIN_MENU = "main_menu"
    RECIPES_MENU = "recipes_menu"
    NUTRIENT_MENU = "nutrient_menu"
    PROFILE_MENU = "profile_menu"
    PRODUCTS_MENU = "products_menu"
    COLLABORATIVE_MENU = auto()
    SETTINGS_MENU = "settings_menu"
    CATEGORIES_MENU = auto()
    
    # Состояния для работы с рецептами
    RECIPE_SEARCH = "recipe_search"
    RECIPE_ADD = "recipe_add"
    RECIPE_EDIT = "recipe_edit"
    RECIPE_VIEW = "recipe_view"
    
    # Состояния для работы с продуктами
    PRODUCT_SEARCH = "product_search"
    PRODUCT_ADD = "product_add"
    PRODUCT_EDIT = "product_edit"
    
    # Состояния для работы с нутриентами
    NUTRIENT_CALC = "nutrient_calc"
    NUTRIENT_ANALYSIS = "nutrient_analysis"
    
    # Состояния для работы с профилем
    PROFILE_EDIT = "profile_edit"
    PROFILE_VIEW = "profile_view"
    
    # Состояния для совместной работы
    COLLABORATIVE_INVITE = "collaborative_invite"
    COLLABORATIVE_ACCEPT = "collaborative_accept"
    
    # Состояния для категорий
    CATEGORY_ADD = "category_add"
    CATEGORY_EDIT = "category_edit"
    ADDING_CATEGORY = auto()
    EDITING_CATEGORY = auto()
    RENAMING_CATEGORY = auto()
    DELETING_CATEGORY = auto()
    CONFIRMING_DELETE = auto()
    CHOOSING_ACTION = auto()
    AWAITING_CATEGORY_NAME = auto()
    AWAITING_CATEGORY_TO_EDIT = auto()
    AWAITING_NEW_CATEGORY_NAME = auto()
    AWAITING_CATEGORY_TO_DELETE = auto()
    CONFIRMING_DELETE_CATEGORY = auto()
    
    # Общие состояния
    WAITING_INPUT = "waiting_input"
    CONFIRMATION = "confirmation"
    ERROR = "error"

# Состояния для работы с ценами
WAITING_PRICE = 1001

# Состояния для ConversationHandler и других сценариев
RECIPE_ADD, PRODUCT_ADD, PRODUCT_SEARCH, RECIPE_SEARCH, NUTRIENT_CALCULATOR = range(5)

# Можно добавить другие состояния, если нужно 