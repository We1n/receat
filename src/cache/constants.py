# src/cache/constants.py

# Шаблоны ключей для кэша
CACHE_KEYS = {
    "users": "users",
    "user": "user_{user_id}",
    "user_by_username": "user_by_username_{username}",
    "user_preferences": "user_preferences_{user_id}",
    "user_favorites": "user_favorites_{user_id}",
    "user_history": "user_history_{user_id}",
    "user_allergies": "user_allergies_{user_id}",
    "user_restrictions": "user_restrictions_{user_id}",
    "recipes": "recipes",
    "recipe": "recipe_{recipe_name}",
    "search": "search_{query}",
    "recipes_by_ingredients": "recipes_by_ingredients_{ingredients}",
    "recipes_by_difficulty": "recipes_by_difficulty_{difficulty}",
    "recipe_servings": "recipe_servings_{recipe_name}_{target_servings}",
    "recipe_cost": "recipe_cost_{recipe_name}",
    "recipe_time": "recipe_time_{recipe_name}",
    "recipes_by_calories": "recipes_by_calories_{min_calories}_{max_calories}",
    "recipes_by_macros": "recipes_by_macros_{macros}",
    "recipe_substitutes": "recipe_substitutes_{ingredient_name}",
    "recipe_with_substitutes": "recipe_with_substitutes_{recipe_name}",
}

# Время жизни кэша (TTL) в секундах
CACHE_TTL = {
    "users": 3600,
    "user": 3600,
    "user_by_username": 3600,
    "user_preferences": 3600,
    "user_favorites": 3600,
    "user_history": 3600,
    "user_allergies": 3600,
    "user_restrictions": 3600,
    "recipes": 3600,
    "recipe": 3600,
    "search": 600,
    "recipes_by_ingredients": 1800,
    "recipes_by_difficulty": 1800,
    "recipe_servings": 1800,
    "recipe_cost": 1800,
    "recipe_time": 1800,
    "recipes_by_calories": 1800,
    "recipes_by_macros": 1800,
    "recipe_substitutes": 1800,
    "recipe_with_substitutes": 1800,
}

# Префиксы для ключей кэша
CACHE_PREFIXES = {
    "users": "usr:",
    "user": "usr:",
    "user_by_username": "usr:",
    "user_preferences": "usr:",
    "user_favorites": "usr:",
    "user_history": "usr:",
    "user_allergies": "usr:",
    "user_restrictions": "usr:",
    "recipes": "rec:",
    "recipe": "rec:",
    "search": "rec:",
    "recipes_by_ingredients": "rec:",
    "recipes_by_difficulty": "rec:",
    "recipe_servings": "rec:",
    "recipe_cost": "rec:",
    "recipe_time": "rec:",
    "recipes_by_calories": "rec:",
    "recipes_by_macros": "rec:",
    "recipe_substitutes": "rec:",
    "recipe_with_substitutes": "rec:",
}

# Заглушки для совместимости
CACHE_ERRORS: dict = {}
CACHE_ERROR_MESSAGES: dict = {} 