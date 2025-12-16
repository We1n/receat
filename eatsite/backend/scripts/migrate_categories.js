/**
 * Скрипт миграции категорий с английского на русский
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DATA_DIR = join(__dirname, '..', 'data');
const WORKSPACES_FILE = join(DATA_DIR, 'workspaces.json');

// Маппинг английских категорий на русские
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

function migrateCategories() {
  if (!existsSync(WORKSPACES_FILE)) {
    console.log('❌ Файл workspaces.json не найден');
    return;
  }

  const workspaces = JSON.parse(readFileSync(WORKSPACES_FILE, 'utf-8'));
  let totalMigrated = 0;
  let workspacesUpdated = 0;

  for (const [workspaceId, workspace] of Object.entries(workspaces)) {
    let workspaceChanged = false;
    
    // Мигрируем продукты
    if (workspace.products && Array.isArray(workspace.products)) {
      workspace.products.forEach(product => {
        if (product.category && CATEGORY_MAPPING[product.category]) {
          const oldCategory = product.category;
          product.category = CATEGORY_MAPPING[oldCategory];
          totalMigrated++;
          workspaceChanged = true;
          console.log(`  - "${product.name}": ${oldCategory} -> ${product.category}`);
        }
      });
    }

    if (workspaceChanged) {
      workspacesUpdated++;
    }
  }

  if (totalMigrated > 0) {
    writeFileSync(WORKSPACES_FILE, JSON.stringify(workspaces, null, 2), 'utf-8');
    console.log(`\n✅ Миграция завершена:`);
    console.log(`   - Обновлено воркспейсов: ${workspacesUpdated}`);
    console.log(`   - Мигрировано продуктов: ${totalMigrated}`);
  } else {
    console.log('✅ Все категории уже на русском языке');
  }
}

migrateCategories();

