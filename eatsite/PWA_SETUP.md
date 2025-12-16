# Настройка PWA для Eatsite

Этот документ описывает настройку PWA (Progressive Web App) для проекта eatsite.

## Что было добавлено

1. **Production сервер** (`server.js`) - раздаёт статические файлы и проксирует API запросы
2. **Настроенный vite-plugin-pwa** - автоматически генерирует Service Worker и манифест
3. **Скрипт копирования PWA файлов** (`scripts/copy-pwa-files.js`)
4. **Иконки для PWA** - автоматически генерируются при первом запуске

## Порт

**Порт: 8082**

Приложение будет доступно на `http://localhost:8082` (или `http://YOUR_SERVER_IP:8082`)

Этот порт выбран чтобы не конфликтовать с текущим проектом CRM App, который использует порт 8081.

## Быстрый старт

### 1. Установка зависимостей

```bash
# Frontend
cd frontend
npm install

# Backend (если еще не установлены)
cd ../backend
npm install
```

### 2. Сборка frontend

```bash
cd frontend
npm run build
```

Это создаст папку `frontend/dist` с собранными файлами.

### 3. Запуск backend

```bash
cd backend
npm start
```

Backend запустится на порту 3000.

### 4. Запуск production сервера

```bash
# Из корня проекта eatsite
node server.js
```

Или через PM2 (рекомендуется для production):

```bash
pm2 start server.js --name eatsite
pm2 save
```

## Настройка на сервере

### Вариант 1: Прямой запуск через PM2

```bash
# На сервере
cd /path/to/eatsite
pm2 start server.js --name eatsite
pm2 save
```

### Вариант 2: Через nginx (рекомендуется)

Если вы используете nginx для проксирования, создайте конфигурацию:

```nginx
# /etc/nginx/sites-available/eatsite
server {
    listen 80;
    server_name your-domain.com;

    # Frontend (PWA)
    location / {
        proxy_pass http://localhost:8082;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API (если нужно проксировать через nginx)
    location /api/ {
        proxy_pass http://localhost:3000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/eatsite /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Структура проекта

```
eatsite/
├── backend/              # Backend API (порт 3000)
│   ├── server.js
│   └── ...
├── frontend/            # Frontend PWA
│   ├── dist/            # Собранные файлы (создаётся после npm run build)
│   ├── index.html
│   ├── main.js
│   └── vite.config.js
├── scripts/             # Скрипты сборки
│   └── copy-pwa-files.js
└── server.js           # Production сервер (порт 8082)
```

## Команды

### Разработка

```bash
# Frontend (dev режим)
cd frontend
npm run dev

# Backend
cd backend
npm start
```

### Production

```bash
# 1. Сборка frontend
cd frontend
npm run build

# 2. Запуск backend
cd backend
npm start

# 3. Запуск production сервера (из корня eatsite)
node server.js
```

## Переменные окружения

Можно настроить через переменные окружения:

```bash
# Порт production сервера (по умолчанию 8082)
PORT=8082 node server.js

# Порт backend (по умолчанию 3000)
BACKEND_PORT=3000 node server.js
```

## Проверка PWA

После запуска сервера:

1. Откройте `http://localhost:8082` в браузере
2. Откройте DevTools (F12) → Application → Service Workers
3. Проверьте, что Service Worker зарегистрирован
4. Проверьте Manifest в Application → Manifest
5. Попробуйте установить PWA через меню браузера

## Иконки

Иконки автоматически генерируются при первом запуске сервера, если их нет в `frontend/dist/icons/`.

Для production рекомендуется использовать реальные иконки:
- `frontend/dist/icons/icon-192.png` (192x192)
- `frontend/dist/icons/icon-512.png` (512x512)

## Troubleshooting

### Service Worker не регистрируется

1. Проверьте, что файл `frontend/dist/sw.js` существует
2. Проверьте консоль браузера на наличие ошибок
3. Убедитесь, что сервер правильно отдаёт файл по пути `/sw.js`

### Manifest не загружается

1. Проверьте, что файл `frontend/dist/manifest.json` существует
2. Проверьте путь к иконкам в manifest.json
3. Убедитесь, что иконки существуют по указанным путям

### API запросы не работают

1. Убедитесь, что backend запущен на порту 3000
2. Проверьте, что production сервер правильно проксирует запросы
3. Проверьте CORS настройки в backend

## Размещение на том же хостинге, что и CRM App

Если вы размещаете на том же сервере, что и CRM App:

1. **CRM App** использует порт **8081**
2. **Eatsite** использует порт **8082**

Оба могут работать одновременно. Настройте nginx для проксирования:

```nginx
# CRM App
location /schedule {
    proxy_pass http://localhost:8081/schedule;
}

# Eatsite
location /pantry {
    proxy_pass http://localhost:8082;
}
```

Или используйте разные поддомены/домены.

