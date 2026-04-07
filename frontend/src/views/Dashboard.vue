<template>
  <section class="dashboard-page">
    <div class="hero-panel">
      <div>
        <span class="eyebrow">Рабочая панель</span>
        <h1>Система выпуска электронных сертификатов и документов ТОГУ</h1>
        <p>
          Управление мероприятиями, шаблонами, реестром, личным кабинетом получателя и журналом аудита
          в соответствии с ролями и ограничениями брендбука.
        </p>
      </div>

      <div class="hero-metrics">
        <div v-for="metric in metrics" :key="metric.label" class="metric-card">
          <strong>{{ metric.value }}</strong>
          <span>{{ metric.label }}</span>
        </div>
      </div>
    </div>

    <div v-loading="loading" class="dashboard-stack">
      <el-alert
        title="Фирменные параметры шаблонов заблокированы"
        type="warning"
        :closable="false"
        description="Цвета, шрифты, логотипы, поля и грид-система отмечены как обязательные для соблюдения брендбука ТОГУ."
      />

      <el-tabs v-model="activeTab" class="workspace-tabs">
        <el-tab-pane label="Обзор" name="overview">
          <div class="grid-two">
            <el-card>
              <template #header>Права текущей роли</template>
              <div class="tag-grid">
                <el-tag type="primary">{{ summary?.current_user?.role_label }}</el-tag>
                <el-tag :type="summary?.capabilities?.can_manage_events ? 'success' : 'info'">Мероприятия</el-tag>
                <el-tag :type="summary?.capabilities?.can_issue_documents ? 'success' : 'info'">Выпуск документов</el-tag>
                <el-tag :type="summary?.capabilities?.can_review_registry ? 'success' : 'info'">Реестр проверки</el-tag>
                <el-tag :type="summary?.capabilities?.can_view_audit ? 'success' : 'info'">Аудит</el-tag>
              </div>
            </el-card>

            <el-card>
              <template #header>Комплаенс и регламенты</template>
              <ul class="plain-list">
                <li v-for="note in summary?.brand_requirements?.compliance_notes || []" :key="note">{{ note }}</li>
              </ul>
            </el-card>
          </div>

          <div class="grid-two">
            <el-card>
              <template #header>Последние мероприятия</template>
              <el-table :data="summary?.upcoming_events || []" empty-text="Нет данных">
                <el-table-column prop="title" label="Мероприятие" min-width="200" />
                <el-table-column prop="event_type" label="Тип" width="140" />
                <el-table-column prop="start_date" label="Дата начала" width="130" />
              </el-table>
            </el-card>

            <el-card>
              <template #header>Последние документы</template>
              <el-table :data="summary?.recent_documents || []" empty-text="Нет данных">
                <el-table-column prop="number" label="Номер" width="150" />
                <el-table-column prop="participant_name" label="Получатель" min-width="180" />
                <el-table-column prop="event_title" label="Мероприятие" min-width="180" />
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="Мероприятия" name="events">
          <div class="grid-two">
            <el-card v-if="canManageEvents">
              <template #header>Создать мероприятие</template>
              <el-form :model="eventForm" label-position="top">
                <el-form-item label="Название">
                  <el-input v-model="eventForm.title" />
                </el-form-item>
                <el-form-item label="Организатор">
                  <el-input v-model="eventForm.organizer" />
                </el-form-item>
                <div class="grid-two compact-grid">
                  <el-form-item label="Дата начала">
                    <el-date-picker v-model="eventForm.start_date" type="date" value-format="YYYY-MM-DD" />
                  </el-form-item>
                  <el-form-item label="Дата окончания">
                    <el-date-picker v-model="eventForm.end_date" type="date" value-format="YYYY-MM-DD" />
                  </el-form-item>
                </div>
                <el-form-item label="Тип">
                  <el-input v-model="eventForm.event_type" />
                </el-form-item>
                <el-form-item label="Контактный email">
                  <el-input v-model="eventForm.contact_email" />
                </el-form-item>
                <el-form-item label="Описание">
                  <el-input v-model="eventForm.description" type="textarea" :rows="4" />
                </el-form-item>
                <el-button type="primary" @click="createEvent">Создать</el-button>
              </el-form>
            </el-card>

            <el-card>
              <template #header>Реестр мероприятий</template>
              <el-table :data="events" highlight-current-row @current-change="selectEvent">
                <el-table-column prop="title" label="Название" min-width="220" />
                <el-table-column prop="event_type" label="Тип" width="130" />
                <el-table-column prop="participants_count" label="Участники" width="110" />
                <el-table-column prop="documents_count" label="Документы" width="110" />
                <el-table-column prop="status" label="Статус" width="120" />
              </el-table>
            </el-card>
          </div>

          <div class="grid-two">
            <el-card v-if="canManageEvents">
              <template #header>Импорт участников</template>
              <el-select v-model="selectedEventId" placeholder="Выберите мероприятие" class="w-full">
                <el-option v-for="event in events" :key="event.id" :label="event.title" :value="event.id" />
              </el-select>
              <p class="helper-text">Формат строки: ФИО; email; статус; достижение; часы; категория</p>
              <el-input v-model="participantImportText" type="textarea" :rows="8" />
              <el-button type="primary" class="top-gap" @click="importParticipants">Импортировать</el-button>
            </el-card>

            <el-card>
              <template #header>Участники выбранного мероприятия</template>
              <el-table :data="participants" empty-text="Выберите мероприятие">
                <el-table-column prop="full_name" label="ФИО" min-width="200" />
                <el-table-column prop="email" label="Email" min-width="190" />
                <el-table-column prop="award_category" label="Категория" width="120" />
                <el-table-column prop="hours" label="Часы" width="80" />
                <el-table-column prop="documents_count" label="Документы" width="100" />
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="Шаблоны" name="templates">
          <div class="grid-two">
            <el-card v-if="canManageEvents">
              <template #header>Конструктор шаблона</template>
              <el-form :model="templateForm" label-position="top">
                <el-form-item label="Название">
                  <el-input v-model="templateForm.name" />
                </el-form-item>
                <el-form-item label="Ориентация A4">
                  <el-radio-group v-model="templateForm.orientation">
                    <el-radio-button label="landscape">Горизонтально</el-radio-button>
                    <el-radio-button label="portrait">Вертикально</el-radio-button>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="Описание">
                  <el-input v-model="templateForm.description" type="textarea" :rows="4" />
                </el-form-item>
                <el-form-item label="Переменные">
                  <el-select v-model="templateForm.allowed_fields" multiple class="w-full">
                    <el-option v-for="field in templateFields" :key="field" :label="field" :value="field" />
                  </el-select>
                </el-form-item>
                <el-button type="primary" @click="createTemplate">Сохранить шаблон</el-button>
              </el-form>
            </el-card>

            <el-card>
              <template #header>Список шаблонов</template>
              <el-table :data="templates">
                <el-table-column prop="name" label="Шаблон" min-width="220" />
                <el-table-column prop="orientation" label="Ориентация" width="130" />
                <el-table-column prop="brand_book_locked" label="Брендбук" width="100">
                  <template #default="{ row }">{{ row.brand_book_locked ? 'Да' : 'Нет' }}</template>
                </el-table-column>
                <el-table-column prop="documents_generated" label="Выпусков" width="100" />
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="Документы" name="documents">
          <div class="grid-two">
            <el-card v-if="canIssueDocuments">
              <template #header>Выпуск документов</template>
              <el-form :model="issueForm" label-position="top">
                <el-form-item label="Мероприятие">
                  <el-select v-model="issueForm.event_id" class="w-full">
                    <el-option v-for="event in events" :key="event.id" :label="event.title" :value="event.id" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Шаблон">
                  <el-select v-model="issueForm.template_id" class="w-full">
                    <el-option v-for="template in templates" :key="template.id" :label="template.name" :value="template.id" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Подписант">
                  <el-input v-model="issueForm.signatory_name" />
                </el-form-item>
                <el-form-item label="Должность">
                  <el-input v-model="issueForm.signatory_position" />
                </el-form-item>
                <el-form-item label="Рассылка">
                  <el-switch v-model="issueForm.send_email" active-text="Отправить по email" />
                </el-form-item>
                <el-button type="primary" @click="issueDocuments">Выпустить пакет</el-button>
              </el-form>
            </el-card>

            <el-card>
              <template #header>Реестр документов</template>
              <el-table :data="documents">
                <el-table-column prop="number" label="Номер" width="150" />
                <el-table-column prop="full_name" label="Получатель" min-width="180" />
                <el-table-column prop="event_title" label="Мероприятие" min-width="180" />
                <el-table-column prop="signature_status" label="Подпись" min-width="140" />
                <el-table-column prop="status" label="Статус" width="110" />
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="Получатель" name="recipient">
          <div class="grid-two">
            <el-card>
              <template #header>Личный кабинет получателя</template>
              <el-switch
                v-model="recipientConsent"
                active-text="Согласие на обработку персональных данных"
                @change="updateConsent"
              />
              <p class="helper-text">
                Доступ к документам возможен по защищенной персональной ссылке и через авторизацию.
              </p>
            </el-card>

            <el-card>
              <template #header>Мои документы</template>
              <el-table :data="recipientDocuments">
                <el-table-column prop="number" label="Номер" width="150" />
                <el-table-column prop="event_title" label="Мероприятие" min-width="180" />
                <el-table-column prop="signature_status" label="Подпись" min-width="140" />
                <el-table-column label="Проверка" min-width="220">
                  <template #default="{ row }">
                    <el-link :href="row.qr_link" target="_blank">{{ row.qr_link }}</el-link>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane v-if="canViewAudit" label="Аудит" name="audit">
          <el-card>
            <template #header>Журнал событий</template>
            <el-table :data="auditLogs">
              <el-table-column prop="created_at" label="Дата" width="180" />
              <el-table-column prop="actor_role" label="Роль" width="140" />
              <el-table-column prop="action" label="Действие" min-width="180" />
              <el-table-column prop="entity_type" label="Сущность" width="120" />
              <el-table-column label="Детали" min-width="240">
                <template #default="{ row }">{{ formatDetails(row.details) }}</template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/axios'

