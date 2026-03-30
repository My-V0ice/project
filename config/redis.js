const Redis = require('redis');
const logger = require('../utils/logger');

const redisClient = Redis.createClient({
    socket: {
        host: process.env.REDIS_HOST || 'localhost',
        port: process.env.REDIS_PORT || 6379
    },
    password: process.env.REDIS_PASSWORD || undefined
});

redisClient.on('connect', () => {
    logger.info('✅ Подключение к Redis установлено');
});

redisClient.on('error', (err) => {
    logger.error('❌ Ошибка Redis:', err);
});

redisClient.connect();

module.exports = redisClient;