"""
Модуль конфигурации приложения

Этот модуль предоставляет функциональность для:
- Загрузки конфигурации из переменных окружения
- Настройки логирования
- Создания необходимых директорий
- Управления настройками приложения
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Отладочная информация
print(f"Текущая директория: {os.getcwd()}")
print(f"Файл .env существует: {os.path.exists('.env')}")
print(f"BOT_TOKEN из окружения: {os.getenv('BOT_TOKEN')}")

class Config:
    """Конфигурация приложения"""
    
    # Токен бота
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Настройки логирования
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
    LOG_MAX_FILES = int(os.getenv('LOG_MAX_FILES', 5))
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 5 * 1024 * 1024))  # 5MB
    
    # Настройки кэширования
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # Время жизни кэша в секундах
    CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', 1000))  # Максимальный размер кэша
    
    # Настройки мониторинга
    MONITOR_ENABLED = os.getenv('MONITOR_ENABLED', 'true').lower() == 'true'
    MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', 60))  # Интервал мониторинга в секундах
    
    # Настройки безопасности
    ADMIN_ID = int(os.getenv('ADMIN', '0'))  # ID администратора для мониторинга
    ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
    ALLOWED_USERS = [int(id) for id in os.getenv('ALLOWED_USERS', '').split(',') if id]
    
    # Настройки производительности
    MAX_CONNECTIONS = int(os.getenv('MAX_CONNECTIONS', 10))
    TIMEOUT = int(os.getenv('TIMEOUT', 30))
    
    # Настройки локализации
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'ru')
    SUPPORTED_LANGUAGES = os.getenv('SUPPORTED_LANGUAGES', 'ru,en').split(',')
    
    # Настройки темы
    DEFAULT_THEME = os.getenv('DEFAULT_THEME', 'light')
    SUPPORTED_THEMES = os.getenv('SUPPORTED_THEMES', 'light,dark,system').split(',')
    
    # Настройки кэширования пользователей
    USER_CACHE_TTL = int(os.getenv('USER_CACHE_TTL', '600'))  # 10 минут
    USER_CACHE_MAX_SIZE = int(os.getenv('USER_CACHE_MAX_SIZE', '1000'))  # Максимальное количество пользователей в кэше
    USER_CACHE_CLEANUP_INTERVAL = int(os.getenv('USER_CACHE_CLEANUP_INTERVAL', '300'))  # Интервал очистки кэша в секундах
    
    # Пути к директориям
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    USER_DATA_DIR = os.path.join(DATA_DIR, "user_data")
    RECIPES_DIR = os.path.join(DATA_DIR, "recipes")
    INGREDIENTS_DIR = os.path.join(DATA_DIR, "ingredients")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    
    # JSON файлы
    RECIPES_FILE = Path(os.path.join(DATA_DIR, "recipes.json"))
    USER_DATA_FILE = Path(os.path.join(USER_DATA_DIR, "user_data.json"))
    # SHOPPING_LISTS_FILE = Path(os.path.join(DATA_DIR, "shopping_lists.json"))  # УДАЛЕНО: функционал не реализован
    INGREDIENTS_FILE = Path(os.path.join(INGREDIENTS_DIR, "ingredients.json"))
    
    # Настройки планировщика питания
    TARGET_CALORIES_MIN = int(os.getenv('TARGET_CALORIES_MIN', 2000))
    TARGET_CALORIES_MAX = int(os.getenv('TARGET_CALORIES_MAX', 2200))
    
    # Создание директорий, если они не существуют
    @classmethod
    def create_dirs(cls):
        """Создание необходимых директорий"""
        dirs = [
            cls.DATA_DIR,
            cls.USER_DATA_DIR,
            cls.RECIPES_DIR,
            cls.INGREDIENTS_DIR,
            cls.LOG_DIR
        ]
        
        for directory in dirs:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logging.info(f"Создана директория: {directory}")
        
        # Создание JSON файлов, если они не существуют
        json_files = [
            cls.RECIPES_FILE,
            cls.USER_DATA_FILE,
            # cls.SHOPPING_LISTS_FILE,  # УДАЛЕНО: функционал не реализован
            cls.INGREDIENTS_FILE
        ]
        
        for json_file in json_files:
            if not json_file.exists():
                json_file.parent.mkdir(parents=True, exist_ok=True)
                with open(json_file, 'w', encoding='utf-8') as f:
                    f.write('{}')
                logging.info(f"Создан файл: {json_file}")

def get_bot_token() -> str:
    """Получение токена бота"""
    if not Config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")
    return Config.BOT_TOKEN

def setup_logging() -> None:
    """Настройка логирования"""
    # Создаем директорию для логов, если она не существует
    if not os.path.exists(Config.LOG_DIR):
        os.makedirs(Config.LOG_DIR)
    
    # Настраиваем формат логов
    formatter = logging.Formatter(Config.LOG_FORMAT)
    
    # Настраиваем файловый обработчик
    log_file = os.path.join(Config.LOG_DIR, Config.LOG_FILE)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_MAX_FILES
    )
    file_handler.setFormatter(formatter)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(Config.LOG_LEVEL)
    root_logger.addHandler(file_handler)
    
    logging.info("Логирование настроено")

# Создаем логгер для модуля
logger = logging.getLogger(__name__)

# Экспорт для совместимости с импортами
settings = Config  # ✅ Для модулей, которые ожидают settings 