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
- **URL (через Nginx)**: https://155-212-165-45.nip.io/eat/
- **URL (прямой доступ)**: http://155.212.165.45:8082/eat/
- **WebSocket путь**: wss://155-212-165-45.nip.io/ws

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
MAX_CLIENTS_PER_WORKSPACE=25
NODE_ENV=production
```

**Важно**: `MAX_CLIENTS_PER_WORKSPACE` также должен быть указан в `ecosystem.config.js` для PM2.

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

## Nginx конфигурация

- **Файл конфигурации**: `/etc/nginx/sites-available/crm-app`
- **Локальная копия**: `eatsite/nginx.conf`
- **Перезагрузка Nginx**: `sudo nginx -t && sudo systemctl reload nginx`

### Маршрутизация:
- `/eat/` → проксируется на `http://localhost:8082` (frontend)
- `/ws` → проксируется на `http://localhost:3000/` (WebSocket backend)
- `/workspace/*` → проксируется на `http://localhost:3000` (API backend)
- `/products`, `/recipes`, `/categories`, `/export`, `/health`, `/base-basket` → проксируются на `http://localhost:3000` (API backend)
- `/schedule` → проксируется на `http://localhost:8081/schedule` (CRM)
- `/` → проксируется на `http://localhost:8081` (CRM, fallback)

## Важные файлы на сервере

### eatsite
- `/home/webapp/projects/eatsite/server.js` - Frontend сервер (обрабатывает `/eat/` путь)
- `/home/webapp/projects/eatsite/backend/server.js` - Backend API сервер
- `/home/webapp/projects/eatsite/ecosystem.config.js` - PM2 конфигурация
- `/home/webapp/projects/eatsite/.env` - Переменные окружения
- `/home/webapp/projects/eatsite/frontend/dist/` - Собранный frontend (загружается через WinSCP)

### Nginx
- `/etc/nginx/sites-available/crm-app` - Основная конфигурация
- `/var/log/nginx/error.log` - Логи ошибок
- `/var/log/nginx/access.log` - Логи доступа

## Особенности server.js

`server.js` обрабатывает:
- Прямой доступ к `/eat/` (убирает префикс перед поиском файлов)
- Статические ресурсы: `/eat/assets/...`, `/eat/icons/...`, `/eat/manifest.webmanifest`, `/eat/sw.js`
- API проксирование к backend (порт 3000)
- SPA роутинг (все маршруты отдают `index.html`)

## SSL/HTTPS

- **Домен**: `155-212-165-45.nip.io` (с валидным SSL от Let's Encrypt)
- **IP**: `155.212.165.45` (без SSL, будет ошибка сертификата)
- **Рекомендация**: Использовать домен с `.nip.io` для HTTPS доступа

## Обновление файлов на сервере

### Через WinSCP:
1. Подключитесь к серверу (155.212.165.45, пользователь webapp)
2. Замените нужные файлы в `/home/webapp/projects/eatsite/`
3. Перезапустите PM2: `pm2 restart eatsite-frontend` или `pm2 restart eatsite-backend`

### Важные файлы для замены:
- `server.js` - при изменении логики frontend сервера
- `backend/server.js` - при изменении backend API
- `ecosystem.config.js` - при изменении PM2 конфигурации
- `frontend/dist/` - при обновлении frontend (собирается локально)

