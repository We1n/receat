/**
 * Shared Pantry PWA - Backend Server
 * 
 * Server-first архитектура:
 * - Все изменения сразу пишутся на сервер
 * - WebSocket для синхронизации между клиентами
 * - Workspace-based изоляция данных
 */

import express from 'express';
import { WebSocketServer } from 'ws';
import cors from 'cors';
import { v4 as uuidv4 } from 'uuid';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { PRODUCT_CATEGORIES } from './config/categories.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Маппинг английских категорий на русские (для обратной совместимости)
const CATEGORY_MAPPING = {
  'vegetables': 'Овощи',
  'fruits': 'Фрукты',
  'dairy': 'Молочные продукты',
  'meat': 'Мясо',
  'fish': 'Рыба',
  'eggs': 'Яйца',
  'legumes': 'Бобовые',
  'grains': 'Крупы',
  'bread': 'Хлеб',
  'nuts': 'Орехи',
  'spices': 'Специи',
  'beverages': 'Напитки',
  'oils': 'Жиры и масла',
  'sauces': 'Соусы',
  'other': 'Прочее'
};

// Функция нормализации категории (переводит английские на русские)
function normalizeCategory(category) {
  if (!category) return 'Прочее';
  // Если категория на английском, переводим на русский
  if (CATEGORY_MAPPING[category.toLowerCase()]) {
    return CATEGORY_MAPPING[category.toLowerCase()];
  }
  // Если категория уже на русском, возвращаем как есть
  return category;
}

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Storage
const DATA_DIR = join(__dirname, 'data');
const WORKSPACES_FILE = join(DATA_DIR, 'workspaces.json');

// Инициализация хранилища
if (!existsSync(DATA_DIR)) {
  mkdirSync(DATA_DIR, { recursive: true });
}

function loadWorkspaces() {
  if (!existsSync(WORKSPACES_FILE)) {
    return {};
  }
  return JSON.parse(readFileSync(WORKSPACES_FILE, 'utf-8'));
}

function saveWorkspaces(workspaces) {
  writeFileSync(WORKSPACES_FILE, JSON.stringify(workspaces, null, 2));
}

// WebSocket сервер
const server = app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});

const wss = new WebSocketServer({ server });

// Хранилище активных WebSocket соединений по workspace_id
const wsConnections = new Map();

wss.on('connection', (ws, req) => {
  const workspaceId = new URL(req.url, `http://${req.headers.host}`).searchParams.get('workspace_id');
  const clientToken = new URL(req.url, `http://${req.headers.host}`).searchParams.get('client_token');

  if (!workspaceId || !clientToken) {
    ws.close(1008, 'Missing workspace_id or client_token');
    return;
  }

  // Проверка доступа
  const workspaces = loadWorkspaces();
  const workspace = workspaces[workspaceId];
  
  if (!workspace || !workspace.active_clients.includes(clientToken)) {
    ws.close(1008, 'Access denied');
    return;
  }

  // Добавляем соединение
  if (!wsConnections.has(workspaceId)) {
    wsConnections.set(workspaceId, new Set());
  }
  wsConnections.get(workspaceId).add(ws);

  ws.on('close', () => {
    const connections = wsConnections.get(workspaceId);
    if (connections) {
      connections.delete(ws);
      if (connections.size === 0) {
        wsConnections.delete(workspaceId);
      }
    }
  });

  // Нормализуем категории продуктов перед отправкой
  const normalizedProducts = (workspace.products || []).map(product => ({
    ...product,
    category: normalizeCategory(product.category)
  }));

  // Отправка текущего состояния при подключении
  ws.send(JSON.stringify({
    type: 'state',
    data: {
      products: normalizedProducts,
      recipes: workspace.recipes || []
    }
  }));
});

// Broadcast обновления всем клиентам workspace
function broadcastToWorkspace(workspaceId, message) {
  const connections = wsConnections.get(workspaceId);
  if (connections) {
    connections.forEach(ws => {
      if (ws.readyState === 1) { // OPEN
        ws.send(JSON.stringify(message));
      }
    });
  }
}

