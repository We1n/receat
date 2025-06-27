# 🛡️ Руководство по системе валидации EatBot

## 📋 Обзор

Новая система валидации EatBot основана на **Pydantic** и предоставляет унифицированный интерфейс для валидации всех входящих данных пользователя. Система обеспечивает:

- ✅ **Типизированную валидацию** всех входящих данных
- ✅ **Централизованную обработку ошибок** 
- ✅ **Стандартизированные сообщения** об ошибках
- ✅ **Легкое масштабирование** и добавление новых форм
- ✅ **Улучшенную надежность** системы

## 🏗️ Архитектура

### Основные компоненты

```
src/validators/
├── schemas.py          # Схемы DTO на основе Pydantic
├── input_handler.py    # Унифицированный обработчик ввода
└── __pycache__/
```

### Схемы данных (DTO)

Все схемы определены в `src/validators/schemas.py`:

- **RecipeDTO** - валидация рецептов
- **UserProfileDTO** - валидация профилей пользователей  
- **UserMealDTO** - валидация приемов пищи
- **CategoryDTO** - валидация категорий
- **ProductDTO** - валидация продуктов
- **SearchQueryDTO** - валидация поисковых запросов
- **FilterDTO** - валидация фильтров

### Унифицированный обработчик

`InputHandler` в `src/validators/input_handler.py` предоставляет:

- Валидацию данных по схемам
- Обработку ошибок валидации
- Парсинг callback данных
- Санитизацию текста
- Декораторы для автоматической валидации

## 🚀 Быстрый старт

### 1. Валидация простых данных

```python
from src.validators.input_handler import InputHandler

# Создание обработчика
input_handler = InputHandler()

# Валидация данных
validation_result = input_handler.validate_input(
    data={"name": "Борщ", "category": "Супы"},
    schema_name="RecipeDTO",
    user_message="Ошибка валидации рецепта"
)

# Проверка результата
if isinstance(validation_result, ValidationErrorResponse):
    # Ошибка валидации
    errors = validation_result.errors
    print(f"Ошибки: {errors}")
else:
    # Успешная валидация
    validated_data = validation_result
    print(f"Данные валидны: {validated_data}")
```

### 2. Использование декоратора

```python
from src.validators.input_handler import validate_input_decorator

@validate_input_decorator("RecipeDTO", "Ошибка валидации рецепта")
async def add_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Данные уже валидированы
    validated_data = context.user_data.get('validated_data')
    # ... обработка данных
```

### 3. Валидация в обработчиках

```python
from src.validators.input_handler import InputHandler

class RecipeHandler:
    def __init__(self):
        self.input_handler = InputHandler()
    
    async def handle_recipe_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Извлечение данных пользователя
        user_data = self.input_handler.extract_user_data(update)
        
        # Валидация
        validation_result = self.input_handler.validate_input(
            data=user_data,
            schema_name="RecipeDTO",
            user_message="Ошибка валидации рецепта"
        )
        
        if isinstance(validation_result, ValidationErrorResponse):
            await self.handle_validation_error(update, validation_result)
            return
        
        # Обработка валидных данных
        await self.process_recipe(update, validation_result)
```

## 📝 Создание новых схем

### 1. Определение схемы

```python
from pydantic import BaseModel, Field, validator

class NewEntityDTO(BaseModel):
    """DTO для новой сущности"""
    name: str = Field(..., min_length=1, max_length=100, description="Название")
    description: Optional[str] = Field(None, max_length=500, description="Описание")
    active: bool = Field(True, description="Активность")
    
    @validator('name')
    def validate_name(cls, v):
        """Валидация названия"""
        if not v.strip():
            raise ValueError("Название не может быть пустым")
        return v.strip()
```

### 2. Добавление в InputHandler

```python
# В src/validators/input_handler.py
def __init__(self):
    self.validators = {
        # ... существующие схемы
        "NewEntityDTO": NewEntityDTO,
    }
```

### 3. Создание парсера (если нужно)

```python
def parse_new_entity_input(self, text: str) -> Dict[str, Any]:
    """Парсинг ввода новой сущности"""
    try:
        # Логика парсинга
        return {
            "name": text.strip(),
            "description": None,
            "active": True
        }
    except Exception as e:
        logger.error(f"Ошибка парсинга: {e}")
        return {}
```

## 🔧 Обработка ошибок

### Стандартные ошибки валидации

```python
# Получение ошибок
if isinstance(validation_result, ValidationErrorResponse):
    errors = validation_result.errors
    message = validation_result.message
    
    # Форматирование для пользователя
    error_text = "❌ Ошибки валидации:\n\n"
    for field, error in errors.items():
        error_text += f"• {field}: {error}\n"
```

### Пользовательские сообщения об ошибках

```python
# Создание кастомного сообщения
validation_result = input_handler.validate_input(
    data=data,
    schema_name="RecipeDTO",
    user_message="Пожалуйста, проверьте данные рецепта"
)
```

## 🧪 Тестирование

### Тестирование схем

