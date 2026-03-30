const rolesHierarchy = {
    superadmin: ['admin', 'verifier', 'recipient', 'auditor'],
    admin: ['verifier', 'recipient'],
    verifier: ['recipient'],
    recipient: [],
    auditor: ['recipient']
};

const hasPermission = (userRole, requiredRole) => {
    if (userRole === requiredRole) return true;
    if (rolesHierarchy[userRole] && rolesHierarchy[userRole].includes(requiredRole)) {
        return true;
    }
    return false;
};

const rbacMiddleware = (requiredRoles) => {
    return (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({ error: 'Требуется авторизация' });
        }
        
        const userRole = req.user.role;
        const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
        const hasAccess = roles.some(role => hasPermission(userRole, role));
        
        if (!hasAccess) {
            return res.status(403).json({
                error: 'Доступ запрещен',
                message: `Роль "${userRole}" не имеет доступа к этому ресурсу`
            });
        }
        
        next();
    };
};

module.exports = rbacMiddleware;