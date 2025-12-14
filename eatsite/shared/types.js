/**
 * Shared types and models for Shared Pantry PWA
 */

/**
 * @typedef {Object} Product
 * @property {string} id
 * @property {string} name
 * @property {string} category
 * @property {boolean} in_stock
 * @property {number|null} quantity
 * @property {string|null} unit
 */

/**
 * @typedef {Object} Recipe
 * @property {string} id
 * @property {string} name
 * @property {string[]} product_ids
 * @property {string|null} notes
 */

/**
 * @typedef {Object} WorkspaceState
 * @property {string} workspace_id
 * @property {Product[]} products
 * @property {Recipe[]} recipes
 * @property {string[]} active_clients
 */

/**
 * Product categories (фиксированные)
 */
export const PRODUCT_CATEGORIES = [
  'vegetables',
  'fruits',
  'dairy',
  'meat',
  'grains',
  'spices',
  'beverages',
  'other'
];

/**
 * WebSocket message types
 */
export const WS_MESSAGE_TYPES = {
  STATE: 'state',
  PRODUCT_CREATED: 'product_created',
  PRODUCT_UPDATED: 'product_updated',
  PRODUCT_DELETED: 'product_deleted',
  RECIPE_CREATED: 'recipe_created',
  RECIPE_UPDATED: 'recipe_updated',
  RECIPE_DELETED: 'recipe_deleted'
};





