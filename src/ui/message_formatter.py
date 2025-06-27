"""
Базовый класс для форматирования сообщений
"""

from typing import Optional, Dict, Any
from telegram import InlineKeyboardMarkup
from src.ui.navigation import NavigationManager, NavigationSection

class MessageFormatter:
    """Базовый класс для форматирования сообщений"""
    
    def __init__(self):
        """Инициализация форматтера сообщений"""
        self.navigation = NavigationManager()
    
    def format_message(
        self,
        text: str,
        section: Optional[NavigationSection] = None,
        keyboard: Optional[InlineKeyboardMarkup] = None,
        tip: Optional[str] = None,
        error: Optional[str] = None,
        success: Optional[str] = None,
        warning: Optional[str] = None,
        info: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Форматирует сообщение с дополнительными элементами
        
        Args:
            text: Основной текст сообщения
            section: Раздел навигации
            keyboard: Клавиатура
            tip: Подсказка
            error: Сообщение об ошибке
            success: Сообщение об успехе
            warning: Предупреждение
            info: Информационное сообщение
            **kwargs: Дополнительные параметры
            
        Returns:
            Dict[str, Any]: Отформатированное сообщение
        """
        formatted_text = text
        
        # Добавляем хлебные крошки
        if section:
            formatted_text = f"{self.navigation.get_breadcrumbs(section)}\n\n{formatted_text}"
        
        # Добавляем подсказку
        if tip:
            formatted_text += f"\n\n💡 *Совет:*\n{tip}"
        
        # Добавляем сообщения
        if error:
            formatted_text += f"\n\n❌ *Ошибка:*\n{error}"
        if success:
            formatted_text += f"\n\n✅ *Успех:*\n{success}"
        if warning:
            formatted_text += f"\n\n⚠️ *Внимание:*\n{warning}"
        if info:
            formatted_text += f"\n\nℹ️ *Информация:*\n{info}"
        
        # Форматируем дополнительные параметры
        if kwargs:
            formatted_text = formatted_text.format(**kwargs)
        
        return {
            'text': formatted_text,
            'reply_markup': keyboard or (self.navigation.get_section_keyboard(section) if section else None),
            'parse_mode': 'Markdown'
        }
    
    def format_error(self, error: str, section: Optional[NavigationSection] = None) -> Dict[str, Any]:
        """
        Форматирует сообщение об ошибке
        
        Args:
            error: Текст ошибки
            section: Раздел навигации
            
        Returns:
            Dict[str, Any]: Отформатированное сообщение об ошибке
        """
        return self.format_message(
            text="❌ *Произошла ошибка*",
            section=section,
            error=error
        )
    
    def format_success(self, message: str, section: Optional[NavigationSection] = None) -> Dict[str, Any]:
        """
        Форматирует сообщение об успехе
        
        Args:
            message: Текст сообщения
            section: Раздел навигации
            
        Returns:
            Dict[str, Any]: Отформатированное сообщение об успехе
        """
        return self.format_message(
            text="✅ *Успешно*",
            section=section,
            success=message
        )
    
    def format_warning(self, message: str, section: Optional[NavigationSection] = None) -> Dict[str, Any]:
        """
        Форматирует предупреждение
        
        Args:
            message: Текст предупреждения
            section: Раздел навигации
            
        Returns:
            Dict[str, Any]: Отформатированное предупреждение
        """
        return self.format_message(
            text="⚠️ *Внимание*",
            section=section,
            warning=message
        )
    
    def format_info(self, message: str, section: Optional[NavigationSection] = None) -> Dict[str, Any]:
        """
        Форматирует информационное сообщение
        
        Args:
            message: Текст сообщения
            section: Раздел навигации
            
        Returns:
            Dict[str, Any]: Отформатированное информационное сообщение
        """
        return self.format_message(
            text="ℹ️ *Информация*",
            section=section,
            info=message
        ) 