/**
 * Shared Pantry PWA - Frontend
 * 
 * Server-first архитектура:
 * - Все изменения сразу отправляются на сервер
 * - WebSocket для получения обновлений
 * - Нет локального кеширования данных
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:3000';
const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:3000';

// State
let workspaceId = null;
let clientToken = null;
let ws = null;
let currentProducts = [];
let currentRecipes = [];

// DOM Elements (инициализируются после загрузки DOM)
let screens = {};
let productCategories = [];
let editingProductId = null;
let editingRecipeId = null;

// Инициализация DOM элементов
function initDOMElements() {
  screens = {
    publicLanding: document.getElementById('public-landing'),
    outOfStock: document.getElementById('out-of-stock'),
    inStock: document.getElementById('in-stock'),
    productEdit: document.getElementById('product-edit'),
    recipes: document.getElementById('recipes'),
    recipeEdit: document.getElementById('recipe-edit')
  };
}

// Инициализация
function init() {
  // Инициализируем DOM элементы
  initDOMElements();
  
  // Проверяем сохранённый токен
  clientToken = localStorage.getItem('client_token');
  workspaceId = localStorage.getItem('workspace_id');

  if (clientToken && workspaceId) {
    connectToWorkspace(workspaceId, clientToken);
  } else {
    showScreen('publicLanding');
  }

  setupEventListeners();
}

function setupEventListeners() {
  // Join workspace
  document.getElementById('join-btn')?.addEventListener('click', async () => {
    const input = document.getElementById('workspace-input');
    const id = input.value.trim();
    if (id) {
      await joinWorkspace(id);
    }
  });

  // Toggle views
  document.getElementById('toggle-view-btn')?.addEventListener('click', () => {
    showScreen('inStock');
  });

  document.getElementById('toggle-view-btn-2')?.addEventListener('click', () => {
    showScreen('outOfStock');
  });

  // Add product buttons
  document.getElementById('add-product-btn')?.addEventListener('click', () => {
    openProductForm();
  });

  document.getElementById('add-product-btn-2')?.addEventListener('click', () => {
    openProductForm();
  });

  // Close edit form
  document.getElementById('close-edit-btn')?.addEventListener('click', () => {
    showScreen('outOfStock');
  });

  // Delete product
  document.getElementById('delete-product-btn')?.addEventListener('click', async () => {
    if (editingProductId && confirm('Удалить продукт?')) {
      await deleteProduct(editingProductId);
      showScreen('outOfStock');
    }
  });

  // Navigation
  document.getElementById('nav-recipes-btn')?.addEventListener('click', () => {
    showScreen('recipes');
    renderRecipes();
  });

  document.getElementById('nav-recipes-btn-2')?.addEventListener('click', () => {
    showScreen('recipes');
    renderRecipes();
  });

  document.getElementById('nav-products-btn')?.addEventListener('click', () => {
    showScreen('outOfStock');
  });

  // Recipes
  document.getElementById('add-recipe-btn')?.addEventListener('click', () => {
    openRecipeForm();
  });

  document.getElementById('close-recipe-btn')?.addEventListener('click', () => {
    showScreen('recipes');
  });

  document.getElementById('delete-recipe-btn')?.addEventListener('click', async () => {
    if (editingRecipeId && confirm('Удалить рецепт?')) {
      await deleteRecipe(editingRecipeId);
      showScreen('recipes');
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
  });
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
      alert('Workspace переполнен (максимум 2 клиента)');
    }
  } catch (error) {
    console.error('Failed to join workspace:', error);
    alert('Ошибка подключения к workspace');
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

async function loadInitialState() {
  try {
    // Загружаем категории
    const categoriesResponse = await fetch(`${API_BASE}/categories`);
    if (categoriesResponse.ok) {
      productCategories = await categoriesResponse.json();
      populateCategorySelect();
    }

    // Загружаем состояние
    const response = await fetch(`${API_BASE}/workspace/${workspaceId}/state`, {
      headers: getAuthHeaders()
    });

    if (response.ok) {
      const data = await response.json();
      currentProducts = data.products || [];
      currentRecipes = data.recipes || [];
      renderProducts();
      renderRecipes();
      showScreen('outOfStock');
    } else {
      throw new Error('Failed to load state');
    }
  } catch (error) {
    console.error('Failed to load initial state:', error);
    alert('Ошибка загрузки данных');
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
      renderProducts();
      break;
    case 'product_created':
    case 'product_updated':
      const index = currentProducts.findIndex(p => p.id === message.data.id);
      if (index >= 0) {
        currentProducts[index] = message.data;
      } else {
        currentProducts.push(message.data);
      }
      renderProducts();
      break;
    case 'product_deleted':
      currentProducts = currentProducts.filter(p => p.id !== message.data.id);
      renderProducts();
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

  container.innerHTML = products.map(product => `
    <div class="product-item" data-id="${product.id}">
      <div class="product-info">
        <span class="product-name">${product.name}</span>
        <span class="product-category">${product.category}</span>
        ${product.quantity ? `<span class="product-quantity">${product.quantity} ${product.unit || ''}</span>` : ''}
      </div>
      <button class="edit-btn" onclick="editProduct('${product.id}')">Редактировать</button>
    </div>
  `).join('');
}

function openProductForm(productId = null) {
  editingProductId = productId;
  const product = productId ? currentProducts.find(p => p.id === productId) : null;

  document.getElementById('edit-product-name').textContent = product ? product.name : 'Новый продукт';
  document.getElementById('edit-name').value = product?.name || '';
  document.getElementById('edit-category').value = product?.category || '';
  document.getElementById('edit-in-stock').checked = product?.in_stock || false;
  document.getElementById('edit-quantity').value = product?.quantity || '';
  document.getElementById('edit-unit').value = product?.unit || '';
  
  const deleteBtn = document.getElementById('delete-product-btn');
  if (deleteBtn) {
    deleteBtn.style.display = productId ? 'block' : 'none';
  }

  // Обновляем обработчик формы
  const form = document.getElementById('product-edit-form');
  const existingHandler = form._submitHandler;
  if (existingHandler) {
    form.removeEventListener('submit', existingHandler);
  }

  const submitHandler = async (e) => {
    e.preventDefault();
    const name = document.getElementById('edit-name').value;
    const category = document.getElementById('edit-category').value;
    const inStock = document.getElementById('edit-in-stock').checked;
    const quantity = document.getElementById('edit-quantity').value;
    const unit = document.getElementById('edit-unit').value;

    if (!name || !category) {
      alert('Заполните название и категорию');
      return;
    }

    if (productId) {
      await updateProduct(productId, {
        name,
        category,
        in_stock: inStock,
        quantity: quantity || null,
        unit: unit || null
      });
    } else {
      await createProduct({
        name,
        category,
        in_stock: inStock,
        quantity: quantity || null,
        unit: unit || null
      });
    }
    showScreen('outOfStock');
  };

  form._submitHandler = submitHandler;
  form.addEventListener('submit', submitHandler);

  showScreen('productEdit');
}

window.editProduct = function(productId) {
  openProductForm(productId);
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
    alert('Ошибка создания продукта');
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
    alert('Ошибка обновления продукта');
  }
}

async function deleteProduct(productId) {
  try {
    const response = await fetch(`${API_BASE}/products/${productId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to delete product');
    }
  } catch (error) {
    console.error('Failed to delete product:', error);
    alert('Ошибка удаления продукта');
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
        <button class="edit-btn" onclick="editRecipe('${recipe.id}')">Редактировать</button>
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
}

// Запуск приложения после загрузки DOM
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

