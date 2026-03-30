// src/components/Documents/DocumentGenerateForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '../UI/Input';
import { Button } from '../UI/Button';
import { Event } from '../../types';

const generateSchema = z.object({
  eventId: z.string().min(1, 'Выберите мероприятие'),
  fullName: z.string().min(1, 'ФИО участника обязательно'),
  awardCategory: z.string().optional(),
  templateId: z.string().optional(),
});

type GenerateFormData = z.infer<typeof generateSchema>;

interface DocumentGenerateFormProps {
  events: Event[];
  onSubmit: (data: GenerateFormData & { eventTitle: string }) => void;
  isLoading?: boolean;
}

export const DocumentGenerateForm: React.FC<DocumentGenerateFormProps> = ({
  events,
  onSubmit,
  isLoading,
}) => {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<GenerateFormData>({
    resolver: zodResolver(generateSchema),
  });

  const selectedEventId = watch('eventId');
  const selectedEvent = events.find((e) => e.id === selectedEventId);

  const handleFormSubmit = (data: GenerateFormData) => {
    onSubmit({
      ...data,
      eventTitle: selectedEvent?.title || '',
    });
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Мероприятие
        </label>
        <select
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          {...register('eventId')}
        >
          <option value="">Выберите мероприятие</option>
          {events.map((event) => (
            <option key={event.id} value={event.id}>
              {event.title} ({new Date(event.startDate).toLocaleDateString('ru-RU')})
            </option>
          ))}
        </select>
        {errors.eventId && (
          <p className="mt-1 text-sm text-red-600">{errors.eventId.message}</p>
        )}
      </div>

      <Input
        label="ФИО участника"
        placeholder="Иванов Иван Иванович"
        error={errors.fullName?.message}
        {...register('fullName')}
      />

      <Input
        label="Категория награды"
        placeholder="Победитель / Призер / Участник / Спикер"
        error={errors.awardCategory?.message}
        {...register('awardCategory')}
      />

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Шаблон документа
        </label>
        <select
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          {...register('templateId')}
        >
          <option value="">Стандартный шаблон</option>
          <option value="certificate">Сертификат участника</option>
          <option value="diploma">Диплом</option>
          <option value="letter">Благодарственное письмо</option>
        </select>
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <Button type="submit" loading={isLoading}>
          Сгенерировать
        </Button>
      </div>
    </form>
  );
};