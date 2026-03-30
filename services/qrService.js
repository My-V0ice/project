const QRCode = require('qrcode');
const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');

class QRService {
    constructor() {
        this.outputDir = path.join(process.env.STORAGE_PATH || './uploads', 'qrcodes');
        
        if (!fs.existsSync(this.outputDir)) {
            fs.mkdirSync(this.outputDir, { recursive: true });
        }
    }
    
    async generate(url, uniqueNumber) {
        try {
            const filename = `qr_${uniqueNumber}.png`;
            const filePath = path.join(this.outputDir, filename);
            
            await QRCode.toFile(filePath, url, {
                color: {
                    dark: '#000000',
                    light: '#FFFFFF'
                },
                width: parseInt(process.env.QR_SIZE) || 200,
                margin: 2,
                errorCorrectionLevel: process.env.QR_ERROR_CORRECTION || 'M'
            });
            
            logger.info(`QR-код сгенерирован: ${filename}`);
            return filePath;
            
        } catch (error) {
            logger.error('QR generation error:', error);
            throw error;
        }
    }
    
    async generateBase64(url) {
        try {
            const qrDataUrl = await QRCode.toDataURL(url, {
                width: parseInt(process.env.QR_SIZE) || 200,
                margin: 2,
                errorCorrectionLevel: 'M'
            });
            return qrDataUrl;
        } catch (error) {
            logger.error('QR generation error:', error);
            throw error;
        }
    }
}

module.exports = new QRService();