const loading = ref(false)
const activeTab = ref('overview')
const summary = ref(null)
const events = ref([])
const participants = ref([])
const templates = ref([])
const documents = ref([])
const recipientDocuments = ref([])
const auditLogs = ref([])
const awardCategories = ref([])
const recipientConsent = ref(true)
const selectedEventId = ref(null)
const participantImportText = ref(
  'Соколова Анна Петровна; anna@example.com; Подтвержден; Участие в пленарной секции; 8; Участник',
)

const eventForm = reactive({
  title: 'Конкурс молодежных проектов',
  organizer: 'ТОГУ',
  start_date: '',
  end_date: '',
  event_type: 'Конкурс',
  description: 'Мероприятие для генерации сертификатов, дипломов и благодарственных писем.',
  contact_email: 'org@togu.example',
  brand_name: 'ТОГУ',
  division_name: 'Цифровая кафедра',
})

const templateFields = [
  'full_name',
  'status',
  'event_title',
  'event_date',
  'hours',
  'document_number',
  'qr_link',
  'signatory_name',
  'signatory_position',
]

const templateForm = reactive({
  name: 'Диплом победителя ТОГУ',
  orientation: 'landscape',
  description: 'Шаблон с брендированными ограничениями по цветам, шрифтам и сетке.',
  allowed_fields: [...templateFields],
})

