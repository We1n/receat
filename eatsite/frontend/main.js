/**
 * Shared Pantry PWA - Frontend
 * 
 * Server-first архитектура:
 * - Все изменения сразу отправляются на сервер
 * - WebSocket для получения обновлений
 * - Нет локального кеширования данных
 */

// Импортируем стили
import './styles.css';

// Используем относительные пути для API (проксируется через server.js)
// Для продакшена можно задать через переменные окружения VITE_API_URL и VITE_WS_URL
// Если VITE_API_URL не задан, используем '/eat' для продакшена (когда base = '/eat/')
const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.MODE === 'production' ? '/eat' : '');
// WebSocket использует текущий хост с заменой протокола
// WebSocket подключается напрямую к backend на порт 3000
const getWSBase = () => {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL;
  }
  // Определяем WebSocket URL на основе текущего хоста
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const hostname = window.location.hostname; // Только hostname без порта
  // WebSocket подключается напрямую к backend на порт 3000
  // Для HTTPS используем тот же hostname (nginx проксирует), для HTTP - добавляем порт 3000
  if (protocol === 'wss:') {
    // HTTPS - nginx проксирует WebSocket, используем тот же hostname
    return `${protocol}//${hostname}/ws`;
  } else {
    // HTTP - подключаемся напрямую к backend на порт 3000
    return `${protocol}//${hostname}:3000/ws`;
  }
};
const WS_BASE = getWSBase();

// State
let workspaceId = null;
let clientToken = null;
let ws = null;
let currentProducts = [];
let currentRecipes = [];
let baseBasket = [];
let currentPrices = {};
let stores = [];

// DOM Elements (инициализируются после загрузки DOM)
let screens = {};
let productCategories = [];
let editingProductId = null;
let editingRecipeId = null;
let currentTab = 'need'; // 'home', 'need', 'base', 'wishlist'
let wishlistProducts = [];

// Инициализация DOM элементов
function initDOMElements() {
  screens = {
    publicLanding: document.getElementById('public-landing'),
    menuScreen: document.getElementById('menu-screen'),
    productEdit: document.getElementById('product-edit'),
    recipes: document.getElementById('recipes'),
    recipeEdit: document.getElementById('recipe-edit')
  };
}

// Инициализация
function init() {
  // Инициализируем DOM элементы
  initDOMElements();
  
  // Инициализируем тему
  initTheme();
  
  // Проверяем сохранённый токен
  clientToken = localStorage.getItem('client_token');
  workspaceId = localStorage.getItem('workspace_id');

  if (clientToken && workspaceId) {
    connectToWorkspace(workspaceId, clientToken);
  } else {
    showScreen('publicLanding');
    // Hide bottom nav on public landing
    const bottomNav = document.getElementById('bottom-nav');
    if (bottomNav) {
      bottomNav.classList.add('hidden');
    }
  }

  setupEventListeners();
}

// Инициализация темы
function initTheme() {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
}

// Переключение темы
function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
}

function setupEventListeners() {
  // Theme toggle
  document.getElementById('theme-toggle-btn')?.addEventListener('click', toggleTheme);
  
  // Join workspace
  document.getElementById('join-btn')?.addEventListener('click', async () => {
    const input = document.getElementById('workspace-input');
    const id = input.value.trim();
    if (id) {
      await joinWorkspace(id);
    }
  });

  // Tab navigation
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      switchTab(tab);
    });
  });

  // Add product button
  document.getElementById('add-product-btn')?.addEventListener('click', () => {
    openProductForm();
  });

  // Init basket button
  document.getElementById('init-basket-btn')?.addEventListener('click', async () => {
    await initBasket();
  });

  // Edit basket button
  document.getElementById('edit-basket-btn')?.addEventListener('click', () => {
    openBasketEditor();
  });

  // Switch workspace button
  document.getElementById('switch-workspace-btn')?.addEventListener('click', () => {
    if (confirm('Выйти из текущего воркспейса и переключиться на другой?')) {
      switchWorkspace();
    }
  });

  // FAQ button
  document.getElementById('faq-btn')?.addEventListener('click', () => {
    showFAQ();
  });

  // Close edit form
  document.getElementById('close-edit-btn')?.addEventListener('click', () => {
    showScreen('menuScreen');
    updateBottomNav('products');
  });

  // Delete product
  document.getElementById('delete-product-btn')?.addEventListener('click', async () => {
    if (editingProductId && confirm('Удалить продукт?')) {
      await deleteProduct(editingProductId);
      showScreen('menuScreen');
      updateBottomNav('products');
    }
  });

  // Bottom Navigation
  document.getElementById('nav-products-tab')?.addEventListener('click', () => {
    showScreen('menuScreen');
    updateBottomNav('products');
  });

  document.getElementById('nav-recipes-tab')?.addEventListener('click', () => {
    showScreen('recipes');
    renderRecipes();
    updateBottomNav('recipes');
  });

  // Recipes
  document.getElementById('add-recipe-btn')?.addEventListener('click', () => {
    openRecipeForm();
  });

  document.getElementById('close-recipe-btn')?.addEventListener('click', () => {
    showScreen('recipes');
    updateBottomNav('recipes');
  });

  document.getElementById('delete-recipe-btn')?.addEventListener('click', async () => {
    if (editingRecipeId && confirm('Удалить рецепт?')) {
      await deleteRecipe(editingRecipeId);
      showScreen('recipes');
      updateBottomNav('recipes');
    }
  });

  // Recipe form submit
  document.getElementById('recipe-edit-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('edit-recipe-name-input').value;
    const productsInput = document.getElementById('edit-recipe-products').value;
    const notes = document.getElementById('edit-recipe-notes').value;

    const productIds = productsInput.split(',').map(s => s.trim()).filter(Boolean);

    if (editingRecipeId) {
      await updateRecipe(editingRecipeId, { name, product_ids: productIds, notes: notes || null });
    } else {
      await createRecipe({ name, product_ids: productIds, notes: notes || null });
    }
    showScreen('recipes');
    updateBottomNav('recipes');
  });
}

