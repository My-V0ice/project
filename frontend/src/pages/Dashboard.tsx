// src/pages/Dashboard.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { eventsApi } from '../api/events';
import { documentsApi } from '../api/documents';
import { useAuthStore } from '../store/authStore';

export const Dashboard: React.FC = () => {
  const { user } = useAuthStore();

  const { data: events } = useQuery({
    queryKey: ['events'],
    queryFn: eventsApi.getAll,
  });

  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: documentsApi.getAll,
    enabled: user?.role !== 'auditor',
  });

  const stats = [
    {
      label: 'Мероприятий',
      value: events?.length || 0,
      icon: '📅',
      color: 'bg-blue-500',
    },
    {
      label: 'Документов',
      value: documents?.length || 0,
      icon: '📄',
      color: 'bg-green-500',
    },
    {
      label: 'Активных мероприятий',
      value: events?.filter((e) => new Date(e.endDate) > new Date()).length || 0,
      icon: '🎯',
      color: 'bg-yellow-500',
    },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Дашборд</h1>
      <p className="text-gray-600 mb-8">Добро пожаловать, {user?.fullName}!</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="bg-white rounded-lg shadow-sm p-6 border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{stat.label}</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{stat.value}</p>
              </div>
              <div className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center text-2xl`}>
                {stat.icon}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h2 className="font-semibold text-gray-900">Последние мероприятия</h2>
          </div>
          <div className="p-4">
            {events?.slice(0, 5).map((event) => (
              <div key={event.id} className="py-2 border-b border-gray-100 last:border-0">
                <p className="font-medium text-gray-900">{event.title}</p>
                <p className="text-sm text-gray-500">
                  {new Date(event.startDate).toLocaleDateString('ru-RU')} -{' '}
                  {new Date(event.endDate).toLocaleDateString('ru-RU')}
                </p>
              </div>
            ))}
            {(!events || events.length === 0) && (
              <p className="text-gray-500 text-center py-4">Нет мероприятий</p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h2 className="font-semibold text-gray-900">Последние документы</h2>
          </div>
          <div className="p-4">
            {documents?.slice(0, 5).map((doc) => (
              <div key={doc.id} className="py-2 border-b border-gray-100 last:border-0">
                <p className="font-medium text-gray-900">{doc.uniqueNumber}</p>
                <p className="text-sm text-gray-500">{doc.participantName}</p>
              </div>
            ))}
            {(!documents || documents.length === 0) && (
              <p className="text-gray-500 text-center py-4">Нет документов</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};