// Middleware для проверки доступа
function requireAccess(req, res, next) {
  // Для маршрутов типа /products/:id или /recipes/:id, 
  // req.params.id - это ID продукта/рецепта, а не workspace_id
  // Поэтому workspace_id должен быть только в заголовках или query
  const workspaceId = req.params.workspaceId || req.headers['x-workspace-id'] || req.query.workspace_id;
  const clientToken = req.headers['x-client-token'] || req.query.client_token;

  if (!workspaceId || !clientToken) {
    return res.status(401).json({ error: 'Missing workspace_id or client_token' });
  }

  const workspaces = loadWorkspaces();
  const workspace = workspaces[workspaceId];

  if (!workspace) {
    return res.status(404).json({ error: 'Workspace not found' });
  }

  if (!workspace.active_clients.includes(clientToken)) {
    return res.status(403).json({ error: 'Access denied' });
  }

  req.workspace = workspace;
  req.workspaceId = workspaceId;
  req.clientToken = clientToken;
  next();
}

// ===== API Routes =====

// Workspace
app.get('/workspace/:id', (req, res) => {
  const workspaces = loadWorkspaces();
  const workspace = workspaces[req.params.id];

  if (!workspace) {
    return res.status(404).json({ error: 'Workspace not found' });
  }

  // Публичная информация (без данных)
  res.json({
    workspace_id: req.params.id,
    active_clients_count: workspace.active_clients.length
  });
});

app.post('/workspace/:id/join', (req, res) => {
  const workspaceId = req.params.id;
  const workspaces = loadWorkspaces();
  let workspace = workspaces[workspaceId];

  if (!workspace) {
    // Создаём новый workspace
    workspace = {
      workspace_id: workspaceId,
      products: [],
      recipes: [],
      active_clients: [],
      prices: {}, // Инициализируем цены
      base_basket: BASE_BASKET // Инициализируем базовую корзину по умолчанию
    };
  } else {
    // Если у существующего workspace нет базовой корзины, добавляем по умолчанию
    if (!workspace.base_basket) {
      workspace.base_basket = BASE_BASKET;
    }
    // Если у существующего workspace нет цен, инициализируем
    if (!workspace.prices) {
      workspace.prices = {};
    }
  }

  // Проверка лимита клиентов
  const MAX_CLIENTS_PER_WORKSPACE = parseInt(process.env.MAX_CLIENTS_PER_WORKSPACE || '10', 10);
  if (workspace.active_clients.length >= MAX_CLIENTS_PER_WORKSPACE) {
    return res.status(403).json({ 
      error: `Workspace is full (max ${MAX_CLIENTS_PER_WORKSPACE} clients)`,
      can_access: false
    });
  }

  // Генерируем новый client_token
  const clientToken = uuidv4();
  workspace.active_clients.push(clientToken);

  workspaces[workspaceId] = workspace;
  saveWorkspaces(workspaces);

  res.json({
    client_token: clientToken,
    workspace_id: workspaceId,
    can_access: true
  });
});

app.get('/workspace/:id/state', requireAccess, (req, res) => {
  // Нормализуем категории продуктов перед отправкой
  const normalizedProducts = (req.workspace.products || []).map(product => ({
    ...product,
    category: normalizeCategory(product.category)
  }));

  res.json({
    workspace_id: req.workspaceId,
    products: normalizedProducts,
    recipes: req.workspace.recipes || []
  });
});

// Products
app.get('/products', requireAccess, (req, res) => {
  // Нормализуем категории продуктов перед отправкой
  const normalizedProducts = (req.workspace.products || []).map(product => ({
    ...product,
    category: normalizeCategory(product.category)
  }));
  res.json(normalizedProducts);
});

app.post('/products', requireAccess, (req, res) => {
  const workspaces = loadWorkspaces();
  const workspace = workspaces[req.workspaceId];

  const product = {
    id: uuidv4(),
    name: req.body.name,
    category: normalizeCategory(req.body.category),
    in_stock: req.body.in_stock ?? false,
    wishlist: req.body.wishlist ?? false,
    quantity: req.body.quantity || null,
    unit: req.body.unit || null
  };

  workspace.products = workspace.products || [];
  workspace.products.push(product);
  saveWorkspaces(workspaces);

  broadcastToWorkspace(req.workspaceId, {
    type: 'product_created',
    data: product
  });

  res.json(product);
});

app.patch('/products/:id', requireAccess, (req, res) => {
  const workspaces = loadWorkspaces();
  const workspace = workspaces[req.workspaceId];
  const productIndex = workspace.products.findIndex(p => p.id === req.params.id);

  if (productIndex === -1) {
    return res.status(404).json({ error: 'Product not found' });
  }

  const product = workspace.products[productIndex];
  const updates = { ...req.body };
  // Нормализуем категорию если она обновляется
  if (updates.category) {
    updates.category = normalizeCategory(updates.category);
  }
  Object.assign(product, updates);
  saveWorkspaces(workspaces);

  broadcastToWorkspace(req.workspaceId, {
    type: 'product_updated',
    data: product
  });

  res.json(product);
});

