"""
Фабрика сообщений для EatBot
Централизованное управление текстами с поддержкой форматирования и локализации
"""
import logging
from typing import Dict, Any, Optional
from src.ui.messages_main import Messages

logger = logging.getLogger(__name__)

class MessageFactory:
    """Фабрика для создания сообщений с форматированием"""
    
    @classmethod
    def get(cls, message_type: str, **params) -> str:
        """
        Получает сообщение по типу с форматированием
        
        Args:
            message_type: Тип сообщения в формате section.subsection
            **params: Параметры для форматирования
        """
        try:
            # Разбираем тип сообщения (например, "RECIPES.menu" -> ["RECIPES", "menu"])
            parts = message_type.split('.')
            if len(parts) != 2:
                raise ValueError(f"Invalid message type format: {message_type}. Use 'section.subsection'")
            
            section, subsection = parts
            
            # Получаем сообщение из словаря
            if section not in Messages:
                raise ValueError(f"Unknown message section: {section}")
            
            section_messages = Messages[section]
            if not isinstance(section_messages, dict):
                raise ValueError(f"Section {section} is not a dictionary")
            
            if subsection not in section_messages:
                raise ValueError(f"Unknown message subsection: {subsection} in section {section}")
            
            message_template = section_messages[subsection]
            
            # Форматируем сообщение с параметрами
            if params:
                try:
                    return message_template.format(**params)
                except KeyError as e:
                    logger.warning(f"Missing parameter {e} for message {message_type}")
                    return message_template
            else:
                return message_template
                
        except Exception as e:
            logger.error(f"Error getting message {message_type}: {e}")
            return cls._get_fallback_message(message_type, params)
    
    @classmethod
    def get_main_menu(cls, first_name: str = "пользователь") -> str:
        """Получает сообщение главного меню"""
        return cls.get("MAIN.menu", first_name=first_name)
    
    @classmethod
    def get_welcome(cls) -> str:
        """Получает приветственное сообщение"""
        return cls.get("MAIN.welcome")
    
    @classmethod
    def get_help(cls) -> str:
        """Получает сообщение справки"""
        return cls.get("MAIN.help")
    
    @classmethod
    def get_recipe_menu(cls) -> str:
        """Получает сообщение меню рецептов"""
        return cls.get("RECIPES.menu")
    
    @classmethod
    def get_recipe_search(cls) -> str:
        """Получает сообщение поиска рецептов"""
        return cls.get("RECIPES.search")
    
    @classmethod
    def get_recipe_add(cls) -> str:
        """Получает сообщение добавления рецепта"""
        return cls.get("RECIPES.add")
    
    @classmethod
    def get_recipe_add_success(cls, recipe_name: str) -> str:
        """Получает сообщение успешного добавления рецепта"""
        return cls.get("RECIPES.add_success", recipe_name=recipe_name)
    
    @classmethod
    def get_recipe_delete_confirm(cls, recipe_name: str) -> str:
        """Получает сообщение подтверждения удаления рецепта"""
        return cls.get("RECIPES.delete_confirm", recipe_name=recipe_name)
    
    @classmethod
    def get_recipe_delete_success(cls, recipe_name: str) -> str:
        """Получает сообщение успешного удаления рецепта"""
        return cls.get("RECIPES.delete_success", recipe_name=recipe_name)
    
    @classmethod
    def get_recipe_not_found(cls) -> str:
        """Получает сообщение о ненайденном рецепте"""
        return cls.get("RECIPES.not_found")
    
    @classmethod
    def get_products_menu(cls) -> str:
        """Получает сообщение меню продуктов"""
        return cls.get("PRODUCTS.menu")
    
    @classmethod
    def get_products_search(cls) -> str:
        """Получает сообщение поиска продуктов"""
        return cls.get("PRODUCTS.search")
    
    @classmethod
    def get_products_add(cls) -> str:
        """Получает сообщение добавления продукта"""
        return cls.get("PRODUCTS.add")
    
    @classmethod
    def get_products_search_not_found(cls, product_name: str) -> str:
        """Получает сообщение о ненайденном продукте"""
        return cls.get("PRODUCTS.search_not_found", product_name=product_name)
    
    @classmethod
    def get_products_add_success(cls, product_name: str) -> str:
        """Получает сообщение успешного добавления продукта"""
        return cls.get("PRODUCTS.add_success", product_name=product_name)
    
    @classmethod
    def get_products_search_success(cls, count: int, products_list: str) -> str:
        """Получает сообщение успешного поиска продуктов"""
        return cls.get("PRODUCTS.search_success", count=count, products_list=products_list)
    
    @classmethod
    def get_products_delete_confirm(cls, product_name: str) -> str:
        """Получает сообщение подтверждения удаления продукта"""
        return cls.get("PRODUCTS.delete_confirm", product_name=product_name)
    
    @classmethod
    def get_products_delete_success(cls, product_name: str) -> str:
        """Получает сообщение успешного удаления продукта"""
        return cls.get("PRODUCTS.delete_success", product_name=product_name)
    
    @classmethod
    def get_collaborative_menu(cls) -> str:
        """Получает сообщение меню совместной работы"""
        return cls.get("COLLABORATIVE.menu")
    
    @classmethod
    def get_navigation_back(cls) -> str:
        """Получает сообщение кнопки 'Назад'"""
        return cls.get("NAVIGATION.back")
    
    @classmethod
    def get_navigation_main_menu(cls) -> str:
        """Получает сообщение кнопки 'Главное меню'"""
        return cls.get("NAVIGATION.main_menu")
    
    @classmethod
    def get_navigation_cancel(cls) -> str:
        """Получает сообщение кнопки 'Отмена'"""
        return cls.get("NAVIGATION.cancel")
    
    @classmethod
    def get_navigation_confirm(cls) -> str:
        """Получает сообщение кнопки 'Подтверждение'"""
        return cls.get("NAVIGATION.confirm")
    
    @classmethod
    def get_error(cls, error_type: str = "error", **params) -> str:
        """Получает сообщение об ошибке"""
        return cls.get(f"ERRORS.{error_type}", **params)
    
    @classmethod
    def get_success(cls, success_type: str = "operation_completed", **params) -> str:
        """Получает сообщение об успехе"""
        return cls.get(f"SUCCESS.{success_type}", **params)
    
    @classmethod
    def get_conversation(cls, conv_type: str, **params) -> str:
        """Получает сообщение для диалогов"""
        return cls.get(f"CONVERSATION.{conv_type}", **params)
    
    @classmethod
    def get_welcome_full(cls) -> str:
        """Получает полное приветственное сообщение"""
        return cls.get("WELCOME")
    
    @classmethod
    def _get_fallback_message(cls, message_type: str, params: Dict[str, Any]) -> str:
        """Получает резервное сообщение при ошибке"""
        logger.warning(f"Using fallback message for {message_type}")
        
        if "error" in message_type.lower():
            return "❌ Произошла ошибка. Попробуйте еще раз."
        elif "success" in message_type.lower():
            return "✅ Операция выполнена успешно."
        elif "menu" in message_type.lower():
            return "📋 Меню"
        else:
            return f"💬 Сообщение: {message_type}"
    
    @classmethod
    def format_with_emoji(cls, text: str, emoji: str = "💬") -> str:
        """Добавляет эмодзи к тексту"""
        return f"{emoji} {text}"
    
    @classmethod
    def format_error(cls, error_message: str) -> str:
        """Форматирует сообщение об ошибке"""
        return cls.format_with_emoji(error_message, "❌")
    
    @classmethod
    def format_success(cls, success_message: str) -> str:
        """Форматирует сообщение об успехе"""
        return cls.format_with_emoji(success_message, "✅")
    
    @classmethod
    def format_info(cls, info_message: str) -> str:
        """Форматирует информационное сообщение"""
        return cls.format_with_emoji(info_message, "ℹ️")
    
    @classmethod
    def format_warning(cls, warning_message: str) -> str:
        """Форматирует предупреждающее сообщение"""
        return cls.format_with_emoji(warning_message, "⚠️") 