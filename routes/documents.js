const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const rbac = require('../middleware/rbac');
const { sequelize } = require('../config/database');
const logger = require('../utils/logger');
const pdfGenerator = require('../services/pdfGenerator');
const qrService = require('../services/qrService');
const emailService = require('../services/emailService');

// GET /api/documents - список документов
router.get('/', auth, async (req, res) => {
    try {
        let query = `
            SELECT d.*, e.title as event_title, u.full_name as participant_name
            FROM documents d
            LEFT JOIN events e ON d.event_id = e.id
            LEFT JOIN users u ON d.user_id = u.id
            WHERE 1=1
        `;
        const params = [];
        
        if (req.user.role === 'recipient') {
            query += ` AND d.user_id = $${params.length + 1}`;
            params.push(req.userId);
        }
        
        query += ` ORDER BY d.created_at DESC`;
        
        const documents = await sequelize.query(query, {
            bind: params,
            type: sequelize.QueryTypes.SELECT
        });
        
        res.json(documents);
    } catch (error) {
        logger.error('Get documents error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// GET /api/documents/:id - получить документ
router.get('/:id', auth, async (req, res) => {
    try {
        const documents = await sequelize.query(
            `SELECT d.*, e.title as event_title
             FROM documents d
             LEFT JOIN events e ON d.event_id = e.id
             WHERE d.id = $1`,
            {
                bind: [req.params.id],
                type: sequelize.QueryTypes.SELECT
            }
        );
        
        if (!documents || documents.length === 0) {
            return res.status(404).json({ error: 'Документ не найден' });
        }
        
        const document = documents[0];
        
        if (req.user.role === 'recipient' && document.user_id !== req.userId) {
            return res.status(403).json({ error: 'Доступ запрещен' });
        }
        
        res.json(document);
    } catch (error) {
        logger.error('Get document error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// POST /api/documents/generate - сгенерировать документ
router.post('/generate', [auth, rbac(['admin', 'superadmin'])], async (req, res) => {
    try {
        const { event_id, user_id, award_category, template_id } = req.body;
        
        // Генерация уникального номера документа
        const uniqueNumber = `DOC-${Date.now()}-${Math.random().toString(36).substr(2, 8)}`;
        
        // Генерация QR-кода
        const qrUrl = `${process.env.QR_BASE_URL}/${uniqueNumber}`;
        const qrCodePath = await qrService.generate(qrUrl, uniqueNumber);
        
        // Генерация PDF
        const pdfPath = await pdfGenerator.generate({
            templateId: template_id,
            data: {
                fullName: req.body.fullName,
                eventTitle: req.body.eventTitle,
                date: new Date().toISOString(),
                uniqueNumber: uniqueNumber,
                awardCategory: award_category,
                qrCodePath: qrCodePath
            }
        });
        
        // Сохранение в базу данных
        const result = await sequelize.query(
            `INSERT INTO documents (id, unique_number, event_id, user_id, participant_name, award_category, file_path, qr_code_path, status, created_at)
             VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, 'generated', NOW())
             RETURNING id`,
            {
                bind: [uniqueNumber, event_id, user_id, req.body.fullName, award_category, pdfPath, qrCodePath],
                type: sequelize.QueryTypes.SELECT
            }
        );
        
        res.status(201).json({
            message: 'Документ сгенерирован',
            id: result[0].id,
            uniqueNumber: uniqueNumber,
            pdfPath: pdfPath
        });
        
    } catch (error) {
        logger.error('Generate document error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// POST /api/documents/:id/send - отправить документ по email
router.post('/:id/send', [auth, rbac(['admin', 'superadmin'])], async (req, res) => {
    try {
        const documents = await sequelize.query(
            `SELECT d.*, u.email as user_email, u.full_name as user_name
             FROM documents d
             LEFT JOIN users u ON d.user_id = u.id
             WHERE d.id = $1`,
            {
                bind: [req.params.id],
                type: sequelize.QueryTypes.SELECT
            }
        );
        
        if (!documents || documents.length === 0) {
            return res.status(404).json({ error: 'Документ не найден' });
        }
        
        const document = documents[0];
        
        await emailService.sendDocument({
            to: document.user_email,
            subject: `Ваш документ ${document.unique_number}`,
            documentPath: document.file_path,
            userName: document.user_name,
            documentNumber: document.unique_number
        });
        
        await sequelize.query(
            'UPDATE documents SET status = $1 WHERE id = $2',
            { bind: ['sent', req.params.id] }
        );
        
        res.json({ message: 'Документ отправлен' });
        
    } catch (error) {
        logger.error('Send document error:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

module.exports = router;