app.delete('/products/:id', requireAccess, (req, res) => {
  const workspaces = loadWorkspaces();
  const workspace = workspaces[req.workspaceId];
  const productIndex = workspace.products.findIndex(p => p.id === req.params.id);

  if (productIndex === -1) {
    return res.status(404).json({ error: 'Product not found' });
  }

  workspace.products.splice(productIndex, 1);
  saveWorkspaces(workspaces);

  broadcastToWorkspace(req.workspaceId, {
    type: 'product_deleted',
    data: { id: req.params.id }
  });

  res.json({ success: true });
});

// Recipes
app.get('/recipes', requireAccess, (req, res) => {
  res.json(req.workspace.recipes || []);
});

app.post('/recipes', requireAccess, (req, res) => {
  const workspaces = loadWorkspaces();
  const workspace = workspaces[req.workspaceId];

  const recipe = {
    id: uuidv4(),
    name: req.body.name,
    product_ids: req.body.product_ids || [],
    notes: req.body.notes || null
  };

  workspace.recipes = workspace.recipes || [];
  workspace.recipes.push(recipe);
  saveWorkspaces(workspaces);

  broadcastToWorkspace(req.workspaceId, {
    type: 'recipe_created',
    data: recipe
  });

  res.json(recipe);
});

app.patch('/recipes/:id', requireAccess, (req, res) => {
  const workspaces = loadWorkspaces();
  const workspace = workspaces[req.workspaceId];
  const recipeIndex = workspace.recipes.findIndex(r => r.id === req.params.id);

  if (recipeIndex === -1) {
    return res.status(404).json({ error: 'Recipe not found' });
  }

  const recipe = workspace.recipes[recipeIndex];
  Object.assign(recipe, req.body);
  saveWorkspaces(workspaces);

  broadcastToWorkspace(req.workspaceId, {
    type: 'recipe_updated',
    data: recipe
  });

  res.json(recipe);
});

app.delete('/recipes/:id', requireAccess, (req, res) => {
  const workspaces = loadWorkspaces();
  const workspace = workspaces[req.workspaceId];
  const recipeIndex = workspace.recipes.findIndex(r => r.id === req.params.id);

  if (recipeIndex === -1) {
    return res.status(404).json({ error: 'Recipe not found' });
  }

  workspace.recipes.splice(recipeIndex, 1);
  saveWorkspaces(workspaces);

  broadcastToWorkspace(req.workspaceId, {
    type: 'recipe_deleted',
    data: { id: req.params.id }
  });

  res.json({ success: true });
});

// Export
app.get('/export/json', requireAccess, (req, res) => {
  res.json({
    workspace_id: req.workspaceId,
    products: req.workspace.products || [],
    recipes: req.workspace.recipes || []
  });
});

// Categories (публичный endpoint)
app.get('/categories', (req, res) => {
  res.json(PRODUCT_CATEGORIES);
});

// Базовая корзина продуктов
const BASE_BASKET = [
  // Овощи
  { name: 'Картофель', category: 'Овощи', in_stock: false },
  { name: 'Морковь', category: 'Овощи', in_stock: false },
  { name: 'Лук репчатый', category: 'Овощи', in_stock: false },
  { name: 'Чеснок', category: 'Овощи', in_stock: false },
  { name: 'Помидоры', category: 'Овощи', in_stock: false },
  { name: 'Огурцы', category: 'Овощи', in_stock: false },
  { name: 'Капуста белокочанная', category: 'Овощи', in_stock: false },
  { name: 'Перец болгарский', category: 'Овощи', in_stock: false },
  
  // Фрукты
  { name: 'Яблоки', category: 'Фрукты', in_stock: false },
  { name: 'Бананы', category: 'Фрукты', in_stock: false },
  { name: 'Апельсины', category: 'Фрукты', in_stock: false },
  
  // Молочные продукты
  { name: 'Молоко', category: 'Молочные продукты', in_stock: false },
  { name: 'Сметана', category: 'Молочные продукты', in_stock: false },
  { name: 'Творог', category: 'Молочные продукты', in_stock: false },
  { name: 'Сыр', category: 'Молочные продукты', in_stock: false },
  { name: 'Яйца куриные', category: 'Яйца', in_stock: false },
  
  // Мясо
  { name: 'Куриная грудка', category: 'Мясо', in_stock: false },
  { name: 'Фарш мясной', category: 'Мясо', in_stock: false },
  
  // Крупы
  { name: 'Рис', category: 'Крупы', in_stock: false },
  { name: 'Гречка', category: 'Крупы', in_stock: false },
  { name: 'Овсяные хлопья', category: 'Крупы', in_stock: false },
  { name: 'Макароны из твёрдых сортов', category: 'Крупы', in_stock: false },
  
  // Хлеб
  { name: 'Хлеб ржаной или цельнозерновой', category: 'Хлеб', in_stock: false },
  
  // Специи
  { name: 'Соль', category: 'Специи', in_stock: false },
  { name: 'Перец черный', category: 'Специи', in_stock: false },
  { name: 'Сахар', category: 'Специи', in_stock: false },
  
  // Жиры и масла
  { name: 'Растительное масло', category: 'Жиры и масла', in_stock: false },
  { name: 'Масло сливочное', category: 'Жиры и масла', in_stock: false },
  
  // Напитки
  { name: 'Вода питьевая', category: 'Напитки', in_stock: false },
  { name: 'Чай', category: 'Напитки', in_stock: false },
  
  // Соусы
  { name: 'Майонез', category: 'Соусы', in_stock: false },
  { name: 'Кетчуп', category: 'Соусы', in_stock: false },
  
  // Прочее
  { name: 'Томатная паста', category: 'Прочее', in_stock: false }
];

