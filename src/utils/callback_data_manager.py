"""
Менеджер для работы с длинными callback_data
Хранит сложные данные и возвращает короткие ID для использования в callback_data
"""
import time
import logging
from typing import Dict, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)

class CallbackDataManager:
    """Менеджер для работы с длинными callback_data"""
    
    def __init__(self, max_age_hours: int = 24, max_items: int = 1000):
        """
        Инициализация менеджера
        
        Args:
            max_age_hours: Максимальный возраст данных в часах
            max_items: Максимальное количество элементов в кэше
        """
        self._temp_data: Dict[str, Dict[str, Any]] = {}
        self._counter = 0
        self._max_age_hours = max_age_hours
        self._max_items = max_items
        self._lock = Lock()
        
        logger.info(f"CallbackDataManager initialized with max_age={max_age_hours}h, max_items={max_items}")
    
    def store_complex_data(self, data: Any, data_type: str = "generic") -> str:
        """
        Сохраняет сложные данные и возвращает короткий ID
        
        Args:
            data: Данные для сохранения
            data_type: Тип данных для логирования
            
        Returns:
            Короткий ID для использования в callback_data
        """
        with self._lock:
            # Очищаем старые данные перед добавлением новых
            self._cleanup_old_data()
            
            # Проверяем лимит элементов
            if len(self._temp_data) >= self._max_items:
                self._remove_oldest_items()
            
            # Создаем уникальный ID
            data_id = f"d{self._counter}_{int(time.time())}"
            self._counter += 1
            
            # Сохраняем данные с метаинформацией
            self._temp_data[data_id] = {
                "data": data,
                "type": data_type,
                "timestamp": time.time(),
                "access_count": 0
            }
            
            logger.debug(f"Stored complex data: {data_type} with ID {data_id}")
            return data_id
    
    def get_complex_data(self, data_id: str) -> Optional[Any]:
        """
        Получает сложные данные по ID
        
        Args:
            data_id: ID данных
            
        Returns:
            Сохраненные данные или None, если не найдены
        """
        with self._lock:
            if data_id in self._temp_data:
                # Увеличиваем счетчик обращений
                self._temp_data[data_id]["access_count"] += 1
                
                # Обновляем время последнего доступа
                self._temp_data[data_id]["timestamp"] = time.time()
                
                data = self._temp_data[data_id]["data"]
                logger.debug(f"Retrieved complex data with ID {data_id}")
                return data
            
            logger.warning(f"Complex data not found for ID: {data_id}")
            return None
    
    def remove_data(self, data_id: str) -> bool:
        """
        Удаляет данные по ID
        
        Args:
            data_id: ID данных для удаления
            
        Returns:
            True, если данные были удалены, False, если не найдены
        """
        with self._lock:
            if data_id in self._temp_data:
                del self._temp_data[data_id]
                logger.debug(f"Removed complex data with ID {data_id}")
                return True
            
            logger.warning(f"Attempted to remove non-existent data with ID: {data_id}")
            return False
    
    def cleanup_old_data(self, max_age_hours: Optional[int] = None) -> int:
        """
        Очищает старые данные
        
        Args:
            max_age_hours: Максимальный возраст в часах (если None, используется значение по умолчанию)
            
        Returns:
            Количество удаленных элементов
        """
        if max_age_hours is None:
            max_age_hours = self._max_age_hours
        
        with self._lock:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            expired_ids = [
                data_id for data_id, item in self._temp_data.items()
                if current_time - item["timestamp"] > max_age_seconds
            ]
            
            for data_id in expired_ids:
                del self._temp_data[data_id]
            
            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} old data items")
            
            return len(expired_ids)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику менеджера
        
        Returns:
            Словарь со статистикой
        """
        with self._lock:
            if not self._temp_data:
                return {
                    "total_items": 0,
                    "data_types": {},
                    "oldest_item_age": 0,
                    "newest_item_age": 0
                }
            
            current_time = time.time()
            data_types: Dict[str, int] = {}
            ages = []
            
            for item in self._temp_data.values():
                data_type = item["type"]
                data_types[data_type] = data_types.get(data_type, 0) + 1
                ages.append(current_time - item["timestamp"])
            
            return {
                "total_items": len(self._temp_data),
                "data_types": data_types,
                "oldest_item_age": max(ages) if ages else 0,
                "newest_item_age": min(ages) if ages else 0,
                "max_age_hours": self._max_age_hours,
                "max_items": self._max_items
            }
    
    def _cleanup_old_data(self) -> None:
        """Внутренний метод для очистки старых данных"""
        self.cleanup_old_data()
    
    def _remove_oldest_items(self, remove_count: int = 10) -> None:
        """
        Удаляет самые старые элементы
        
        Args:
            remove_count: Количество элементов для удаления
        """
        # Сортируем по времени создания (самые старые первые)
        sorted_items = sorted(
            self._temp_data.items(),
            key=lambda x: x[1]["timestamp"]
        )
        
        # Удаляем самые старые элементы
        for data_id, _ in sorted_items[:remove_count]:
            del self._temp_data[data_id]
        
        logger.info(f"Removed {remove_count} oldest items due to size limit")

# Глобальный экземпляр менеджера
callback_data_manager = CallbackDataManager() 