const issueForm = reactive({
  event_id: null,
  template_id: null,
  signatory_name: 'Проректор по молодежной политике',
  signatory_position: 'Ответственный за мероприятие',
  signature_type: 'УКЭП',
  send_email: true,
})

const metrics = computed(() => {
  const stats = summary.value?.stats || {}
  return [
    { label: 'Мероприятия', value: stats.events || 0 },
    { label: 'Участники', value: stats.participants || 0 },
    { label: 'Шаблоны', value: stats.templates || 0 },
    { label: 'Документы', value: stats.documents || 0 },
  ]
})

const canManageEvents = computed(() => summary.value?.capabilities?.can_manage_events)
const canIssueDocuments = computed(() => summary.value?.capabilities?.can_issue_documents)
const canViewAudit = computed(() => summary.value?.capabilities?.can_view_audit)

const getErrorMessage = (error, fallback) => error?.response?.data?.detail || fallback

const loadDashboard = async () => {
  loading.value = true
  try {
    const summaryResponse = await api.get('/dashboard/summary')
    summary.value = summaryResponse.data

    const responses = await Promise.all([
      api.get('/events'),
      api.get('/templates'),
      api.get('/documents'),
      api.get('/recipient/documents'),
      api.get('/reference/award-categories'),
      summary.value.capabilities.can_view_audit ? api.get('/audit/logs') : Promise.resolve({ data: [] }),
    ])

    events.value = responses[0].data
    templates.value = responses[1].data
    documents.value = responses[2].data
    recipientDocuments.value = responses[3].data.documents
    recipientConsent.value = responses[3].data.consent_to_processing
    awardCategories.value = responses[4].data
    auditLogs.value = responses[5].data || []

    if (!selectedEventId.value && events.value.length) {
      selectedEventId.value = events.value[0].id
    }
    if (!issueForm.event_id && events.value.length) {
      issueForm.event_id = events.value[0].id
    }
    if (!issueForm.template_id && templates.value.length) {
      issueForm.template_id = templates.value[0].id
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, 'Не удалось загрузить панель управления'))
  } finally {
    loading.value = false
  }
}

