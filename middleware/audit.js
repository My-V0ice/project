const { sequelize } = require('../config/database');
const logger = require('../utils/logger');

const auditMiddleware = (action, entityType) => {
    return async (req, res, next) => {
        const oldJson = res.json;
        let oldData = null;
        let newData = null;
        
        // Сохраняем оригинальные данные если есть
        if (req.body) {
            newData = { ...req.body };
            delete newData.password;
            delete newData.password_hash;
        }
        
        res.json = function(data) {
            oldData = data;
            oldJson.call(this, data);
        };
        
        next();
        
        // После завершения запроса логируем
        res.on('finish', async () => {
            try {
                await sequelize.query(
                    `INSERT INTO audit_logs (id, user_id, action, entity_type, entity_id, old_data, new_data, ip_address, user_agent, created_at)
                     VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8, NOW())`,
                    {
                        bind: [
                            req.userId || null,
                            action,
                            entityType,
                            req.params.id || null,
                            oldData ? JSON.stringify(oldData) : null,
                            newData ? JSON.stringify(newData) : null,
                            req.ip,
                            req.headers['user-agent']
                        ]
                    }
                );
                logger.info(`Аудит: ${action} - ${entityType} - Пользователь: ${req.userId}`);
            } catch (error) {
                logger.error('Ошибка записи аудита:', error);
            }
        });
    };
};

module.exports = auditMiddleware;