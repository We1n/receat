# Информация о сервере

## Подключение

- **IP**: 155.212.165.45
- **Пользователь**: webapp
- **Порт SSH**: 22

## Проекты на сервере

### crm-app (существующий)
- **Путь**: `/home/webapp/projects/crm-app`
- **Порт**: 8081
- **URL**: https://155-212-165-45.nip.io/schedule

### eatsite (новый)
- **Путь**: `/home/webapp/projects/eatsite`
- **Порт frontend**: 8082
- **Порт backend**: 3000

## Управление через PM2

```bash
# Список процессов
pm2 list

# Логи
pm2 logs eatsite-backend
pm2 logs eatsite-frontend

# Перезапуск
pm2 restart all

# Остановка
pm2 stop all
```

## Файл .env на сервере

Создаётся вручную в `/home/webapp/projects/eatsite/.env`:

```
PORT=8082
BACKEND_PORT=3000
BACKEND_HOST=localhost
MAX_CLIENTS_PER_WORKSPACE=5
NODE_ENV=production
```

## Обновление проекта

```bash
cd /home/webapp/projects/eatsite
./update.sh
```

Скрипт автоматически:
- Обновит код с GitHub
- Установит зависимости backend
- Перезапустит PM2 процессы

**Важно**: `frontend/dist` собирается локально и загружается на сервер через WinSCP.

