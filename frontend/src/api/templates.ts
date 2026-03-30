// src/api/templates.ts
import { apiClient } from './client';
import { Template } from '../types';

export const templatesApi = {
  getAll: async (): Promise<Template[]> => {
    const response = await apiClient.get('/templates');
    return response.data;
  },

  getById: async (id: string): Promise<Template> => {
    const response = await apiClient.get(`/templates/${id}`);
    return response.data;
  },

  create: async (data: FormData): Promise<{ message: string; id: string }> => {
    const response = await apiClient.post('/templates', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  update: async (id: string, data: FormData): Promise<{ message: string }> => {
    const response = await apiClient.put(`/templates/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/templates/${id}`);
    return response.data;
  },
};