function switchWorkspace() {
  // Закрываем WebSocket соединение
  if (ws) {
    ws.close();
    ws = null;
  }
  
  // Очищаем данные
  clientToken = null;
  workspaceId = null;
  currentProducts = [];
  currentRecipes = [];
  
  // Очищаем localStorage
  localStorage.removeItem('client_token');
  localStorage.removeItem('workspace_id');
  
  // Показываем экран входа
  showScreen('publicLanding');
  const bottomNav = document.getElementById('bottom-nav');
  if (bottomNav) {
    bottomNav.classList.add('hidden');
  }
  
  // Очищаем поле ввода
  const input = document.getElementById('workspace-input');
  if (input) {
    input.value = '';
    input.focus();
  }
}

async function joinWorkspace(id) {
  try {
    const response = await fetch(`${API_BASE}/workspace/${id}/join`, {
      method: 'POST'
    });

    const data = await response.json();

    if (data.can_access && data.client_token) {
      clientToken = data.client_token;
      workspaceId = data.workspace_id;
      localStorage.setItem('client_token', clientToken);
      localStorage.setItem('workspace_id', workspaceId);
      connectToWorkspace(workspaceId, clientToken);
    } else {
      const maxClients = data.error?.match(/max (\d+) clients/)?.[1] || '2';
      showToast(`Workspace переполнен (максимум ${maxClients} клиентов)`, 'warning', 5000);
    }
  } catch (error) {
    console.error('Failed to join workspace:', error);
    showToast('Ошибка подключения к workspace', 'error', 5000);
  }
}

function connectToWorkspace(id, token) {
  // Закрываем предыдущее соединение
  if (ws) {
    ws.close();
  }

  // Подключаемся к WebSocket
  ws = new WebSocket(`${WS_BASE}?workspace_id=${id}&client_token=${token}`);

  ws.onopen = () => {
    console.log('WebSocket connected');
    loadInitialState();
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleWebSocketMessage(message);
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
    // Показываем публичный экран при потере соединения
    showScreen('publicLanding');
  };
}

// Вспомогательная функция для создания заголовков
function getAuthHeaders() {
  return {
    'X-Client-Token': clientToken,
    'X-Workspace-Id': workspaceId
  };
}

// Toast Notifications
function showToast(message, type = 'info', duration = 3000) {
  const container = getOrCreateToastContainer();
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const icons = {
    success: '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>',
    error: '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
    info: '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
    warning: '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
  };
  
  toast.innerHTML = `
    ${icons[type] || icons.info}
    <div class="toast-content">${message}</div>
    <button class="toast-close" aria-label="Закрыть">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    </button>
  `;
  
  const closeBtn = toast.querySelector('.toast-close');
  const closeToast = () => {
    toast.classList.add('slide-out');
    setTimeout(() => toast.remove(), 300);
  };
  
  closeBtn.addEventListener('click', closeToast);
  container.appendChild(toast);
  
  if (duration > 0) {
    setTimeout(closeToast, duration);
  }
  
  return toast;
}

function getOrCreateToastContainer() {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  return container;
}

// Skeleton Loaders
function showSkeletonLoaders(containerId, count = 6) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  container.innerHTML = Array(count).fill(0).map(() => `
    <div class="skeleton-product">
      <div class="skeleton-line skeleton-title"></div>
      <div class="skeleton-line skeleton-category short"></div>
      <div class="skeleton-actions">
        <div class="skeleton skeleton-button"></div>
        <div class="skeleton skeleton-button"></div>
        <div class="skeleton skeleton-button"></div>
        <div class="skeleton skeleton-button"></div>
      </div>
    </div>
  `).join('');
}

async function loadInitialState() {
  try {
    // Показываем skeleton loaders
    showSkeletonLoaders('products-out-list', 6);
    showSkeletonLoaders('products-in-list', 6);
    
    // Загружаем категории, состояние, магазины и цены параллельно для максимальной скорости
    const [categoriesResponse, stateResponse, storesResponse, pricesResponse] = await Promise.all([
      fetch(`${API_BASE}/categories`),
      fetch(`${API_BASE}/workspace/${workspaceId}/state`, {
        headers: getAuthHeaders()
      }),
      fetch(`${API_BASE}/stores`),
      fetch(`${API_BASE}/prices`, {
        headers: getAuthHeaders()
      }).catch(() => ({ ok: false })) // Если цены не загрузились, продолжаем
    ]);

    // Обрабатываем категории
    if (categoriesResponse.ok) {
      productCategories = await categoriesResponse.json();
      populateCategorySelect();
    }

    // Обрабатываем магазины
    if (storesResponse.ok) {
      const storesData = await storesResponse.json();
      stores = storesData.stores || [];
    }

    // Обрабатываем цены
    if (pricesResponse.ok) {
      currentPrices = await pricesResponse.json();
    }

    // Обрабатываем состояние
    if (stateResponse.ok) {
      const contentType = stateResponse.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await stateResponse.text();
        console.error('Expected JSON but got:', contentType, text.substring(0, 200));
        throw new Error(`Server returned ${contentType} instead of JSON. Response: ${text.substring(0, 100)}`);
      }
      
      const data = await stateResponse.json();
      currentProducts = data.products || [];
      currentRecipes = data.recipes || [];
      wishlistProducts = currentProducts.filter(p => p.wishlist) || [];
      
      // Показываем экран сразу для мгновенной отрисовки
      showScreen('menuScreen');
      switchTab('need');
      updateBottomNav('products');
      
      // Рендерим основные элементы сразу
      renderProducts();
      renderRecipes();
      renderWishlist();
      
      // Загружаем и рендерим базовую корзину асинхронно (не блокируем основной интерфейс)
      loadBaseBasket().then(() => {
        renderBaseBasket();
      });
    } else {
      const text = await stateResponse.text();
      console.error('State response error:', stateResponse.status, stateResponse.statusText, text.substring(0, 200));
      throw new Error(`Failed to load state: ${stateResponse.status} ${stateResponse.statusText}`);
    }
  } catch (error) {
    console.error('Failed to load initial state:', error);
    showToast(`Ошибка загрузки данных: ${error.message}`, 'error', 5000);
  }
}

