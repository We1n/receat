"""
Модуль для валидации данных

Этот модуль предоставляет функции для:
- Валидации ID пользователя
- Валидации дат
- Валидации входных данных
"""

import re
from datetime import datetime
from typing import Union, Optional, Any, Dict, List
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

def validate_user_id(user_id: Union[int, str]) -> bool:
    """
    Валидация ID пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        bool: True если ID валиден, False в противном случае
    """
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
        return user_id > 0
    except (ValueError, TypeError):
        logger.error(f"Невалидный ID пользователя: {user_id}")
        return False

def validate_date(date_str: str, format: str = "%Y-%m-%d") -> bool:
    """
    Валидация даты
    
    Args:
        date_str: Строка с датой
        format: Формат даты
        
    Returns:
        bool: True если дата валидна, False в противном случае
    """
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        logger.error(f"Невалидная дата: {date_str}")
        return False

def validate_phone(phone: str) -> bool:
    """
    Валидация номера телефона
    
    Args:
        phone: Номер телефона
        
    Returns:
        bool: True если номер валиден, False в противном случае
    """
    pattern = r'^\+?[1-9]\d{10,14}$'
    return bool(re.match(pattern, phone))

def validate_email(email: str) -> bool:
    """
    Валидация email
    
    Args:
        email: Email адрес
        
    Returns:
        bool: True если email валиден, False в противном случае
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_weight(weight: Union[int, float]) -> bool:
    """
    Валидация веса
    
    Args:
        weight: Вес в кг
        
    Returns:
        bool: True если вес валиден, False в противном случае
    """
    try:
        weight = float(weight)
        return 20 <= weight <= 300
    except (ValueError, TypeError):
        logger.error(f"Невалидный вес: {weight}")
        return False

def validate_height(height: Union[int, float]) -> bool:
    """
    Валидация роста
    
    Args:
        height: Рост в см
        
    Returns:
        bool: True если рост валиден, False в противном случае
    """
    try:
        height = float(height)
        return 100 <= height <= 250
    except (ValueError, TypeError):
        logger.error(f"Невалидный рост: {height}")
        return False

def validate_age(age: Union[int, str]) -> bool:
    """
    Валидация возраста
    
    Args:
        age: Возраст
        
    Returns:
        bool: True если возраст валиден, False в противном случае
    """
    try:
        age = int(age)
        return 12 <= age <= 120
    except (ValueError, TypeError):
        logger.error(f"Невалидный возраст: {age}")
        return False

def validate_gender(gender: str) -> bool:
    """
    Валидация пола
    
    Args:
        gender: Пол ('male' или 'female')
        
    Returns:
        bool: True если пол валиден, False в противном случае
    """
    return gender.lower() in ['male', 'female']

def validate_activity_level(level: str) -> bool:
    """
    Валидация уровня активности
    
    Args:
        level: Уровень активности
        
    Returns:
        bool: True если уровень валиден, False в противном случае
    """
    valid_levels = ['sedentary', 'light', 'moderate', 'active', 'very_active']
    return level.lower() in valid_levels

def validate_time(time_obj) -> bool:
    """
    Валидация объекта времени
    
    Args:
        time_obj: Объект времени для валидации
        
    Returns:
        bool: True если время корректно, False иначе
    """
    try:
        if not hasattr(time_obj, 'hour') or not hasattr(time_obj, 'minute'):
            return False
        
        if not (0 <= time_obj.hour <= 23 and 0 <= time_obj.minute <= 59):
            return False
        
        return True
    except Exception:
        return False

class Validators:
    """Класс с валидаторами входных данных"""
    
    @staticmethod
    def validate_recipe_name(name: str) -> bool:
        """
        Валидация названия рецепта
        
        Args:
            name: Название рецепта
            
        Returns:
            bool: True если название валидно, False иначе
        """
        if not name or len(name) < 3 or len(name) > 100:
            return False
        return True
    
    @staticmethod
    def validate_ingredient(ingredient: Dict[str, Any]) -> bool:
        """
        Валидация ингредиента
        
        Args:
            ingredient: Словарь с данными ингредиента
            
        Returns:
            bool: True если ингредиент валиден, False иначе
        """
        required_fields = ['name', 'amount', 'unit']
        if not all(field in ingredient for field in required_fields):
            return False
        if not ingredient['name'] or len(ingredient['name']) < 2:
            return False
        if not isinstance(ingredient['amount'], (int, float)) or ingredient['amount'] <= 0:
            return False
        if not ingredient['unit'] or len(ingredient['unit']) < 1:
            return False
        return True
    
    @staticmethod
    def validate_user_input(text: str, min_length: int = 1, max_length: int = 1000) -> bool:
        """
        Валидация пользовательского ввода
        
        Args:
            text: Текст пользователя
            min_length: Минимальная длина
            max_length: Максимальная длина
            
        Returns:
            bool: True если текст валиден, False иначе
        """
        if not text or not isinstance(text, str):
            return False
        if len(text) < min_length or len(text) > max_length:
            return False
        return True
    
    @staticmethod
    def validate_callback_data(data: str, pattern: str) -> bool:
        """
        Валидация callback данных
        
        Args:
            data: Данные callback
            pattern: Регулярное выражение для проверки
            
        Returns:
            bool: True если данные валидны, False иначе
        """
        if not data or not isinstance(data, str):
            return False
        return bool(re.match(pattern, data))
    
    @staticmethod
    def validate_recipe_id(recipe_id: int) -> bool:
        """
        Валидация ID рецепта
        
        Args:
            recipe_id: ID рецепта
            
        Returns:
            bool: True если ID валиден, False иначе
        """
        if not recipe_id or not isinstance(recipe_id, int) or recipe_id <= 0:
            return False
        return True 