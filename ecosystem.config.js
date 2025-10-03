/**
 * PM2 Ecosystem Configuration for Pcloudy Test Case Agent
 *
 * This configuration manages the Python Flask backend using gunicorn.
 * Frontend is served by nginx in production.
 *
 * Usage:
 *   pm2 start ecosystem.config.js --env production
 *   pm2 restart ecosystem.config.js
 *   pm2 stop ecosystem.config.js
 *   pm2 logs pcloudy-backend
 *
 * For production deployment with nginx:
 * 1. Ensure nginx is configured and running
 * 2. Start PM2: pm2 start ecosystem.config.js --env production
 * 3. Access via: https://yourdomain.com
 */

module.exports = {
  apps: [
    {
      name: 'pcloudy-backend',
      script: '.venv/bin/gunicorn',
      args: '--bind 0.0.0.0:5321 --workers 4 --worker-class gevent --timeout 300 --access-logfile - --error-logfile - backend.src.app:app',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      cwd: '/home/ubuntu/Test_Agent',
      env: {
        NODE_ENV: 'development',
        ENV: 'development',
        PYTHONPATH: '/home/ubuntu/Test_Agent/backend/src',
        BACKEND_PORT: '5321',
        BACKEND_URL: 'https://testgen.pcloudy.com'
      },
      env_production: {
        NODE_ENV: 'production',
        ENV: 'production',
        PYTHONPATH: '/home/ubuntu/Test_Agent/backend/src',
        BACKEND_PORT: '5321',
        BACKEND_URL: 'https://testgen.pcloudy.com'
      },
      error_file: './logs/pm2-backend-error.log',
      out_file: './logs/pm2-backend-out.log',
      log_file: './logs/pm2-backend-combined.log',
      time: true,
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ],

  deploy: {
    production: {
      user: 'ubuntu',
      host: 'your-server-ip',
      ref: 'origin/production-deployment',
      repo: 'git@github.com:rishav781/Test_Agent.git',
      path: '/home/ubuntu/Test_Agent',
      'pre-deploy-local': '',
      'post-deploy': 'source .venv/bin/activate && pm2 reload ecosystem.config.js --env production',
      'pre-setup': ''
    }
  }
};