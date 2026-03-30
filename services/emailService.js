const { sendMail } = require('../config/mailer');
const logger = require('../utils/logger');
const fs = require('fs');

class EmailService {
    async sendDocument(options) {
        try {
            const { to, subject, documentPath, userName, documentNumber } = options;
            
            const mailOptions = {
                from: process.env.SMTP_FROM || 'Document System <noreply@localhost>',
                to: to,
                subject: subject || 'Ваш документ',
                html: this.getDocumentEmailTemplate(userName, documentNumber),
                attachments: documentPath && fs.existsSync(documentPath) ? [
                    {
                        filename: `document_${documentNumber}.pdf`,
                        path: documentPath
                    }
                ] : []
            };
            
            const result = await sendMail(mailOptions);
            logger.info(`Документ отправлен: ${documentNumber} -> ${to}`);
            return result;
            
        } catch (error) {
            logger.error('Email send error:', error);
            throw error;
        }
    }
    
    async sendBulk(recipients, template, data) {
        const results = [];
        const batchSize = parseInt(process.env.EMAIL_BATCH_SIZE) || 50;
        
        for (let i = 0; i < recipients.length; i += batchSize) {
            const batch = recipients.slice(i, i + batchSize);
            const promises = batch.map(recipient => 
                this.sendDocument({
                    to: recipient.email,
                    subject: template.subject,
                    documentPath: data[recipient.id]?.documentPath,
                    userName: recipient.fullName,
                    documentNumber: data[recipient.id]?.documentNumber
                }).catch(error => ({ error, recipient }))
            );
            
            const batchResults = await Promise.all(promises);
            results.push(...batchResults);
            
            // Задержка между батчами
            if (i + batchSize < recipients.length) {
                await new Promise(resolve => setTimeout(resolve, parseInt(process.env.EMAIL_RATE_LIMIT_MS) || 1000));
            }
        }
        
        return results;
    }
    
    getDocumentEmailTemplate(userName, documentNumber) {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #0033A0; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; background: #f9f9f9; }
                    .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
                    .button { display: inline-block; padding: 10px 20px; background: #0033A0; color: white; text-decoration: none; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Тихоокеанский государственный университет</h2>
                    </div>
                    <div class="content">
                        <p>Уважаемый(ая) <strong>${userName}</strong>,</p>
                        <p>Ваш документ с номером <strong>${documentNumber}</strong> готов.</p>
                        <p>Вы можете скачать его из личного кабинета.</p>
                        <hr>
                        <p>С уважением,<br>Организационный комитет</p>
                    </div>
                    <div class="footer">
                        <p>Это письмо сгенерировано автоматически. Пожалуйста, не отвечайте на него.</p>
                    </div>
                </div>
            </body>
            </html>
        `;
    }
}

module.exports = new EmailService();