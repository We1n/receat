/**
 * Production сервер для eatsite PWA
 * Раздаёт статические файлы из frontend/dist и проксирует API запросы к backend
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');
const zlib = require('zlib');

const PORT = process.env.PORT || 8082;
const BUILD_DIR = path.join(__dirname, 'frontend', 'dist');
const BACKEND_PORT = process.env.BACKEND_PORT || 3000;

// MIME типы
const mimeTypes = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.webmanifest': 'application/manifest+json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.eot': 'application/vnd.ms-fontobject',
};

/**
 * Генерация PNG иконок для PWA
 */
const crcTable = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) {
      c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    }
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(buf) {
  let c = 0xFFFFFFFF;
  for (let i = 0; i < buf.length; i++) {
    c = crcTable[(c ^ buf[i]) & 0xFF] ^ (c >>> 8);
  }
  return (c ^ 0xFFFFFFFF) >>> 0;
}

function makeChunk(type, data) {
  const typeBuf = Buffer.from(type, 'ascii');
  const len = data ? data.length : 0;
  const out = Buffer.alloc(8 + len + 4);
  out.writeUInt32BE(len, 0);
  typeBuf.copy(out, 4);
  if (len > 0) data.copy(out, 8);
  const crc = crc32(Buffer.concat([typeBuf, data || Buffer.alloc(0)]));
  out.writeUInt32BE(crc, 8 + len);
  return out;
}

function createSolidPng(width, height, rgba) {
  const signature = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
  const ihdrData = Buffer.alloc(13);
  ihdrData.writeUInt32BE(width, 0);
  ihdrData.writeUInt32BE(height, 4);
  ihdrData[8] = 8;
  ihdrData[9] = 6;
  ihdrData[10] = 0;
  ihdrData[11] = 0;
  ihdrData[12] = 0;
  const ihdr = makeChunk('IHDR', ihdrData);

  const row = Buffer.alloc(1 + width * 4);
  row[0] = 0;
  for (let x = 0; x < width; x++) {
    const off = 1 + x * 4;
    row[off] = rgba.r;
    row[off + 1] = rgba.g;
    row[off + 2] = rgba.b;
    row[off + 3] = rgba.a;
  }
  const raw = Buffer.alloc((1 + width * 4) * height);
  for (let y = 0; y < height; y++) {
    row.copy(raw, y * row.length);
  }
  const compressed = zlib.deflateSync(raw);
  const idat = makeChunk('IDAT', compressed);
  const iend = makeChunk('IEND', Buffer.alloc(0));
  return Buffer.concat([signature, ihdr, idat, iend]);
}

function ensurePwaIcons() {
  try {
    const iconsDir = path.join(BUILD_DIR, 'icons');
    if (!fs.existsSync(iconsDir)) {
      fs.mkdirSync(iconsDir, { recursive: true });
    }
    const color = { r: 99, g: 102, b: 241, a: 255 }; // #6366f1 (primary color)
    const targets = [
      { name: 'icon-192.png', w: 192, h: 192 },
      { name: 'icon-512.png', w: 512, h: 512 },
    ];
    for (const t of targets) {
      const filePath = path.join(iconsDir, t.name);
      if (!fs.existsSync(filePath)) {
        const png = createSolidPng(t.w, t.h, color);
        fs.writeFileSync(filePath, png);
        console.log(`✅ [PWA] Сгенерирована иконка ${t.name} (${t.w}x${t.h})`);
      }
    }
  } catch (e) {
    console.error('❌ [PWA] Ошибка при генерации иконок:', e);
  }
}

