const nodemailer = require('nodemailer');
const logger = require('../utils/logger');

// Создаем транспорт только если есть настройки SMTP
let transporter = null;

// Функция для инициализации транспорта (ленивая загрузка)
const getTransporter = () => {
    if (transporter) return transporter;
    
    // Проверяем, настроен ли SMTP
    if (process.env.SMTP_HOST && process.env.SMTP_USER && process.env.SMTP_PASS && 
        process.env.SMTP_USER !== 'your-email@example.com' && 
        process.env.SMTP_PASS !== 'your-password') {
        
        transporter = nodemailer.createTransport({
            host: process.env.SMTP_HOST,
            port: parseInt(process.env.SMTP_PORT) || 587,
            secure: process.env.SMTP_SECURE === 'true',
            auth: {
                user: process.env.SMTP_USER,
                pass: process.env.SMTP_PASS
            }
        });
        
        // Проверяем подключение только в production
        if (process.env.NODE_ENV === 'production') {
            transporter.verify((error, success) => {
                if (error) {
                    logger.error('❌ Ошибка подключения к SMTP:', error);
                } else {
                    logger.info('✅ SMTP подключен');
                }
            });
        } else {
            logger.info('📧 SMTP настроен (режим разработки)');
        }
    } else {
        logger.warn('⚠️ SMTP не настроен. Отправка email будет имитироваться.');
        transporter = null;
    }
    
    return transporter;
};

// Функция отправки email с имитацией при отсутствии SMTP
const sendMail = async (mailOptions) => {
    const smtpTransporter = getTransporter();
    
    if (!smtpTransporter) {
        // Имитация отправки в режиме разработки
        logger.info(`📧 [ИМИТАЦИЯ] Отправка email на: ${mailOptions.to}`);
        logger.info(`📧 [ИМИТАЦИЯ] Тема: ${mailOptions.subject}`);
        logger.info(`📧 [ИМИТАЦИЯ] Вложения: ${mailOptions.attachments?.length || 0} файлов`);
        
        // Возвращаем имитацию успешной отправки
        return {
            messageId: `mock-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            response: '250 2.0.0 OK (simulated)',
            envelope: { from: mailOptions.from, to: [mailOptions.to] }
        };
    }
    
    try {
        const info = await smtpTransporter.sendMail(mailOptions);
        logger.info(`✅ Email отправлен: ${info.messageId} -> ${mailOptions.to}`);
        return info;
    } catch (error) {
        logger.error('❌ Ошибка отправки email:', error);
        throw error;
    }
};

module.exports = {
    getTransporter,
    sendMail
};