// Получение базовой корзины
app.get('/workspace/:id/base-basket', requireAccess, (req, res) => {
  const workspace = req.workspace;
  const baseBasket = workspace.base_basket || BASE_BASKET;
  res.json({
    workspace_id: req.workspaceId,
    base_basket: baseBasket
  });
});

// Обновление базовой корзины
app.put('/workspace/:id/base-basket', requireAccess, (req, res) => {
  const workspaces = loadWorkspaces();
  const workspace = workspaces[req.workspaceId];

  if (!workspace) {
    return res.status(404).json({ error: 'Workspace not found' });
  }

  // Валидация данных
  if (!Array.isArray(req.body.base_basket)) {
    return res.status(400).json({ error: 'base_basket must be an array' });
  }

  // Нормализуем категории в базовой корзине
  const normalizedBasket = req.body.base_basket.map(item => ({
    name: item.name,
    category: normalizeCategory(item.category || 'Прочее'),
    in_stock: false // Базовая корзина всегда с in_stock: false
  }));

  workspace.base_basket = normalizedBasket;
  saveWorkspaces(workspaces);

  res.json({
    success: true,
    base_basket: workspace.base_basket
  });
});

// Инициализация базовой корзины в workspace (добавление в "нужно купить")
app.post('/workspace/:id/init-basket', requireAccess, (req, res) => {
  const workspaces = loadWorkspaces();
  const workspace = workspaces[req.workspaceId];

  if (!workspace) {
    return res.status(404).json({ error: 'Workspace not found' });
  }

  // Используем сохранённую базовую корзину или дефолтную
  const baseBasket = workspace.base_basket || BASE_BASKET;

  // Проверяем, есть ли уже продукты в workspace
  const existingProducts = workspace.products || [];
  const existingNames = new Set(existingProducts.map(p => p.name.toLowerCase()));

  // Добавляем только те продукты, которых еще нет (все с in_stock: false - "нужно купить")
  const newProducts = baseBasket
    .filter(product => !existingNames.has(product.name.toLowerCase()))
    .map(product => ({
      id: uuidv4(),
      name: product.name,
      category: normalizeCategory(product.category),
      in_stock: false, // Всегда "нужно купить"
      quantity: null,
      unit: null
    }));

  workspace.products = [...existingProducts, ...newProducts];
  saveWorkspaces(workspaces);

  // Отправляем обновления через WebSocket
  newProducts.forEach(product => {
    broadcastToWorkspace(req.workspaceId, {
      type: 'product_created',
      data: product
    });
  });

  res.json({
    success: true,
    added: newProducts.length,
    total: workspace.products.length,
    products: newProducts
  });
});

// Stores configuration
app.get('/stores', (req, res) => {
  try {
    const storesFile = join(__dirname, 'config', 'stores.json');
    if (existsSync(storesFile)) {
      const stores = JSON.parse(readFileSync(storesFile, 'utf-8'));
      res.json(stores);
    } else {
      res.json({ stores: [], default_store: null });
    }
  } catch (error) {
    console.error('Error loading stores:', error);
    res.status(500).json({ error: 'Failed to load stores' });
  }
});

// Prices API
// Get all prices for workspace
app.get('/prices', requireAccess, (req, res) => {
  const workspace = req.workspace;
  const prices = workspace.prices || {};
  res.json(prices);
});

