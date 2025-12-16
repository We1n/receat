"""
Модуль для расширенной работы с кэшем
"""

from typing import Any, Optional, Union, Dict, List, Callable
import logging
from datetime import datetime, timedelta
import json
import pickle
from functools import wraps
import hashlib
from .redis_cache import RedisCache

logger = logging.getLogger(__name__)

class EnhancedCache:
    """Расширенный класс для работы с кэшем"""
    
    def __init__(self, redis_cache: RedisCache):
        """
        Инициализация расширенного кэша
        
        Args:
            redis_cache: Экземпляр RedisCache
        """
        self.cache = redis_cache
        self.logger = logger.getChild('EnhancedCache')
        
        # Статистика использования кэша
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0
        }
    
    def cached(self, ttl: Optional[int] = None, key_prefix: str = '', 
               key_builder: Optional[Callable] = None) -> Callable:
        """
        Декоратор для кэширования результатов функций
        
        Args:
            ttl: Время жизни кэша в секундах
            key_prefix: Префикс для ключа кэша
            key_builder: Функция для построения ключа кэша
            
        Returns:
            Callable: Декорированная функция
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Строим ключ кэша
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    # Создаем хеш из аргументов функции
                    key_parts = [str(arg) for arg in args]
                    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                    key_str = "|".join(key_parts)
                    cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(key_str.encode()).hexdigest()}"
                
                # Пробуем получить значение из кэша
                cached_value = self.cache.get(cache_key)
                if cached_value is not None:
                    self.stats['hits'] += 1
                    return cached_value
                
                self.stats['misses'] += 1
                
                # Выполняем функцию и кэшируем результат
                try:
                    result = await func(*args, **kwargs)
                    self.cache.set(cache_key, result, ttl)
                    return result
                except Exception as e:
                    self.stats['errors'] += 1
                    self.logger.error(f"Ошибка при кэшировании результата функции {func.__name__}: {e}")
                    raise
            
            return wrapper
        return decorator
    
    def invalidate_pattern(self, pattern: str) -> bool:
        """
        Инвалидирует все ключи, соответствующие паттерну
        
        Args:
            pattern: Паттерн для поиска ключей
            
        Returns:
            bool: True если успешно, False в случае ошибки
        """
        try:
            keys = self.cache.redis.keys(pattern)
            if keys:
                return self.cache.delete_many(keys)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при инвалидации кэша по паттерну {pattern}: {e}")
            return False
    
    def get_or_set(self, key: str, default_func: Callable, ttl: Optional[int] = None) -> Any:
        """
        Получает значение из кэша или устанавливает новое
        
        Args:
            key: Ключ кэша
            default_func: Функция для получения значения по умолчанию
            ttl: Время жизни в секундах
            
        Returns:
            Any: Значение из кэша или результат default_func
        """
        value = self.cache.get(key)
        if value is not None:
            self.stats['hits'] += 1
            return value
        
        self.stats['misses'] += 1
        value = default_func()
        self.cache.set(key, value, ttl)
        return value
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получает статистику использования кэша
        
        Returns:
            Dict[str, Any]: Статистика использования кэша
        """
        try:
            info = self.cache.redis.info()
            return {
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'errors': self.stats['errors'],
                'hit_rate': self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0,
                'memory_used': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'uptime_days': info.get('uptime_in_days', 0)
            }
        except Exception as e:
            self.logger.error(f"Ошибка при получении статистики кэша: {e}")
            return {}
    
    def reset_stats(self) -> None:
        """Сбрасывает статистику использования кэша"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0
        }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Получает информацию об использовании памяти
        
        Returns:
            Dict[str, Any]: Информация об использовании памяти
        """
        try:
            info = self.cache.redis.info()
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_lua': info.get('used_memory_lua', 0),
                'used_memory_scripts': info.get('used_memory_scripts', 0),
                'used_memory_rss': info.get('used_memory_rss', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', 'N/A'),
                'used_memory_human': info.get('used_memory_human', 'N/A')
            }
        except Exception as e:
            self.logger.error(f"Ошибка при получении информации об использовании памяти: {e}")
            return {} 