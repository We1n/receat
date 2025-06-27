"""
Единая система валидации на основе Pydantic

Этот модуль содержит все схемы валидации для DTO (Data Transfer Objects)
в соответствии с планом рефакторинга унификации обработки пользовательского ввода.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator, model_validator
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# БАЗОВЫЕ СХЕМЫ
# ============================================================================

class BaseResponse(BaseModel):
    """Базовая схема для всех ответов API"""
    success: bool = Field(..., description="Статус операции")
    message: Optional[str] = Field(None, description="Сообщение для пользователя")
    data: Optional[Any] = Field(None, description="Данные ответа")
    errors: Optional[Dict[str, str]] = Field(None, description="Ошибки валидации")

class ValidationErrorResponse(BaseResponse):
    """Схема для ответов с ошибками валидации"""
    success: bool = Field(False, description="Операция не выполнена")
    errors: Dict[str, str] = Field(..., description="Детализированные ошибки по полям")

# ============================================================================
# СХЕМЫ ДЛЯ РЕЦЕПТОВ
# ============================================================================

class IngredientDTO(BaseModel):
    """DTO для ингредиента"""
    name: str = Field(..., min_length=1, max_length=100, description="Название ингредиента")
    amount: float = Field(..., gt=0, le=10000, description="Количество")
    unit: str = Field(..., min_length=1, max_length=20, description="Единица измерения")
    
    @validator('name')
    def validate_name(cls, v):
        """Валидация названия ингредиента"""
        if not v.strip():
            raise ValueError("Название ингредиента не может быть пустым")
        return v.strip()
    
    @validator('unit')
    def validate_unit(cls, v):
        """Валидация единицы измерения"""
        allowed_units = ["г", "кг", "мл", "л", "шт", "ч.л.", "ст.л.", "по вкусу", "щепотка"]
        if v not in allowed_units:
            raise ValueError(f"Недопустимая единица измерения. Разрешены: {', '.join(allowed_units)}")
        return v

class NutrientsDTO(BaseModel):
    """DTO для питательных веществ"""
    calories: float = Field(ge=0, le=10000, description="Калории")
    proteins: float = Field(ge=0, le=1000, description="Белки (г)")
    fats: float = Field(ge=0, le=1000, description="Жиры (г)")
    carbs: float = Field(ge=0, le=1000, description="Углеводы (г)")

class RecipeDTO(BaseModel):
    """DTO для рецепта"""
    name: str = Field(..., description="Название рецепта")
    ingredients: List[IngredientDTO] = Field(..., description="Список ингредиентов")
    instructions: str = Field(..., description="Инструкции по приготовлению")
    nutrients: NutrientsDTO = Field(..., description="Питательные вещества")
    cooking_time: int = Field(..., ge=1, le=1440, description="Время приготовления в минутах")
    difficulty: str = Field(..., description="Сложность")
    portions: int = Field(..., ge=1, le=50, description="Количество порций")
    tags: List[str] = Field(default=[], description="Теги")
    notes: Optional[str] = Field(None, max_length=1000, description="Заметки")
    source: Optional[str] = Field(None, max_length=200, description="Источник")
    
    @validator('difficulty')
    def validate_difficulty(cls, v):
        """Валидация сложности"""
        allowed_levels = ["Легкая", "Средняя", "Сложная"]
        if v not in allowed_levels:
            raise ValueError(f"Недопустимый уровень сложности. Разрешены: {', '.join(allowed_levels)}")
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Валидация тегов"""
        if v:
            for tag in v:
                if len(tag) < 2 or len(tag) > 50:
                    raise ValueError("Теги должны быть от 2 до 50 символов")
        return v