```python
import pytest
from src.validators.schemas import RecipeDTO

def test_recipe_validation():
    # Валидные данные
    valid_data = {
        "name": "Борщ",
        "category": "Супы",
        "ingredients": [{"name": "Свекла", "amount": 1, "unit": "шт"}],
        "instructions": "Варить 30 минут",
        "nutrients": {"calories": 150, "proteins": 5, "fats": 3, "carbs": 20},
        "cooking_time": 30,
        "difficulty": "средний",
        "portions": 4
    }
    
    recipe = RecipeDTO(**valid_data)
    assert recipe.name == "Борщ"
    assert recipe.cooking_time == 30

def test_recipe_validation_error():
    # Невалидные данные
    invalid_data = {
        "name": "",  # Пустое название
        "cooking_time": -1  # Отрицательное время
    }
    
    with pytest.raises(ValidationError):
        RecipeDTO(**invalid_data)
```

### Тестирование InputHandler

```python
from src.validators.input_handler import InputHandler

def test_input_handler():
    handler = InputHandler()
    
    # Тест валидации
    result = handler.validate_input(
        data={"name": "Тест"},
        schema_name="CategoryDTO",
        user_message="Ошибка"
    )
    
    assert not isinstance(result, ValidationErrorResponse)
    assert result.name == "Тест"
```

## 📊 Мониторинг и логирование

### Логирование валидации

```python
import logging

logger = logging.getLogger(__name__)

# В InputHandler автоматически логируются:
# - Успешные валидации
# - Ошибки валидации  
# - Неожиданные ошибки
```

### Метрики

```python
# Отслеживание ошибок валидации
validation_errors = {
    "RecipeDTO": 0,
    "UserProfileDTO": 0,
    "CategoryDTO": 0
}

# Увеличение счетчика при ошибке
if isinstance(validation_result, ValidationErrorResponse):
    validation_errors[schema_name] += 1
```

## 🔄 Миграция с старой системы

### Что изменилось

1. **Старая система**: `src/validators/validators.py` (удалена)
2. **Новая система**: `src/validators/schemas.py` + `src/validators/input_handler.py`

### Шаги миграции

1. **Заменить импорты**:
   ```python
   # Старый импорт
   from src.validators.validators import RecipeValidator
   
   # Новый импорт
   from src.validators.input_handler import InputHandler
   ```

2. **Заменить валидацию**:
   ```python
   # Старый код
   validator = RecipeValidator()
   is_valid, errors = validator.validate_recipe(data)
   
   # Новый код
   handler = InputHandler()
   result = handler.validate_input(data, "RecipeDTO")
   ```

3. **Обновить обработку ошибок**:
   ```python
   # Старый код
   if not is_valid:
       for error in errors:
           print(error.message)
   
   # Новый код
   if isinstance(result, ValidationErrorResponse):
       for field, error in result.errors.items():
           print(f"{field}: {error}")
   ```

## 🎯 Лучшие практики

### 1. Используйте декораторы

```python
@validate_input_decorator("RecipeDTO", "Ошибка валидации рецепта")
async def add_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Код обработчика
```

### 2. Создавайте специфичные сообщения об ошибках

```python
validation_result = input_handler.validate_input(
    data=data,
    schema_name="RecipeDTO", 
    user_message="Пожалуйста, проверьте данные рецепта и попробуйте снова"
)
```

### 3. Логируйте ошибки валидации

```python
if isinstance(validation_result, ValidationErrorResponse):
    logger.warning(f"Ошибка валидации: {validation_result.errors}")
```

### 4. Используйте типизацию

```python
from typing import Union
from src.validators.schemas import ValidationErrorResponse

def process_data(data: Dict[str, Any]) -> Union[RecipeDTO, ValidationErrorResponse]:
    # Код обработки
```

## 🚨 Частые ошибки

### 1. Неправильная проверка результата

```python
# ❌ Неправильно
if not validation_result.is_valid:
    # ...

# ✅ Правильно  
if isinstance(validation_result, ValidationErrorResponse):
    # ...
```

### 2. Забывание обработки ошибок

```python
# ❌ Неправильно
result = input_handler.validate_input(data, "RecipeDTO")
process_data(result)  # Может упасть

# ✅ Правильно
result = input_handler.validate_input(data, "RecipeDTO")
if isinstance(result, ValidationErrorResponse):
    await handle_error(update, result)
    return
process_data(result)
```

### 3. Неправильные схемы

```python
# ❌ Неправильно - нет валидаторов
class BadDTO(BaseModel):
    name: str

# ✅ Правильно - с валидаторами
class GoodDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Название не может быть пустым")
        return v.strip()
```

## 📚 Дополнительные ресурсы

- [Pydantic документация](https://pydantic-docs.helpmanual.io/)
- [Примеры схем в проекте](src/validators/schemas.py)
- [Примеры использования](src/ui/handlers/)
- [Тесты валидации](tests/)

---

**Система валидации готова к использованию! 🎉**

Для вопросов и поддержки обращайтесь к команде разработки. 