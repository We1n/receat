"""
Сервис для работы с ценами на продукты с поддержкой нескольких магазинов.
"""
from typing import Dict, Optional, Union, List
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class PriceService:
    """
    Сервис для работы с ценами на продукты с поддержкой нескольких магазинов.
    
    Attributes:
        prices_file (Path): Путь к файлу с ценами
        stores_file (Path): Путь к файлу с конфигурацией магазинов
        prices (Dict[str, Dict]): Словарь с ценами на продукты
        stores (Dict): Конфигурация магазинов с их приоритетами
    """
    
    def __init__(
        self, 
        prices_file: Union[str, Path] = "data/prices.json",
        stores_file: Union[str, Path] = "data/stores.json"
    ):
        """
        Инициализация сервиса.
        
        Args:
            prices_file: Путь к файлу с ценами
            stores_file: Путь к файлу с конфигурацией магазинов
        """
        self.prices_file = Path(prices_file)
        self.stores_file = Path(stores_file)
        self.stores: Dict = self._load_stores()
        self.prices: Dict[str, Dict] = self._load_prices()
        
    def _load_stores(self) -> Dict:
        """
        Загрузка конфигурации магазинов из файла.
        
        Returns:
            Dict: Конфигурация магазинов
        """
        try:
            if self.stores_file.exists():
                with open(self.stores_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Преобразуем список магазинов в словарь для быстрого доступа
                    stores_dict = {}
                    for store in data.get("stores", []):
                        stores_dict[store["id"]] = {
                            "name": store["name"],
                            "priority": store["priority"],
                            "description": store.get("description", "")
                        }
                    return {
                        "stores": stores_dict,
                        "default_store": data.get("default_store", "store1"),
                        "store_list": sorted(
                            data.get("stores", []),
                            key=lambda x: x.get("priority", 999)
                        )
                    }
            return {"stores": {}, "default_store": "store1", "store_list": []}
        except Exception as e:
            logger.error(f"Ошибка при загрузке магазинов: {e}")
            return {"stores": {}, "default_store": "store1", "store_list": []}
    
    def _load_prices(self) -> Dict:
        """
        Загрузка цен из файла.
        
        Returns:
            Dict: Словарь с ценами
        """
        try:
            if self.prices_file.exists():
                with open(self.prices_file, "r", encoding="utf-8") as f:
                    prices = json.load(f)
                    # Миграция старых данных в новый формат
                    return self._migrate_prices(prices)
            return {}
        except Exception as e:
            logger.error(f"Ошибка при загрузке цен: {e}")
            return {}
    
    def _migrate_prices(self, prices: Dict) -> Dict:
        """
        Миграция старых цен в новый формат с поддержкой магазинов.
        
        Args:
            prices: Старый формат цен
            
        Returns:
            Dict: Новый формат цен
        """
        migrated = {}
        default_store = self.stores.get("default_store", "store1")
        
        for product_name, price_data in prices.items():
            # Если это старый формат (просто price и updated_at)
            if "price" in price_data and "stores" not in price_data:
                migrated[product_name] = {
                    "stores": {
                        default_store: {
                            "price": price_data["price"],
                            "updated_at": price_data.get("updated_at", datetime.now().isoformat())
                        }
                    },
                    "best_store": default_store,
                    "best_price": price_data["price"]
                }
                # Пересчитываем лучшую цену
                self._update_best_price(product_name, migrated[product_name])
            else:
                # Уже новый формат или частично мигрированный
                if "stores" not in price_data:
                    price_data["stores"] = {}
                # Убеждаемся, что best_price и best_store обновлены
                self._update_best_price(product_name, price_data)
                migrated[product_name] = price_data
        
        return migrated
    
    def _update_best_price(self, product_name: str, price_data: Dict) -> None:
        """
        Обновление лучшей цены и магазина для продукта.
        
        Args:
            product_name: Название продукта
            price_data: Данные о ценах продукта
        """
        stores = price_data.get("stores", {})
        if not stores:
            price_data["best_price"] = None
            price_data["best_store"] = None
            return
        
        # Находим магазин с минимальной ценой
        best_store = None
        best_price = None
        
        for store_id, store_data in stores.items():
            price = store_data.get("price")
            if price is not None:
                if best_price is None or price < best_price:
                    best_price = price
                    best_store = store_id
        
        price_data["best_price"] = best_price
        price_data["best_store"] = best_store
            
    def _save_prices(self) -> None:
        """
        Сохранение цен в файл.
        """
        try:
            self.prices_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.prices_file, "w", encoding="utf-8") as f:
                json.dump(self.prices, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при сохранении цен: {e}")
            
    def get_price(self, product_name: str, store_id: Optional[str] = None) -> Optional[Dict]:
        """
        Получение цены продукта.
        
        Args:
            product_name: Название продукта
            store_id: ID магазина (опционально). Если не указан, возвращается лучшая цена.
            
        Returns:
            Optional[Dict]: Данные о цене продукта или None, если продукт не найден
        """
        product_name = product_name.lower()
        price_data = self.prices.get(product_name)
        
        if not price_data:
            return None
        
        # Если указан конкретный магазин
        if store_id:
            stores = price_data.get("stores", {})
            store_price = stores.get(store_id)
            if store_price:
                return {
                    "price": store_price.get("price"),
                    "store_id": store_id,
                    "store_name": self.stores.get("stores", {}).get(store_id, {}).get("name", store_id),
                    "updated_at": store_price.get("updated_at")
                }
            return None
        
        # Возвращаем лучшую цену
        best_store = price_data.get("best_store")
        best_price = price_data.get("best_price")
        
        if best_store and best_price is not None:
            store_data = price_data.get("stores", {}).get(best_store, {})
            return {
                "price": best_price,
                "store_id": best_store,
                "store_name": self.stores.get("stores", {}).get(best_store, {}).get("name", best_store),
                "updated_at": store_data.get("updated_at"),
                "all_stores": self.get_all_store_prices(product_name)
            }
        
        return None
    
    def get_all_store_prices(self, product_name: str) -> Dict[str, Dict]:
        """
        Получение всех цен продукта по магазинам.
        
        Args:
            product_name: Название продукта
            
        Returns:
            Dict: Словарь с ценами по магазинам
        """
        product_name = product_name.lower()
        price_data = self.prices.get(product_name)
        
        if not price_data:
            return {}
        
        stores = price_data.get("stores", {})
        result = {}
        
        for store_id, store_price_data in stores.items():
            store_info = self.stores.get("stores", {}).get(store_id, {})
            result[store_id] = {
                "price": store_price_data.get("price"),
                "store_name": store_info.get("name", store_id),
                "priority": store_info.get("priority", 999),
                "updated_at": store_price_data.get("updated_at")
            }
        
        # Сортируем по приоритету магазина
        return dict(sorted(result.items(), key=lambda x: x[1].get("priority", 999)))
        
    def set_price(
        self, 
        product_name: str, 
        price: float, 
        store_id: Optional[str] = None
    ) -> None:
        """
        Установка цены продукта в магазине.
        
        Args:
            product_name: Название продукта
            price: Цена продукта
            store_id: ID магазина. Если не указан, используется магазин по умолчанию.
        """
        product_name = product_name.lower()
        current_time = datetime.now().isoformat()
        
        # Если магазин не указан, используем магазин по умолчанию
        if not store_id:
            store_id = self.stores.get("default_store", "store1")
        
        # Проверяем, существует ли магазин
        if store_id not in self.stores.get("stores", {}):
            logger.warning(f"Магазин {store_id} не найден в конфигурации. Используется магазин по умолчанию.")
            store_id = self.stores.get("default_store", "store1")
        
        # Инициализируем структуру данных, если продукта нет
        if product_name not in self.prices:
            self.prices[product_name] = {
                "stores": {},
                "best_store": None,
                "best_price": None
            }
        
        # Устанавливаем цену в магазине
        if "stores" not in self.prices[product_name]:
            self.prices[product_name]["stores"] = {}
        
        self.prices[product_name]["stores"][store_id] = {
            "price": price,
            "updated_at": current_time
        }
        
        # Обновляем лучшую цену
        self._update_best_price(product_name, self.prices[product_name])
        
        self._save_prices()
    
    def get_best_price(self, product_name: str) -> Optional[Dict]:
        """
        Получение лучшей (минимальной) цены продукта с указанием магазина.
        
        Args:
            product_name: Название продукта
            
        Returns:
            Optional[Dict]: Данные о лучшей цене или None, если продукт не найден
        """
        return self.get_price(product_name)
        
    def get_all_prices(self) -> Dict:
        """
        Получение всех цен.
        
        Returns:
            Dict: Словарь со всеми ценами
        """
        return self.prices
        
    def delete_price(self, product_name: str, store_id: Optional[str] = None) -> bool:
        """
        Удаление цены продукта.
        
        Args:
            product_name: Название продукта
            store_id: ID магазина (опционально). Если не указан, удаляются все цены продукта.
            
        Returns:
            bool: True, если цена удалена, иначе False
        """
        product_name = product_name.lower()
        
        if product_name not in self.prices:
            return False
        
        # Если указан конкретный магазин, удаляем только его цену
        if store_id:
            stores = self.prices[product_name].get("stores", {})
            if store_id in stores:
                del stores[store_id]
                # Обновляем лучшую цену
                self._update_best_price(product_name, self.prices[product_name])
                # Если больше нет цен, удаляем продукт полностью
                if not stores:
                    del self.prices[product_name]
                self._save_prices()
                return True
            return False
        
        # Удаляем все цены продукта
        del self.prices[product_name]
        self._save_prices()
        return True
    
    def get_stores(self) -> List[Dict]:
        """
        Получение списка всех магазинов с их приоритетами.
        
        Returns:
            List[Dict]: Список магазинов, отсортированный по приоритету
        """
        return self.stores.get("store_list", [])
    
    def get_store_info(self, store_id: str) -> Optional[Dict]:
        """
        Получение информации о магазине.
        
        Args:
            store_id: ID магазина
            
        Returns:
            Optional[Dict]: Информация о магазине или None
        """
        return self.stores.get("stores", {}).get(store_id)
        
    def search_prices(self, query: str) -> Dict:
        """
        Поиск цен по запросу.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Dict: Словарь с найденными ценами
        """
        query = query.lower()
        return {
            name: data
            for name, data in self.prices.items()
            if query in name
        } 