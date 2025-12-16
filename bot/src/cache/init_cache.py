"""
Модуль для инициализации кэша
"""

import logging
from typing import Optional
from src.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)

async def initialize_cache() -> None:
    """
    Инициализация кэша
    """
    try:
        cache_manager = CacheManager.get_instance()
        logger.info("✅ Кэш успешно инициализирован")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации кэша: {e}")
        raise

async def close_cache() -> None:
    """Закрытие кэша"""
    try:
        cache_manager = CacheManager.get_instance()
        await cache_manager.save_cache()
        logger.info("✅ Кэш успешно закрыт")
    except Exception as e:
        logger.error(f"❌ Ошибка закрытия кэша: {e}")
        raise

def get_cache() -> CacheManager:
    """
    Получение экземпляра кэша
    
    Returns:
        CacheManager: Экземпляр кэша
    """
    return CacheManager.get_instance() 