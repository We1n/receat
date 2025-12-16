"""
Сервис для работы с продуктами и их питательной ценностью.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, TypedDict
from datetime import datetime
from src.logger import setup_logger
from src.utils.error_handler import ErrorHandler
from src.cache import cache_result, invalidate_cache
import os
import asyncio
import logging

logger = setup_logger(__name__)

class ProductInfo(TypedDict):
    """Тип для информации о продукте."""
    id: int
    name: str
    nutrients: Dict[str, float]
    unit: str
    description: str
    emoji: str
    created_at: str
    updated_at: str

class ProductService:
    """
    Сервис для работы с продуктами.
    
    Предоставляет методы для:
    - Управление продуктами
    - Получение информации о продуктах
    - Расчет питательной ценности
    """
    
    def __init__(self) -> None:
        """Инициализация сервиса."""
        self.products_file = Path("data/products.json")
        self._load_data()
        logger.info("✅ Сервис продуктов инициализирован")
    
    def _load_data(self) -> None:
        """Загрузка данных о продуктах."""
        try:
            if not self.products_file.exists():
                self._create_default_data()
            with open(self.products_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict) and isinstance(loaded.get("products"), list):
                    self.data = loaded
                else:
                    self.data = {"products": [], "last_update": None}
            logger.info("✅ Данные о продуктах загружены")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки данных: {str(e)}")
            self.data = {"products": [], "last_update": None}
    
    def _save_data(self) -> None:
        """Сохранение данных о продуктах."""
        try:
            self.data["last_update"] = datetime.now().isoformat()
            with open(self.products_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            logger.info("✅ Данные о продуктах сохранены")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения данных: {str(e)}")
    
    def _create_default_data(self) -> None:
        """Создание базовой структуры данных."""
        default_data = {
            "products": [
                {
                    "id": 1,
                    "name": "Куриная грудка",
                    "nutrients": {
                        "calories": 110.0,
                        "protein": 23.0,
                        "fat": 2.0,
                        "carbs": 0.0,
                        "fiber": 0.0,
                        "sugar": 0.0,
                        "sodium": 70.0,
                        "cholesterol": 60.0
                    },
                    "unit": "г",
                    "description": "Диетическое мясо с высоким содержанием белка",
                    "emoji": "🍗",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "id": 2,
                    "name": "Рис",
                    "nutrients": {
                        "calories": 130.0,
                        "protein": 2.7,
                        "fat": 0.3,
                        "carbs": 28.0,
                        "fiber": 0.4,
                        "sugar": 0.1,
                        "sodium": 1.0,
                        "cholesterol": 0.0
                    },
                    "unit": "г",
                    "description": "Популярная крупа, богатая углеводами",
                    "emoji": "🍚",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "id": 3,
                    "name": "Яблоко",
                    "nutrients": {
                        "calories": 52.0,
                        "protein": 0.3,
                        "fat": 0.2,
                        "carbs": 14.0,
                        "fiber": 2.4,
                        "sugar": 10.0,
                        "sodium": 1.0,
                        "cholesterol": 0.0
                    },
                    "unit": "г",
                    "description": "Популярный фрукт, богатый клетчаткой и витаминами",
                    "emoji": "🍎",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            ],
            "last_update": datetime.now().isoformat()
        }
        self.data = default_data
        self._save_data()
        logger.info("✅ Создана базовая структура данных о продуктах")
    
    @ErrorHandler.handle_errors
    @cache_result(ttl=3600, key_template="product_{product_id}")
    async def get_product(self, product_id: int) -> Optional[ProductInfo]:
        """
        Получение информации о продукте.
        
        Args:
            product_id: ID продукта
            
        Returns:
            Optional[ProductInfo]: Информация о продукте
        """
        for product in self.data["products"]:
            if product["id"] == product_id:
                return product
        return None
    
    def get_all_products(self) -> List[ProductInfo]:
        """
        Получение списка всех продуктов.
        
        Returns:
            List[ProductInfo]: Список продуктов
        """
        return self.data["products"]
    
    @ErrorHandler.handle_errors
    def add_product(self, name: str, nutrients: Dict[str, float], unit: str, description: str, emoji: str) -> ProductInfo:
        """
        Добавление нового продукта.
        
        Args:
            name: Название продукта
            nutrients: Питательные вещества (calories, protein, fat, carbs, fiber, sugar, sodium, cholesterol)
            unit: Единица измерения
            description: Описание
            emoji: Эмодзи
            
        Returns:
            ProductInfo: Информация о добавленном продукте
        """
        # Генерируем новый ID
        new_id = max(p["id"] for p in self.data["products"]) + 1 if self.data["products"] else 1
        
        # Приводим нутриенты к единому виду
        nutrients = {
            "calories": float(nutrients.get("calories", 0)),
            "protein": float(nutrients.get("protein", 0)),
            "fat": float(nutrients.get("fat", 0)),
            "carbs": float(nutrients.get("carbs", 0)),
            "fiber": float(nutrients.get("fiber", 0)),
            "sugar": float(nutrients.get("sugar", 0)),
            "sodium": float(nutrients.get("sodium", 0)),
            "cholesterol": float(nutrients.get("cholesterol", 0)),
        }
        
        # Создаем новый продукт
        new_product = {
            "id": new_id,
            "name": name,
            "nutrients": nutrients,
            "unit": unit,
            "description": description,
            "emoji": emoji,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Добавляем в список
        self.data["products"].append(new_product)
        self._save_data()
        
        logger.info(f"✅ Добавлен новый продукт: {name}")
        return new_product  # type: ignore
    
    @ErrorHandler.handle_errors
    def update_product(self, product_id: int, **kwargs: Any) -> Optional[ProductInfo]:
        """
        Обновление информации о продукте.
        
        Args:
            product_id: ID продукта
            **kwargs: Поля для обновления
            
        Returns:
            Optional[ProductInfo]: Обновленная информация
        """
        # Ищем продукт
        for product in self.data["products"]:
            if product["id"] == product_id:
                # Обновляем поля
                for key, value in kwargs.items():
                    if key == "nutrients":
                        # Приводим нутриенты к единому виду
                        value = {
                            "calories": float(value.get("calories", 0)),
                            "protein": float(value.get("protein", 0)),
                            "fat": float(value.get("fat", 0)),
                            "carbs": float(value.get("carbs", 0)),
                            "fiber": float(value.get("fiber", 0)),
                            "sugar": float(value.get("sugar", 0)),
                            "sodium": float(value.get("sodium", 0)),
                            "cholesterol": float(value.get("cholesterol", 0)),
                        }
                        product[key] = value
                    elif key in product:
                        product[key] = value
                
                # Обновляем время изменения
                product["updated_at"] = datetime.now().isoformat()
                
                self._save_data()
                logger.info(f"✅ Обновлен продукт: {product['name']}")
                return product
        
        logger.warning(f"⚠️ Продукт с ID {product_id} не найден")
        return None
    
    @ErrorHandler.handle_errors
    async def delete_product(self, product_id: int) -> bool:
        logger = logging.getLogger(__name__)
        logger.info(f"[DEBUG] Вход в delete_product: product_id={product_id}")
        found = False
        for i, product in enumerate(self.data["products"]):
            if product["id"] == product_id:
                del self.data["products"][i]
                found = True
                break
        if not found:
            logger.warning(f"[DEBUG] Продукт не найден для удаления: {product_id}")
            return False
        try:
            logger.info(f"[DEBUG] Сохраняю данные после удаления продукта {product_id}")
            await asyncio.to_thread(self._save_data)
            logger.info(f"[DEBUG] Данные успешно сохранены после удаления продукта {product_id}")
            return True
        except Exception as e:
            logger.error(f"[DEBUG] Ошибка при сохранении данных после удаления продукта {product_id}: {e}")
            return False

    def calculate_nutrients(self, product: ProductInfo, amount: float) -> Dict[str, float]:
        """Рассчитать нутриенты для указанного количества продукта"""
        try:
            # Расчет нутриентов
            nutrients = {
                "calories": product["nutrients"].get("calories", 0) * amount / 100,
                "protein": product["nutrients"].get("protein", 0) * amount / 100,
                "fat": product["nutrients"].get("fat", 0) * amount / 100,
                "carbs": product["nutrients"].get("carbs", 0) * amount / 100,
                "fiber": product["nutrients"].get("fiber", 0) * amount / 100,
                "sugar": product["nutrients"].get("sugar", 0) * amount / 100,
                "sodium": product["nutrients"].get("sodium", 0) * amount / 100,
                "cholesterol": product["nutrients"].get("cholesterol", 0) * amount / 100,
            }
            
            return nutrients
        
        except Exception as e:
            print(f"Ошибка расчета нутриентов: {str(e)}")
            return {
                "calories": 0,
                "protein": 0,
                "fat": 0,
                "carbs": 0,
                "fiber": 0,
                "sugar": 0,
                "sodium": 0,
                "cholesterol": 0
            }

    def get_history(self) -> List[Dict[str, Any]]:
        """Получить историю продуктов"""
        try:
            file_path = os.path.join("data", "product_history.json")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    history: List[Dict[str, Any]] = json.load(f)
                    return history
            return []
        except Exception as e:
            print(f"Ошибка загрузки истории: {str(e)}")
            return []

    def add_to_history(self, product_id: int) -> None:
        """Добавить продукт в историю"""
        try:
            # Получение продукта
            product = self.get_product(product_id)
            if not product:
                return
            
            # Загрузка истории
            history = self.get_history()
            
            # Добавление записи
            history.append({
                "id": product_id,
                "name": product["name"],
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Сохранение истории
            file_path = os.path.join("data", "product_history.json")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"Ошибка добавления в историю: {str(e)}")

    def search_products(self, query: str) -> List[ProductInfo]:
        """
        Поиск продуктов по названию (частичное совпадение, регистронезависимо).
        Args:
            query: поисковый запрос
        Returns:
            List[ProductInfo]: Список найденных продуктов
        """
        query = query.strip().lower()
        if not query:
            return []
        return [p for p in self.data["products"] if query in p["name"].lower()]

    async def invalidate_cache(self):
        """Асинхронно сбрасывает кэш, если он есть."""
        if hasattr(self, 'data'):
            self.data = None
        if hasattr(self, '_cache'):
            self._cache = {}
        # Можно добавить дополнительные действия по сбросу кэша
        return True 