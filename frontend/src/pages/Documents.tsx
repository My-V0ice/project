// src/pages/Documents.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { documentsApi } from '../api/documents';
import { eventsApi } from '../api/events';
import { Button } from '../components/UI/Button';
import { Modal } from '../components/UI/Modal';
import { DocumentGenerateForm } from '../components/Documents/DocumentGenerateForm';
import { useAuthStore } from '../store/authStore';

export const Documents: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<any>(null);
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: documentsApi.getAll,
  });

  const { data: events } = useQuery({
    queryKey: ['events'],
    queryFn: eventsApi.getAll,
    enabled: user?.role === 'admin' || user?.role === 'superadmin',
  });

  const generateMutation = useMutation({
    mutationFn: documentsApi.generate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setIsModalOpen(false);
      toast.success('Документ сгенерирован');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Ошибка генерации');
    },
  });

  const sendMutation = useMutation({
    mutationFn: documentsApi.send,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast.success('Документ отправлен на email');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Ошибка отправки');
    },
  });

  const canGenerate = user?.role === 'admin' || user?.role === 'superadmin';
  const canSend = user?.role === 'admin' || user?.role === 'superadmin';

  const getStatusBadge = (status: string) => {
    const statuses: Record<string, { color: string; label: string }> = {
      generated: { color: 'bg-yellow-100 text-yellow-800', label: 'Сгенерирован' },
      sent: { color: 'bg-blue-100 text-blue-800', label: 'Отправлен' },
      signed: { color: 'bg-green-100 text-green-800', label: 'Подписан' },
      error: { color: 'bg-red-100 text-red-800', label: 'Ошибка' },
    };
    const s = statuses[status] || { color: 'bg-gray-100 text-gray-800', label: status };
    return <span className={`px-2 py-1 rounded-full text-xs font-medium ${s.color}`}>{s.label}</span>;
  };

  if (isLoading) {
    return <div className="text-center py-8">Загрузка...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Документы</h1>
        {canGenerate && (
          <Button onClick={() => setIsModalOpen(true)}>+ Сгенерировать документ</Button>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Номер
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Участник
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Мероприятие
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Статус
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Дата
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Действия
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {documents?.map((doc) => (
              <tr key={doc.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{doc.uniqueNumber}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{doc.participantName}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">{doc.eventTitle || '-'}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(doc.status)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">
                    {new Date(doc.createdAt).toLocaleDateString('ru-RU')}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={() => setSelectedDocument(doc)}
                    className="text-blue-600 hover:text-blue-900 mr-3"
                  >
                    Просмотр
                  </button>
                  {canSend && doc.status === 'generated' && (
                    <button
                      onClick={() => sendMutation.mutate(doc.id)}
                      className="text-green-600 hover:text-green-900"
                    >
                      Отправить
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {(!documents || documents.length === 0) && (
        <div className="text-center py-12 text-gray-500">
          Нет документов. Сгенерируйте первый документ.
        </div>
      )}

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Генерация документа">
        <DocumentGenerateForm
          events={events || []}
          onSubmit={(data) => generateMutation.mutate(data)}
          isLoading={generateMutation.isPending}
        />
      </Modal>

      <Modal
        isOpen={!!selectedDocument}
        onClose={() => setSelectedDocument(null)}
        title={`Документ ${selectedDocument?.uniqueNumber || ''}`}
        size="large"
      >
        {selectedDocument && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-500">Номер документа</label>
                <p className="mt-1 text-lg font-semibold text-gray-900">{selectedDocument.uniqueNumber}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Статус</label>
                <div className="mt-1">{getStatusBadge(selectedDocument.status)}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Участник</label>
                <p className="mt-1 text-gray-900">{selectedDocument.participantName}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Мероприятие</label>
                <p className="mt-1 text-gray-900">{selectedDocument.eventTitle || '-'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Категория награды</label>
                <p className="mt-1 text-gray-900">{selectedDocument.awardCategory || '-'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Дата создания</label>
                <p className="mt-1 text-gray-900">
                  {new Date(selectedDocument.createdAt).toLocaleString('ru-RU')}
                </p>
              </div>
            </div>
            {selectedDocument.filePath && (
              <div className="pt-4">
                <a
                  href={`http://localhost:3000${selectedDocument.filePath}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Скачать документ
                </a>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};