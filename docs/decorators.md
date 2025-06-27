# 🎭 Декораторы

## 📋 Описание

Модуль содержит декораторы для логирования действий пользователей.

## 🎯 Функциональность

- Логирование действий
- Сбор метрик
- Обработка ошибок
- Сохранение логов в файл

## 🛠️ Классы

### LogContext

```python
class LogContext:
    def __init__(self, action_name: str, user_id: int)
```

Класс для хранения контекста логирования.

**Параметры:**

- `action_name`: Название действия
- `user_id`: ID пользователя

**Атрибуты:**

- `action_name`: Название действия
- `user_id`: ID пользователя
- `start_time`: Время начала действия
- `end_time`: Время окончания действия
- `duration`: Длительность действия
- `success`: Успешность выполнения
- `error`: Сообщение об ошибке
- `context`: Дополнительный контекст

**Методы:**

- `to_dict()`: Преобразует контекст в словарь
- `to_json()`: Преобразует контекст в JSON

## 🛠️ Декораторы

### log_action

```python
def log_action(
    action_name: str,
    log_file: Optional[str] = None,
    collect_metrics: bool = False,
    context: Optional[Dict] = None
)
```

Декоратор для логирования действий.

**Параметры:**

- `action_name`: Название действия
- `log_file`: Путь к файлу для сохранения логов
- `collect_metrics`: Собирать ли метрики
- `context`: Дополнительный контекст

**Возвращает:**

- Декоратор для функции

## 📝 Примеры использования

### Базовое логирование

```python
@log_action("check_price")
async def check_price(user_id: int, product: str):
    return await price_service.get_price(product)
```

### Логирование с метриками

```python
@log_action("check_price", collect_metrics=True)
async def check_price(user_id: int, product: str):
    return await price_service.get_price(product)
```

### Логирование в файл

```python
@log_action("check_price", log_file="prices.log")
async def check_price(user_id: int, product: str):
    return await price_service.get_price(product)
```

### Логирование с контекстом

```python
@log_action("check_price", context={"product": "молоко"})
async def check_price(user_id: int, product: str):
    return await price_service.get_price(product)
```

## 🔍 Обработка ошибок

- Логирование ошибок
- Сохранение стека вызовов
- Информация о параметрах
- Время выполнения

## 📊 Метрики

- Время выполнения
- Количество вызовов
- Количество ошибок
- Параметры вызовов
- Результаты выполнения

## 🔒 Безопасность

- Валидация входных данных
- Безопасное сохранение логов
- Защита от инъекций
- Шифрование чувствительных данных

## ⚡ Производительность

- Асинхронное логирование
- Буферизация логов
- Оптимизация записи
- Эффективное хранение

## 📈 Мониторинг

- Логирование действий
- Отслеживание ошибок
- Сбор метрик
- Анализ использования

## 🧪 Тесты

- Модульные тесты
- Интеграционные тесты
- Тесты производительности
- Тесты безопасности