function populateCategorySelect() {
  const select = document.getElementById('edit-category');
  if (!select) return;
  
  select.innerHTML = '<option value="">Выберите категорию</option>' +
    productCategories.map(cat => `<option value="${cat}">${cat}</option>`).join('');
}

function handleWebSocketMessage(message) {
  switch (message.type) {
    case 'state':
      currentProducts = message.data.products || [];
      currentRecipes = message.data.recipes || [];
      wishlistProducts = currentProducts.filter(p => p.wishlist) || [];
      renderProducts();
      renderWishlist();
      break;
    case 'product_created':
    case 'product_updated':
      const index = currentProducts.findIndex(p => p.id === message.data.id);
      if (index >= 0) {
        currentProducts[index] = message.data;
      } else {
        currentProducts.push(message.data);
      }
      wishlistProducts = currentProducts.filter(p => p.wishlist) || [];
      renderProducts();
      renderWishlist();
      break;
    case 'product_deleted':
      currentProducts = currentProducts.filter(p => p.id !== message.data.id);
      wishlistProducts = currentProducts.filter(p => p.wishlist) || [];
      renderProducts();
      renderWishlist();
      break;
    case 'recipe_created':
    case 'recipe_updated':
      const recipeIndex = currentRecipes.findIndex(r => r.id === message.data.id);
      if (recipeIndex >= 0) {
        currentRecipes[recipeIndex] = message.data;
      } else {
        currentRecipes.push(message.data);
      }
      renderRecipes();
      break;
    case 'recipe_deleted':
      currentRecipes = currentRecipes.filter(r => r.id !== message.data.id);
      renderRecipes();
      break;
    case 'price_updated':
      if (message.data && message.data.product_name) {
        currentPrices[message.data.product_name] = message.data.price_data;
        renderProducts(); // Перерисовываем продукты для обновления цен
      }
      break;
    case 'price_deleted':
      if (message.data && message.data.product_name) {
        if (message.data.store_id) {
          // Удалена цена в конкретном магазине
          if (currentPrices[message.data.product_name]) {
            delete currentPrices[message.data.product_name].stores[message.data.store_id];
            // Обновляем best_price и best_store
            const stores = currentPrices[message.data.product_name].stores;
            let bestPrice = null;
            let bestStore = null;
            for (const [sid, storeData] of Object.entries(stores)) {
              const price = storeData.price;
              if (price !== null && price !== undefined) {
                if (bestPrice === null || price < bestPrice) {
                  bestPrice = price;
                  bestStore = sid;
                }
              }
            }
            currentPrices[message.data.product_name].best_price = bestPrice;
            currentPrices[message.data.product_name].best_store = bestStore;
            if (Object.keys(stores).length === 0) {
              delete currentPrices[message.data.product_name];
            }
          }
        } else {
          // Удалены все цены продукта
          delete currentPrices[message.data.product_name];
        }
        renderProducts(); // Перерисовываем продукты для обновления цен
      }
      break;
  }
}

function renderProducts() {
  const outOfStock = currentProducts.filter(p => !p.in_stock);
  const inStock = currentProducts.filter(p => p.in_stock);

  renderProductList('products-out-list', outOfStock);
  renderProductList('products-in-list', inStock);
}

function renderProductList(containerId, products) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (products.length === 0) {
    container.innerHTML = '<p class="empty-message">Нет продуктов</p>';
    return;
  }

  container.innerHTML = products.map(product => {
    const isInStock = product.in_stock;
    const toggleIcon = isInStock ? 'minus' : 'plus';
    const toggleTitle = isInStock ? 'Убрать из "В наличии"' : 'Добавить в "В наличии"';
    const toggleClass = isInStock ? 'toggle-stock-btn remove-btn' : 'toggle-stock-btn add-btn';
    
    // Получаем цену продукта
    const productName = product.name.toLowerCase();
    const priceData = currentPrices[productName];
    let priceDisplay = '';
    
    if (priceData && priceData.best_price !== null && priceData.best_price !== undefined) {
      const bestPrice = priceData.best_price;
      const bestStoreId = priceData.best_store;
      const bestStore = stores.find(s => s.id === bestStoreId);
      const storeName = bestStore ? bestStore.name : bestStoreId;
      
      // Показываем лучшую цену и количество магазинов
      const storeCount = Object.keys(priceData.stores || {}).length;
      priceDisplay = `
        <div class="product-price">
          <span class="price-value">${bestPrice.toFixed(2)} ₽</span>
          <span class="price-store">${storeName}</span>
          ${storeCount > 1 ? `<span class="price-stores-count">(${storeCount} магазинов)</span>` : ''}
        </div>
      `;
    }
    
    return `
    <div class="product-item" data-id="${product.id}">
      <div class="product-info">
        <span class="product-name">${product.name}</span>
        <span class="product-category">${product.category}</span>
        ${product.quantity ? `<span class="product-quantity">${product.quantity} ${product.unit || ''}</span>` : ''}
        ${priceDisplay}
      </div>
      <div class="product-actions">
        <button class="${toggleClass} icon-btn" onclick="toggleProductStock('${product.id}')" title="${toggleTitle}" aria-label="${toggleTitle}">
          ${toggleIcon === 'plus' ? `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          ` : `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          `}
        </button>
        <button class="price-btn icon-btn" onclick="openPriceDialog('${product.id}', '${product.name.replace(/'/g, "\\'")}')" title="Установить цену" aria-label="Установить цену">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="1" x2="12" y2="23"></line>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
          </svg>
        </button>
        <button class="edit-btn icon-btn" onclick="editProduct('${product.id}')" title="Редактировать" aria-label="Редактировать">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
        </button>
        <button class="delete-btn-inline icon-btn" onclick="deleteProductQuick('${product.id}', '${product.name.replace(/'/g, "\\'")}')" title="Удалить" aria-label="Удалить">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            <line x1="10" y1="11" x2="10" y2="17"></line>
            <line x1="14" y1="11" x2="14" y2="17"></line>
          </svg>
        </button>
      </div>
    </div>
  `;
  }).join('');
}

