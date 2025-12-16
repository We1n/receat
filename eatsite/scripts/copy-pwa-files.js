/**
 * Скрипт для копирования PWA файлов в dist после сборки
 */
const fs = require('fs');
const path = require('path');

// Читаем base path из vite.config.js
let basePath = '/';
try {
  const viteConfigPath = path.join(__dirname, '..', 'frontend', 'vite.config.js');
  const viteConfigContent = fs.readFileSync(viteConfigPath, 'utf8');
  const baseMatch = viteConfigContent.match(/base:\s*['"`]([^'"`]+)['"`]/);
  if (baseMatch) {
    basePath = baseMatch[1];
  }
} catch (e) {
  console.warn('⚠️  Не удалось прочитать base path из vite.config.js, используем "/"');
}

const distDir = path.join(__dirname, '..', 'frontend', 'dist');
const iconsDir = path.join(distDir, 'icons');

// Создаем dist если его нет
if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir, { recursive: true });
}

// Копируем favicon.ico в корень dist (если он есть в assets)
const faviconDest = path.join(distDir, 'favicon.ico');
try {
  const assetsDir = path.join(distDir, 'assets');
  if (fs.existsSync(assetsDir)) {
    const files = fs.readdirSync(assetsDir);
    const faviconFile = files.find(f => f.startsWith('favicon-') && f.endsWith('.ico'));
    if (faviconFile) {
      const faviconSourcePath = path.join(assetsDir, faviconFile);
      fs.copyFileSync(faviconSourcePath, faviconDest);
      console.log('✅ favicon.ico скопирован в корень dist');
    }
  }
} catch (e) {
  console.warn('⚠️  Не удалось скопировать favicon.ico:', e.message);
}

// Создаем папку icons если её нет
if (!fs.existsSync(iconsDir)) {
  fs.mkdirSync(iconsDir, { recursive: true });
}

// Копируем PWA иконки из корня eatsite в dist/icons
const REQUIRED_PWA_ICONS = [
  { name: 'icon-192.png', source: path.join(__dirname, '..', 'icon-192.png') },
  { name: 'icon-512.png', source: path.join(__dirname, '..', 'icon-512.png') }
];

REQUIRED_PWA_ICONS.forEach((icon) => {
  const destPath = path.join(iconsDir, icon.name);
  if (fs.existsSync(icon.source)) {
    try {
      fs.copyFileSync(icon.source, destPath);
      console.log(`✅ Иконка ${icon.name} скопирована в dist/icons/`);
    } catch (e) {
      console.warn(`⚠️  Не удалось скопировать ${icon.name}:`, e.message);
    }
  } else {
    console.warn(`⚠️  Исходный файл ${icon.source} не найден, иконка ${icon.name} не будет скопирована`);
  }
});

// Проверяем наличие manifest.webmanifest в dist
const manifestPath = path.join(distDir, 'manifest.webmanifest');
if (!fs.existsSync(manifestPath)) {
  console.warn('⚠️  manifest.webmanifest not found in dist, vite-plugin-pwa should generate it');
} else {
  console.log('✅ manifest.webmanifest found in dist');
}

// Проверяем наличие service worker в dist
const swPath = path.join(distDir, 'sw.js');
const swPathAlt = path.join(distDir, 'service-worker.js');
if (!fs.existsSync(swPath) && !fs.existsSync(swPathAlt)) {
  console.warn('⚠️  Service Worker not found in dist, vite-plugin-pwa should generate it');
} else {
  console.log('✅ Service Worker found in dist');
}

// Добавляем ссылку на manifest.json в index.html если её нет
const indexPath = path.join(distDir, 'index.html');
if (fs.existsSync(indexPath)) {
  let htmlContent = fs.readFileSync(indexPath, 'utf8');
  
  // Исправляем ссылку на favicon.ico (заменяем путь с assets на корень с учетом base path)
  const faviconLinkRe = /<link[^>]*rel=["']icon["'][^>]*href=["'][^"']*favicon[^"']*["'][^>]*>/gi;
  const faviconHref = basePath + (basePath.endsWith('/') ? '' : '/') + 'favicon.ico';
  if (faviconLinkRe.test(htmlContent)) {
    htmlContent = htmlContent.replace(faviconLinkRe, `  <link rel="icon" type="image/x-icon" href="${faviconHref}">`);
    console.log('✅ Обновлена ссылка на favicon.ico в index.html');
  } else if (fs.existsSync(faviconDest)) {
    // Добавляем ссылку на favicon.ico если её нет, но файл существует
    const faviconLink = `  <link rel="icon" type="image/x-icon" href="${faviconHref}">\n`;
    if (htmlContent.includes('<title>')) {
      htmlContent = htmlContent.replace('<title>', faviconLink + '  <title>');
      console.log('✅ Добавлена ссылка на favicon.ico в index.html');
    }
  }
  
  // Удаляем любые существующие ссылки на манифест
  const manifestLinkTagRe = /<link[^>]*rel=["']manifest["'][^>]*>\s*/gi;
  if (manifestLinkTagRe.test(htmlContent)) {
    htmlContent = htmlContent.replace(manifestLinkTagRe, '');
    console.log('♻️  Удалены существующие ссылки rel="manifest" из index.html');
  }

  // Добавляем ссылку на manifest.webmanifest с учетом base path
  const manifestHref = basePath + (basePath.endsWith('/') ? '' : '/') + 'manifest.webmanifest';
  const manifestLink = `  <link rel="manifest" href="${manifestHref}">\n`;
  
  if (htmlContent.includes('</head>')) {
    if (!htmlContent.includes(manifestLink.trim())) {
      htmlContent = htmlContent.replace('</head>', manifestLink + '</head>');
      console.log('✅ Добавлена ссылка на manifest.json в index.html');
    }
  } else if (htmlContent.includes('<head>')) {
    if (!htmlContent.includes(manifestLink.trim())) {
      htmlContent = htmlContent.replace('<head>', '<head>\n' + manifestLink);
      console.log('✅ Добавлена ссылка на manifest.json в index.html');
    }
  } else {
    console.warn('⚠️  Не удалось найти тег <head> в index.html для добавления ссылок');
  }

  fs.writeFileSync(indexPath, htmlContent, 'utf8');
} else {
  console.warn('⚠️  index.html not found in dist, skipping manifest link addition');
}

console.log('✅ PWA files check completed');

