/**
 * Скрипт для заполнения продуктовой корзины
 * Заполняет корзину базовым списком продуктов на неделю для одного человека
 */

const API_BASE = 'http://localhost:3000';

// Список продуктов для добавления
const products = [
  // Зерновые и хлеб
  { name: 'Хлеб ржаной или цельнозерновой', category: 'Хлеб', quantity: '1', unit: 'буханка' },
  { name: 'Гречка', category: 'Крупы', quantity: '1', unit: 'кг' },
  { name: 'Рис (круглый или длинный)', category: 'Крупы', quantity: '1', unit: 'кг' },
  { name: 'Овсяные хлопья', category: 'Крупы', quantity: '0.8-1', unit: 'кг' },
  { name: 'Макароны из твёрдых сортов', category: 'Крупы', quantity: '0.8-1', unit: 'кг' },
  
  // Белок: мясо, рыба, яйца, бобовые
  { name: 'Куриная грудка/бедро без кожи', category: 'Мясо', quantity: '1.5-2', unit: 'кг' },
  { name: 'Индейка или постная говядина', category: 'Мясо', quantity: '0.8-1', unit: 'кг' },
  { name: 'Рыба (минтай, хек, скумбрия или лосось)', category: 'Рыба', quantity: '1-1.5', unit: 'кг' },
  { name: 'Яйца', category: 'Яйца', quantity: '20-30', unit: 'шт' },
  { name: 'Фасоль/чечевица/нут (сухие или в банке)', category: 'Бобовые', quantity: '1-1.5', unit: 'кг' },
  
  // Овощи
  { name: 'Картофель', category: 'Овощи', quantity: '3-4', unit: 'кг' },
  { name: 'Морковь', category: 'Овощи', quantity: '1-1.5', unit: 'кг' },
  { name: 'Лук репчатый', category: 'Овощи', quantity: '1-1.5', unit: 'кг' },
  { name: 'Капуста белокочанная или пекинская', category: 'Овощи', quantity: '1', unit: 'кочан' },
  { name: 'Свёкла', category: 'Овощи', quantity: '1-2', unit: 'кг' },
  { name: 'Тыква', category: 'Овощи', quantity: '1-2', unit: 'кг' },
  { name: 'Замороженные овощные смеси/брокколи/цветная капуста', category: 'Овощи', quantity: '1-2', unit: 'кг' },
  
  // Фрукты, ягоды, орехи
  { name: 'Яблоки', category: 'Фрукты', quantity: '1.5-2', unit: 'кг' },
  { name: 'Бананы/цитрусовые', category: 'Фрукты', quantity: '1-1.5', unit: 'кг' },
  { name: 'Замороженные ягоды', category: 'Фрукты', quantity: '0.5-1', unit: 'кг' },
  { name: 'Орехи (арахис, грецкие, миндаль)', category: 'Орехи', quantity: '300-500', unit: 'г' },
  
  // Жиры, соусы, прочее
  { name: 'Масло растительное (подсолнечное/оливковое)', category: 'Жиры и масла', quantity: '0.5', unit: 'л' },
  { name: 'Семечки подсолнечника/тыквы', category: 'Орехи', quantity: '200-300', unit: 'г' },
  { name: 'Растительное молоко (овсяное, рисовое, миндальное)', category: 'Напитки', quantity: '1-2', unit: 'л' },
  { name: 'Томатная паста/помидоры в собственном соку', category: 'Соусы', quantity: '2-3', unit: 'банки' },
  { name: 'Соль', category: 'Специи', quantity: null, unit: null },
  { name: 'Перец', category: 'Специи', quantity: null, unit: null },
  { name: 'Базовые специи', category: 'Специи', quantity: null, unit: null },
  { name: 'Чай/кофе', category: 'Напитки', quantity: null, unit: null },
  { name: 'Тёмный шоколад или сухофрукты', category: 'Прочее', quantity: null, unit: null },
];

async function fillPantry(workspaceId) {
  try {
    // Присоединяемся к workspace
    console.log(`Присоединяемся к workspace: ${workspaceId}`);
    const joinResponse = await fetch(`${API_BASE}/workspace/${workspaceId}/join`, {
      method: 'POST'
    });

    if (!joinResponse.ok) {
      throw new Error(`Ошибка присоединения: ${joinResponse.statusText}`);
    }

    const joinData = await joinResponse.json();
    
    if (!joinData.can_access) {
      throw new Error('Не удалось получить доступ к workspace');
    }

    const clientToken = joinData.client_token;
    const headers = {
      'Content-Type': 'application/json',
      'X-Client-Token': clientToken,
      'X-Workspace-Id': workspaceId
    };

    console.log(`Успешно подключились. Добавляем ${products.length} продуктов...`);

    // Добавляем продукты
    for (const product of products) {
      const response = await fetch(`${API_BASE}/products`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          name: product.name,
          category: product.category,
          in_stock: false,
          quantity: product.quantity,
          unit: product.unit
        })
      });

      if (!response.ok) {
        console.error(`Ошибка при добавлении ${product.name}: ${response.statusText}`);
      } else {
        console.log(`✓ Добавлен: ${product.name}`);
      }
    }

    console.log('\n✅ Корзина успешно заполнена!');
    console.log(`Workspace ID: ${workspaceId}`);
    console.log(`Откройте http://localhost:5173 и введите workspace ID: ${workspaceId}`);

  } catch (error) {
    console.error('Ошибка:', error.message);
    process.exit(1);
  }
}

// Получаем workspace ID из аргументов или создаём новый
const workspaceId = process.argv[2] || 'default';

fillPantry(workspaceId);



