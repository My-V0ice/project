// src/types/index.ts

export type UserRole = 'superadmin' | 'admin' | 'verifier' | 'recipient' | 'auditor';

export interface User {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  department?: string;
  isActive?: boolean;
  createdAt?: string;
}

export interface Event {
  id: string;
  title: string;
  organizer: string;
  startDate: string;
  endDate: string;
  type?: string;
  description?: string;
  contactInfo?: Record<string, any>;
  createdBy?: string;
  createdByName?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface Document {
  id: string;
  uniqueNumber: string;
  eventId: string;
  eventTitle?: string;
  userId?: string;
  participantName: string;
  status: 'generated' | 'sent' | 'signed' | 'error';
  awardCategory?: string;
  filePath?: string;
  qrCodePath?: string;
  signedAt?: string;
  signedBy?: string;
  createdAt: string;
}

export interface Template {
  id: string;
  name: string;
  description?: string;
  type: 'certificate' | 'diploma' | 'letter';
  filePath?: string;
  variables: string[];
  createdBy?: string;
  createdAt: string;
}

export interface AuditLog {
  id: string;
  userId?: string;
  userName?: string;
  action: string;
  entityType: string;
  entityId?: string;
  oldData?: any;
  newData?: any;
  ipAddress?: string;
  userAgent?: string;
  createdAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}