export const textUsers = [
  {
    id: 1,
    full_name: 'Системный администратор',
    email: 'admin@togu.example',
    role: 'superadmin',
    role_label: 'Суперадминистратор',
    brand_name: 'ТОГУ',
    division_name: 'Цифровая кафедра',
  },
  {
    id: 2,
    full_name: 'Администратор подразделения',
    email: 'manager@togu.example',
    role: 'division_admin',
    role_label: 'Администратор подразделения',
    brand_name: 'ТОГУ',
    division_name: 'Цифровая кафедра',
  },
  {
    id: 3,
    full_name: 'Основной получатель',
    email: 'recipient@togu.example',
    role: 'recipient',
    role_label: 'Получатель',
    brand_name: 'ТОГУ',
    division_name: 'Цифровая кафедра',
  },
]

export const textTemplates = [
  {
    id: 1,
    name: 'Сертификат участника ТОГУ',
    orientation: 'landscape',
    description: 'Стандартный сертификат участника мероприятия.',
    brand_name: 'ТОГУ',
    documents_generated: 2,
  },
  {
    id: 2,
    name: 'Диплом победителя ТОГУ',
    orientation: 'portrait',
    description: 'Официальный шаблон диплома победителя.',
    brand_name: 'ТОГУ',
    documents_generated: 1,
  },
]

export const textDocuments = [
  {
    id: 1,
    number: 'TOGU-2026-00001',
    full_name: 'Основной получатель',
    event_title: 'Форум студенческих инициатив',
    signature_status: 'Подписан',
    status: 'выдан',
    template_id: 1,
    issued_by: 1,
    issued_at: '2026-04-10T12:00:00',
  },
  {
    id: 2,
    number: 'TOGU-2026-00002',
    full_name: 'Алексей Петров',
    event_title: 'Форум студенческих инициатив',
    signature_status: 'Подписан',
    status: 'выдан',
    template_id: 1,
    issued_by: 2,
    issued_at: '2026-04-11T12:00:00',
  },
  {
    id: 3,
    number: 'TOGU-2026-00003',
    full_name: 'Елена Смирнова',
    event_title: 'Школа проектного управления',
    signature_status: 'Подписан',
    status: 'выдан',
    template_id: 2,
    issued_by: 2,
    issued_at: '2026-04-12T12:00:00',
  },
]