// Автоподсказка категории на основе названия
function suggestCategory(productName) {
  if (!productName) return null;
  
  const name = productName.toLowerCase();
  
  // Словарь соответствий
  const categoryMap = {
    'яйц': 'Яйца',
    'молок': 'Молочные продукты',
    'сыр': 'Молочные продукты',
    'творог': 'Молочные продукты',
    'сметан': 'Молочные продукты',
    'йогурт': 'Молочные продукты',
    'кефир': 'Молочные продукты',
    'куриц': 'Мясо',
    'говядин': 'Мясо',
    'свинин': 'Мясо',
    'индейк': 'Мясо',
    'рыб': 'Рыба',
    'минтай': 'Рыба',
    'хек': 'Рыба',
    'лосось': 'Рыба',
    'фасоль': 'Бобовые',
    'чечевиц': 'Бобовые',
    'нут': 'Бобовые',
    'гречк': 'Крупы',
    'рис': 'Крупы',
    'овсян': 'Крупы',
    'макарон': 'Крупы',
    'хлеб': 'Хлеб',
    'картофел': 'Овощи',
    'морков': 'Овощи',
    'лук': 'Овощи',
    'капуст': 'Овощи',
    'помидор': 'Овощи',
    'огурц': 'Овощи',
    'яблок': 'Фрукты',
    'банан': 'Фрукты',
    'апельсин': 'Фрукты',
    'орех': 'Орехи',
    'семечк': 'Орехи',
    'соль': 'Специи',
    'перец': 'Специи',
    'специ': 'Специи',
    'чай': 'Напитки',
    'кофе': 'Напитки',
    'масло': 'Жиры и масла',
    'паста': 'Соусы',
    'кетчуп': 'Соусы',
    'майонез': 'Соусы'
  };
  
  for (const [keyword, category] of Object.entries(categoryMap)) {
    if (name.includes(keyword)) {
      return category;
    }
  }
  
  return null;
}

// Валидация количества в зависимости от единицы измерения
function validateQuantity(quantity, unit) {
  if (!quantity) return { valid: true };
  
  const qty = parseFloat(quantity);
  if (isNaN(qty) || qty < 0) {
    return { valid: false, message: 'Количество должно быть положительным числом' };
  }
  
  // Для штучных единиц - только целые числа
  const pieceUnits = ['шт', 'штук', 'штуки', 'шт.', 'piece', 'pcs'];
  if (unit && pieceUnits.some(u => unit.toLowerCase().includes(u.toLowerCase()))) {
    if (!Number.isInteger(qty)) {
      return { valid: false, message: 'Для штучных единиц количество должно быть целым числом' };
    }
  }
  
  return { valid: true };
}

