const express = require('express');
const router = express.Router();
const { body, validationResult } = require('express-validator');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { sequelize } = require('../config/database');
const logger = require('../utils/logger');

// POST /api/auth/login - вход в систему
router.post('/login', [
    body('email').isEmail().normalizeEmail(),
    body('password').notEmpty()
], async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }
    
    try {
        const { email, password } = req.body;
        
        const users = await sequelize.query(
            'SELECT id, email, password_hash, full_name, role FROM users WHERE email = $1 AND is_active = true',
            {
                bind: [email],
                type: sequelize.QueryTypes.SELECT
            }
        );
        
        if (!users || users.length === 0) {
            return res.status(401).json({ error: 'Неверный email или пароль' });
        }
        
        const user = users[0];
        const isValidPassword = await bcrypt.compare(password, user.password_hash);
        
        if (!isValidPassword) {
            return res.status(401).json({ error: 'Неверный email или пароль' });
        }
        
        const token = jwt.sign(
            { userId: user.id, email: user.email, role: user.role },
            process.env.JWT_SECRET,
            { expiresIn: process.env.JWT_EXPIRES_IN }
        );
        
        res.json({
            token,
            user: {
                id: user.id,
                email: user.email,
                fullName: user.full_name,
                role: user.role
            }
        });
        
    } catch (error) {
        logger.error('Login error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// POST /api/auth/register - регистрация (только для администраторов)
router.post('/register', [
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 6 }),
    body('fullName').notEmpty(),
    body('role').isIn(['admin', 'verifier', 'recipient', 'auditor'])
], async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }
    
    try {
        const { email, password, fullName, role, department } = req.body;
        
        const existingUsers = await sequelize.query(
            'SELECT id FROM users WHERE email = $1',
            { bind: [email], type: sequelize.QueryTypes.SELECT }
        );
        
        if (existingUsers && existingUsers.length > 0) {
            return res.status(400).json({ error: 'Пользователь с таким email уже существует' });
        }
        
        const passwordHash = await bcrypt.hash(password, parseInt(process.env.BCRYPT_ROUNDS) || 10);
        
        await sequelize.query(
            `INSERT INTO users (id, email, password_hash, full_name, role, department, created_at)
             VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, NOW())`,
            {
                bind: [email, passwordHash, fullName, role, department || null]
            }
        );
        
        res.status(201).json({ message: 'Пользователь успешно создан' });
        
    } catch (error) {
        logger.error('Registration error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// GET /api/auth/me - получить информацию о текущем пользователе
router.get('/me', require('../middleware/auth'), async (req, res) => {
    try {
        const users = await sequelize.query(
            'SELECT id, email, full_name, role, department, created_at FROM users WHERE id = $1',
            {
                bind: [req.userId],
                type: sequelize.QueryTypes.SELECT
            }
        );
        
        if (!users || users.length === 0) {
            return res.status(404).json({ error: 'Пользователь не найден' });
        }
        
        res.json(users[0]);
    } catch (error) {
        logger.error('Get me error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

module.exports = router;