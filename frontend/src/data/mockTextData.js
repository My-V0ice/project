export const mockUsers = [
  {
    id: 101,
    full_name: 'Иванова Мария Сергеевна',
    email: 'm.ivanova@togu.example',
    role: 'recipient',
    role_label: 'Получатель',
  },
  {
    id: 102,
    full_name: 'Петров Артем Игоревич',
    email: 'a.petrov@togu.example',
    role: 'division_admin',
    role_label: 'Администратор подразделения',
  },
  {
    id: 103,
    full_name: 'Смирнова Елена Андреевна',
    email: 'e.smirnova@togu.example',
    role: 'reviewer',
    role_label: 'Проверяющий',
  },
  {
    id: 104,
    full_name: 'Кузнецов Дмитрий Олегович',
    email: 'd.kuznetsov@togu.example',
    role: 'auditor',
    role_label: 'Наблюдатель / аудитор',
  },
]

export const mockTemplates = [
  {
    id: 201,
    name: 'Сертификат участника ТОГУ',
    orientation: 'landscape',
    brand_book_locked: true,
    documents_generated: 24,
  },
  {
    id: 202,
    name: 'Диплом победителя ТОГУ',
    orientation: 'portrait',
    brand_book_locked: true,
    documents_generated: 9,
  },
  {
    id: 203,
    name: 'Благодарственное письмо организатору',
    orientation: 'landscape',
    brand_book_locked: true,
    documents_generated: 12,
  },
]

export const mockDocuments = [
  {
    id: 301,
    number: 'TOGU-2026-00031',
    full_name: 'Иванова Мария Сергеевна',
    event_title: 'Форум студенческих инициатив',
    signature_status: 'Подписан УКЭП',
    status: 'issued',
  },
  {
    id: 302,
    number: 'TOGU-2026-00032',
    full_name: 'Петров Артем Игоревич',
    event_title: 'Школа проектного управления',
    signature_status: 'Подписан УКЭП',
    status: 'delivered',
  },
  {
    id: 303,
    number: 'TOGU-2026-00033',
    full_name: 'Смирнова Елена Андреевна',
    event_title: 'День карьеры ТОГУ',
    signature_status: 'Подписан УКЭП',
    status: 'issued',
  },
]

export const mockRecipientDocuments = [
  {
    id: 401,
    number: 'TOGU-2026-00031',
    event_title: 'Форум студенческих инициатив',
    signature_status: 'Подписан УКЭП',
    issued_at: '2026-03-10T10:20:00',
    qr_link: '/verify/mock-00031',
  },
  {
    id: 402,
    number: 'TOGU-2026-00032',
    event_title: 'Школа проектного управления',
    signature_status: 'Подписан УКЭП',
    issued_at: '2026-03-18T09:00:00',
    qr_link: '/verify/mock-00032',
  },
  {
    id: 403,
    number: 'TOGU-2026-00033',
    event_title: 'День карьеры ТОГУ',
    signature_status: 'Подписан УКЭП',
    issued_at: '2026-04-01T12:45:00',
    qr_link: '/verify/mock-00033',
  },
]

