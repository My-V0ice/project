const { body, param, query, validationResult } = require('express-validator');

// Валидатор для ID
const validateId = param('id').isUUID().withMessage('Некорректный ID');

// Валидатор для пагинации
const validatePagination = [
    query('page').optional().isInt({ min: 1 }).toInt(),
    query('limit').optional().isInt({ min: 1, max: 100 }).toInt()
];

// Валидатор для создания мероприятия
const validateEvent = [
    body('title').notEmpty().withMessage('Название обязательно').isLength({ max: 500 }),
    body('organizer').notEmpty().withMessage('Организатор обязателен'),
    body('start_date').isISO8601().withMessage('Некорректная дата начала'),
    body('end_date').isISO8601().withMessage('Некорректная дата окончания'),
    body('type').optional().isString(),
    body('description').optional().isString(),
    body('contact_info').optional().isObject()
];

// Валидатор для регистрации
const validateRegister = [
    body('email').isEmail().withMessage('Некорректный email'),
    body('password').isLength({ min: 6 }).withMessage('Пароль должен быть не менее 6 символов'),
    body('fullName').notEmpty().withMessage('ФИО обязательно'),
    body('role').isIn(['admin', 'verifier', 'recipient', 'auditor']).withMessage('Некорректная роль')
];

// Middleware для проверки ошибок валидации
const handleValidationErrors = (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }
    next();
};

module.exports = {
    validateId,
    validatePagination,
    validateEvent,
    validateRegister,
    handleValidationErrors
};