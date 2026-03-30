// src/components/Layout/Header.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useAuth } from '../../hooks/useAuth';

export const Header: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { logout } = useAuth();

  const getRoleName = (role: string) => {
    const roles: Record<string, string> = {
      superadmin: 'Суперадминистратор',
      admin: 'Администратор',
      verifier: 'Проверяющий',
      recipient: 'Участник',
      auditor: 'Наблюдатель',
    };
    return roles[role] || role;
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center space-x-4">
          <div className="text-blue-600 font-bold text-xl">ТОГУ</div>
          <div className="text-gray-600">Система управления документами</div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-sm font-medium text-gray-900">{user?.fullName}</div>
            <div className="text-xs text-gray-500">{getRoleName(user?.role || '')}</div>
          </div>
          <button
            onClick={() => logout()}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
};