class RecipeSearchDTO(BaseModel):
    """DTO для поиска рецептов"""
    query: Optional[str] = Field(None, max_length=100, description="Поисковый запрос")
    max_cooking_time: Optional[int] = Field(None, ge=1, le=1440, description="Максимальное время приготовления")
    difficulty: Optional[str] = Field(None, description="Сложность")
    max_calories: Optional[float] = Field(None, ge=0, le=10000, description="Максимальная калорийность")
    tags: Optional[List[str]] = Field(None, description="Теги")
    page: int = Field(1, ge=1, description="Номер страницы")
    limit: int = Field(10, ge=1, le=50, description="Количество результатов на странице")

# ============================================================================
# СХЕМЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================================

class UserProfileDTO(BaseModel):
    """DTO для профиля пользователя"""
    user_id: int = Field(..., gt=0, description="ID пользователя")
    username: str = Field(..., min_length=3, max_length=32, description="Имя пользователя")
    first_name: Optional[str] = Field(None, max_length=64, description="Имя")
    last_name: Optional[str] = Field(None, max_length=64, description="Фамилия")
    weight: Optional[float] = Field(None, ge=20, le=300, description="Вес в кг")
    height: Optional[float] = Field(None, ge=100, le=250, description="Рост в см")
    age: Optional[int] = Field(None, ge=12, le=120, description="Возраст")
    gender: Optional[str] = Field(None, description="Пол")
    activity_level: Optional[str] = Field(None, description="Уровень активности")
    target_calories: Optional[int] = Field(None, ge=800, le=5000, description="Целевые калории")
    
    @validator('username')
    def validate_username(cls, v):
        """Валидация имени пользователя"""
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Имя пользователя может содержать только буквы, цифры и подчеркивания")
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        """Валидация пола"""
        if v and v.lower() not in ['male', 'female', 'мужской', 'женский']:
            raise ValueError("Пол должен быть 'male'/'мужской' или 'female'/'женский'")
        return v.lower() if v else v
    
    @validator('activity_level')
    def validate_activity_level(cls, v):
        """Валидация уровня активности"""
        if v and v.lower() not in ['low', 'medium', 'high', 'низкий', 'средний', 'высокий']:
            raise ValueError("Недопустимый уровень активности")
        return v.lower() if v else v

class UserMealDTO(BaseModel):
    """DTO для приема пищи пользователя"""
    user_id: int = Field(..., gt=0, description="ID пользователя")
    meal_type: str = Field(..., description="Тип приема пищи")
    recipe_id: Optional[int] = Field(None, gt=0, description="ID рецепта")
    custom_food: Optional[str] = Field(None, max_length=200, description="Собственная еда")
    amount: float = Field(..., gt=0, le=10000, description="Количество")
    unit: str = Field(..., description="Единица измерения")
    calories: float = Field(..., ge=0, le=10000, description="Калории")
    proteins: float = Field(..., ge=0, le=1000, description="Белки")
    fats: float = Field(..., ge=0, le=1000, description="Жиры")
    carbs: float = Field(..., ge=0, le=1000, description="Углеводы")
    date: datetime = Field(default_factory=datetime.now, description="Дата приема пищи")
    notes: Optional[str] = Field(None, max_length=500, description="Заметки")
    
    @validator('meal_type')
    def validate_meal_type(cls, v):
        """Валидация типа приема пищи"""
        allowed_types = ["завтрак", "обед", "ужин", "перекус", "десерт"]
        if v.lower() not in allowed_types:
            raise ValueError(f"Недопустимый тип приема пищи. Разрешены: {', '.join(allowed_types)}")
        return v.lower()
    
    @model_validator(mode='after')
    def validate_recipe_or_custom_food(self):
        """Проверка наличия рецепта или собственной еды"""
        recipe_id = self.recipe_id
        custom_food = self.custom_food
        
        if not recipe_id and not custom_food:
            raise ValueError("Необходимо указать либо ID рецепта, либо собственную еду")
        
        if recipe_id and custom_food:
            raise ValueError("Нельзя указывать одновременно ID рецепта и собственную еду")
        
        return self

# ============================================================================
# СХЕМЫ ДЛЯ ПРОДУКТОВ
# ============================================================================