// Get price for specific product
app.get('/prices/:productName', requireAccess, (req, res) => {
  const workspace = req.workspace;
  const prices = workspace.prices || {};
  const productName = decodeURIComponent(req.params.productName).toLowerCase();
  const priceData = prices[productName];
  
  if (!priceData) {
    return res.status(404).json({ error: 'Price not found' });
  }
  
  res.json(priceData);
});

// Set/Update price for product in store
app.post('/prices', requireAccess, (req, res) => {
  const workspaces = loadWorkspaces();
  const workspace = workspaces[req.workspaceId];
  
  const { product_name, price, store_id } = req.body;
  
  if (!product_name || price === undefined || price === null) {
    return res.status(400).json({ error: 'product_name and price are required' });
  }
  
  const productName = product_name.toLowerCase();
  const storesFile = join(__dirname, 'config', 'stores.json');
  let storesConfig = { stores: {}, default_store: 'yarkie' };
  
  if (existsSync(storesFile)) {
    storesConfig = JSON.parse(readFileSync(storesFile, 'utf-8'));
  }
  
  const selectedStoreId = store_id || storesConfig.default_store;
  
  // Проверяем, что магазин существует
  const storeList = storesConfig.stores || [];
  const storeInfo = storeList.find(s => s.id === selectedStoreId);
  
  if (!storeInfo) {
    return res.status(400).json({ error: `Invalid store_id: ${selectedStoreId}. Available stores: ${storeList.map(s => s.id).join(', ')}` });
  }
  
  // Initialize prices if not exists
  if (!workspace.prices) {
    workspace.prices = {};
  }
  
  // Initialize product price data if not exists
  if (!workspace.prices[productName]) {
    workspace.prices[productName] = {
      stores: {},
      best_store: null,
      best_price: null
    };
  }
  
  // Set price in store
  const currentTime = new Date().toISOString();
  workspace.prices[productName].stores[selectedStoreId] = {
    price: parseFloat(price),
    updated_at: currentTime
  };
  
  // Update best price
  const stores = workspace.prices[productName].stores;
  let bestPrice = null;
  let bestStore = null;
  
  for (const [storeId, storeData] of Object.entries(stores)) {
    const storePrice = storeData.price;
    if (storePrice !== null && storePrice !== undefined) {
      if (bestPrice === null || storePrice < bestPrice) {
        bestPrice = storePrice;
        bestStore = storeId;
      }
    }
  }
  
  workspace.prices[productName].best_price = bestPrice;
  workspace.prices[productName].best_store = bestStore;
  
  saveWorkspaces(workspaces);
  
  // Broadcast update via WebSocket
  broadcastToWorkspace(req.workspaceId, {
    type: 'price_updated',
    data: {
      product_name: productName,
      price_data: workspace.prices[productName]
    }
  });
  
  res.json(workspace.prices[productName]);
});

// Delete price for product (all stores or specific store)
app.delete('/prices/:productName', requireAccess, (req, res) => {
  const workspaces = loadWorkspaces();
  const workspace = workspaces[req.workspaceId];
  const productName = decodeURIComponent(req.params.productName).toLowerCase();
  const { store_id } = req.query;
  
  if (!workspace.prices || !workspace.prices[productName]) {
    return res.status(404).json({ error: 'Price not found' });
  }
  
  if (store_id) {
    // Delete price for specific store
    if (workspace.prices[productName].stores[store_id]) {
      delete workspace.prices[productName].stores[store_id];
      
      // Update best price
      const stores = workspace.prices[productName].stores;
      let bestPrice = null;
      let bestStore = null;
      
      for (const [sid, storeData] of Object.entries(stores)) {
        const storePrice = storeData.price;
        if (storePrice !== null && storePrice !== undefined) {
          if (bestPrice === null || storePrice < bestPrice) {
            bestPrice = storePrice;
            bestStore = sid;
          }
        }
      }
      
      workspace.prices[productName].best_price = bestPrice;
      workspace.prices[productName].best_store = bestStore;
      
      // If no stores left, delete product entry
      if (Object.keys(stores).length === 0) {
        delete workspace.prices[productName];
      }
    }
  } else {
    // Delete all prices for product
    delete workspace.prices[productName];
  }
  
  saveWorkspaces(workspaces);
  
  // Broadcast update via WebSocket
  broadcastToWorkspace(req.workspaceId, {
    type: 'price_deleted',
    data: {
      product_name: productName,
      store_id: store_id || null
    }
  });
  
  res.json({ success: true });
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

