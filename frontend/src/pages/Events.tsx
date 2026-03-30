// src/pages/Events.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { eventsApi } from '../api/events';
import { Button } from '../components/UI/Button';
import { Modal } from '../components/UI/Modal';
import { EventForm } from '../components/Events/EventForm';
import { useAuthStore } from '../store/authStore';

export const Events: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const { data: events, isLoading } = useQuery({
    queryKey: ['events'],
    queryFn: eventsApi.getAll,
  });

  const createMutation = useMutation({
    mutationFn: eventsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      setIsModalOpen(false);
      toast.success('Мероприятие создано');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Ошибка создания');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: eventsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      toast.success('Мероприятие удалено');
    },
  });

  const canEdit = user?.role === 'superadmin' || user?.role === 'admin';

  if (isLoading) {
    return <div className="text-center py-8">Загрузка...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Мероприятия</h1>
        {canEdit && (
          <Button onClick={() => setIsModalOpen(true)}>+ Создать мероприятие</Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {events?.map((event) => (
          <div key={event.id} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-blue-50">
              <h3 className="font-semibold text-lg text-gray-900">{event.title}</h3>
              <p className="text-sm text-gray-600 mt-1">{event.organizer}</p>
            </div>
            <div className="p-4 space-y-2">
              <div className="flex items-center text-sm text-gray-600">
                <span className="w-24">Даты:</span>
                <span>
                  {new Date(event.startDate).toLocaleDateString('ru-RU')} -{' '}
                  {new Date(event.endDate).toLocaleDateString('ru-RU')}
                </span>
              </div>
              {event.type && (
                <div className="flex items-center text-sm text-gray-600">
                  <span className="w-24">Тип:</span>
                  <span>{event.type}</span>
                </div>
              )}
              {event.description && (
                <div className="text-sm text-gray-600">
                  <p className="font-medium mb-1">Описание:</p>
                  <p className="text-gray-500">{event.description}</p>
                </div>
              )}
              {canEdit && (
                <div className="pt-2 flex justify-end">
                  <button
                    onClick={() => {
                      if (confirm('Удалить мероприятие?')) {
                        deleteMutation.mutate(event.id);
                      }
                    }}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Удалить
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {(!events || events.length === 0) && (
        <div className="text-center py-12 text-gray-500">
          Нет мероприятий. Создайте первое мероприятие.
        </div>
      )}

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Создание мероприятия">
        <EventForm
          onSubmit={(data) => createMutation.mutate(data)}
          isLoading={createMutation.isPending}
        />
      </Modal>
    </div>
  );
};