const loadAudit = async () => {
  if (!summary.value?.capabilities?.can_view_audit) return
  try {
    const { data } = await api.get('/audit/logs')
    auditLogs.value = data
  } catch (error) {
    auditLogs.value = []
    ElMessage.error(getErrorMessage(error, 'Не удалось загрузить журнал аудита'))
  }
}

const loadParticipants = async () => {
  if (!selectedEventId.value) {
    participants.value = []
    return
  }
  try {
    const { data } = await api.get(`/events/${selectedEventId.value}/participants`)
    participants.value = data
  } catch (error) {
    participants.value = []
    ElMessage.error(getErrorMessage(error, 'Не удалось загрузить участников'))
  }
}

const selectEvent = (row) => {
  if (row?.id) {
    selectedEventId.value = row.id
  }
}

const createEvent = async () => {
  try {
    await api.post('/events', eventForm)
    ElMessage.success('Мероприятие создано')
    await loadDashboard()
    await loadParticipants()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, 'Не удалось создать мероприятие'))
  }
}

const parseParticipantLines = () => {
  return participantImportText.value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [full_name, email, status = 'Подтвержден', achievement = '', hours = '0', award_category = 'Участник'] =
        line.split(';').map((part) => part.trim())

      return {
        full_name,
        email,
        status,
        achievement,
        hours: Number(hours || 0),
        award_category: awardCategories.value.includes(award_category) ? award_category : 'Участник',
      }
    })
}

const importParticipants = async () => {
  if (!selectedEventId.value) {
    ElMessage.warning('Сначала выберите мероприятие')
    return
  }

  try {
    await api.post(`/events/${selectedEventId.value}/participants/import`, {
      participants: parseParticipantLines(),
    })
    ElMessage.success('Участники импортированы')
    await loadDashboard()
    await loadParticipants()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, 'Не удалось импортировать участников'))
  }
}

const createTemplate = async () => {
  try {
    await api.post('/templates', templateForm)
    ElMessage.success('Шаблон сохранен')
    await loadDashboard()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, 'Не удалось создать шаблон'))
  }
}

const issueDocuments = async () => {
  try {
    const { data } = await api.post('/documents/issue', issueForm)
    ElMessage.success(`Выпущено документов: ${data.issued}`)
    await loadDashboard()
    await loadParticipants()
    await loadAudit()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, 'Не удалось выпустить документы'))
  }
}

const updateConsent = async () => {
  try {
    await api.put('/recipient/consent', { consent_to_processing: recipientConsent.value })
    ElMessage.success('Согласие обновлено')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, 'Не удалось обновить согласие'))
  }
}

const formatDetails = (details) => JSON.stringify(details || {}, null, 0)

watch(selectedEventId, loadParticipants)

onMounted(async () => {
  await loadDashboard()
  await loadParticipants()
})
</script>
