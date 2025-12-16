"""
Модуль с декораторами для кэширования
"""

import asyncio
import functools
import hashlib
import json
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

T = TypeVar('T')

def cache_result(
    ttl: Optional[int] = None,
    tags: Optional[Union[str, List[str]]] = None,
    is_async: bool = False,
    cache_type: str = 'default',
    key_prefix: Optional[str] = None
) -> Callable:
    """
    Универсальный декоратор для кэширования результатов функций
    
    Args:
        ttl: Время жизни кэша в секундах
        tags: Теги для инвалидации кэша
        is_async: Флаг асинхронной функции
        cache_type: Тип кэша
        key_prefix: Префикс для ключа кэша
        
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            """
            Обертка для асинхронных функций
            
            Args:
                *args: Позиционные аргументы
                **kwargs: Именованные аргументы
                
            Returns:
                T: Результат выполнения функции
            """
            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)
            cache_manager = CacheManager.get_instance(cache_type)
            
            # Пытаемся получить результат из кэша
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Кэш-попадание для {func.__name__}")
                return cached_result
            
            # Выполняем функцию и кэшируем результат
            result = await func(*args, **kwargs)
            await cache_manager.set(
                cache_key,
                result,
                ttl=ttl,
                tags=tags
            )
            logger.debug(f"Результат {func.__name__} закэширован")
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            """
            Обертка для синхронных функций
            
            Args:
                *args: Позиционные аргументы
                **kwargs: Именованные аргументы
                
            Returns:
                T: Результат выполнения функции
            """
            # Временно отключаем кэширование для синхронных функций
            # чтобы избежать конфликта event loop
            logger.debug(f"Кэширование отключено для синхронной функции {func.__name__}")
            return func(*args, **kwargs)
        
        return async_wrapper if is_async else sync_wrapper
    
    return decorator

def cache_method(
    ttl: Optional[int] = None,
    tags: Optional[Union[str, List[str]]] = None,
    is_async: bool = False,
    cache_type: str = 'default',
    key_prefix: Optional[str] = None
) -> Callable:
    """
    Декоратор для кэширования методов классов
    
    Args:
        ttl: Время жизни кэша в секундах
        tags: Теги для инвалидации кэша
        is_async: Флаг асинхронной функции
        cache_type: Тип кэша
        key_prefix: Префикс для ключа кэша
        
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
            """
            Обертка для асинхронных методов
            
            Args:
                self: Экземпляр класса
                *args: Позиционные аргументы
                **kwargs: Именованные аргументы
                
            Returns:
                T: Результат выполнения метода
            """
            # Используем имя класса как префикс
            method_prefix = f"{self.__class__.__name__}.{func.__name__}"
            cache_key = _generate_cache_key(
                func,
                args,
                kwargs,
                key_prefix or method_prefix
            )
            cache_manager = CacheManager.get_instance(cache_type)
            
            # Пытаемся получить результат из кэша
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Кэш-попадание для {method_prefix}")
                return cached_result
            
            # Выполняем метод и кэшируем результат
            result = await func(self, *args, **kwargs)
            await cache_manager.set(
                cache_key,
                result,
                ttl=ttl,
                tags=tags
            )
            logger.debug(f"Результат {method_prefix} закэширован")
            return result
        
        @functools.wraps(func)
        def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
            """
            Обертка для синхронных методов
            
            Args:
                self: Экземпляр класса
                *args: Позиционные аргументы
                **kwargs: Именованные аргументы
                
            Returns:
                T: Результат выполнения метода
            """
            # Временно отключаем кэширование для синхронных методов
            # чтобы избежать конфликта event loop
            logger.debug(f"Кэширование отключено для синхронного метода {self.__class__.__name__}.{func.__name__}")
            return func(self, *args, **kwargs)
        
        return async_wrapper if is_async else sync_wrapper
    
    return decorator

def _generate_cache_key(
    func: Callable,
    args: tuple,
    kwargs: dict,
    key_prefix: Optional[str] = None
) -> str:
    """
    Генерация ключа кэша
    
    Args:
        func: Функция
        args: Позиционные аргументы
        kwargs: Именованные аргументы
        key_prefix: Префикс для ключа
        
    Returns:
        str: Ключ кэша
    """
    # Формируем префикс ключа
    prefix = key_prefix or f"{func.__module__}.{func.__name__}"
    
    # Сериализуем аргументы
    args_str = json.dumps(args, sort_keys=True)
    kwargs_str = json.dumps(kwargs, sort_keys=True)
    
    # Создаем хеш
    key = f"{prefix}:{args_str}:{kwargs_str}"
    return hashlib.md5(key.encode()).hexdigest()

async def invalidate_by_tag(tag: str, cache_type: str = 'default') -> bool:
    """
    Инвалидация кэша по тегу
    
    Args:
        tag: Тег для инвалидации
        cache_type: Тип кэша
        
    Returns:
        bool: True если успешно, False в противном случае
    """
    try:
        cache_manager = CacheManager.get_instance(cache_type)
        return await cache_manager.invalidate_by_tag(tag)
    except Exception as e:
        logger.error(f"Ошибка при инвалидации кэша по тегу {tag}: {e}")
        return False

async def invalidate_by_tags(tags: List[str], cache_type: str = 'default') -> bool:
    """
    Инвалидация кэша по нескольким тегам
    
    Args:
        tags: Список тегов для инвалидации
        cache_type: Тип кэша
        
    Returns:
        bool: True если успешно, False в противном случае
    """
    try:
        cache_manager = CacheManager.get_instance(cache_type)
        return await cache_manager.invalidate_by_tags(tags)
    except Exception as e:
        logger.error(f"Ошибка при инвалидации кэша по тегам {tags}: {e}")
        return False 