// src/api/events.ts
import { apiClient } from './client';
import { Event } from '../types';

export const eventsApi = {
  getAll: async (): Promise<Event[]> => {
    const response = await apiClient.get('/events');
    return response.data;
  },

  getById: async (id: string): Promise<Event> => {
    const response = await apiClient.get(`/events/${id}`);
    return response.data;
  },

  create: async (data: Partial<Event>): Promise<{ message: string; id: string }> => {
    const response = await apiClient.post('/events', data);
    return response.data;
  },

  update: async (id: string, data: Partial<Event>): Promise<{ message: string }> => {
    const response = await apiClient.put(`/events/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/events/${id}`);
    return response.data;
  },
};