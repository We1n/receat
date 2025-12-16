/**
 * Скрипт для инициализации workspace с базовым набором продуктов
 * Использование: node scripts/init_products.js <workspace_id>
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { v4 as uuidv4 } from 'uuid';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DATA_DIR = join(__dirname, '..', 'data');
const WORKSPACES_FILE = join(DATA_DIR, 'workspaces.json');

// Базовый список продуктов по категориям
const BASE_PRODUCTS = [
  // Овощи (vegetables)
  { name: 'Картофель', category: 'vegetables', in_stock: false },
  { name: 'Морковь', category: 'vegetables', in_stock: false },
  { name: 'Лук репчатый', category: 'vegetables', in_stock: false },
  { name: 'Чеснок', category: 'vegetables', in_stock: false },
  { name: 'Помидоры', category: 'vegetables', in_stock: false },
  { name: 'Огурцы', category: 'vegetables', in_stock: false },
  { name: 'Капуста белокочанная', category: 'vegetables', in_stock: false },
  { name: 'Свекла', category: 'vegetables', in_stock: false },
  { name: 'Перец болгарский', category: 'vegetables', in_stock: false },
  { name: 'Кабачки', category: 'vegetables', in_stock: false },
  
  // Фрукты (fruits)
  { name: 'Яблоки', category: 'fruits', in_stock: false },
  { name: 'Бананы', category: 'fruits', in_stock: false },
  { name: 'Апельсины', category: 'fruits', in_stock: false },
  { name: 'Лимоны', category: 'fruits', in_stock: false },
  { name: 'Груши', category: 'fruits', in_stock: false },
  { name: 'Мандарины', category: 'fruits', in_stock: false },
  
  // Молочные продукты (dairy)
  { name: 'Молоко', category: 'dairy', in_stock: false },
  { name: 'Сметана', category: 'dairy', in_stock: false },
  { name: 'Творог', category: 'dairy', in_stock: false },
  { name: 'Сыр', category: 'dairy', in_stock: false },
  { name: 'Йогурт', category: 'dairy', in_stock: false },
  { name: 'Кефир', category: 'dairy', in_stock: false },
  { name: 'Масло сливочное', category: 'dairy', in_stock: false },
  { name: 'Яйца куриные', category: 'dairy', in_stock: false },
  
  // Мясо (meat)
  { name: 'Куриная грудка', category: 'meat', in_stock: false },
  { name: 'Говядина', category: 'meat', in_stock: false },
  { name: 'Свинина', category: 'meat', in_stock: false },
  { name: 'Фарш мясной', category: 'meat', in_stock: false },
  { name: 'Колбаса', category: 'meat', in_stock: false },
  { name: 'Сосиски', category: 'meat', in_stock: false },
  
  // Крупы (grains)
  { name: 'Рис', category: 'grains', in_stock: false },
  { name: 'Гречка', category: 'grains', in_stock: false },
  { name: 'Овсянка', category: 'grains', in_stock: false },
  { name: 'Макароны', category: 'grains', in_stock: false },
  { name: 'Пшено', category: 'grains', in_stock: false },
  { name: 'Перловка', category: 'grains', in_stock: false },
  { name: 'Мука пшеничная', category: 'grains', in_stock: false },
  { name: 'Хлеб белый', category: 'grains', in_stock: false },
  { name: 'Хлеб черный', category: 'grains', in_stock: false },
  
  // Специи (spices)
  { name: 'Соль', category: 'spices', in_stock: false },
  { name: 'Перец черный', category: 'spices', in_stock: false },
  { name: 'Сахар', category: 'spices', in_stock: false },
  { name: 'Мука', category: 'spices', in_stock: false },
  { name: 'Растительное масло', category: 'spices', in_stock: false },
  { name: 'Уксус', category: 'spices', in_stock: false },
  { name: 'Лавровый лист', category: 'spices', in_stock: false },
  { name: 'Паприка', category: 'spices', in_stock: false },
  
  // Напитки (beverages)
  { name: 'Вода питьевая', category: 'beverages', in_stock: false },
  { name: 'Чай черный', category: 'beverages', in_stock: false },
  { name: 'Чай зеленый', category: 'beverages', in_stock: false },
  { name: 'Кофе', category: 'beverages', in_stock: false },
  { name: 'Сок', category: 'beverages', in_stock: false },
  { name: 'Газировка', category: 'beverages', in_stock: false },
  
  // Прочее (other)
  { name: 'Консервы рыбные', category: 'other', in_stock: false },
  { name: 'Томатная паста', category: 'other', in_stock: false },
  { name: 'Майонез', category: 'other', in_stock: false },
  { name: 'Кетчуп', category: 'other', in_stock: false },
  { name: 'Горчица', category: 'other', in_stock: false },
  { name: 'Мед', category: 'other', in_stock: false },
  { name: 'Орехи', category: 'other', in_stock: false },
  { name: 'Шоколад', category: 'other', in_stock: false },
];

function loadWorkspaces() {
  if (!existsSync(WORKSPACES_FILE)) {
    return {};
  }
  return JSON.parse(readFileSync(WORKSPACES_FILE, 'utf-8'));
}

function saveWorkspaces(workspaces) {
  if (!existsSync(DATA_DIR)) {
    mkdirSync(DATA_DIR, { recursive: true });
  }
  writeFileSync(WORKSPACES_FILE, JSON.stringify(workspaces, null, 2));
}

function initWorkspace(workspaceId) {
  const workspaces = loadWorkspaces();
  
  // Создаем или обновляем workspace
  const workspace = {
    workspace_id: workspaceId,
    products: BASE_PRODUCTS.map(product => ({
      id: uuidv4(),
      name: product.name,
      category: product.category,
      in_stock: product.in_stock,
      quantity: null,
      unit: null
    })),
    recipes: [],
    active_clients: []
  };
  
  workspaces[workspaceId] = workspace;
  saveWorkspaces(workspaces);
  
  console.log(`✅ Workspace "${workspaceId}" инициализирован с ${BASE_PRODUCTS.length} продуктами`);
  console.log(`\nКатегории:`);
  const byCategory = BASE_PRODUCTS.reduce((acc, p) => {
    acc[p.category] = (acc[p.category] || 0) + 1;
    return acc;
  }, {});
  Object.entries(byCategory).forEach(([cat, count]) => {
    console.log(`  ${cat}: ${count} продуктов`);
  });
}

// Получаем workspace_id из аргументов
const workspaceId = process.argv[2] || 'default-pantry';

if (!workspaceId) {
  console.error('Использование: node scripts/init_products.js <workspace_id>');
  process.exit(1);
}

initWorkspace(workspaceId);






