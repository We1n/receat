"""
Декораторы для кэширования
"""

import functools
import logging
from typing import Any, Callable, Optional, TypeVar, cast, Awaitable
from src.cache.init_cache import get_cache
from src.cache.constants import CACHE_KEYS, CACHE_TTL, CACHE_ERRORS, CACHE_ERROR_MESSAGES
import inspect

logger = logging.getLogger(__name__)

T = TypeVar('T')

def cache_result(
    key_template: str,
    ttl: Optional[int] = None,
    prefix: Optional[str] = None
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Декоратор для кэширования результата функции
    
    Args:
        key_template: Шаблон ключа кэша
        ttl: Время жизни кэша в секундах
        prefix: Префикс для ключа
        
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                # Получаем кэш
                cache = get_cache()
                if not cache:
                    logger.warning("❌ Кэш не инициализирован")
                    return await func(*args, **kwargs)
                    
                # Формируем ключ
                bound_args = inspect.signature(func).bind(*args, **kwargs)
                bound_args.apply_defaults()
                all_args = bound_args.arguments
                key = key_template.format(**all_args)
                if prefix:
                    key = f"{prefix}{key}"
                    
                # Пробуем получить из кэша
                cached = await cache.get(key)
                if cached is not None:
                    logger.debug(f"✅ Получено из кэша: {key}")
                    return cast(T, cached)
                    
                # Выполняем функцию
                result = await func(*args, **kwargs)
                
                # Сохраняем в кэш
                if result is not None:
                    await cache.set(key, result, ttl)
                    logger.debug(f"✅ Сохранено в кэш: {key}")
                    
                return result
                
            except Exception as e:
                logger.error(f"❌ Ошибка кэширования: {e}")
                return await func(*args, **kwargs)
                
        return cast(Callable[..., Awaitable[T]], wrapper)
    return decorator
    
def invalidate_cache(
    key_template: str,
    prefix: Optional[str] = None
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Декоратор для инвалидации кэша
    
    Args:
        key_template: Шаблон ключа кэша
        prefix: Префикс для ключа
        
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                # Получаем кэш
                cache = get_cache()
                if not cache:
                    logger.warning("❌ Кэш не инициализирован")
                    return await func(*args, **kwargs)
                    
                # Формируем ключ
                bound_args = inspect.signature(func).bind(*args, **kwargs)
                bound_args.apply_defaults()
                all_args = bound_args.arguments
                key = key_template.format(**all_args)
                if prefix:
                    key = f"{prefix}:{key}"
                    
                # Выполняем функцию
                result = await func(*args, **kwargs)
                
                # Инвалидируем кэш
                await cache.invalidate(key)
                logger.debug(f"✅ Инвалидирован кэш: {key}")
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Ошибка инвалидации кэша: {e}")
                return await func(*args, **kwargs)
                
        return cast(Callable[..., Awaitable[T]], wrapper)
    return decorator
    
def cache_method(
    method_name: str,
    ttl: Optional[int] = None
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Декоратор для кэширования метода класса
    
    Args:
        method_name: Имя метода
        ttl: Время жизни кэша в секундах
        
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
            try:
                # Получаем кэш
                cache = get_cache()
                if not cache:
                    logger.warning("❌ Кэш не инициализирован")
                    return await func(self, *args, **kwargs)
                    
                # Формируем ключ
                key = f"{self.__class__.__name__}:{method_name}:{id(self)}"
                
                # Пробуем получить из кэша
                cached = await cache.get(key)
                if cached is not None:
                    logger.debug(f"✅ Получено из кэша: {key}")
                    return cast(T, cached)
                    
                # Выполняем метод
                result = await func(self, *args, **kwargs)
                
                # Сохраняем в кэш
                if result is not None:
                    await cache.set(key, result, ttl)
                    logger.debug(f"✅ Сохранено в кэш: {key}")
                    
                return result
                
            except Exception as e:
                logger.error(f"❌ Ошибка кэширования метода: {e}")
                return await func(self, *args, **kwargs)
                
        return cast(Callable[..., Awaitable[T]], wrapper)
    return decorator 