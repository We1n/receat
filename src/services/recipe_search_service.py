from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from src.utils.cache import cache
from src.exceptions.base import AppError
from src.services.recipe_service import RecipeService

logger = logging.getLogger(__name__)

class RecipeSearchService:
    """Сервис для поиска рецептов"""
    
    def __init__(self, recipe_service: RecipeService):
        """
        Инициализация сервиса поиска рецептов
        
        Args:
            recipe_service: Сервис для работы с рецептами
        """
        self.recipe_service = recipe_service
        self.min_similarity = 80
    
    @cache(ttl=300)  # Кэшируем на 5 минут
    async def search_recipes(
        self, 
        query: str, 
        page: int = 1, 
        per_page: int = 5, 
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = 'relevance',
        sort_order: str = 'desc'
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Поиск рецептов с пагинацией и фильтрами
        
        Args:
            query: Поисковый запрос
            page: Номер страницы
            per_page: Количество рецептов на странице
            filters: Словарь с фильтрами
            sort_by: Поле для сортировки (relevance, calories, cooking_time, created_at)
            sort_order: Порядок сортировки (asc, desc)
            
        Returns:
            tuple: (список рецептов, общее количество рецептов)
        """
        try:
            # Получаем все рецепты
            recipes = self.recipe_service.get_all_recipes()
            
            logger.info(f"[Поиск рецептов] Получено рецептов: {len(recipes)}")
            if recipes:
                logger.info(f"[Поиск рецептов] Пример рецепта: {recipes[0]}")
            
            # Фильтруем рецепты по запросу с учетом нечеткого поиска
            filtered_recipes = []
            for recipe in recipes:
                # Проверяем совпадение в названии
                title_similarity = fuzz.ratio(query.lower(), recipe.get('name', '').lower())
                # Проверяем совпадение в описании
                desc_similarity = fuzz.ratio(query.lower(), recipe.get('description', '').lower())
                # Проверяем совпадение в ингредиентах
                ing_similarities = [
                    fuzz.ratio(query.lower(), ing.get('name', '').lower())
                    for ing in recipe.get('ingredients', [])
                ]
                
                # Если есть совпадение выше порога
                if (title_similarity >= self.min_similarity or
                    desc_similarity >= self.min_similarity or
                    any(sim >= self.min_similarity for sim in ing_similarities)):
                    filtered_recipes.append(recipe)
            
            # Применяем дополнительные фильтры
            if filters:
                filtered_recipes = self._apply_filters(filtered_recipes, filters)
            
            # Сортируем результаты
            filtered_recipes = self._sort_recipes(filtered_recipes, sort_by, sort_order, query)
            
            # Применяем пагинацию
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_recipes = filtered_recipes[start_idx:end_idx]
            
            return paginated_recipes, len(filtered_recipes)
            
        except Exception as e:
            logger.exception(f"Ошибка при поиске рецептов: {e}")
            raise AppError(message=f"Ошибка при поиске рецептов: {e}", error_code="RECIPE_SEARCH_FAILED")
    
    def _apply_filters(self, recipes: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Применение фильтров к списку рецептов
        
        Args:
            recipes: Список рецептов
            filters: Словарь с фильтрами
            
        Returns:
            List[Dict]: Отфильтрованный список рецептов
        """
        filtered = recipes.copy()
        
        if 'difficulty' in filters:
            filtered = [
                r for r in filtered 
                if r['difficulty'] == filters['difficulty']
            ]
            
        if 'max_calories' in filters:
            filtered = [
                r for r in filtered 
                if r['calories'] <= filters['max_calories']
            ]
            
        if 'min_calories' in filters:
            filtered = [
                r for r in filtered 
                if r['calories'] >= filters['min_calories']
            ]
            
        if 'max_cooking_time' in filters:
            filtered = [
                r for r in filtered 
                if r['cooking_time'] <= filters['max_cooking_time']
            ]
            
        if 'min_cooking_time' in filters:
            filtered = [
                r for r in filtered 
                if r['cooking_time'] >= filters['min_cooking_time']
            ]
            
        if 'categories' in filters:
            filtered = [
                r for r in filtered 
                if any(cat in r['categories'] for cat in filters['categories'])
            ]
            
        if 'ingredients' in filters:
            filtered = [
                r for r in filtered 
                if all(
                    any(
                        fuzz.ratio(ing.get('name', '').lower(), req_ing.lower()) >= self.min_similarity
                        for ing in r.get('ingredients', [])
                    )
                    for req_ing in filters['ingredients']
                )
            ]
            
        return filtered
    
    def _sort_recipes(
        self,
        recipes: List[Dict[str, Any]],
        sort_by: str,
        sort_order: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Сортировка рецептов
        
        Args:
            recipes: Список рецептов
            sort_by: Поле для сортировки
            sort_order: Порядок сортировки
            query: Поисковый запрос
            
        Returns:
            List[Dict]: Отсортированный список рецептов
        """
        if sort_by == 'relevance':
            # Сортируем по релевантности
            recipes.sort(
                key=lambda x: (
                    fuzz.ratio(query.lower(), x.get('name', '').lower()) * 2 +
                    fuzz.ratio(query.lower(), x.get('description', '').lower()) +
                    sum(
                        fuzz.ratio(query.lower(), ing.get('name', '').lower())
                        for ing in x.get('ingredients', [])
                    )
                ),
                reverse=(sort_order == 'desc')
            )
        elif sort_by == 'calories':
            recipes.sort(
                key=lambda x: x['calories'],
                reverse=(sort_order == 'desc')
            )
        elif sort_by == 'cooking_time':
            recipes.sort(
                key=lambda x: x['cooking_time'],
                reverse=(sort_order == 'desc')
            )
        elif sort_by == 'created_at':
            recipes.sort(
                key=lambda x: x['created_at'],
                reverse=(sort_order == 'desc')
            )
            
        return recipes
    
    @cache(ttl=300)  # Кэшируем на 5 минут
    async def get_recipe_by_id(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение рецепта по ID
        
        Args:
            recipe_id: ID рецепта
            
        Returns:
            Рецепт или None, если не найден
        """
        try:
            return await self.recipe_service.get_recipe_by_id(recipe_id)
        except Exception as e:
            logger.error(f"Ошибка при получении рецепта: {e}")
            raise AppError(f"Ошибка при получении рецепта: {e}", error_code="RECIPE_SEARCH_FAILED")
    
    @cache(ttl=300)  # Кэшируем на 5 минут
    async def get_recipes_by_ingredients(
        self,
        ingredients: List[str],
        page: int = 1,
        per_page: int = 5
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Поиск рецептов по ингредиентам
        
        Args:
            ingredients: Список ингредиентов
            page: Номер страницы
            per_page: Количество рецептов на странице
            
        Returns:
            tuple: (список рецептов, общее количество рецептов)
        """
        try:
            # Получаем все рецепты
            recipes = self.recipe_service.get_all_recipes()
            
            # Фильтруем рецепты по ингредиентам с учетом нечеткого поиска
            filtered_recipes = []
            for recipe in recipes:
                recipe_ingredients = [ing.get('name', '').lower() for ing in recipe.get('ingredients', [])]
                if all(
                    any(
                        fuzz.ratio(req_ing.lower(), ing) >= self.min_similarity
                        for ing in recipe_ingredients
                    )
                    for req_ing in ingredients
                ):
                    filtered_recipes.append(recipe)
            
            # Применяем пагинацию
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_recipes = filtered_recipes[start_idx:end_idx]
            
            return paginated_recipes, len(filtered_recipes)
            
        except Exception as e:
            logger.error(f"Ошибка при поиске рецептов по ингредиентам: {e}")
            raise AppError(message=f"Ошибка при поиске рецептов по ингредиентам: {e}", error_code="RECIPE_SEARCH_FAILED")
    
    @cache(ttl=300)  # Кэшируем на 5 минут
    async def get_recipes_by_difficulty(
        self,
        difficulty: str,
        page: int = 1,
        per_page: int = 5
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Поиск рецептов по сложности
        
        Args:
            difficulty: Сложность рецепта
            page: Номер страницы
            per_page: Количество рецептов на странице
            
        Returns:
            tuple: (список рецептов, общее количество рецептов)
        """
        try:
            # Получаем все рецепты
            recipes = self.recipe_service.get_all_recipes()
            
            # Фильтруем рецепты по сложности
            filtered_recipes = [
                recipe for recipe in recipes
                if fuzz.ratio(recipe['difficulty'].lower(), difficulty.lower()) >= self.min_similarity
            ]
            
            # Применяем пагинацию
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_recipes = filtered_recipes[start_idx:end_idx]
            
            return paginated_recipes, len(filtered_recipes)
            
        except Exception as e:
            logger.error(f"Ошибка при поиске рецептов по сложности: {e}")
            raise AppError(message=f"Ошибка при поиске рецептов по сложности: {e}", error_code="RECIPE_SEARCH_FAILED")
    
    @cache(ttl=300)  # Кэшируем на 5 минут
    async def get_recipes_by_cooking_time(
        self,
        min_time: Optional[int] = None,
        max_time: Optional[int] = None,
        page: int = 1,
        per_page: int = 5
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Поиск рецептов по времени приготовления
        
        Args:
            min_time: Минимальное время приготовления
            max_time: Максимальное время приготовления
            page: Номер страницы
            per_page: Количество рецептов на странице
            
        Returns:
            tuple: (список рецептов, общее количество рецептов)
        """
        try:
            # Получаем все рецепты
            recipes = self.recipe_service.get_all_recipes()
            
            # Фильтруем рецепты по времени приготовления
            filtered_recipes = recipes.copy()
            
            if min_time is not None:
                filtered_recipes = [
                    r for r in filtered_recipes
                    if r['cooking_time'] >= min_time
                ]
                
            if max_time is not None:
                filtered_recipes = [
                    r for r in filtered_recipes
                    if r['cooking_time'] <= max_time
                ]
            
            # Применяем пагинацию
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_recipes = filtered_recipes[start_idx:end_idx]
            
            return paginated_recipes, len(filtered_recipes)
            
        except Exception as e:
            logger.error(f"Ошибка при поиске рецептов по времени приготовления: {e}")
            raise AppError(message=f"Ошибка при поиске рецептов по времени приготовления: {e}", error_code="RECIPE_SEARCH_FAILED")
    
    @cache(ttl=300)  # Кэшируем на 5 минут
    async def get_recipes_by_calories(
        self,
        min_calories: Optional[int] = None,
        max_calories: Optional[int] = None,
        page: int = 1,
        per_page: int = 5
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Поиск рецептов по калорийности
        
        Args:
            min_calories: Минимальная калорийность
            max_calories: Максимальная калорийность
            page: Номер страницы
            per_page: Количество рецептов на странице
            
        Returns:
            tuple: (список рецептов, общее количество рецептов)
        """
        try:
            # Получаем все рецепты
            recipes = self.recipe_service.get_all_recipes()
            
            # Фильтруем рецепты по калорийности
            filtered_recipes = recipes.copy()
            
            if min_calories is not None:
                filtered_recipes = [
                    r for r in filtered_recipes
                    if r['calories'] >= min_calories
                ]
                
            if max_calories is not None:
                filtered_recipes = [
                    r for r in filtered_recipes
                    if r['calories'] <= max_calories
                ]
            
            # Применяем пагинацию
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_recipes = filtered_recipes[start_idx:end_idx]
            
            return paginated_recipes, len(filtered_recipes)
            
        except Exception as e:
            logger.error(f"Ошибка при поиске рецептов по калорийности: {e}")
            raise AppError(message=f"Ошибка при поиске рецептов по калорийности: {e}", error_code="RECIPE_SEARCH_FAILED") 