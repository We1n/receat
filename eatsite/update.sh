#!/bin/bash
# Скрипт обновления eatsite с GitHub
# Использование: ./update.sh

set -e  # Остановка при ошибке

echo "🔄 Обновление eatsite с GitHub..."

# Проверка что мы в правильной директории
if [ ! -f "server.js" ]; then
    echo "❌ Ошибка: запустите скрипт из корня проекта eatsite"
    exit 1
fi

# Проверка что мы от пользователя webapp
if [ "$USER" != "webapp" ]; then
    echo "⚠️  Внимание: рекомендуется запускать от пользователя webapp"
    echo "   Текущий пользователь: $USER"
    read -p "Продолжить? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Сохранение текущей директории
PROJECT_DIR=$(pwd)
echo "📁 Директория проекта: $PROJECT_DIR"

# Обновление с GitHub
echo ""
echo "📥 Получение обновлений с GitHub..."
git pull origin main || {
    echo "❌ Ошибка при обновлении с GitHub"
    exit 1
}

# Установка зависимостей backend (если обновился package.json)
if [ -f "backend/package.json" ]; then
    echo ""
    echo "📦 Проверка зависимостей backend..."
    cd backend
    if [ "package.json" -nt "node_modules/.package-lock.json" ] 2>/dev/null || [ ! -d "node_modules" ]; then
        echo "📥 Установка зависимостей backend..."
        npm install --production
    else
        echo "✅ Зависимости backend актуальны"
    fi
    cd ..
fi

# Перезапуск PM2 процессов
echo ""
echo "🔄 Перезапуск процессов PM2..."
pm2 restart eatsite-backend || echo "⚠️  eatsite-backend не найден в PM2"
pm2 restart eatsite-frontend || echo "⚠️  eatsite-frontend не найден в PM2"

# Проверка статуса
echo ""
echo "📊 Статус процессов:"
pm2 list | grep -E "eatsite|NAME" || echo "⚠️  Процессы eatsite не найдены"

echo ""
echo "✅ Обновление завершено!"
echo ""
echo "💡 Полезные команды:"
echo "   pm2 logs eatsite-backend --lines 50"
echo "   pm2 logs eatsite-frontend --lines 50"
echo "   pm2 status"




