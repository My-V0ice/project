// src/components/Templates/TemplateForm.tsx
import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '../UI/Input';
import { Button } from '../UI/Button';

const templateSchema = z.object({
  name: z.string().min(1, 'Название обязательно'),
  description: z.string().optional(),
  type: z.enum(['certificate', 'diploma', 'letter']),
  content: z.string().min(1, 'Содержимое шаблона обязательно'),
  variables: z.string().optional(),
});

type TemplateFormData = z.infer<typeof templateSchema>;

interface TemplateFormProps {
  onSubmit: (data: TemplateFormData & { variables: string[] }) => void;
  isLoading?: boolean;
}

const variableSuggestions = [
  '{FULL_NAME}', '{EVENT_TITLE}', '{DATE}', '{UNIQUE_NUMBER}',
  '{AWARD_CATEGORY}', '{HOURS}', '{STATUS}', '{ORGANIZER}'
];

export const TemplateForm: React.FC<TemplateFormProps> = ({ onSubmit, isLoading }) => {
  const [selectedVariables, setSelectedVariables] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<TemplateFormData>({
    resolver: zodResolver(templateSchema),
    defaultValues: {
      type: 'certificate',
    },
  });

  const content = watch('content');

  const addVariable = (variable: string) => {
    const newContent = (content || '') + variable;
    setValue('content', newContent);
    if (!selectedVariables.includes(variable)) {
      setSelectedVariables([...selectedVariables, variable]);
    }
  };

  const handleFormSubmit = (data: TemplateFormData) => {
    // Извлекаем переменные из содержимого
    const variableRegex = /\{([^}]+)\}/g;
    const variables = [...new Set(
      Array.from(data.content.matchAll(variableRegex), m => m[1])
    )];
    
    onSubmit({
      ...data,
      variables,
    });
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <Input
        label="Название шаблона"
        placeholder="Сертификат участника"
        error={errors.name?.message}
        {...register('name')}
      />

      <Input
        label="Описание"
        placeholder="Краткое описание шаблона"
        error={errors.description?.message}
        {...register('description')}
      />

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Тип документа
        </label>
        <select
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          {...register('type')}
        >
          <option value="certificate">Сертификат</option>
          <option value="diploma">Диплом</option>
          <option value="letter">Благодарственное письмо</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Доступные переменные
        </label>
        <div className="flex flex-wrap gap-2 mb-3">
          {variableSuggestions.map((variable) => (
            <button
              key={variable}
              type="button"
              onClick={() => addVariable(variable)}
              className="px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded transition-colors"
            >
              {variable}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Содержимое шаблона (HTML)
        </label>
        <textarea
          rows={12}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          placeholder={`<div style="text-align: center;">
  <h1>{EVENT_TITLE}</h1>
  <p>Награждается {FULL_NAME}</p>
  <p>Дата: {DATE}</p>
  <p>Номер документа: {UNIQUE_NUMBER}</p>
</div>`}
          {...register('content')}
        />
        {errors.content && (
          <p className="mt-1 text-sm text-red-600">{errors.content.message}</p>
        )}
      </div>

      {selectedVariables.length > 0 && (
        <div className="bg-blue-50 p-3 rounded-lg">
          <p className="text-sm font-medium text-blue-800 mb-1">Используемые переменные:</p>
          <div className="flex flex-wrap gap-1">
            {selectedVariables.map((v) => (
              <span key={v} className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
                {v}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="flex justify-end space-x-3 pt-4">
        <Button type="submit" loading={isLoading}>
          Создать шаблон
        </Button>
      </div>
    </form>
  );
};