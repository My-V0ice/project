// src/api/documents.ts
import { apiClient } from './client';
import { Document } from '../types';

export const documentsApi = {
  getAll: async (): Promise<Document[]> => {
    const response = await apiClient.get('/documents');
    return response.data;
  },

  getById: async (id: string): Promise<Document> => {
    const response = await apiClient.get(`/documents/${id}`);
    return response.data;
  },

  generate: async (data: {
    eventId: string;
    userId?: string;
    fullName: string;
    eventTitle: string;
    awardCategory?: string;
    templateId?: string;
  }): Promise<{ message: string; id: string; uniqueNumber: string; pdfPath: string }> => {
    const response = await apiClient.post('/documents/generate', data);
    return response.data;
  },

  send: async (id: string): Promise<{ message: string }> => {
    const response = await apiClient.post(`/documents/${id}/send`);
    return response.data;
  },
};