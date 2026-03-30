// src/components/Events/EventForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '../UI/Input';
import { Button } from '../UI/Button';

const eventSchema = z.object({
  title: z.string().min(1, 'Название обязательно'),
  organizer: z.string().min(1, 'Организатор обязателен'),
  startDate: z.string().min(1, 'Дата начала обязательна'),
  endDate: z.string().min(1, 'Дата окончания обязательна'),
  type: z.string().optional(),
  description: z.string().optional(),
});

type EventFormData = z.infer<typeof eventSchema>;

interface EventFormProps {
  onSubmit: (data: EventFormData) => void;
  isLoading?: boolean;
}

export const EventForm: React.FC<EventFormProps> = ({ onSubmit, isLoading }) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EventFormData>({
    resolver: zodResolver(eventSchema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Input
        label="Название"
        placeholder="Введите название мероприятия"
        error={errors.title?.message}
        {...register('title')}
      />
      <Input
        label="Организатор"
        placeholder="ФГБОУ ВО «ТОГУ»"
        error={errors.organizer?.message}
        {...register('organizer')}
      />
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Дата начала"
          type="date"
          error={errors.startDate?.message}
          {...register('startDate')}
        />
        <Input
          label="Дата окончания"
          type="date"
          error={errors.endDate?.message}
          {...register('endDate')}
        />
      </div>
      <Input
        label="Тип мероприятия"
        placeholder="Конференция, семинар, олимпиада..."
        error={errors.type?.message}
        {...register('type')}
      />
      <Input
        label="Описание"
        placeholder="Краткое описание мероприятия"
        error={errors.description?.message}
        {...register('description')}
      />
      <div className="flex justify-end space-x-3 pt-4">
        <Button type="submit" loading={isLoading}>
          Создать
        </Button>
      </div>
    </form>
  );
};