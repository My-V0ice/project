// src/components/Layout/Sidebar.tsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

const menuItems = [
  { path: '/dashboard', label: 'Дашборд', icon: '📊', roles: ['superadmin', 'admin', 'verifier', 'recipient', 'auditor'] },
  { path: '/events', label: 'Мероприятия', icon: '📅', roles: ['superadmin', 'admin', 'verifier'] },
  { path: '/documents', label: 'Документы', icon: '📄', roles: ['superadmin', 'admin', 'recipient'] },
  { path: '/templates', label: 'Шаблоны', icon: '🎨', roles: ['superadmin', 'admin'] },
  { path: '/audit', label: 'Журнал аудита', icon: '📋', roles: ['superadmin', 'auditor'] },
];

export const Sidebar: React.FC = () => {
  const { user } = useAuthStore();

  const filteredMenu = menuItems.filter((item) =>
    item.roles.includes(user?.role || '')
  );

  return (
    <aside className="w-64 bg-white shadow-sm border-r border-gray-200 min-h-[calc(100vh-73px)]">
      <nav className="p-4 space-y-1">
        {filteredMenu.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-600'
                  : 'text-gray-700 hover:bg-gray-50'
              }`
            }
          >
            <span className="text-xl">{item.icon}</span>
            <span className="text-sm font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};