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

  // Отправка текущего состояния при подключении
  ws.send(JSON.stringify({
    type: 'state',
    data: {
      products: workspace.products || [],
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
  const workspaceId = req.params.id || req.params.workspaceId || req.headers['x-workspace-id'] || req.query.workspace_id;
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
      active_clients: []
    };
  }

  // Проверка лимита клиентов
  if (workspace.active_clients.length >= 2) {
    return res.status(403).json({ 
      error: 'Workspace is full (max 2 clients)',
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
  res.json({
    workspace_id: req.workspaceId,
    products: req.workspace.products || [],
    recipes: req.workspace.recipes || []
  });
});

// Products
app.get('/products', requireAccess, (req, res) => {
  res.json(req.workspace.products || []);
});

app.post('/products', requireAccess, (req, res) => {
  const workspaces = loadWorkspaces();
  const workspace = workspaces[req.workspaceId];

  const product = {
    id: uuidv4(),
    name: req.body.name,
    category: req.body.category || 'other',
    in_stock: req.body.in_stock ?? false,
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
  Object.assign(product, req.body);
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

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

