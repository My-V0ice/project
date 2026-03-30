const PDFDocument = require('pdfkit');
const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');

class PDFGenerator {
    constructor() {
        this.outputDir = path.join(process.env.STORAGE_PATH || './uploads', 'pdfs');
        
        if (!fs.existsSync(this.outputDir)) {
            fs.mkdirSync(this.outputDir, { recursive: true });
        }
    }
    
    async generate(options) {
        try {
            const { template, data, outputName } = options;
            const filename = outputName || `${Date.now()}_${data.uniqueNumber || 'document'}.pdf`;
            const filePath = path.join(this.outputDir, filename);
            
            const doc = new PDFDocument({
                size: 'A4',
                layout: template.orientation === 'landscape' ? 'landscape' : 'portrait',
                margins: {
                    top: template.margins?.top || 50,
                    bottom: template.margins?.bottom || 50,
                    left: template.margins?.left || 50,
                    right: template.margins?.right || 50
                }
            });
            
            const writeStream = fs.createWriteStream(filePath);
            doc.pipe(writeStream);
            
            // Установка шрифтов
            if (template.fonts) {
                // Загрузка шрифтов из брендбука
                // Здесь логика загрузки шрифтов
            }
            
            // Генерация содержимого из шаблона
            await this.renderContent(doc, template, data);
            
            // Добавление QR-кода
            if (data.qrCodePath && fs.existsSync(data.qrCodePath)) {
                doc.image(data.qrCodePath, doc.page.width - 100, doc.page.height - 100, {
                    width: 80,
                    height: 80
                });
            }
            
            doc.end();
            
            return new Promise((resolve, reject) => {
                writeStream.on('finish', () => resolve(filePath));
                writeStream.on('error', reject);
            });
            
        } catch (error) {
            logger.error('PDF generation error:', error);
            throw error;
        }
    }
    
    async renderContent(doc, template, data) {
        // Заголовок
        if (template.title) {
            doc.fontSize(18)
               .font('Helvetica-Bold')
               .text(this.replaceVariables(template.title, data), { align: 'center' });
            doc.moveDown();
        }
        
        // Основной текст
        if (template.content) {
            doc.fontSize(12)
               .font('Helvetica')
               .text(this.replaceVariables(template.content, data));
        }
        
        // Подписи
        if (template.signatures) {
            doc.moveDown(2);
            template.signatures.forEach(signature => {
                doc.fontSize(10)
                   .text(signature.label + ': _________________', { align: 'right' });
            });
        }
    }
    
    replaceVariables(text, data) {
        const variables = {
            '{FULL_NAME}': data.fullName || '',
            '{EVENT_TITLE}': data.eventTitle || '',
            '{DATE}': data.date || new Date().toLocaleDateString('ru-RU'),
            '{UNIQUE_NUMBER}': data.uniqueNumber || '',
            '{AWARD_CATEGORY}': data.awardCategory || '',
            '{HOURS}': data.hours || '',
            '{STATUS}': data.status || ''
        };
        
        let result = text;
        for (const [key, value] of Object.entries(variables)) {
            result = result.replace(new RegExp(key, 'g'), value);
        }
        
        return result;
    }
}

module.exports = new PDFGenerator();