const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const rbac = require('../middleware/rbac');
const upload = require('../config/multer');
const { sequelize } = require('../config/database');
const logger = require('../utils/logger');

// GET /api/templates - список шаблонов
router.get('/', auth, async (req, res) => {
    try {
        const templates = await sequelize.query(
            `SELECT * FROM templates WHERE 1=1
             ${req.user.role === 'admin' ? 'AND created_by = $1' : ''}
             ORDER BY created_at DESC`,
            {
                bind: req.user.role === 'admin' ? [req.userId] : [],
                type: sequelize.QueryTypes.SELECT
            }
        );
        
        res.json(templates);
    } catch (error) {
        logger.error('Get templates error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// POST /api/templates - создать шаблон
router.post('/', [auth, rbac(['admin', 'superadmin']), upload.single('template')], async (req, res) => {
    try {
        const { name, description, type, variables } = req.body;
        const filePath = req.file ? req.file.path : null;
        
        const result = await sequelize.query(
            `INSERT INTO templates (id, name, description, type, file_path, variables, created_by, created_at)
             VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, NOW())
             RETURNING id`,
            {
                bind: [name, description, type, filePath, variables || '[]', req.userId],
                type: sequelize.QueryTypes.SELECT
            }
        );
        
        res.status(201).json({
            message: 'Шаблон создан',
            id: result[0].id
        });
        
    } catch (error) {
        logger.error('Create template error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

module.exports = router;