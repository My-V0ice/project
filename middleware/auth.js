const jwt = require('jsonwebtoken');
const { sequelize } = require('../config/database');
const logger = require('../utils/logger');

const authMiddleware = async (req, res, next) => {
    try {
        const authHeader = req.headers.authorization;
        
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ error: 'Требуется авторизация' });
        }
        
        const token = authHeader.split(' ')[1];
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        
        const users = await sequelize.query(
            'SELECT id, email, full_name, role FROM users WHERE id = $1 AND is_active = true',
            {
                bind: [decoded.userId],
                type: sequelize.QueryTypes.SELECT
            }
        );
        
        if (!users || users.length === 0) {
            return res.status(401).json({ error: 'Пользователь не найден' });
        }
        
        req.user = users[0];
        req.userId = users[0].id;
        
        next();
    } catch (error) {
        if (error.name === 'JsonWebTokenError') {
            return res.status(401).json({ error: 'Недействительный токен' });
        }
        if (error.name === 'TokenExpiredError') {
            return res.status(401).json({ error: 'Срок действия токена истек' });
        }
        
        logger.error('Auth middleware error:', error);
        return res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
};

module.exports = authMiddleware;