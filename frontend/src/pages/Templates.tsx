// src/pages/Templates.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { templatesApi } from '../api/templates';
import { Button } from '../components/UI/Button';
import { Modal } from '../components/UI/Modal';
import { TemplateForm } from '../components/Templates/TemplateForm';

export const Templates: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: templates, isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: templatesApi.getAll,
  });

  const createMutation = useMutation({
    mutationFn: templatesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setIsModalOpen(false);
      toast.success('Шаблон создан');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Ошибка создания');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: templatesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      toast.success('Шаблон удален');
    },
  });

  const getTypeLabel = (type: string) => {
    const types: Record<string, string> = {
      certificate: 'Сертификат',
      diploma: 'Диплом',
      letter: 'Благодарственное письмо',
    };
    return types[type] || type;
  };

  if (isLoading) {
    return <div className="text-center py-8">Загрузка...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Шаблоны документов</h1>
        <Button onClick={() => setIsModalOpen(true)}>+ Создать шаблон</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates?.map((template) => (
          <div key={template.id} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-lg text-gray-900">{template.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{getTypeLabel(template.type)}</p>
                </div>
                <button
                  onClick={() => {
                    if (confirm('Удалить шаблон?')) {
                      deleteMutation.mutate(template.id);
                    }
                  }}
                  className="text-red-600 hover:text-red-800"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="p-4 space-y-3">
              {template.description && (
                <p className="text-sm text-gray-600">{template.description}</p>
              )}
              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">Доступные переменные:</p>
                <div className="flex flex-wrap gap-1">
                  {template.variables.map((variable) => (
                    <span
                      key={variable}
                      className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                    >
                      {'{' + variable + '}'}
                    </span>
                  ))}
                </div>
              </div>
              <div className="pt-2">
                <button
                  onClick={() => window.open(`http://localhost:3000${template.filePath}`, '_blank')}
                  className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  Предпросмотр
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {(!templates || templates.length === 0) && (
        <div className="text-center py-12 text-gray-500">
          Нет шаблонов. Создайте первый шаблон документа.
        </div>
      )}

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Создание шаблона" size="large">
        <TemplateForm
          onSubmit={(data) => createMutation.mutate(data)}
          isLoading={createMutation.isPending}
        />
      </Modal>
    </div>
  );
};