const server = http.createServer((req, res) => {
  // CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(200, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-Client-Token, X-Workspace-Id',
      'Access-Control-Max-Age': '86400',
    });
    res.end();
    return;
  }

  const parsedUrl = url.parse(req.url || '/', true);
  const pathname = parsedUrl.pathname || '/';

  // Проксирование API запросов к backend
  if (pathname.startsWith('/api/') || pathname.startsWith('/workspace/') || 
      pathname.startsWith('/products') || pathname.startsWith('/recipes') || 
      pathname.startsWith('/categories') || pathname.startsWith('/export') || 
      pathname.startsWith('/health')) {
    const apiPath = pathname + (parsedUrl.search || '');
    console.log(`[PROXY] Proxying ${req.method} ${req.url} -> localhost:${BACKEND_PORT}${apiPath}`);
    
    const options = {
      hostname: 'localhost',
      port: BACKEND_PORT,
      path: apiPath,
      method: req.method,
      headers: {
        ...req.headers,
        host: `localhost:${BACKEND_PORT}`,
      },
    };

    const proxyReq = http.request(options, (proxyRes) => {
      const headers = { ...proxyRes.headers };
      headers['Access-Control-Allow-Origin'] = '*';
      res.writeHead(proxyRes.statusCode, headers);
      proxyRes.pipe(res);
    });

    proxyReq.on('error', (err) => {
      console.error(`[PROXY ERROR] Failed to proxy to API: ${err.message}`);
      res.writeHead(502, { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      });
      res.end(JSON.stringify({ error: 'API server unavailable', details: err.message }));
    });

    // Передаём тело запроса
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      req.pipe(proxyReq);
    } else {
      proxyReq.end();
    }
    return;
  }

  // WebSocket upgrade для проксирования (если нужно)
  if (req.headers.upgrade === 'websocket') {
    // WebSocket соединения обрабатываются напрямую backend'ом
    // Здесь просто возвращаем ошибку, так как WebSocket должен подключаться напрямую к backend
    res.writeHead(426, { 'Upgrade': 'websocket' });
    res.end('WebSocket connections should be made directly to backend');
    return;
  }

  // Service Worker
  if (pathname === '/sw.js' || pathname === '/service-worker.js') {
    const swPath = path.join(BUILD_DIR, 'sw.js');
    const swPathAlt = path.join(BUILD_DIR, 'service-worker.js');
    
    const serveSwFile = (swPath) => {
      fs.readFile(swPath, (readErr, data) => {
        if (readErr) {
          res.writeHead(500, { 'Content-Type': 'text/plain' });
          res.end('500 Internal Server Error');
          return;
        }
        const headers = {
          'Content-Type': 'application/javascript',
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Service-Worker-Allowed': '/',
          'X-Content-Type-Options': 'nosniff',
        };
        res.writeHead(200, headers);
        res.end(data);
      });
    };
    
    fs.access(swPath, fs.constants.F_OK, (err) => {
      if (err) {
        fs.access(swPathAlt, fs.constants.F_OK, (altErr) => {
          if (altErr) {
            console.error(`[ERROR] Service Worker not found: ${swPath} or ${swPathAlt}`);
            res.writeHead(404, { 'Content-Type': 'text/plain' });
            res.end('404 Not Found');
            return;
          }
          serveSwFile(swPathAlt);
        });
        return;
      }
      serveSwFile(swPath);
    });
    return;
  }

  // Manifest.json / manifest.webmanifest
  if (pathname === '/manifest.json' || pathname === '/manifest.webmanifest') {
    // vite-plugin-pwa генерирует manifest.webmanifest
    const manifestPath = path.join(BUILD_DIR, 'manifest.webmanifest');
    const manifestPathAlt = path.join(BUILD_DIR, 'manifest.json');
    
    const serveManifest = (filePath) => {
      fs.readFile(filePath, (readErr, data) => {
        if (readErr) {
          console.error(`[ERROR] Cannot read manifest from ${filePath}:`, readErr.message);
          res.writeHead(500, { 'Content-Type': 'text/plain' });
          res.end('500 Internal Server Error');
          return;
        }
        const headers = {
          'Content-Type': 'application/manifest+json',
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'public, max-age=3600',
          'X-Content-Type-Options': 'nosniff',
        };
        res.writeHead(200, headers);
        res.end(data);
      });
    };
    
    fs.access(manifestPath, fs.constants.F_OK, (err) => {
      if (err) {
        fs.access(manifestPathAlt, fs.constants.F_OK, (altErr) => {
          if (altErr) {
            console.error(`[ERROR] Manifest not found: ${manifestPath} or ${manifestPathAlt}`);
            res.writeHead(404, { 'Content-Type': 'text/plain' });
            res.end('404 Not Found');
            return;
          }
          serveManifest(manifestPathAlt);
        });
        return;
      }
      serveManifest(manifestPath);
    });
    return;
  }

  // Иконки
  if (pathname.startsWith('/icons/')) {
    const iconPath = path.join(BUILD_DIR, pathname);
    fs.access(iconPath, fs.constants.F_OK, (err) => {
      if (err) {
        console.error(`[ERROR] Icon not found: ${pathname} -> ${iconPath}`);
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('404 Not Found');
        return;
      }
      const ext = path.extname(iconPath).toLowerCase();
      const contentType = mimeTypes[ext] || 'application/octet-stream';
      fs.readFile(iconPath, (readErr, data) => {
        if (readErr) {
          res.writeHead(500, { 'Content-Type': 'text/plain' });
          res.end('500 Internal Server Error');
          return;
        }
        const headers = {
          'Content-Type': contentType,
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'public, max-age=31536000, immutable',
          'X-Content-Type-Options': 'nosniff',
        };
        res.writeHead(200, headers);
        res.end(data);
      });
    });
    return;
  }

  // Обработка пути для SPA
  let filePath = pathname;
  if (filePath === '/') {
    filePath = '/index.html';
  }

  // Убираем начальный слэш для работы с файловой системой
  const fullPath = path.join(BUILD_DIR, filePath);
  const ext = path.extname(fullPath).toLowerCase();
  const contentType = mimeTypes[ext] || 'application/octet-stream';

  // Проверяем существование файла
  fs.access(fullPath, fs.constants.F_OK, (err) => {
    if (err) {
      // Если файл не найден, проверяем, является ли это статическим ресурсом
      const isStaticResource = ext && ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf', '.eot', '.ico', '.json'].includes(ext);
      
      // Если это статический ресурс, возвращаем 404
      if (isStaticResource) {
        console.error(`[ERROR] Static resource not found: ${pathname}`);
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('404 Not Found');
        return;
      }

      // Для всех остальных путей отдаём index.html для SPA роутинга
      const indexPath = path.join(BUILD_DIR, 'index.html');
      console.log(`[SPA Routing] Serving index.html for path: ${pathname}`);
      fs.readFile(indexPath, (err, data) => {
        if (err) {
          console.error(`[ERROR] Cannot read index.html from ${indexPath}:`, err.message);
          res.writeHead(404, { 'Content-Type': 'text/plain' });
          res.end(`404 Not Found - index.html not found at ${indexPath}`);
          return;
        }
        res.writeHead(200, {
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0, private',
          'Pragma': 'no-cache',
          'Expires': '0',
          'Access-Control-Allow-Origin': '*',
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'SAMEORIGIN',
        });
        res.end(data);
      });
      return;
    }

    // Читаем и отправляем файл
    console.log(`[FILE] Serving: ${pathname} -> ${fullPath}`);
    fs.readFile(fullPath, (err, data) => {
      if (err) {
        console.error(`[ERROR] Cannot read file ${fullPath}:`, err.message);
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('500 Internal Server Error');
        return;
      }

      const headers = {
        'Content-Type': contentType,
        'Access-Control-Allow-Origin': '*',
        'X-Content-Type-Options': 'nosniff',
      };

      // Кэширование для статических ресурсов
      if (ext && ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf', '.eot'].includes(ext)) {
        headers['Cache-Control'] = 'public, max-age=31536000, immutable';
      } else {
        headers['Cache-Control'] = 'no-cache, no-store, must-revalidate';
      }

      console.log(`[SUCCESS] Served: ${pathname} (${data.length} bytes)`);
      res.writeHead(200, headers);
      res.end(data);
    });
  });
});

// Проверяем существование BUILD_DIR при запуске
if (!fs.existsSync(BUILD_DIR)) {
  console.error(`❌ ERROR: Build directory not found: ${BUILD_DIR}`);
  console.error(`   Please run: cd frontend && npm run build`);
  process.exit(1);
}

const indexPath = path.join(BUILD_DIR, 'index.html');
if (!fs.existsSync(indexPath)) {
  console.error(`❌ ERROR: index.html not found at: ${indexPath}`);
  console.error(`   Please run: cd frontend && npm run build`);
  process.exit(1);
}

// Гарантируем наличие PWA-иконок
ensurePwaIcons();

server.listen(PORT, () => {
  console.log(`🚀 Eatsite server running at http://localhost:${PORT}`);
  console.log(`📁 Serving files from: ${BUILD_DIR}`);
  console.log(`✅ SPA routing enabled - all routes will serve index.html`);
  console.log(`✅ API proxy enabled - API requests will be proxied to localhost:${BACKEND_PORT}`);
  console.log(`✅ index.html found at: ${indexPath}`);
});

// Обработка ошибок
server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`❌ Port ${PORT} is already in use`);
  } else {
    console.error('❌ Server error:', err);
  }
  process.exit(1);
});

