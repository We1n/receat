"""
Сервис поиска рецептов для EatBot
Обеспечивает поиск рецептов по названию и ингредиентам
"""
import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from src.services.recipe_service import RecipeService

logger = logging.getLogger(__name__)

class RecipeSearchService:
    """Сервис для поиска рецептов"""
    
    def __init__(self, recipe_service: Optional[RecipeService] = None):
        self.recipe_service = recipe_service or RecipeService()
        self.logger = logging.getLogger(__name__)
    
    async def search_recipes(self, query: str, page: int = 1, per_page: int = 10) -> Tuple[List[Dict[str, Any]], int]:
        """
        Поиск рецептов по запросу
        
        Args:
            query: Поисковый запрос
            page: Номер страницы (начиная с 1)
            per_page: Количество результатов на странице
            
        Returns:
            Tuple[List[Dict], int]: (рецепты, общее количество)
        """
        if not query or not query.strip():
            return [], 0
        
        query = query.strip().lower()
        self.logger.info(f"Поиск рецептов: '{query}' (страница {page})")
        
        try:
            # Получаем все рецепты
            all_recipes = self.recipe_service.get_all_recipes()
            
            if not all_recipes:
                return [], 0
            
            # Фильтруем рецепты по запросу
            matching_recipes = []
            
            for recipe in all_recipes:
                if self._recipe_matches_query(recipe, query):
                    matching_recipes.append(recipe)
            
            # Сортируем по релевантности
            matching_recipes.sort(key=lambda r: self._calculate_relevance(r, query), reverse=True)
            
            total_count = len(matching_recipes)
            
            # Применяем пагинацию
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_recipes = matching_recipes[start_idx:end_idx]
            
            self.logger.info(f"Найдено рецептов: {total_count}, показано: {len(paginated_recipes)}")
            
            return paginated_recipes, total_count
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска рецептов: {e}")
            return [], 0
    
    def _recipe_matches_query(self, recipe: Dict[str, Any], query: str) -> bool:
        """
        Проверяет, соответствует ли рецепт поисковому запросу
        
        Args:
            recipe: Рецепт для проверки
            query: Поисковый запрос
            
        Returns:
            bool: True если рецепт соответствует запросу
        """
        # Проверяем название рецепта
        name = recipe.get('name', '').lower()
        if query in name:
            return True
        
        # Проверяем ингредиенты
        ingredients = recipe.get('ingredients', [])
        for ingredient in ingredients:
            if isinstance(ingredient, dict):
                ingredient_name = ingredient.get('name', '').lower()
            else:
                ingredient_name = str(ingredient).lower()
            
            if query in ingredient_name:
                return True
        
        # Проверяем инструкции
        instructions = recipe.get('instructions', '').lower()
        if query in instructions:
            return True
        
        # Проверяем теги
        tags = recipe.get('tags', [])
        for tag in tags:
            if query in str(tag).lower():
                return True
        
        return False
    
    def _calculate_relevance(self, recipe: Dict[str, Any], query: str) -> float:
        """
        Вычисляет релевантность рецепта для поискового запроса
        
        Args:
            recipe: Рецепт для оценки
            query: Поисковый запрос
            
        Returns:
            float: Оценка релевантности (больше = лучше)
        """
        relevance = 0.0
        
        # Название имеет наибольший вес
        name = recipe.get('name', '').lower()
        if query in name:
            relevance += 10.0
            # Точное совпадение в начале названия
            if name.startswith(query):
                relevance += 5.0
        
        # Ингредиенты имеют средний вес
        ingredients = recipe.get('ingredients', [])
        for ingredient in ingredients:
            if isinstance(ingredient, dict):
                ingredient_name = ingredient.get('name', '').lower()
            else:
                ingredient_name = str(ingredient).lower()
            
            if query in ingredient_name:
                relevance += 3.0
                # Точное совпадение ингредиента
                if ingredient_name == query:
                    relevance += 2.0
        
        # Инструкции имеют меньший вес
        instructions = recipe.get('instructions', '').lower()
        if query in instructions:
            relevance += 1.0
        
        # Теги имеют средний вес
        tags = recipe.get('tags', [])
        for tag in tags:
            tag_str = str(tag).lower()
            if query in tag_str:
                relevance += 2.0
        
        return relevance
    
    async def search_by_ingredients(self, ingredients: List[str], page: int = 1, per_page: int = 10) -> Tuple[List[Dict[str, Any]], int]:
        """
        Поиск рецептов по списку ингредиентов
        
        Args:
            ingredients: Список ингредиентов для поиска
            page: Номер страницы
            per_page: Количество результатов на странице
            
        Returns:
            Tuple[List[Dict], int]: (рецепты, общее количество)
        """
        if not ingredients:
            return [], 0
        
        self.logger.info(f"Поиск рецептов по ингредиентам: {ingredients}")
        
        try:
            all_recipes = self.recipe_service.get_all_recipes()
            
            if not all_recipes:
                return [], 0
            
            # Фильтруем рецепты, которые содержат хотя бы один из ингредиентов
            matching_recipes = []
            
            for recipe in all_recipes:
                recipe_ingredients = self._extract_ingredient_names(recipe.get('ingredients', []))
                
                # Проверяем, есть ли пересечение ингредиентов
                common_ingredients = set(ingredients) & set(recipe_ingredients)
                if common_ingredients:
                    # Добавляем информацию о совпадающих ингредиентах
                    recipe_copy = recipe.copy()
                    recipe_copy['matching_ingredients'] = list(common_ingredients)
                    recipe_copy['match_count'] = len(common_ingredients)
                    matching_recipes.append(recipe_copy)
            
            # Сортируем по количеству совпадающих ингредиентов
            matching_recipes.sort(key=lambda r: r.get('match_count', 0), reverse=True)
            
            total_count = len(matching_recipes)
            
            # Применяем пагинацию
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_recipes = matching_recipes[start_idx:end_idx]
            
            self.logger.info(f"Найдено рецептов по ингредиентам: {total_count}")
            
            return paginated_recipes, total_count
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска по ингредиентам: {e}")
            return [], 0
    
    def _extract_ingredient_names(self, ingredients: List[Any]) -> List[str]:
        """
        Извлекает названия ингредиентов из списка
        
        Args:
            ingredients: Список ингредиентов
            
        Returns:
            List[str]: Список названий ингредиентов
        """
        names = []
        
        for ingredient in ingredients:
            if isinstance(ingredient, dict):
                name = ingredient.get('name', '').strip()
            else:
                name = str(ingredient).strip()
            
            if name:
                names.append(name.lower())
        
        return names
    
    async def get_popular_recipes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получает популярные рецепты (для демонстрации)
        
        Args:
            limit: Максимальное количество рецептов
            
        Returns:
            List[Dict]: Список популярных рецептов
        """
        try:
            all_recipes = self.recipe_service.get_all_recipes()
            
            if not all_recipes:
                return []
            
            # Простая логика: берем первые N рецептов
            # В будущем можно добавить логику на основе просмотров/оценок
            popular_recipes = all_recipes[:limit]
            
            self.logger.info(f"Получено популярных рецептов: {len(popular_recipes)}")
            
            return popular_recipes
            
        except Exception as e:
            self.logger.error(f"Ошибка получения популярных рецептов: {e}")
            return []
    
    async def get_recent_recipes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получает недавно добавленные рецепты
        
        Args:
            limit: Максимальное количество рецептов
            
        Returns:
            List[Dict]: Список недавних рецептов
        """
        try:
            all_recipes = self.recipe_service.get_all_recipes()
            
            if not all_recipes:
                return []
            
            # Сортируем по дате добавления (если есть)
            # Пока просто берем последние добавленные
            recent_recipes = all_recipes[-limit:]
            
            self.logger.info(f"Получено недавних рецептов: {len(recent_recipes)}")
            
            return recent_recipes
            
        except Exception as e:
            self.logger.error(f"Ошибка получения недавних рецептов: {e}")
            return [] 