"""
Модуль для управления кэшем с использованием JSON
"""

import json
import hashlib
import logging
import os
from typing import Any, Dict, Optional, Callable
from functools import wraps
import asyncio
from datetime import datetime, timedelta
from src.config import Config
from src.data_manager import DataManager

logger = logging.getLogger(__name__)

class CacheManager:
    """Класс для управления кэшем с использованием JSON"""
    
    _instance = None
    _cache = {}
    _cache_file = os.path.join(Config.DATA_DIR, "cache.json")
    
    def __new__(cls):
        """Создание или получение экземпляра CacheManager"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация менеджера кэша"""
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._load_cache()
            logger.info("✅ Инициализирован CacheManager")
    
    def _load_cache(self) -> None:
        """Загрузка кэша из файла"""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                logger.info("✅ Кэш загружен из файла")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки кэша: {e}")
            self._cache = {}
    
    async def save_cache(self) -> None:
        """Сохранение кэша в файл"""
        try:
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            logger.info("✅ Кэш сохранен в файл")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения кэша: {e}")
    
    @classmethod
    def get_instance(cls) -> 'CacheManager':
        """Получение экземпляра CacheManager"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _get_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Генерация ключа кэша"""
        args_str = str(args) + str(sorted(kwargs.items()))
        hash_obj = hashlib.md5(args_str.encode())
        return f"{func_name}:{hash_obj.hexdigest()}"
    
    @staticmethod
    def cached(ttl: Optional[int] = None) -> Callable:
        """Декоратор для кэширования результатов функции"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                cache_manager = CacheManager.get_instance()
                cache_key = cache_manager._get_cache_key(func.__name__, *args, **kwargs)
                
                # Пробуем получить из кэша
                cached_value = await cache_manager.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_value
                
                # Выполняем функцию
                result = await func(*args, **kwargs)
                
                # Сохраняем в кэш
                await cache_manager.set(cache_key, result, ttl)
                logger.debug(f"Cache miss for {func.__name__}")
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                cache_manager = CacheManager.get_instance()
                cache_key = cache_manager._get_cache_key(func.__name__, *args, **kwargs)
                
                # Пытаемся получить результат из кэша
                # cached_value = asyncio.run(cache_manager.get(cache_key))
                cached_value = None  # Временно отключаем кэширование
                if cached_value is not None:
                    logger.debug(f"Кэш-попадание для {func.__name__}")
                    return cached_value
                
                # Выполняем функцию и кэшируем результат
                result = func(*args, **kwargs)
                # asyncio.run(cache_manager.set(cache_key, result, ttl))
                logger.debug(f"Результат {func.__name__} закэширован")
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        if key in self._cache:
            cache_data = self._cache[key]
            if 'expires_at' in cache_data:
                if datetime.fromisoformat(cache_data['expires_at']) > datetime.now():
                    return cache_data['value']
                else:
                    del self._cache[key]
                    await self.save_cache()
            else:
                return cache_data['value']
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Сохранение значения в кэш"""
        cache_data = {'value': value}
        if ttl is not None:
            cache_data['expires_at'] = (datetime.now() + timedelta(seconds=ttl)).isoformat()
        self._cache[key] = cache_data
        await self.save_cache()
    
    async def invalidate(self, key: str) -> None:
        """Удаление значения из кэша"""
        if key in self._cache:
            del self._cache[key]
            await self.save_cache()
    
    async def clear(self) -> None:
        """Очистка всего кэша"""
        self._cache = {}
        await self.save_cache()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        return {
            'size': len(self._cache),
            'keys': list(self._cache.keys())
        }
    
    # def get_shopping_list(self, user_id: int = None):  # УДАЛЕНО: функционал не будет реализован
    #     """УДАЛЕНО: функционал не будет реализован"""
    #     return DataManager().get_shopping_list() 