class ProductNutrientsDTO(BaseModel):
    """DTO для питательных веществ продукта"""
    calories: float = Field(ge=0, le=10000, description="Калории (ккал)")
    protein: float = Field(ge=0, le=1000, description="Белки (г)")
    fat: float = Field(ge=0, le=1000, description="Жиры (г)")
    carbs: float = Field(ge=0, le=1000, description="Углеводы (г)")
    fiber: Optional[float] = Field(0, ge=0, le=100, description="Клетчатка (г)")
    sugar: Optional[float] = Field(0, ge=0, le=100, description="Сахар (г)")
    sodium: Optional[float] = Field(0, ge=0, le=10000, description="Натрий (мг)")
    cholesterol: Optional[float] = Field(0, ge=0, le=1000, description="Холестерин (мг)")

class ProductDTO(BaseModel):
    """DTO для продукта"""
    name: str = Field(..., description="Название продукта")
    nutrients: ProductNutrientsDTO = Field(..., description="Питательные вещества")
    unit: str = Field("г", description="Единица измерения")
    description: Optional[str] = Field(None, max_length=500, description="Описание")
    emoji: Optional[str] = Field(None, max_length=10, description="Эмодзи")
    
    @validator('name')
    def validate_name(cls, v):
        """Валидация названия продукта"""
        if not v.strip():
            raise ValueError("Название продукта не может быть пустым")
        return v.strip()
    
    @validator('unit')
    def validate_unit(cls, v):
        """Валидация единицы измерения"""
        allowed_units = ["г", "кг", "мл", "л", "шт"]
        if v not in allowed_units:
            raise ValueError(f"Недопустимая единица измерения. Разрешены: {', '.join(allowed_units)}")
        return v

class ProductSearchDTO(BaseModel):
    """DTO для поиска продуктов"""
    query: str = Field(..., min_length=1, max_length=100, description="Поисковый запрос")
    
    @validator('query')
    def validate_query(cls, v):
        """Валидация поискового запроса"""
        if not v.strip():
            raise ValueError("Поисковый запрос не может быть пустым")
        return v.strip()

class ProductCalculatorDTO(BaseModel):
    """DTO для калькулятора продуктов"""
    amount: float = Field(..., gt=0, le=10000, description="Количество в граммах")
    
    @validator('amount')
    def validate_amount(cls, v):
        """Валидация количества"""
        if v <= 0:
            raise ValueError("Количество должно быть больше нуля")
        if v > 10000:
            raise ValueError("Количество не может превышать 10000 грамм")
        return v

# ============================================================================
# СХЕМЫ ДЛЯ НУТРИЕНТОВ
# ============================================================================

class NutrientSearchDTO(BaseModel):
    """DTO для поиска нутриентов"""
    query: str = Field(..., min_length=1, max_length=100, description="Поисковый запрос")
    
    @validator('query')
    def validate_query(cls, v):
        """Валидация поискового запроса"""
        if not v.strip():
            raise ValueError("Поисковый запрос не может быть пустым")
        return v.strip()

class NutrientCalculatorDTO(BaseModel):
    """DTO для калькулятора нутриентов"""
    amount: float = Field(..., gt=0, le=10000, description="Количество в граммах")
    
    @validator('amount')
    def validate_amount(cls, v):
        """Валидация количества"""
        if v <= 0:
            raise ValueError("Количество должно быть больше нуля")
        if v > 10000:
            raise ValueError("Количество не может превышать 10000 грамм")
        return v

# ============================================================================
# СХЕМЫ ДЛЯ ПОИСКА И ФИЛЬТРАЦИИ
# ============================================================================

class SearchQueryDTO(BaseModel):
    """DTO для поискового запроса"""
    query: str = Field(..., min_length=1, max_length=100, description="Поисковый запрос")
    search_type: str = Field("recipe", description="Тип поиска")
    fuzzy: bool = Field(True, description="Нечеткий поиск")
    
    @validator('search_type')
    def validate_search_type(cls, v):
        """Валидация типа поиска"""
        allowed_types = ["recipe", "ingredient", "user"]
        if v not in allowed_types:
            raise ValueError(f"Недопустимый тип поиска. Разрешены: {', '.join(allowed_types)}")
        return v