function openProductForm(productId = null) {
  editingProductId = productId;
  const product = productId ? currentProducts.find(p => p.id === productId) : null;

  document.getElementById('edit-product-name').textContent = product ? product.name : 'Новый продукт';
  document.getElementById('edit-name').value = product?.name || '';
  document.getElementById('edit-category').value = product?.category || '';
  document.getElementById('edit-in-stock').checked = product?.in_stock || false;
  document.getElementById('edit-wishlist').checked = product?.wishlist || false;
  document.getElementById('edit-quantity').value = product?.quantity || '';
  document.getElementById('edit-unit').value = product?.unit || '';
  
  const deleteBtn = document.getElementById('delete-product-btn');
  if (deleteBtn) {
    deleteBtn.style.display = productId ? 'block' : 'none';
  }
  
  // Добавляем обработчики для автоподсказки и валидации
  const nameInput = document.getElementById('edit-name');
  const categorySelect = document.getElementById('edit-category');
  const quantityInput = document.getElementById('edit-quantity');
  const unitInput = document.getElementById('edit-unit');
  
  // Удаляем старые обработчики если есть
  const newNameHandler = (e) => {
    if (!productId) { // Только для новых продуктов
      const suggested = suggestCategory(e.target.value);
      if (suggested && !categorySelect.value) {
        categorySelect.value = suggested;
        // Визуальная подсказка
        categorySelect.style.backgroundColor = '#e0f2fe';
        setTimeout(() => {
          categorySelect.style.backgroundColor = '';
        }, 2000);
      }
    }
  };
  
  const newQuantityHandler = () => {
    const quantity = quantityInput.value;
    const unit = unitInput.value;
    const validation = validateQuantity(quantity, unit);
    
    if (!validation.valid) {
      quantityInput.setCustomValidity(validation.message);
      quantityInput.reportValidity();
    } else {
      quantityInput.setCustomValidity('');
    }
  };
  
  const newUnitHandler = () => {
    newQuantityHandler(); // Перепроверяем при изменении единицы
    
    // Динамически меняем step для количества в зависимости от единицы
    const unit = unitInput.value.toLowerCase();
    const pieceUnits = ['шт', 'штук', 'штуки', 'шт.', 'piece', 'pcs'];
    const isPieceUnit = pieceUnits.some(u => unit.includes(u));
    
    if (isPieceUnit) {
      quantityInput.step = '1';
      quantityInput.setAttribute('step', '1');
    } else {
      quantityInput.step = '0.1';
      quantityInput.setAttribute('step', '0.1');
    }
  };
  
  // Удаляем старые обработчики
  nameInput.removeEventListener('input', nameInput._categoryHandler);
  quantityInput.removeEventListener('input', quantityInput._quantityHandler);
  quantityInput.removeEventListener('blur', quantityInput._quantityHandler);
  unitInput.removeEventListener('input', unitInput._unitHandler);
  unitInput.removeEventListener('blur', unitInput._unitHandler);
  
  // Сохраняем ссылки для последующего удаления
  nameInput._categoryHandler = newNameHandler;
  quantityInput._quantityHandler = newQuantityHandler;
  unitInput._unitHandler = newUnitHandler;
  
  // Добавляем новые обработчики
  nameInput.addEventListener('input', newNameHandler);
  quantityInput.addEventListener('input', newQuantityHandler);
  quantityInput.addEventListener('blur', newQuantityHandler);
  unitInput.addEventListener('input', newUnitHandler);
  unitInput.addEventListener('blur', newUnitHandler);
  
  // Устанавливаем правильный step при загрузке формы
  if (product?.unit) {
    const unit = product.unit.toLowerCase();
    const pieceUnits = ['шт', 'штук', 'штуки', 'шт.', 'piece', 'pcs'];
    const isPieceUnit = pieceUnits.some(u => unit.includes(u));
    quantityInput.step = isPieceUnit ? '1' : '0.1';
  }

  // Обновляем обработчик формы
  const form = document.getElementById('product-edit-form');
  const existingHandler = form._submitHandler;
  if (existingHandler) {
    form.removeEventListener('submit', existingHandler);
  }

  const submitHandler = async (e) => {
    e.preventDefault();
    const name = document.getElementById('edit-name').value.trim();
    const category = document.getElementById('edit-category').value;
    const inStock = document.getElementById('edit-in-stock').checked;
    const wishlist = document.getElementById('edit-wishlist').checked;
    const quantity = document.getElementById('edit-quantity').value.trim();
    const unit = document.getElementById('edit-unit').value.trim();

    if (!name || !category) {
      showToast('Заполните название и категорию', 'warning');
      return;
    }
    
    // Валидация количества
    if (quantity) {
      const validation = validateQuantity(quantity, unit);
      if (!validation.valid) {
        showToast(validation.message, 'warning');
        return;
      }
    }

    if (productId) {
      await updateProduct(productId, {
        name,
        category,
        in_stock: inStock,
        wishlist: wishlist,
        quantity: quantity || null,
        unit: unit || null
      });
    } else {
      await createProduct({
        name,
        category,
        in_stock: inStock,
        wishlist: wishlist,
        quantity: quantity || null,
        unit: unit || null
      });
      showToast(productId ? 'Продукт обновлён' : 'Продукт создан', 'success');
    }
    showScreen('menuScreen');
    updateBottomNav('products');
  };

  form._submitHandler = submitHandler;
  form.addEventListener('submit', submitHandler);

  showScreen('productEdit');
}

window.editProduct = function(productId) {
  openProductForm(productId);
};

window.deleteProductQuick = async function(productId, productName) {
  if (confirm(`Удалить "${productName}"?`)) {
    try {
      const result = await deleteProduct(productId);
      // Если продукт уже был удален, список уже обновлен
      // Иначе обновится через WebSocket
      if (result && result.alreadyDeleted) {
        console.log('Product was already deleted, list updated locally');
      }
      showToast('Продукт удалён', 'success');
    } catch (error) {
      console.error('Ошибка удаления:', error);
      showToast('Ошибка удаления продукта', 'error');
    }
  }
};

window.toggleProductStock = async function(productId) {
  const product = currentProducts.find(p => p.id === productId);
  if (!product) return;

  const newStatus = !product.in_stock;
  
  try {
    await updateProduct(productId, {
      in_stock: newStatus
    });
    // Список обновится автоматически через WebSocket
  } catch (error) {
    console.error('Ошибка переключения статуса:', error);
    showToast('Ошибка обновления статуса продукта', 'error');
  }
};

async function createProduct(productData) {
  try {
    const response = await fetch(`${API_BASE}/products`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(productData)
    });

    if (!response.ok) {
      throw new Error('Failed to create product');
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to create product:', error);
    showToast('Ошибка создания продукта', 'error');
    throw error;
  }
}

