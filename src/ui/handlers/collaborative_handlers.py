from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from typing import Callable, Any
from datetime import datetime

from src.services.data_service import DataService
from src.ui.handlers.callback_handler import CallbackHandler
from src.ui.messages_main import Messages
from src.ui.keyboards import KeyboardFactory
from src.ui.ui_service import ui_service

class CollaborativeHandlers:
    """
    Обработчики для совместной работы
    """
    
    def __init__(self, data_service: DataService):
        """
        Инициализация обработчиков
        
        Args:
            data_service: Сервис для работы с данными
        """
        self.data_service = data_service
    
    async def invite_collaborator(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Приглашает пользователя для совместной работы
        
        Args:
            update: Обновление от Telegram
            context: Контекст обработчика
        """
        if not update.effective_user or not update.message:
            return
        user_id = update.effective_user.id
        collaborator_id = context.args[0] if context.args else None
        
        if not collaborator_id:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=Messages["COLLABORATIVE"]["invite_error"],
                reply_markup=KeyboardFactory.get("back")
            )
            return
        
        # Получаем данные пользователя
        user_data = self.data_service.get_user_data(user_id)
        
        # Добавляем приглашение
        if 'collaborations' not in user_data:
            user_data['collaborations'] = []
        
        user_data['collaborations'].append({
            'collaborator_id': collaborator_id,
            'status': 'pending',
            'timestamp': datetime.now().isoformat()
        })
        
        # Сохраняем изменения
        self.data_service.save_user_data(user_id, user_data)
        
        # Получаем данные приглашенного пользователя
        collaborator_data = self.data_service.get_user_data(collaborator_id)
        
        # Добавляем приглашение в данные приглашенного
        if 'collaboration_invites' not in collaborator_data:
            collaborator_data['collaboration_invites'] = []
        
        collaborator_data['collaboration_invites'].append({
            'user_id': user_id,
            'status': 'pending',
            'timestamp': datetime.now().isoformat()
        })
        
        # Сохраняем изменения
        self.data_service.save_user_data(collaborator_id, collaborator_data)
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=Messages["COLLABORATIVE"]["invite_success"],
            reply_markup=KeyboardFactory.get("collaborative_menu")
        )
    
    async def accept_invite(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Принимает приглашение для совместной работы
        
        Args:
            update: Обновление от Telegram
            context: Контекст обработчика
        """
        if not update.effective_user or not update.message:
            return
        user_id = update.effective_user.id
        inviter_id = context.args[0] if context.args else None
        
        if not inviter_id:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=Messages["COLLABORATIVE"]["accept_error"],
                reply_markup=KeyboardFactory.get("back")
            )
            return
        
        # Получаем данные пользователя
        user_data = self.data_service.get_user_data(user_id)
        
        # Обновляем статус приглашения
        for invite in user_data.get('collaboration_invites', []):
            if invite['user_id'] == inviter_id and invite['status'] == 'pending':
                invite['status'] = 'accepted'
                invite['accepted_at'] = datetime.now().isoformat()
                break
        
        # Сохраняем изменения
        self.data_service.save_user_data(user_id, user_data)
        
        # Получаем данные пригласившего пользователя
        inviter_data = self.data_service.get_user_data(inviter_id)
        
        # Обновляем статус приглашения
        for collaboration in inviter_data.get('collaborations', []):
            if collaboration['collaborator_id'] == user_id and collaboration['status'] == 'pending':
                collaboration['status'] = 'accepted'
                collaboration['accepted_at'] = datetime.now().isoformat()
                break
        
        # Сохраняем изменения
        self.data_service.save_user_data(inviter_id, inviter_data)
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=Messages["COLLABORATIVE"]["accept_success"],
            reply_markup=KeyboardFactory.get("collaborative_menu")
        )
    
    async def reject_invite(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Отклоняет приглашение для совместной работы
        
        Args:
            update: Обновление от Telegram
            context: Контекст обработчика
        """
        if not update.effective_user or not update.message:
            return
        user_id = update.effective_user.id
        inviter_id = context.args[0] if context.args else None
        
        if not inviter_id:
            await ui_service._send_or_edit_message(
                update=update,
                context=context,
                text=Messages["COLLABORATIVE"]["reject_error"],
                reply_markup=KeyboardFactory.get("back")
            )
            return
        
        # Получаем данные пользователя
        user_data = self.data_service.get_user_data(user_id)
        
        # Обновляем статус приглашения
        for invite in user_data.get('collaboration_invites', []):
            if invite['user_id'] == inviter_id and invite['status'] == 'pending':
                invite['status'] = 'rejected'
                invite['rejected_at'] = datetime.now().isoformat()
                break
        
        # Сохраняем изменения
        self.data_service.save_user_data(user_id, user_data)
        
        # Получаем данные пригласившего пользователя
        inviter_data = self.data_service.get_user_data(inviter_id)
        
        # Обновляем статус приглашения
        for collaboration in inviter_data.get('collaborations', []):
            if collaboration['collaborator_id'] == user_id and collaboration['status'] == 'pending':
                collaboration['status'] = 'rejected'
                collaboration['rejected_at'] = datetime.now().isoformat()
                break
        
        # Сохраняем изменения
        self.data_service.save_user_data(inviter_id, inviter_data)
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=Messages["COLLABORATIVE"]["reject_success"],
            reply_markup=KeyboardFactory.get("collaborative_menu")
        )
    
    async def show_collaborations(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Показывает список совместных работ
        
        Args:
            update: Обновление от Telegram
            context: Контекст обработчика
        """
        if not update.effective_user or not update.message:
            return
        user_id = update.effective_user.id
        
        # Получаем данные пользователя
        user_data = self.data_service.get_user_data(user_id)
        
        # Формируем список совместных работ
        collaborations = user_data.get('collaborations', [])
        
        if not collaborations:
            text = "🤝 *Совместные работы*\n\nУ вас пока нет совместных работ."
        else:
            text = "🤝 *Совместные работы*\n\nВаши совместные работы:\n\n"
            for collab in collaborations:
                status_emoji = "⏳" if collab['status'] == 'pending' else "✅" if collab['status'] == 'accepted' else "❌"
                text += f"{status_emoji} Пользователь {collab['collaborator_id']} - {collab['status']}\n"
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=KeyboardFactory.get("collaborative_menu")
        )
    
    async def show_invites(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Показывает список приглашений
        
        Args:
            update: Обновление от Telegram
            context: Контекст обработчика
        """
        if not update.effective_user or not update.message:
            return
        user_id = update.effective_user.id
        
        # Получаем данные пользователя
        user_data = self.data_service.get_user_data(user_id)
        
        # Формируем список приглашений
        invites = user_data.get('collaboration_invites', [])
        
        if not invites:
            text = "📨 *Приглашения*\n\nУ вас нет новых приглашений."
        else:
            text = "📨 *Приглашения*\n\nВаши приглашения:\n\n"
            for invite in invites:
                if invite['status'] == 'pending':
                    text += f"⏳ Приглашение от пользователя {invite['user_id']}\n"
        
        await ui_service._send_or_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=KeyboardFactory.get("collaborative_menu")
        )

def setup_collaborative_handlers(application: Application, data_service: DataService, callback_handler: CallbackHandler):
    """
    Настройка обработчиков для совместной работы
    
    Args:
        application: Приложение Telegram
        data_service: Сервис для работы с данными
        callback_handler: Обработчик callback-запросов
    """
    collaborative_handlers = CollaborativeHandlers(data_service)
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("invite", collaborative_handlers.invite_collaborator))
    application.add_handler(CommandHandler("accept", collaborative_handlers.accept_invite))
    application.add_handler(CommandHandler("reject", collaborative_handlers.reject_invite))
    application.add_handler(CommandHandler("collaborations", collaborative_handlers.show_collaborations))
    application.add_handler(CommandHandler("invites", collaborative_handlers.show_invites))
    
    # Обработчики колбэков
    application.add_handler(CallbackQueryHandler(
        callback_handler.handle_collaborative_callback,
        pattern="^collaborative:"
    ))
