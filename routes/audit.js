const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const rbac = require('../middleware/rbac');
const { sequelize } = require('../config/database');
const logger = require('../utils/logger');

// GET /api/audit - журнал событий (только для наблюдателей и суперадминистратора)
router.get('/', [auth, rbac(['superadmin', 'auditor'])], async (req, res) => {
    try {
        const { limit = 100, offset = 0, startDate, endDate, action, userId } = req.query;
        
        let query = `
            SELECT a.*, u.email, u.full_name as user_name
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE 1=1
        `;
        const params = [];
        
        if (startDate) {
            query += ` AND a.created_at >= $${params.length + 1}`;
            params.push(startDate);
        }
        if (endDate) {
            query += ` AND a.created_at <= $${params.length + 1}`;
            params.push(endDate);
        }
        if (action) {
            query += ` AND a.action = $${params.length + 1}`;
            params.push(action);
        }
        if (userId) {
            query += ` AND a.user_id = $${params.length + 1}`;
            params.push(userId);
        }
        
        query += ` ORDER BY a.created_at DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
        params.push(parseInt(limit), parseInt(offset));
        
        const logs = await sequelize.query(query, {
            bind: params,
            type: sequelize.QueryTypes.SELECT
        });
        
        res.json(logs);
    } catch (error) {
        logger.error('Get audit logs error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// GET /api/audit/actions - список доступных действий
router.get('/actions', [auth, rbac(['superadmin', 'auditor'])], async (req, res) => {
    try {
        const actions = await sequelize.query(
            'SELECT DISTINCT action FROM audit_logs ORDER BY action',
            { type: sequelize.QueryTypes.SELECT }
        );
        
        res.json(actions.map(a => a.action));
    } catch (error) {
        logger.error('Get audit actions error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

module.exports = router;