async function updateProduct(productId, updates) {
  try {
    const response = await fetch(`${API_BASE}/products/${productId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(updates)
    });

    if (!response.ok) {
      throw new Error('Failed to update product');
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to update product:', error);
    showToast('Ошибка обновления продукта', 'error');
    throw error;
  }
}

async function deleteProduct(productId) {
  try {
    if (!workspaceId || !clientToken) {
      throw new Error('Не авторизован. Переподключитесь к workspace.');
    }

    const headers = getAuthHeaders();
    console.log('Deleting product:', productId, 'Workspace:', workspaceId, 'Headers:', headers);

    const response = await fetch(`${API_BASE}/products/${productId}`, {
      method: 'DELETE',
      headers: headers
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Delete error response:', response.status, errorData);
      
      if (response.status === 404) {
        // Продукт уже удален - просто обновим список локально
        currentProducts = currentProducts.filter(p => p.id !== productId);
        renderProducts();
        return { success: true, alreadyDeleted: true };
      }
      
      if (response.status === 401 || response.status === 403) {
        throw new Error('Нет доступа. Переподключитесь к workspace.');
      }
      
      throw new Error(errorData.error || `Ошибка сервера: ${response.status}`);
    }
    
    // Успешное удаление - список обновится через WebSocket
    const result = await response.json();
    console.log('Product deleted successfully:', result);
    return result;
  } catch (error) {
    console.error('Failed to delete product:', error);
    // Не показываем alert если продукт уже был удален
    if (!error.message.includes('уже был удалён') && !error.alreadyDeleted) {
      alert(`Ошибка удаления: ${error.message}`);
    }
    throw error;
  }
}

// Recipes functions
function renderRecipes() {
  const container = document.getElementById('recipes-list');
  if (!container) return;

  if (currentRecipes.length === 0) {
    container.innerHTML = '<p class="empty-message">Нет рецептов</p>';
    return;
  }

  container.innerHTML = currentRecipes.map(recipe => {
    const productNames = recipe.product_ids
      .map(id => {
        const product = currentProducts.find(p => p.id === id);
        return product ? product.name : id;
      })
      .join(', ');

    return `
      <div class="recipe-item" data-id="${recipe.id}">
        <div class="recipe-info">
          <h3>${recipe.name}</h3>
          <p class="recipe-products">Продукты: ${productNames || 'не указаны'}</p>
          ${recipe.notes ? `<p class="recipe-notes">${recipe.notes}</p>` : ''}
        </div>
        <button class="edit-btn icon-btn" onclick="editRecipe('${recipe.id}')" title="Редактировать" aria-label="Редактировать">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
        </button>
      </div>
    `;
  }).join('');
}

function openRecipeForm(recipeId = null) {
  editingRecipeId = recipeId;
  const recipe = recipeId ? currentRecipes.find(r => r.id === recipeId) : null;

  document.getElementById('edit-recipe-name').textContent = recipe ? recipe.name : 'Новый рецепт';
  document.getElementById('edit-recipe-name-input').value = recipe?.name || '';
  document.getElementById('edit-recipe-products').value = recipe?.product_ids?.join(', ') || '';
  document.getElementById('edit-recipe-notes').value = recipe?.notes || '';

  const deleteBtn = document.getElementById('delete-recipe-btn');
  if (deleteBtn) {
    deleteBtn.style.display = recipeId ? 'block' : 'none';
  }

  showScreen('recipeEdit');
}

window.editRecipe = function(recipeId) {
  openRecipeForm(recipeId);
};

async function createRecipe(recipeData) {
  try {
    const response = await fetch(`${API_BASE}/recipes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(recipeData)
    });

    if (!response.ok) {
      throw new Error('Failed to create recipe');
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to create recipe:', error);
    alert('Ошибка создания рецепта');
  }
}

async function updateRecipe(recipeId, updates) {
  try {
    const response = await fetch(`${API_BASE}/recipes/${recipeId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(updates)
    });

    if (!response.ok) {
      throw new Error('Failed to update recipe');
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to update recipe:', error);
    alert('Ошибка обновления рецепта');
  }
}

async function deleteRecipe(recipeId) {
  try {
    const response = await fetch(`${API_BASE}/recipes/${recipeId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to delete recipe');
    }
  } catch (error) {
    console.error('Failed to delete recipe:', error);
    alert('Ошибка удаления рецепта');
  }
}

function showScreen(screenName) {
  Object.values(screens).forEach(screen => {
    if (screen) screen.classList.add('hidden');
  });
  screens[screenName]?.classList.remove('hidden');
  
  // Update bottom navigation visibility and active state
  const bottomNav = document.getElementById('bottom-nav');
  if (bottomNav) {
    // Hide nav on public landing and edit screens
    if (screenName === 'publicLanding' || screenName === 'productEdit' || screenName === 'recipeEdit') {
      bottomNav.classList.add('hidden');
    } else {
      bottomNav.classList.remove('hidden');
      // Update active state based on screen
      if (screenName === 'menuScreen') {
        updateBottomNav('products');
      } else if (screenName === 'recipes') {
        updateBottomNav('recipes');
      }
    }
  }
}

function updateBottomNav(activeTab) {
  const productsTab = document.getElementById('nav-products-tab');
  const recipesTab = document.getElementById('nav-recipes-tab');
  
  if (productsTab && recipesTab) {
    // Remove active state from all tabs
    productsTab.classList.remove('active');
    productsTab.removeAttribute('aria-current');
    recipesTab.classList.remove('active');
    recipesTab.removeAttribute('aria-current');
    
    // Set active state
    if (activeTab === 'products') {
      productsTab.classList.add('active');
      productsTab.setAttribute('aria-current', 'page');
    } else if (activeTab === 'recipes') {
      recipesTab.classList.add('active');
      recipesTab.setAttribute('aria-current', 'page');
    }
  }
}

// Tab switching functionality
function switchTab(tabName) {
  currentTab = tabName;
  
  // Update tab buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    const isActive = btn.dataset.tab === tabName;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-selected', isActive);
  });
  
  // Update tab panels
  document.querySelectorAll('.tab-panel').forEach(panel => {
    const isActive = panel.id === `tab-panel-${tabName}`;
    panel.classList.toggle('active', isActive);
    panel.setAttribute('aria-hidden', !isActive);
  });

  // Обновляем базовую корзину при переключении на таб
  if (tabName === 'base') {
    renderBaseBasket();
  }
}

// Render wishlist
function renderWishlist() {
  const container = document.getElementById('wishlist-list');
  if (!container) return;

  wishlistProducts = currentProducts.filter(p => p.wishlist) || [];

  if (wishlistProducts.length === 0) {
    container.innerHTML = '<p class="empty-message">Нет продуктов в списке желаний</p>';
    return;
  }

  renderProductList('wishlist-list', wishlistProducts);
}

