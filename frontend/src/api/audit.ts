// src/api/audit.ts
import { apiClient } from './client';
import { AuditLog } from '../types';

export const auditApi = {
  getAll: async (filters?: { startDate?: string; endDate?: string; action?: string }): Promise<AuditLog[]> => {
    const params = new URLSearchParams();
    if (filters?.startDate) params.append('startDate', filters.startDate);
    if (filters?.endDate) params.append('endDate', filters.endDate);
    if (filters?.action) params.append('action', filters.action);
    const response = await apiClient.get(`/audit?${params.toString()}`);
    return response.data;
  },

  getActions: async (): Promise<string[]> => {
    const response = await apiClient.get('/audit/actions');
    return response.data;
  },
};