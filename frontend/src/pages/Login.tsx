// src/pages/Login.tsx
import React from 'react';
import { LoginForm } from '../components/Auth/LoginForm';

export const Login: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="text-center">
            <h1 className="text-3xl font-bold text-blue-600">ТОГУ</h1>
            <h2 className="mt-6 text-2xl font-bold text-gray-900">
              Система управления документами
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Войдите в систему для продолжения работы
            </p>
          </div>
        </div>
        <div className="bg-white py-8 px-6 shadow rounded-lg">
          <LoginForm />
        </div>
      </div>
    </div>
  );
};