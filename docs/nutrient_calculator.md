# 🧮 Калькулятор нутриентов

## 📝 Описание

Калькулятор нутриентов - это инструмент для расчета и анализа питательной ценности продуктов с учетом различных факторов:

- Уровень активности
- Цели (похудение/поддержание/набор массы)
- Тип диеты
- Количество продукта

## 🎯 Возможности

- Расчет калорий и макронутриентов
- Учет уровня активности
- Учет целей пользователя
- Учет типа диеты
- Рекомендации по питанию
- История потребления
- Статистика и аналитика

## 🔧 Технические детали

### Модели данных

#### NutrientCalculation

```python
@dataclass
class NutrientCalculation:
    calories: float
    proteins: float
    fats: float
    carbs: float
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None
    timestamp: datetime = datetime.now()
```

#### NutrientRecommendation

```python
@dataclass
class NutrientRecommendation:
    message: str
    priority: int = 0
    category: str = "general"
```

#### NutrientGoal

```python
@dataclass
class NutrientGoal:
    calories: float
    proteins: float
    fats: float
    carbs: float
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None
    activity_level: str = "moderate"
    goal_type: str = "maintenance"
    diet_type: str = "regular"
    timestamp: datetime = datetime.now()
```

### Константы

#### Множители активности

```python
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9
}
```

#### Множители целей

```python
GOAL_MULTIPLIERS = {
    "weight_loss": 0.85,
    "maintenance": 1.0,
    "muscle_gain": 1.15
}
```

#### Соотношения макронутриентов по типам диет

```python
DIET_MACRO_RATIOS = {
    "keto": {"proteins": 0.25, "fats": 0.70, "carbs": 0.05},
    "paleo": {"proteins": 0.30, "fats": 0.40, "carbs": 0.30},
    "vegan": {"proteins": 0.20, "fats": 0.30, "carbs": 0.50},
    "vegetarian": {"proteins": 0.25, "fats": 0.35, "carbs": 0.40},
    "regular": {"proteins": 0.30, "fats": 0.30, "carbs": 0.40}
}
```

## 📊 База данных

### Таблицы

#### nutrient_products

```sql
CREATE TABLE nutrient_products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    calories FLOAT NOT NULL,
    proteins FLOAT NOT NULL,
    fats FLOAT NOT NULL,
    carbs FLOAT NOT NULL,
    fiber FLOAT,
    sugar FLOAT,
    sodium FLOAT,
    category VARCHAR(50) DEFAULT 'other',
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### nutrient_goals

```sql
CREATE TABLE nutrient_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    calories FLOAT NOT NULL,
    proteins FLOAT NOT NULL,
    fats FLOAT NOT NULL,
    carbs FLOAT NOT NULL,
    fiber FLOAT,
    sugar FLOAT,
    sodium FLOAT,
    activity_level VARCHAR(50) DEFAULT 'moderate',
    goal_type VARCHAR(50) DEFAULT 'maintenance',
    diet_type VARCHAR(50) DEFAULT 'regular',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### nutrient_intakes

```sql
CREATE TABLE nutrient_intakes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    product_id INTEGER NOT NULL REFERENCES nutrient_products(id),
    quantity FLOAT NOT NULL,
    calories FLOAT NOT NULL,
    proteins FLOAT NOT NULL,
    fats FLOAT NOT NULL,
    carbs FLOAT NOT NULL,
    fiber FLOAT,
    sugar FLOAT,
    sodium FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Индексы

```sql
CREATE INDEX idx_nutrient_products_name ON nutrient_products(name);
CREATE INDEX idx_nutrient_products_category ON nutrient_products(category);
CREATE INDEX idx_nutrient_goals_user_id ON nutrient_goals(user_id);
CREATE INDEX idx_nutrient_intakes_user_id ON nutrient_intakes(user_id);
CREATE INDEX idx_nutrient_intakes_product_id ON nutrient_intakes(product_id);
CREATE INDEX idx_nutrient_intakes_timestamp ON nutrient_intakes(timestamp);
```

## 🧪 Тестирование

### Тесты

#### test_calculate_nutrients

```python
@pytest.mark.asyncio
async def test_calculate_nutrients(calculator, sample_product):
    result = await calculator.calculate_nutrients(
        user_id=1,
        product_id=1,
        quantity=200,
        activity_level="moderate",
        goal="maintenance",
        diet_type="regular"
    )
    
    assert isinstance(result, NutrientCalculation)
    assert result.calories == 310
    assert result.proteins == 31
    assert result.fats == 15.5
    assert result.carbs == 46.5
```

#### test_get_recommendations

```python
@pytest.mark.asyncio
async def test_get_recommendations(calculator):
    calculation = NutrientCalculation(
        calories=2000,
        proteins=50,
        fats=30,
        carbs=250,
        fiber=20,
        sugar=60,
        sodium=2400
    )
    
    recommendations = await calculator.get_recommendations(calculation)
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert all(isinstance(r, NutrientRecommendation) for r in recommendations)
```

## 📈 Использование

### Пример расчета нутриентов

```python
# Создаем калькулятор
calculator = NutrientCalculatorService(db_manager)

# Рассчитываем нутриенты
result = await calculator.calculate_nutrients(
    user_id=1,
    product_id=1,
    quantity=200,
    activity_level="moderate",
    goal="maintenance",
    diet_type="regular"
)

# Получаем рекомендации
recommendations = await calculator.get_recommendations(result)

# Выводим результат
print(f"Калории: {result.calories:.1f} ккал")
print(f"Белки: {result.proteins:.1f} г")
print(f"Жиры: {result.fats:.1f} г")
print(f"Углеводы: {result.carbs:.1f} г")

for rec in recommendations:
    print(f"• {rec.message}")
```

## 🔍 Рекомендации

### Макронутриенты

- Белки: 20-40% от общего количества калорий
- Жиры: 20-40% от общего количества калорий
- Углеводы: 30-60% от общего количества калорий

### Микронутриенты

- Клетчатка: минимум 25 г в день
- Сахар: максимум 50 г в день
- Натрий: максимум 2300 мг в день

## 📚 Дополнительная информация

### Типы диет

- Кето: высокое содержание жиров, низкое содержание углеводов
- Палео: натуральные продукты, без обработанной пищи
- Веган: только растительная пища
- Вегетарианский: растительная пища + молочные продукты и яйца
- Обычная: сбалансированное питание

### Уровни активности

- Малоподвижный: сидячий образ жизни
- Легкая: легкие упражнения 1-3 раза в неделю
- Умеренная: умеренные упражнения 3-5 раз в неделю
- Активная: интенсивные упражнения 6-7 раз в неделю
- Очень активная: очень интенсивные упражнения каждый день

### Цели

- Похудение: дефицит калорий
- Поддержание: баланс калорий
- Набор массы: профицит калорий 