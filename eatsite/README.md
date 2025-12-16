# Shared Pantry PWA

Простой web/PWA-сервис для учёта продуктов на двух устройствах.

## Структура проекта

```
eatsite/
├── backend/          # API сервер (Node.js + Express + WebSocket)
│   ├── config/       # Конфигурация (категории продуктов)
│   ├── data/         # JSON хранилище (создаётся автоматически)
│   └── server.js     # Основной сервер
├── frontend/         # PWA клиент (Vanilla JS + Vite)
│   ├── index.html
│   ├── main.js
│   └── styles.css
├── shared/           # Общие типы/модели
└── ARCHITECTURE.md   # Подробная архитектура
```

## Быстрый старт

### Требования

- Node.js 18+ (для backend и frontend)
- npm или yarn

### Backend

```bash
cd backend
npm install
npm start
```

Сервер запустится на `http://localhost:3000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend запустится на `http://localhost:5173`

## Использование

1. Запустите backend и frontend
2. Откройте frontend в браузере
3. Введите `workspace_id` (любая строка, например `my-pantry`)
4. Нажмите "Присоединиться"
5. Сохраните `client_token` (он будет сохранён в localStorage)
6. Откройте на втором устройстве и повторите шаги 3-4

**Важно**: Максимум 2 активных клиента на один workspace.

## API Endpoints

### Workspace
- `GET /workspace/:id` - информация о workspace
- `POST /workspace/:id/join` - присоединиться к workspace
- `GET /workspace/:id/state` - получить состояние (требует `X-Client-Token`)

### Products
- `GET /products` - список продуктов (требует `X-Client-Token`)
- `POST /products` - создать продукт
- `PATCH /products/:id` - обновить продукт
- `DELETE /products/:id` - удалить продукт

### Recipes
- `GET /recipes` - список рецептов
- `POST /recipes` - создать рецепт
- `PATCH /recipes/:id` - обновить рецепт
- `DELETE /recipes/:id` - удалить рецепт

### Другие
- `GET /categories` - список категорий продуктов
- `GET /export/json` - экспорт всего workspace
- `GET /health` - проверка здоровья сервера

## Технологии

- **Backend**: Node.js + Express + WebSocket (ws)
- **Frontend**: Vanilla JavaScript + Vite + PWA
- **Sync**: WebSocket для real-time синхронизации
- **Storage**: JSON файлы (backend/data/workspaces.json)

## Production Deployment

**⚠️ Важно:** 
- Сборка `frontend/dist` выполняется **локально** на вашем компьютере, затем загружается на сервер
- Eatsite размещается рядом с существующим проектом `crm-app`
- Все операции выполняются от пользователя `webapp`

### Быстрый деплой на сервер

```bash
# 1. Локально: Сборка frontend
cd frontend && npm run build

# 2. Загрузите файлы на сервер через WinSCP:
#    - backend/ (без node_modules и data)
#    - frontend/dist/
#    - server.js, ecosystem.config.js, update.sh

# 3. На сервере (от пользователя webapp):
cd /home/webapp/projects/eatsite
mkdir -p logs backend/data
cd backend && npm install --production
cd ..
# Создайте .env файл (см. ENV_EXAMPLE.txt)
pm2 start ecosystem.config.js
pm2 save
```

Подробная информация о сервере: см. [server-info.md](../server-info.md) в корне репозитория.

