/**
 * PM2 Ecosystem конфигурация для eatsite
 * 
 * Использование:
 *   pm2 start ecosystem.config.js
 *   pm2 save
 */

module.exports = {
  apps: [
    {
      name: 'eatsite-backend',
      script: './backend/server.js',
      cwd: '/home/webapp/projects/eatsite',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
        MAX_CLIENTS_PER_WORKSPACE: 25
      },
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M'
    },
    {
      name: 'eatsite-frontend',
      script: './server.js',
      cwd: '/home/webapp/projects/eatsite',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production',
        PORT: 8082,
        BACKEND_PORT: 3000,
        BACKEND_HOST: 'localhost'
      },
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    }
  ]
};

