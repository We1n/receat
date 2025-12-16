"""
Сервис для работы с ценами на продукты.
"""
from typing import Dict, Optional, Union
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class PriceService:
    """
    Сервис для работы с ценами на продукты.
    
    Attributes:
        prices_file (Path): Путь к файлу с ценами
        prices (Dict[str, Dict]): Словарь с ценами на продукты
    """
    
    def __init__(self, prices_file: Union[str, Path] = "data/prices.json"):
        """
        Инициализация сервиса.
        
        Args:
            prices_file: Путь к файлу с ценами
        """
        self.prices_file = Path(prices_file)
        self.prices: Dict[str, Dict] = self._load_prices()
        
    def _load_prices(self) -> Dict:
        """
        Загрузка цен из файла.
        
        Returns:
            Dict: Словарь с ценами
        """
        try:
            if self.prices_file.exists():
                with open(self.prices_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Ошибка при загрузке цен: {e}")
            return {}
            
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
            
    def get_price(self, product_name: str) -> Optional[Dict]:
        """
        Получение цены продукта.
        
        Args:
            product_name: Название продукта
            
        Returns:
            Optional[Dict]: Данные о цене продукта или None, если продукт не найден
        """
        return self.prices.get(product_name.lower())
        
    def set_price(self, product_name: str, price: float) -> None:
        """
        Установка цены продукта.
        
        Args:
            product_name: Название продукта
            price: Цена продукта
        """
        product_name = product_name.lower()
        current_time = datetime.now().isoformat()
        
        self.prices[product_name] = {
            "price": price,
            "updated_at": current_time
        }
        
        self._save_prices()
        
    def get_all_prices(self) -> Dict:
        """
        Получение всех цен.
        
        Returns:
            Dict: Словарь со всеми ценами
        """
        return self.prices
        
    def delete_price(self, product_name: str) -> bool:
        """
        Удаление цены продукта.
        
        Args:
            product_name: Название продукта
            
        Returns:
            bool: True, если цена удалена, иначе False
        """
        if product_name.lower() in self.prices:
            del self.prices[product_name.lower()]
            self._save_prices()
            return True
        return False
        
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