const express = require('express');
const router = express.Router();
const { body, validationResult } = require('express-validator');
const auth = require('../middleware/auth');
const rbac = require('../middleware/rbac');
const audit = require('../middleware/audit');
const { sequelize } = require('../config/database');
const logger = require('../utils/logger');

// GET /api/events - список мероприятий
router.get('/', auth, async (req, res) => {
    try {
        let query = `
            SELECT e.*, u.full_name as created_by_name
            FROM events e
            LEFT JOIN users u ON e.created_by = u.id
            WHERE 1=1
        `;
        const params = [];
        
        // Фильтрация для администратора подразделения
        if (req.user.role === 'admin') {
            query += ` AND e.created_by = $${params.length + 1}`;
            params.push(req.userId);
        }
        
        query += ` ORDER BY e.created_at DESC`;
        
        const events = await sequelize.query(query, {
            bind: params,
            type: sequelize.QueryTypes.SELECT
        });
        
        res.json(events);
    } catch (error) {
        logger.error('Get events error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// GET /api/events/:id - получить мероприятие по ID
router.get('/:id', auth, async (req, res) => {
    try {
        const events = await sequelize.query(
            `SELECT e.*, u.full_name as created_by_name
             FROM events e
             LEFT JOIN users u ON e.created_by = u.id
             WHERE e.id = $1`,
            {
                bind: [req.params.id],
                type: sequelize.QueryTypes.SELECT
            }
        );
        
        if (!events || events.length === 0) {
            return res.status(404).json({ error: 'Мероприятие не найдено' });
        }
        
        const event = events[0];
        
        // Проверка доступа для администратора подразделения
        if (req.user.role === 'admin' && event.created_by !== req.userId) {
            return res.status(403).json({ error: 'Доступ запрещен' });
        }
        
        res.json(event);
    } catch (error) {
        logger.error('Get event error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// POST /api/events - создать мероприятие
router.post('/', [
    auth,
    rbac(['admin', 'superadmin']),
    body('title').notEmpty().isLength({ max: 500 }),
    body('organizer').notEmpty(),
    body('start_date').isISO8601(),
    body('end_date').isISO8601(),
    body('type').optional(),
    body('description').optional(),
    body('contact_info').optional()
], async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }
    
    try {
        const { title, organizer, start_date, end_date, type, description, contact_info } = req.body;
        
        const result = await sequelize.query(
            `INSERT INTO events (id, title, organizer, start_date, end_date, type, description, contact_info, created_by, created_at)
             VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8, NOW())
             RETURNING id`,
            {
                bind: [title, organizer, start_date, end_date, type, description, contact_info || null, req.userId],
                type: sequelize.QueryTypes.SELECT
            }
        );
        
        res.status(201).json({
            message: 'Мероприятие успешно создано',
            id: result[0].id
        });
        
    } catch (error) {
        logger.error('Create event error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// PUT /api/events/:id - обновить мероприятие
router.put('/:id', [
    auth,
    rbac(['admin', 'superadmin']),
    body('title').optional().isLength({ max: 500 }),
    body('organizer').optional(),
    body('start_date').optional().isISO8601(),
    body('end_date').optional().isISO8601()
], async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }
    
    try {
        // Проверка существования мероприятия
        const existing = await sequelize.query(
            'SELECT created_by FROM events WHERE id = $1',
            { bind: [req.params.id], type: sequelize.QueryTypes.SELECT }
        );
        
        if (!existing || existing.length === 0) {
            return res.status(404).json({ error: 'Мероприятие не найдено' });
        }
        
        // Проверка прав администратора подразделения
        if (req.user.role === 'admin' && existing[0].created_by !== req.userId) {
            return res.status(403).json({ error: 'Доступ запрещен' });
        }
        
        const updates = [];
        const values = [];
        let paramIndex = 1;
        
        if (req.body.title) {
            updates.push(`title = $${paramIndex++}`);
            values.push(req.body.title);
        }
        if (req.body.organizer) {
            updates.push(`organizer = $${paramIndex++}`);
            values.push(req.body.organizer);
        }
        if (req.body.start_date) {
            updates.push(`start_date = $${paramIndex++}`);
            values.push(req.body.start_date);
        }
        if (req.body.end_date) {
            updates.push(`end_date = $${paramIndex++}`);
            values.push(req.body.end_date);
        }
        if (req.body.type) {
            updates.push(`type = $${paramIndex++}`);
            values.push(req.body.type);
        }
        if (req.body.description !== undefined) {
            updates.push(`description = $${paramIndex++}`);
            values.push(req.body.description);
        }
        if (req.body.contact_info !== undefined) {
            updates.push(`contact_info = $${paramIndex++}`);
            values.push(req.body.contact_info);
        }
        
        updates.push(`updated_at = NOW()`);
        values.push(req.params.id);
        
        await sequelize.query(
            `UPDATE events SET ${updates.join(', ')} WHERE id = $${paramIndex}`,
            { bind: values }
        );
        
        res.json({ message: 'Мероприятие обновлено' });
        
    } catch (error) {
        logger.error('Update event error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// DELETE /api/events/:id - удалить мероприятие
router.delete('/:id', [auth, rbac(['admin', 'superadmin'])], async (req, res) => {
    try {
        const existing = await sequelize.query(
            'SELECT created_by FROM events WHERE id = $1',
            { bind: [req.params.id], type: sequelize.QueryTypes.SELECT }
        );
        
        if (!existing || existing.length === 0) {
            return res.status(404).json({ error: 'Мероприятие не найдено' });
        }
        
        if (req.user.role === 'admin' && existing[0].created_by !== req.userId) {
            return res.status(403).json({ error: 'Доступ запрещен' });
        }
        
        await sequelize.query(
            'DELETE FROM events WHERE id = $1',
            { bind: [req.params.id] }
        );
        
        res.json({ message: 'Мероприятие удалено' });
        
    } catch (error) {
        logger.error('Delete event error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

module.exports = router;