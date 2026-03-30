require('dotenv').config();
const app = require('./app');
const { sequelize } = require('./config/database');
const logger = require('./utils/logger');

const PORT = process.env.PORT || 3000;
const HOST = process.env.HOST || 'localhost';

async function startServer() {
    try {
        // Проверка подключения к базе данных
        await sequelize.authenticate();
        logger.info('✅ Подключение к PostgreSQL установлено');
        
        // Синхронизация моделей (только в development)
        if (process.env.NODE_ENV === 'development') {
            await sequelize.sync({ alter: true });
            logger.info('✅ Модели синхронизированы');
        }
        
        // Запуск сервера
        const server = app.listen(PORT, HOST, () => {
            logger.info(`
            ════════════════════════════════════════════════════════
            🚀 Сервер Document System запущен
            📡 Адрес: http://${HOST}:${PORT}
            🌍 Окружение: ${process.env.NODE_ENV}
            📅 Время: ${new Date().toISOString()}
            ════════════════════════════════════════════════════════
            `);
        });
        
        // Graceful shutdown
        const shutdown = async (signal) => {
            logger.info(`${signal} получен, остановка сервера...`);
            server.close(async () => {
                logger.info('HTTP сервер остановлен');
                await sequelize.close();
                logger.info('Подключение к БД закрыто');
                process.exit(0);
            });
            
            // Принудительное завершение через 10 секунд
            setTimeout(() => {
                logger.error('Принудительное завершение процесса');
                process.exit(1);
            }, 10000);
        };
        
        process.on('SIGTERM', () => shutdown('SIGTERM'));
        process.on('SIGINT', () => shutdown('SIGINT'));
        
    } catch (error) {
        logger.error('❌ Ошибка при запуске сервера:', error);
        process.exit(1);
    }
}

startServer();