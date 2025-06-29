"""
Сервис поиска продуктов для EatBot
Обеспечивает поиск продуктов по различным критериям с поддержкой пагинации
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
import re

logger = logging.getLogger(__name__)

class ProductSearchService:
    """Сервис для поиска продуктов с поддержкой различных критериев"""
    
    def __init__(self, product_service):
        self.product_service = product_service
        self.logger = logging.getLogger(__name__)
    
    async def search_products(
        self, 
        query: str = "", 
        category: str = "", 
        min_calories: Optional[float] = None,
        max_calories: Optional[float] = None,
        page: int = 1, 
        per_page: int = 10
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Поиск продуктов по различным критериям
        
        Args:
            query: Поисковый запрос (название продукта)
            category: Категория продукта
            min_calories: Минимальная калорийность
            max_calories: Максимальная калорийность
            page: Номер страницы
            per_page: Количество продуктов на странице
            
        Returns:
            Tuple[List[Dict], int]: (список продуктов, общее количество)
        """
        self.logger.info(f"Поиск продуктов: query='{query}', category='{category}', page={page}")
        
        try:
            # Получаем все продукты
            all_products = self.product_service.get_all_products()
            
            if not all_products:
                return [], 0
            
            # Фильтруем продукты по критериям
            filtered_products = self._filter_products(
                all_products, query, category, min_calories, max_calories
            )
            
            # Сортируем по релевантности
            sorted_products = self._sort_by_relevance(filtered_products, query)
            
            # Применяем пагинацию
            total = len(sorted_products)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_products = sorted_products[start_idx:end_idx]
            
            self.logger.info(f"Найдено продуктов: {total}, показано: {len(paginated_products)}")
            
            return paginated_products, total
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска продуктов: {e}")
            return [], 0
    
    def _filter_products(
        self, 
        products: List[Dict[str, Any]], 
        query: str, 
        category: str,
        min_calories: float,
        max_calories: float
    ) -> List[Dict[str, Any]]:
        """Фильтрация продуктов по критериям"""
        filtered = []
        
        query_lower = query.lower().strip() if query else ""
        category_lower = category.lower().strip() if category else ""
        
        for product in products:
            # Фильтр по названию
            if query_lower:
                product_name = product.get('name', '').lower()
                if query_lower not in product_name:
                    continue
            
            # Фильтр по категории
            if category_lower:
                product_category = product.get('category', '').lower()
                if category_lower not in product_category:
                    continue
            
            # Фильтр по калорийности
            if min_calories is not None or max_calories is not None:
                nutrition = product.get('nutrition', {})
                calories = nutrition.get('calories', 0)
                
                if min_calories is not None and calories < min_calories:
                    continue
                if max_calories is not None and calories > max_calories:
                    continue
            
            filtered.append(product)
        
        return filtered
    
    def _sort_by_relevance(self, products: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Сортировка продуктов по релевантности"""
        if not query:
            return products
        
        query_lower = query.lower()
        
        def relevance_score(product):
            score = 0
            name = product.get('name', '').lower()
            
            # Точное совпадение в начале названия
            if name.startswith(query_lower):
                score += 100
            
            # Точное совпадение слова
            elif query_lower in name.split():
                score += 50
            
            # Частичное совпадение
            elif query_lower in name:
                score += 25
            
            # Дополнительные бонусы
            category = product.get('category', '').lower()
            if query_lower in category:
                score += 10
            
            return score
        
        return sorted(products, key=relevance_score, reverse=True)
    
    async def search_by_nutrition(
        self,
        min_protein: Optional[float] = None,
        max_protein: Optional[float] = None,
        min_fat: Optional[float] = None,
        max_fat: Optional[float] = None,
        min_carbs: Optional[float] = None,
        max_carbs: Optional[float] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Поиск продуктов по пищевой ценности
        
        Args:
            min_protein: Минимальное количество белков
            max_protein: Максимальное количество белков
            min_fat: Минимальное количество жиров
            max_fat: Максимальное количество жиров
            min_carbs: Минимальное количество углеводов
            max_carbs: Максимальное количество углеводов
            page: Номер страницы
            per_page: Количество продуктов на странице
            
        Returns:
            Tuple[List[Dict], int]: (список продуктов, общее количество)
        """
        self.logger.info(f"Поиск продуктов по пищевой ценности: page={page}")
        
        try:
            all_products = self.product_service.get_all_products()
            
            if not all_products:
                return [], 0
            
            # Фильтруем по пищевой ценности
            filtered_products = []
            for product in all_products:
                nutrition = product.get('nutrition', {})
                
                protein = nutrition.get('protein', 0)
                fat = nutrition.get('fat', 0)
                carbs = nutrition.get('carbs', 0)
                
                # Проверяем все критерии
                if min_protein is not None and protein < min_protein:
                    continue
                if max_protein is not None and protein > max_protein:
                    continue
                if min_fat is not None and fat < min_fat:
                    continue
                if max_fat is not None and fat > max_fat:
                    continue
                if min_carbs is not None and carbs < min_carbs:
                    continue
                if max_carbs is not None and carbs > max_carbs:
                    continue
                
                filtered_products.append(product)
            
            # Применяем пагинацию
            total = len(filtered_products)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_products = filtered_products[start_idx:end_idx]
            
            self.logger.info(f"Найдено продуктов по пищевой ценности: {total}")
            
            return paginated_products, total
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска продуктов по пищевой ценности: {e}")
            return [], 0
    
    async def get_categories(self) -> List[str]:
        """Получение списка всех категорий продуктов"""
        try:
            all_products = self.product_service.get_all_products()
            categories = set()
            
            for product in all_products:
                category = product.get('category', '').strip()
                if category:
                    categories.add(category)
            
            return sorted(list(categories))
            
        except Exception as e:
            self.logger.error(f"Ошибка получения категорий: {e}")
            return []
    
    async def get_nutrition_stats(self) -> Dict[str, Any]:
        """Получение статистики по пищевой ценности продуктов"""
        try:
            all_products = self.product_service.get_all_products()
            
            if not all_products:
                return {
                    'total_products': 0,
                    'avg_calories': 0,
                    'avg_protein': 0,
                    'avg_fat': 0,
                    'avg_carbs': 0
                }
            
            total_calories = 0
            total_protein = 0
            total_fat = 0
            total_carbs = 0
            products_with_nutrition = 0
            
            for product in all_products:
                nutrition = product.get('nutrition', {})
                if nutrition:
                    total_calories += nutrition.get('calories', 0)
                    total_protein += nutrition.get('protein', 0)
                    total_fat += nutrition.get('fat', 0)
                    total_carbs += nutrition.get('carbs', 0)
                    products_with_nutrition += 1
            
            if products_with_nutrition == 0:
                return {
                    'total_products': len(all_products),
                    'avg_calories': 0,
                    'avg_protein': 0,
                    'avg_fat': 0,
                    'avg_carbs': 0
                }
            
            return {
                'total_products': len(all_products),
                'products_with_nutrition': products_with_nutrition,
                'avg_calories': round(total_calories / products_with_nutrition, 1),
                'avg_protein': round(total_protein / products_with_nutrition, 1),
                'avg_fat': round(total_fat / products_with_nutrition, 1),
                'avg_carbs': round(total_carbs / products_with_nutrition, 1)
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {
                'total_products': 0,
                'avg_calories': 0,
                'avg_protein': 0,
                'avg_fat': 0,
                'avg_carbs': 0
            } 