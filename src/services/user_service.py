from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json
from pathlib import Path
from src.utils.error_handler import ErrorHandler, ValidationError, NotFoundError
from src.cache import (
    cache_result,
    invalidate_cache,
)
from src.cache.constants import CACHE_KEYS, CACHE_TTL, CACHE_PREFIXES

logger = logging.getLogger(__name__)

class UserService:
    """
    Сервис для работы с пользователями.
    Обеспечивает полный функционал создания, редактирования, поиска и управления пользователями.
    """
    
    def __init__(self, users_file: Optional[Path] = None):
        """
        Инициализация сервиса
        :param users_file: путь к JSON-файлу пользователей (для тестов)
        """
        self.data_dir = Path("data")
        self.users_file = users_file if users_file is not None else self.data_dir / "users.json"
        
        # Загружаем данные
        self._load_data()
    
    def _load_data(self) -> None:
        """
        Загрузка данных из JSON-файла
        """
        try:
            if self.users_file.exists():
                with open(self.users_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.users = data.get("users", [])
            else:
                self.users = []
            
            logger.info("✅ Данные пользователей успешно загружены")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки данных пользователей: {e}")
            self.users = []
    
    def _save_data(self) -> None:
        """
        Сохранение данных в JSON-файл
        """
        try:
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump({
                    "users": self.users,
                    "last_update": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=4)
            
            logger.info("✅ Данные пользователей успешно сохранены")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения данных пользователей: {e}")
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['users'],
        ttl=CACHE_TTL['users'],
        prefix=CACHE_PREFIXES['users']
    )
    async def get_users(self) -> List[Dict[str, Any]]:
        """
        Получает список пользователей
        
        Returns:
            list: Список пользователей
        """
        return self.users
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['user'],
        ttl=CACHE_TTL['user'],
        prefix=CACHE_PREFIXES['user']
    )
    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """
        Получает пользователя по ID
        
        Args:
            user_id: ID пользователя
            
        Returns:
            dict: Данные пользователя
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        for user in self.users:
            if user["id"] == user_id:
                return user
        raise NotFoundError(f"❌ Пользователь с ID {user_id} не найден")
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['user_by_username'],
        ttl=CACHE_TTL['user'],
        prefix=CACHE_PREFIXES['user']
    )
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по имени пользователя
        
        Args:
            username: Имя пользователя
            
        Returns:
            Optional[dict]: Данные пользователя или None
        """
        for user in self.users:
            if user["username"].lower() == username.lower():
                return user
        return None
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['users'],
        prefix=CACHE_PREFIXES['users']
    )
    async def add_user(self, username: str, first_name: Optional[str] = None, last_name: Optional[str] = None) -> int:
        """
        Добавляет нового пользователя
        
        Args:
            username: Имя пользователя
            first_name: Имя
            last_name: Фамилия
            
        Returns:
            int: ID нового пользователя
            
        Raises:
            ValidationError: Если пользователь с таким именем уже существует
        """
        # Проверяем существование пользователя
        existing = await self.get_user_by_username(username)
        if existing:
            raise ValidationError(f"❌ Пользователь с именем '{username}' уже существует")
        
        # Создаем нового пользователя
        new_id = max([user["id"] for user in self.users], default=0) + 1
        new_user: dict = {
            "id": new_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "preferences": {
                "language": "ru",
                "notifications": True,
                "theme": "light"
            },
            "favorites": [],
            "history": [],
            "allergies": [],
            "restrictions": []
        }
        
        # Добавляем пользователя
        self.users.append(new_user)
        
        # Сохраняем данные
        self._save_data()
        
        return new_id
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['user'],
        prefix=CACHE_PREFIXES['user']
    )
    async def update_user(self, user_id: int, data: Dict[str, Any]) -> bool:
        """
        Обновляет пользователя
        
        Args:
            user_id: ID пользователя
            data: Новые данные
            
        Returns:
            bool: True если обновление успешно
            
        Raises:
            NotFoundError: Если пользователь не найден
            ValidationError: Если пользователь с таким именем уже существует
        """
        # Проверяем существование пользователя
        user = await self.get_user(user_id)
        if not user:
            raise NotFoundError(f"❌ Пользователь с ID {user_id} не найден")
        
        # Проверяем новое имя пользователя
        if "username" in data:
            existing = await self.get_user_by_username(data["username"])
            if existing and existing["id"] != user_id:
                raise ValidationError(f"❌ Пользователь с именем '{data['username']}' уже существует")
        
        # Обновляем данные
        user.update(data)
        user["updated_at"] = datetime.now().isoformat()
        
        # Сохраняем данные
        self._save_data()
        
        return True
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['user'],
        prefix=CACHE_PREFIXES['user']
    )
    async def delete_user(self, user_id: int) -> bool:
        """
        Удаляет пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если удаление успешно
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        # Проверяем существование пользователя
        user = await self.get_user(user_id)
        if not user:
            raise NotFoundError(f"❌ Пользователь с ID {user_id} не найден")
        
        # Удаляем пользователя
        self.users = [u for u in self.users if u["id"] != user_id]
        
        # Сохраняем данные
        self._save_data()
        
        return True
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['user_preferences'],
        ttl=CACHE_TTL['user'],
        prefix=CACHE_PREFIXES['user']
    )
    async def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Получает настройки пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            dict: Настройки пользователя
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        return user.get("preferences", {})
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['user_preferences'],
        prefix=CACHE_PREFIXES['user']
    )
    async def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """
        Обновляет настройки пользователя
        
        Args:
            user_id: ID пользователя
            preferences: Новые настройки
            
        Returns:
            bool: True если обновление успешно
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        user["preferences"].update(preferences)
        user["updated_at"] = datetime.now().isoformat()
        
        # Сохраняем данные
        self._save_data()
        
        return True
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['user_favorites'],
        ttl=CACHE_TTL['user'],
        prefix=CACHE_PREFIXES['user']
    )
    async def get_user_favorites(self, user_id: int) -> List[int]:
        """
        Получает избранные рецепты пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            list: Список ID избранных рецептов
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        return user.get("favorites", [])
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['user_favorites'],
        prefix=CACHE_PREFIXES['user']
    )
    async def add_to_favorites(self, user_id: int, recipe_id: int) -> bool:
        """
        Добавляет рецепт в избранное
        
        Args:
            user_id: ID пользователя
            recipe_id: ID рецепта
            
        Returns:
            bool: True если добавление успешно
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        if recipe_id not in user["favorites"]:
            user["favorites"].append(recipe_id)
            user["updated_at"] = datetime.now().isoformat()
            
            # Сохраняем данные
            self._save_data()
        
        return True
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['user_favorites'],
        prefix=CACHE_PREFIXES['user']
    )
    async def remove_from_favorites(self, user_id: int, recipe_id: int) -> bool:
        """
        Удаляет рецепт из избранного
        
        Args:
            user_id: ID пользователя
            recipe_id: ID рецепта
            
        Returns:
            bool: True если удаление успешно
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        if recipe_id in user["favorites"]:
            user["favorites"].remove(recipe_id)
            user["updated_at"] = datetime.now().isoformat()
            
            # Сохраняем данные
            self._save_data()
        
        return True
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['user_history'],
        ttl=CACHE_TTL['user'],
        prefix=CACHE_PREFIXES['user']
    )
    async def get_user_history(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получает историю просмотров пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            list: История просмотров
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        return user.get("history", [])
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['user_history'],
        prefix=CACHE_PREFIXES['user']
    )
    async def add_to_history(self, user_id: int, recipe_id: int) -> bool:
        """
        Добавляет рецепт в историю просмотров
        
        Args:
            user_id: ID пользователя
            recipe_id: ID рецепта
            
        Returns:
            bool: True если добавление успешно
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        
        # Добавляем запись в историю
        history_entry = {
            "recipe_id": recipe_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Удаляем старую запись с таким же recipe_id, если она есть
        user["history"] = [h for h in user["history"] if h["recipe_id"] != recipe_id]
        
        # Добавляем новую запись в начало списка
        user["history"].insert(0, history_entry)
        
        # Ограничиваем историю последними 50 записями
        user["history"] = user["history"][:50]
        
        user["updated_at"] = datetime.now().isoformat()
        
        # Сохраняем данные
        self._save_data()
        
        return True
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['user_history'],
        prefix=CACHE_PREFIXES['user']
    )
    async def clear_history(self, user_id: int) -> bool:
        """
        Очищает историю просмотров пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если очистка успешна
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        user["history"] = []
        user["updated_at"] = datetime.now().isoformat()
        
        # Сохраняем данные
        self._save_data()
        
        return True
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['user_allergies'],
        ttl=CACHE_TTL['user'],
        prefix=CACHE_PREFIXES['user']
    )
    async def get_user_allergies(self, user_id: int) -> List[str]:
        """
        Получает список аллергий пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            list: Список аллергий
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        return user.get("allergies", [])
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['user_allergies'],
        prefix=CACHE_PREFIXES['user']
    )
    async def add_allergy(self, user_id: int, allergy: str) -> bool:
        """
        Добавляет аллергию в список пользователя
        
        Args:
            user_id: ID пользователя
            allergy: Название аллергии
            
        Returns:
            bool: True если добавление успешно
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        if allergy not in user["allergies"]:
            user["allergies"].append(allergy)
            user["updated_at"] = datetime.now().isoformat()
            
            # Сохраняем данные
            self._save_data()
        
        return True
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['user_allergies'],
        prefix=CACHE_PREFIXES['user']
    )
    async def remove_allergy(self, user_id: int, allergy: str) -> bool:
        """
        Удаляет аллергию из списка пользователя
        
        Args:
            user_id: ID пользователя
            allergy: Название аллергии
            
        Returns:
            bool: True если удаление успешно
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        if allergy in user["allergies"]:
            user["allergies"].remove(allergy)
            user["updated_at"] = datetime.now().isoformat()
            
            # Сохраняем данные
            self._save_data()
        
        return True
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['user_restrictions'],
        ttl=CACHE_TTL['user'],
        prefix=CACHE_PREFIXES['user']
    )
    async def get_user_restrictions(self, user_id: int) -> List[str]:
        """
        Получает список ограничений пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            list: Список ограничений
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        return user.get("restrictions", [])
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['user_restrictions'],
        prefix=CACHE_PREFIXES['user']
    )
    async def add_restriction(self, user_id: int, restriction: str) -> bool:
        """
        Добавляет ограничение в список пользователя
        
        Args:
            user_id: ID пользователя
            restriction: Название ограничения
            
        Returns:
            bool: True если добавление успешно
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        if restriction not in user["restrictions"]:
            user["restrictions"].append(restriction)
            user["updated_at"] = datetime.now().isoformat()
            
            # Сохраняем данные
            self._save_data()
        
        return True
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['user_restrictions'],
        prefix=CACHE_PREFIXES['user']
    )
    async def remove_restriction(self, user_id: int, restriction: str) -> bool:
        """
        Удаляет ограничение из списка пользователя
        
        Args:
            user_id: ID пользователя
            restriction: Название ограничения
            
        Returns:
            bool: True если удаление успешно
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        user = await self.get_user(user_id)
        if restriction in user["restrictions"]:
            user["restrictions"].remove(restriction)
            user["updated_at"] = datetime.now().isoformat()
            
            # Сохраняем данные
            self._save_data()
        
        return True 