class FilterDTO(BaseModel):
    """DTO для фильтров"""
    categories: Optional[List[str]] = Field(None, description="Категории")
    difficulty_levels: Optional[List[str]] = Field(None, description="Уровни сложности")
    cooking_time_range: Optional[Dict[str, int]] = Field(None, description="Диапазон времени приготовления")
    calories_range: Optional[Dict[str, float]] = Field(None, description="Диапазон калорий")
    tags: Optional[List[str]] = Field(None, description="Теги")
    
    @validator('cooking_time_range')
    def validate_cooking_time_range(cls, v):
        """Валидация диапазона времени приготовления"""
        if v:
            if 'min' in v and (v['min'] < 0 or v['min'] > 1440):
                raise ValueError("Минимальное время приготовления должно быть от 0 до 1440 минут")
            if 'max' in v and (v['max'] < 0 or v['max'] > 1440):
                raise ValueError("Максимальное время приготовления должно быть от 0 до 1440 минут")
            if 'min' in v and 'max' in v and v['min'] > v['max']:
                raise ValueError("Минимальное время не может быть больше максимального")
        return v
    
    @validator('calories_range')
    def validate_calories_range(cls, v):
        """Валидация диапазона калорий"""
        if v:
            if 'min' in v and (v['min'] < 0 or v['min'] > 10000):
                raise ValueError("Минимальная калорийность должна быть от 0 до 10000")
            if 'max' in v and (v['max'] < 0 or v['max'] > 10000):
                raise ValueError("Максимальная калорийность должна быть от 0 до 10000")
            if 'min' in v and 'max' in v and v['min'] > v['max']:
                raise ValueError("Минимальная калорийность не может быть больше максимальной")
        return v

# ============================================================================
# СХЕМЫ ДЛЯ ОТВЕТОВ
# ============================================================================

class RecipeResponse(BaseResponse):
    """Ответ с рецептом"""
    data: Optional[RecipeDTO] = Field(None, description="Данные рецепта")

class RecipeListResponse(BaseResponse):
    """Ответ со списком рецептов"""
    data: Optional[List[RecipeDTO]] = Field(None, description="Список рецептов")
    pagination: Optional[Dict[str, Any]] = Field(None, description="Информация о пагинации")

class UserProfileResponse(BaseResponse):
    """Ответ с профилем пользователя"""
    data: Optional[UserProfileDTO] = Field(None, description="Данные профиля")

class UserMealResponse(BaseResponse):
    """Ответ с приемом пищи"""
    data: Optional[UserMealDTO] = Field(None, description="Данные приема пищи")

# ============================================================================
# УТИЛИТЫ ДЛЯ ВАЛИДАЦИИ
# ============================================================================

def validate_and_format_errors(validation_error) -> Dict[str, str]:
    """
    Форматирование ошибок валидации Pydantic в стандартный формат
    
    Args:
        validation_error: Объект ошибки валидации Pydantic
        
    Returns:
        Dict[str, str]: Словарь с ошибками по полям
    """
    errors = {}
    for error in validation_error.errors():
        field = '.'.join(str(loc) for loc in error['loc'])
        message = error['msg']
        errors[field] = message
        logger.warning(f"Ошибка валидации поля '{field}': {message}")
    return errors

def create_error_response(validation_error, user_message: str = "Ошибка валидации данных") -> ValidationErrorResponse:
    """
    Создание стандартизированного ответа с ошибками валидации
    
    Args:
        validation_error: Объект ошибки валидации Pydantic
        user_message: Сообщение для пользователя
        
    Returns:
        ValidationErrorResponse: Ответ с ошибками
    """
    errors = validate_and_format_errors(validation_error)
    return ValidationErrorResponse(
        success=False,
        message=user_message,
        data=None,
        errors=errors
    ) 