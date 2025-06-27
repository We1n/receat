from typing import Any, Optional, Dict
import json
import time
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)

class Cache:
    """Класс для кэширования данных"""
    
    def __init__(self, ttl: int = 300):  # TTL по умолчанию 5 минут
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
        
    def set(self, key: str, value: Any) -> None:
        """Установить значение в кэш"""
        self._cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
        logger.debug(f"Cache set for key: {key}")
        
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        if key in self._cache:
            item = self._cache[key]
            if time.time() - item['timestamp'] < self.ttl:
                logger.debug(f"Cache hit for key: {key}")
                return item['value']
            else:
                logger.debug(f"Cache expired for key: {key}")
                del self._cache[key]
        return None
            
    def delete(self, key: str) -> None:
        """Удалить значение из кэша"""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted for key: {key}")
            
    def clear(self) -> None:
        """Очистить весь кэш"""
        self._cache.clear()
        logger.debug("Cache cleared")
            
    def get_all(self) -> Dict[str, Any]:
        """
        Получение всех значений из кэша
        
        Returns:
            Словарь с ключами и значениями
        """
        try:
            return {k: v['value'] for k, v in self._cache.items() 
                   if time.time() - v['timestamp'] < self.ttl}
        except Exception as e:
            logger.error(f"Ошибка при получении всех значений из кэша: {e}")
            return {}
            
    def exists(self, key: str) -> bool:
        """
        Проверка существования ключа в кэше
        
        Args:
            key: Ключ
            
        Returns:
            True, если ключ существует и не истек срок действия
        """
        return key in self._cache and time.time() - self._cache[key]['timestamp'] < self.ttl
            
    def ttl(self, key: str) -> Optional[int]:
        """
        Получение оставшегося времени жизни ключа
        
        Args:
            key: Ключ
            
        Returns:
            Оставшееся время в секундах или None, если ключ не существует
        """
        if key in self._cache:
            return self.ttl - (time.time() - self._cache[key]['timestamp'])
        return None

def cache(ttl: int = 300):
    """
    Декоратор для кэширования результатов функций
    
    Args:
        ttl: Время жизни кэша в секундах (по умолчанию 5 минут)
    """
    cache_instance = Cache(ttl)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Создаем ключ кэша из имени функции и аргументов
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Пробуем получить значение из кэша
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Если значения нет в кэше, выполняем функцию
            result = await func(*args, **kwargs)
            
            # Сохраняем результат в кэш
            cache_instance.set(cache_key, result)
            
            return result
        return wrapper
    return decorator 