async function loadBaseBasket() {
  if (!workspaceId || !clientToken) {
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/workspace/${workspaceId}/base-basket`, {
      headers: getAuthHeaders()
    });

    if (response.ok) {
      const data = await response.json();
      baseBasket = data.base_basket || [];
    }
  } catch (error) {
    console.error('Failed to load base basket:', error);
  }
}

function renderBaseBasket() {
  const container = document.getElementById('base-basket-list');
  if (!container) return;

  if (baseBasket.length === 0) {
    container.innerHTML = '<p class="empty-message">Базовая корзина пуста. Нажмите "Редактировать корзину" чтобы добавить продукты.</p>';
    return;
  }

  // Группируем по категориям
  const byCategory = {};
  baseBasket.forEach(item => {
    const cat = item.category || 'Прочее';
    if (!byCategory[cat]) {
      byCategory[cat] = [];
    }
    byCategory[cat].push(item);
  });

  container.innerHTML = Object.entries(byCategory)
    .map(([category, items]) => `
      <div class="basket-category">
        <h3>${category}</h3>
        <ul class="basket-items">
          ${items.map(item => `<li>${item.name}</li>`).join('')}
        </ul>
      </div>
    `).join('');
}

function openBasketEditor() {
  // Создаём модальное окно для редактирования
  const modal = document.createElement('div');
  modal.className = 'basket-editor-modal';
  modal.innerHTML = `
    <div class="basket-editor-content">
      <header>
        <h2>Редактирование базовой корзины</h2>
        <button class="close-btn" onclick="this.closest('.basket-editor-modal').remove()">✕</button>
      </header>
      <div class="basket-editor-body">
        <div id="basket-editor-list"></div>
        <button id="add-basket-item-btn" class="add-item-btn">+ Добавить продукт</button>
      </div>
      <div class="basket-editor-actions">
        <button id="save-basket-btn" class="save-btn">💾 Сохранить</button>
        <button class="cancel-btn" onclick="this.closest('.basket-editor-modal').remove()">Отмена</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // Рендерим список продуктов для редактирования
  renderBasketEditor();

  // Обработчики
  document.getElementById('add-basket-item-btn')?.addEventListener('click', () => {
    addBasketItem();
  });

  document.getElementById('save-basket-btn')?.addEventListener('click', async () => {
    await saveBaseBasket();
    modal.remove();
  });
}

function renderBasketEditor() {
  const container = document.getElementById('basket-editor-list');
  if (!container) return;

  if (baseBasket.length === 0) {
    container.innerHTML = '<p class="empty-message">Корзина пуста. Добавьте продукты.</p>';
    return;
  }

  container.innerHTML = baseBasket.map((item, index) => `
    <div class="basket-editor-item" data-index="${index}">
      <input type="text" class="basket-item-name" value="${item.name}" placeholder="Название продукта">
      <select class="basket-item-category">
        ${productCategories.map(cat => 
          `<option value="${cat}" ${cat === item.category ? 'selected' : ''}>${cat}</option>`
        ).join('')}
      </select>
      <button class="delete-basket-item-btn" onclick="removeBasketItem(${index})">🗑️</button>
    </div>
  `).join('');
}

function addBasketItem() {
  baseBasket.push({
    name: '',
    category: 'Прочее',
    in_stock: false
  });
  renderBasketEditor();
}

window.removeBasketItem = function(index) {
  baseBasket.splice(index, 1);
  renderBasketEditor();
};

async function saveBaseBasket() {
  if (!workspaceId || !clientToken) {
    alert('Не авторизован. Переподключитесь к workspace.');
    return;
  }

  // Собираем данные из формы
  const items = Array.from(document.querySelectorAll('.basket-editor-item')).map(itemEl => {
    const nameInput = itemEl.querySelector('.basket-item-name');
    const categorySelect = itemEl.querySelector('.basket-item-category');
    return {
      name: nameInput.value.trim(),
      category: categorySelect.value,
      in_stock: false
    };
  }).filter(item => item.name); // Убираем пустые

  try {
    const response = await fetch(`${API_BASE}/workspace/${workspaceId}/base-basket`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ base_basket: items })
    });

    if (!response.ok) {
      throw new Error('Failed to save base basket');
    }

    const result = await response.json();
    baseBasket = result.base_basket || [];
    renderBaseBasket();
    alert('✅ Базовая корзина сохранена!');
  } catch (error) {
    console.error('Failed to save base basket:', error);
    alert('Ошибка сохранения базовой корзины');
  }
}

