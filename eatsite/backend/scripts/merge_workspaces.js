/**
 * Скрипт для переноса продуктов из pantry-week-1 в workspace 123
 */

import { readFileSync, writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DATA_DIR = join(__dirname, '..', 'data');
const WORKSPACES_FILE = join(DATA_DIR, 'workspaces.json');

const workspaces = JSON.parse(readFileSync(WORKSPACES_FILE, 'utf-8'));

const sourceWorkspace = 'pantry-week-1';
const targetWorkspace = '123';

if (!workspaces[sourceWorkspace]) {
  console.error(`Workspace ${sourceWorkspace} не найден`);
  process.exit(1);
}

if (!workspaces[targetWorkspace]) {
  console.error(`Workspace ${targetWorkspace} не найден`);
  process.exit(1);
}

const sourceProducts = workspaces[sourceWorkspace].products || [];
const targetProducts = workspaces[targetWorkspace].products || [];

console.log(`Переносим ${sourceProducts.length} продуктов из ${sourceWorkspace} в ${targetWorkspace}`);
console.log(`В целевом workspace уже есть ${targetProducts.length} продуктов`);

// Объединяем продукты (избегаем дубликатов по имени)
const existingNames = new Set(targetProducts.map(p => p.name.toLowerCase()));
const productsToAdd = sourceProducts.filter(p => !existingNames.has(p.name.toLowerCase()));

workspaces[targetWorkspace].products = [...targetProducts, ...productsToAdd];

writeFileSync(WORKSPACES_FILE, JSON.stringify(workspaces, null, 2));

console.log(`✅ Добавлено ${productsToAdd.length} продуктов`);
console.log(`Всего продуктов в ${targetWorkspace}: ${workspaces[targetWorkspace].products.length}`);



