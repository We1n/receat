# Основные сообщения бота
Messages = {
    "MAIN": {
        "menu": "👋 Привет, {first_name}!\n\n🏠 *Главное меню*\n\nЯ твой помощник по питанию. Выбери раздел, чтобы начать:",
        "welcome": "🤖 *Добро пожаловать в EatBot!*\n\nЯ помогу вам с рецептами и продуктами.",
        "help": "📚 *Справка*\n\nИспользуйте меню для навигации по функциям бота."
    },
    "RECIPES": {
        "menu": "📚 *Меню рецептов*\n\nВыберите действие:\n\n🔍 **Поиск** — найти рецепты по ингредиентам\n➕ **Добавить** — создать новый рецепт\n📋 **Мои рецепты** — просмотр сохраненных рецептов",
        "search": "🔍 *Поиск рецептов*\n\nВведите название или ингредиенты:\n\n💡 **Примеры:**\n• яйца\n• курица\n• овсянка\n\n🔙 Для отмены нажмите «Назад»",
        "add": "➕ *Добавление рецепта*\n\nВведите название рецепта:\n\n💡 **Советы:**\n• Используйте понятные названия\n• Минимум 3 символа\n• Избегайте специальных символов",
        "list": "📋 *Мои рецепты*\n\nЗдесь будут ваши сохраненные рецепты.",
        "add_success": "✅ *Рецепт добавлен!*\n\nРецепт «{recipe_name}» успешно сохранен.\n\n🔙 Вернуться в меню рецептов",
        "delete_confirm": "🗑️ *Подтверждение удаления*\n\nВы действительно хотите удалить рецепт «{recipe_name}»?\n\n⚠️ Это действие необратимо!",
        "delete_success": "✅ *Рецепт удален!*\n\nРецепт «{recipe_name}» успешно удален.\n\n🔙 Вернуться в меню рецептов",
        "not_found": "❌ *Рецепт не найден*\n\nЗапрашиваемый рецепт не найден или был удален.\n\n🔙 Вернуться в меню рецептов"
    },
    "PRODUCTS": {
        "menu": "🍏 *Меню продуктов*\n\nВыберите действие:\n\n🔍 **Поиск** — найти продукт по названию\n➕ **Добавить** — добавить новый продукт",
        "search": "🔍 *Поиск продукта*\n\nВведите название продукта для поиска:\n\n💡 **Примеры:**\n• яблоко\n• куриная грудка\n• овсянка\n\n🔙 Для отмены нажмите «Назад»",
        "add": "➕ *Добавление продукта*\n\nВведите информацию о продукте в формате:\n\n**Название:** [название продукта]\n**Калории:** [количество на 100г]\n**Белки:** [граммы на 100г]\n**Жиры:** [граммы на 100г]\n**Углеводы:** [граммы на 100г]\n\n💡 **Пример:**\nНазвание: Яблоко\nКалории: 52\nБелки: 0.4\nЖиры: 0.2\nУглеводы: 14",
        "search_not_found": "❌ *Ошибка поиска*\n\nПродукт «{product_name}» не найден.\n\n💡 Попробуйте:\n• Проверить написание\n• Использовать похожие названия\n• Добавить продукт, если его нет\n\n🔙 Вернуться в меню продуктов",
        "add_success": "✅ *Продукт добавлен!*\n\n{product_name} успешно добавлен в базу данных.\n\n🔙 Вернуться в меню продуктов",
        "search_success": "✅ *Поиск завершен!*\n\nНайдено {count} продуктов:\n\n{products_list}\n\n🔙 Вернуться в меню продуктов",
        "delete_confirm": "🗑️ *Подтверждение удаления*\n\nВы действительно хотите удалить продукт «{product_name}»?\n\n⚠️ Это действие необратимо!",
        "delete_success": "✅ *Продукт удален!*\n\nПродукт «{product_name}» успешно удален.\n\n🔙 Вернуться в меню продуктов"
    },
    "COLLABORATIVE": {
        "menu": "👥 *Совместная работа*\n\nВыберите действие:",
        "invite": "➕ *Приглашение*\n\nВведите ID пользователя для приглашения:",
        "list": "👥 *Мои коллаборации*\n\nВаши совместные проекты:",
        "join": "🤝 *Присоединение*\n\nВведите код приглашения:"
    },
    "NAVIGATION": {
        "back": "◀️ *Назад*\n\nВозврат в предыдущее меню.",
        "main_menu": "🏠 *Главное меню*\n\nВозврат в главное меню.",
        "cancel": "❌ *Отмена*\n\nОперация отменена.",
        "confirm": "✅ *Подтверждение*\n\nОперация подтверждена.",
        "error": "❌ *Ошибка*\n\nПроизошла ошибка. Попробуйте еще раз.",
        "success": "✅ *Успех*\n\nОперация выполнена успешно.",
        "loading": "⏳ *Загрузка*\n\nПожалуйста, подождите...",
        "not_found": "🔍 *Не найдено*\n\nЗапрашиваемые данные не найдены.",
        "empty": "📭 *Пусто*\n\nДанные отсутствуют.",
        "help": "❓ *Помощь*\n\nИспользуйте /help для получения справки."
    },
    "COMMON": {
        "back": "◀️ *Назад*\n\nВозврат в предыдущее меню.",
        "cancel": "❌ *Отмена*\n\nОперация отменена.",
        "confirm": "✅ *Подтверждение*\n\nОперация подтверждена.",
        "error": "❌ *Ошибка*\n\nПроизошла ошибка. Попробуйте еще раз.",
        "success": "✅ *Успех*\n\nОперация выполнена успешно.",
        "loading": "⏳ *Загрузка*\n\nПожалуйста, подождите...",
        "not_found": "🔍 *Не найдено*\n\nЗапрашиваемые данные не найдены.",
        "empty": "📭 *Пусто*\n\nДанные отсутствуют.",
        "help": "❓ *Помощь*\n\nИспользуйте /help для получения справки."
    },
    "ERRORS": {
        "not_found": "❌ *Не найдено*\n\nЗапрашиваемые данные не найдены.",
        "invalid_input": "❌ *Некорректный ввод*\n\n{correct_format}\n\n💡 **Пример:**\n{example}",
        "permission_denied": "❌ *Доступ запрещен*\n\nУ вас нет прав для выполнения этой операции.",
        "server_error": "❌ *Ошибка сервера*\n\nПроизошла внутренняя ошибка. Попробуйте позже.",
        "validation_error": "❌ *Ошибка валидации*\n\n{field}: {error}\n\n💡 Проверьте правильность ввода.",
        "network_error": "❌ *Ошибка сети*\n\nПроблема с подключением. Проверьте интернет и попробуйте снова."
    },
    "SUCCESS": {
        "created": "✅ *Создано*\n\nОбъект успешно создан.",
        "updated": "✅ *Обновлено*\n\nОбъект успешно обновлен.",
        "deleted": "✅ *Удалено*\n\nОбъект успешно удален.",
        "saved": "✅ *Сохранено*\n\nДанные успешно сохранены.",
        "operation_completed": "✅ *Операция завершена*\n\nДействие выполнено успешно."
    },
    "WELCOME": (
        "👋 Добро пожаловать в EatBot!\n\n"
        "Здесь вы можете добавлять и искать рецепты, вести списки покупок и получать советы по питанию.\n\n"
        "📋 Чтобы добавить рецепт, используйте следующий формат:\n"
        "- Сначала введите название рецепта.\n"
        "- Затем отправьте все ингредиенты списком, каждый ингредиент — с новой строки.\n"
        "- После ингредиентов сделайте пустую строку и напишите инструкцию (порядок приготовления).\n\n"
        "Пример:\n"
        "Омлет с сыром\n"
        "Яйца 2 шт\n"
        "Молоко 50 мл\n"
        "Сыр 30 г\n"
        "\n"
        "Приготовление:\n"
        "1. Взбейте яйца с молоком.\n"
        "2. Вылейте на сковороду, добавьте сыр.\n"
        "3. Готовьте до готовности.\n\n"
        "Вы также можете воспользоваться меню для других функций! 🍏"
    ),
    "CONVERSATION": {
        "recipe_add_start": "➕ *Добавление рецепта*\n\nВведите название рецепта:\n\n💡 **Советы:**\n• Используйте понятные названия\n• Минимум 3 символа\n• Избегайте специальных символов\n\n🔙 Для отмены нажмите «Назад»",
        "recipe_name_saved": "✅ Название: *{name}*\n\nТеперь введите все ингредиенты списком, каждый ингредиент — с новой строки.\n\n💡 **Пример:**\n• 2 яйца\n• 100г муки\n• 50мл молока\n• Соль по вкусу\n\n🔙 Для отмены нажмите «Назад»",
        "recipe_ingredients_saved": "✅ Ингредиенты сохранены:\n\n{ingredients_list}\n\nТеперь введите пошаговую инструкцию приготовления:\n\n💡 **Советы:**\n• Опишите каждый шаг подробно\n• Укажите время приготовления\n• Добавьте полезные советы\n\n🔙 Для отмены нажмите «Назад»",
        "recipe_preview": "📖 *Предварительный просмотр*\n\n*Название:* {name}\n\n*Ингредиенты:*\n{ingredients_list}\n\n*Инструкции:*\n{instructions}\n\nПодтвердите добавление рецепта или отмените:",
        "recipe_added": "✅ Рецепт «{name}» успешно добавлен!\n\n🔙 Вернуться в меню рецептов",
        "recipe_cancelled": "❌ Добавление рецепта отменено.\n\n🔙 Вернуться в меню рецептов"
    }
} 