async function initBasket() {
  if (!workspaceId || !clientToken) {
    alert('Не авторизован. Переподключитесь к workspace.');
    return;
  }

  if (!confirm('Добавить все продукты из базовой корзины в "Нужно купить"? Существующие продукты не будут дублироваться.')) {
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/workspace/${workspaceId}/init-basket`, {
      method: 'POST',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to init basket');
    }

    const result = await response.json();
    
    if (result.added > 0) {
      alert(`✅ Добавлено ${result.added} продуктов в "Нужно купить"!\nВсего продуктов: ${result.total}`);
      // Переключаемся на таб "Нужно" чтобы увидеть добавленные продукты
      switchTab('need');
      // Список обновится автоматически через WebSocket
    } else {
      alert('Все продукты из базовой корзины уже есть в вашем списке.');
    }
  } catch (error) {
    console.error('Failed to init basket:', error);
    alert('Ошибка добавления базовой корзины');
  }
}

function showFAQ() {
  const modal = document.createElement('div');
  modal.className = 'faq-modal';
  modal.innerHTML = `
    <div class="faq-content">
      <header>
        <h2>Помощь и FAQ</h2>
        <button class="close-btn" onclick="this.closest('.faq-modal').remove()">✕</button>
      </header>
      <div class="faq-body">
        <div class="faq-section">
          <h3>📋 Быстрая памятка</h3>
          <ul class="faq-list">
            <li><strong>Вкладка "Нужно":</strong> Продукты, которые нужно купить (in_stock: false)</li>
            <li><strong>Вкладка "Дома":</strong> Продукты, которые уже есть (in_stock: true)</li>
            <li><strong>Кнопка "+":</strong> Быстро добавить продукт в "Дома" (в наличии)</li>
            <li><strong>Кнопка "-":</strong> Быстро убрать продукт из "Дома" (нужно купить)</li>
            <li><strong>Кнопка ✏️:</strong> Редактировать продукт (название, категория, количество)</li>
            <li><strong>Кнопка 🗑️:</strong> Удалить продукт</li>
            <li><strong>Вкладка "Базовая":</strong> Настройте стандартный набор продуктов, который можно добавить одним нажатием</li>
            <li><strong>Вкладка "Хочухи":</strong> Список желаний (продукты с пометкой ⭐)</li>
          </ul>
        </div>
        <div class="faq-section">
          <h3>🔄 Смена воркспейса</h3>
          <p>Нажмите кнопку 🔄 в правом верхнем углу, чтобы выйти из текущего воркспейса и подключиться к другому. Каждый воркспейс имеет свой набор продуктов и базовую корзину.</p>
        </div>
        <div class="faq-section">
          <h3>👥 Работа в команде</h3>
          <p>Один воркспейс может иметь до 5 активных клиентов. Все изменения синхронизируются в реальном времени через WebSocket.</p>
        </div>
        <div class="faq-section">
          <h3>🛒 Базовая корзина</h3>
          <p>Настройте свой стандартный набор продуктов в вкладке "Базовая". Кнопка "Добавить в 'Нужно купить'" перенесёт все продукты из базовой корзины в список покупок (без дублирования существующих).</p>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

// Price management functions
window.openPriceDialog = function(productId, productName) {
  const product = currentProducts.find(p => p.id === productId);
  if (!product) return;
  
  const productNameLower = productName.toLowerCase();
  const priceData = currentPrices[productNameLower];
  
  // Создаем модальное окно для установки цены
  const modal = document.createElement('div');
  modal.className = 'price-modal';
  modal.innerHTML = `
    <div class="price-modal-content">
      <header>
        <h2>💰 Установить цену: ${productName}</h2>
        <button class="close-btn" onclick="this.closest('.price-modal').remove()">✕</button>
      </header>
      <div class="price-modal-body">
        <div class="price-form">
          <label>
            <span>Магазин:</span>
            <select id="price-store-select">
              ${stores.map(store => `<option value="${store.id}">${store.name}</option>`).join('')}
            </select>
          </label>
          <label>
            <span>Цена (₽):</span>
            <input type="number" id="price-value-input" step="0.01" min="0" placeholder="0.00">
          </label>
        </div>
        ${priceData && Object.keys(priceData.stores || {}).length > 0 ? `
          <div class="price-list">
            <h3>Текущие цены:</h3>
            <ul>
              ${Object.entries(priceData.stores).map(([storeId, storeData]) => {
                const store = stores.find(s => s.id === storeId);
                const storeName = store ? store.name : storeId;
                const isBest = storeId === priceData.best_store;
                return `
                  <li class="${isBest ? 'best-price' : ''}">
                    <span class="store-name">${storeName}:</span>
                    <span class="price-value">${storeData.price.toFixed(2)} ₽</span>
                    ${isBest ? '<span class="best-badge">🎯 Лучшая</span>' : ''}
                    <button class="delete-price-btn" onclick="deletePrice('${productNameLower}', '${storeId}')">🗑️</button>
                  </li>
                `;
              }).join('')}
            </ul>
            ${priceData.best_price !== null ? `
              <div class="best-price-info">
                🎯 Лучшая цена: <strong>${priceData.best_price.toFixed(2)} ₽</strong> 
                в <strong>${stores.find(s => s.id === priceData.best_store)?.name || priceData.best_store}</strong>
              </div>
            ` : ''}
          </div>
        ` : '<p class="no-prices">Цены не установлены</p>'}
      </div>
      <div class="price-modal-actions">
        <button id="save-price-btn" class="save-btn">💾 Сохранить цену</button>
        <button class="cancel-btn" onclick="this.closest('.price-modal').remove()">Отмена</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  // Обработчик сохранения
  document.getElementById('save-price-btn').addEventListener('click', async () => {
    const storeId = document.getElementById('price-store-select').value;
    const priceValue = parseFloat(document.getElementById('price-value-input').value);
    
    if (isNaN(priceValue) || priceValue < 0) {
      alert('Введите корректную цену');
      return;
    }
    
    try {
      await setPrice(productName, priceValue, storeId);
      modal.remove();
    } catch (error) {
      console.error('Failed to set price:', error);
      alert('Ошибка установки цены');
    }
  });
};

window.deletePrice = async function(productName, storeId) {
  if (!confirm('Удалить цену в этом магазине?')) {
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE}/prices/${encodeURIComponent(productName)}?store_id=${storeId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete price');
    }
    
    // Обновляем локальные данные
    if (currentPrices[productName]) {
      delete currentPrices[productName].stores[storeId];
      const stores = currentPrices[productName].stores;
      if (Object.keys(stores).length === 0) {
        delete currentPrices[productName];
      } else {
        // Пересчитываем лучшую цену
        let bestPrice = null;
        let bestStore = null;
        for (const [sid, storeData] of Object.entries(stores)) {
          const price = storeData.price;
          if (price !== null && price !== undefined) {
            if (bestPrice === null || price < bestPrice) {
              bestPrice = price;
              bestStore = sid;
            }
          }
        }
        currentPrices[productName].best_price = bestPrice;
        currentPrices[productName].best_store = bestStore;
      }
    }
    
    renderProducts();
    
    // Переоткрываем диалог для обновления списка цен
    const product = currentProducts.find(p => p.name.toLowerCase() === productName);
    if (product) {
      openPriceDialog(product.id, product.name);
    }
  } catch (error) {
    console.error('Failed to delete price:', error);
    alert('Ошибка удаления цены');
  }
};

async function setPrice(productName, price, storeId) {
  try {
    const response = await fetch(`${API_BASE}/prices`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        product_name: productName,
        price: price,
        store_id: storeId
      })
    });
    
    if (!response.ok) {
      throw new Error('Failed to set price');
    }
    
    const priceData = await response.json();
    currentPrices[productName.toLowerCase()] = priceData;
    renderProducts();
    
    return priceData;
  } catch (error) {
    console.error('Failed to set price:', error);
    throw error;
  }
}

// Запуск приложения после загрузки DOM
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

