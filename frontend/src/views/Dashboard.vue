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
              <template #header>Добавить зарегистрированных пользователей</template>
              <el-select v-model="selectedEventId" placeholder="Выберите мероприятие" class="w-full">
                <el-option v-for="event in events" :key="event.id" :label="event.title" :value="event.id" />
              </el-select>
              <p class="helper-text">Можно добавить только пользователей, уже зарегистрированных в системе.</p>
              <el-select
                v-model="selectedUserIds"
                multiple
                filterable
                collapse-tags
                collapse-tags-tooltip
                placeholder="Выберите пользователей"
                class="w-full"
              >
                <el-option
                  v-for="user in registeredUsers"
                  :key="user.id"
                  :label="`${user.full_name} (${user.email})`"
                  :value="user.id"
                />
              </el-select>
              <div class="grid-two compact-grid top-gap">
                <el-form-item label="Статус">
                  <el-input v-model="participantAssignForm.status" />
                </el-form-item>
                <el-form-item label="Категория">
                  <el-select v-model="participantAssignForm.award_category" class="w-full">
                    <el-option v-for="category in awardCategories" :key="category" :label="category" :value="category" />
                  </el-select>
                </el-form-item>
              </div>
              <el-form-item label="Достижение">
                <el-input v-model="participantAssignForm.achievement" type="textarea" :rows="3" />
              </el-form-item>
              <el-form-item label="Часы">
                <el-input-number v-model="participantAssignForm.hours" :min="0" :max="1000" class="w-full" />
              </el-form-item>
              <el-button type="primary" class="top-gap" @click="addRegisteredUsersToEvent">Добавить в мероприятие</el-button>
            </el-card>

            <el-card v-if="canManageEvents">
              <template #header>Импорт участников CSV/XLSX</template>
              <el-select v-model="selectedEventId" placeholder="Выберите мероприятие" class="w-full">
                <el-option v-for="event in events" :key="event.id" :label="event.title" :value="event.id" />
              </el-select>
              <input class="file-input top-gap" type="file" accept=".csv,.xlsx" @change="handleImportFileChange" />
              <div v-if="importPreview" class="import-summary">
                <div class="verify-grid">
                  <div class="verify-item">
                    <span>Всего строк</span>
                    <strong>{{ importPreview.rows_total }}</strong>
                  </div>
                  <div class="verify-item">
                    <span>Готово к импорту</span>
                    <strong>{{ importPreview.rows_valid }}</strong>
                  </div>
                  <div class="verify-item">
                    <span>Ошибки</span>
                    <strong>{{ importPreview.rows_failed }}</strong>
                  </div>
                </div>
                <el-table :data="importPreview.sample" size="small">
                  <el-table-column prop="row_number" label="#" width="70" />
                  <el-table-column label="ФИО" min-width="180">
                    <template #default="{ row }">{{ row.data.full_name }}</template>
                  </el-table-column>
                  <el-table-column label="Email" min-width="180">
                    <template #default="{ row }">{{ row.data.email }}</template>
                  </el-table-column>
                  <el-table-column label="Ошибки" min-width="180">
                    <template #default="{ row }">{{ row.errors.join(', ') || 'Нет' }}</template>
                  </el-table-column>
                </el-table>
                <el-button type="primary" class="top-gap" :disabled="!importPreview.rows_valid" @click="commitParticipantImport">
                  Импортировать валидные строки
                </el-button>
              </div>
            </el-card>

            <el-card>
              <template #header>Участники мероприятия</template>
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
          <div class="template-workbench">
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
                <div class="document-actions">
                  <el-button type="primary" @click="createTemplate">Создать шаблон</el-button>
                  <el-button :disabled="!selectedTemplateId" @click="saveTemplateLayout">Сохранить макет</el-button>
                </div>
              </el-form>
            </el-card>

            <el-card>
              <template #header>Список шаблонов</template>
              <el-table :data="templates" highlight-current-row @current-change="selectTemplate">
                <el-table-column prop="name" label="Шаблон" min-width="220" />
                <el-table-column prop="orientation" label="Ориентация" width="130" />
                <el-table-column prop="brand_book_locked" label="Брендбук" width="100">
                  <template #default="{ row }">{{ row.brand_book_locked ? 'Да' : 'Нет' }}</template>
                </el-table-column>
                <el-table-column prop="documents_generated" label="Выпусков" width="100" />
              </el-table>
            </el-card>
          </div>

          <div class="template-designer">
            <el-card>
              <template #header>
                <div class="document-details-header">
                  <div>
                    <p class="document-details-eyebrow">Визуальный редактор</p>
                    <h2>{{ selectedTemplate?.name || 'Выберите шаблон' }}</h2>
                  </div>
                  <el-tag type="primary">A4 {{ designer.orientation === 'landscape' ? 'горизонтально' : 'вертикально' }}</el-tag>
                </div>
              </template>

              <div class="designer-toolbar">
                <el-select v-model="newElementField" placeholder="Переменная" class="designer-toolbar__select">
                  <el-option v-for="field in templateFields" :key="field" :label="field" :value="field" />
                </el-select>
                <el-button @click="addDesignerElement('variable')">Добавить текст</el-button>
                <el-button @click="addDesignerElement('qr')">QR</el-button>
                <el-button @click="addDesignerElement('signature')">Подпись</el-button>
                <el-button :disabled="!selectedElement" @click="duplicateDesignerElement">Дублировать</el-button>
                <el-button :disabled="!selectedElement" type="danger" plain @click="removeDesignerElement">Удалить</el-button>
              </div>

              <div class="designer-layout">
                <div
                  class="designer-canvas"
                  :class="`designer-canvas--${designer.orientation}`"
                  @pointermove="moveDesignerElement"
                  @pointerup="finishDesignerDrag"
                  @pointerleave="finishDesignerDrag"
                >
                  <div class="designer-page">
                    <div class="designer-safe-area"></div>
                    <div
                      v-for="element in sortedDesignerElements"
                      :key="element.id"
                      class="designer-element"
                      :class="[
                        `designer-element--${element.type}`,
                        { 'designer-element--active': selectedElementId === element.id },
                      ]"
                      :style="designerElementStyle(element)"
                      @pointerdown.stop="startDesignerDrag($event, element)"
                      @click.stop="selectedElementId = element.id"
                    >
                      <span>{{ element.label }}</span>
                    </div>
                  </div>
                </div>

                <aside class="designer-side">
                  <template v-if="selectedElement">
                    <el-form label-position="top">
                      <el-form-item label="Слой">
                        <el-input v-model="selectedElement.label" />
                      </el-form-item>
                      <div class="grid-two compact-grid">
                        <el-form-item label="X, %">
                          <el-input-number v-model="selectedElement.x" :min="0" :max="100" />
                        </el-form-item>
                        <el-form-item label="Y, %">
                          <el-input-number v-model="selectedElement.y" :min="0" :max="100" />
                        </el-form-item>
                        <el-form-item label="Ширина, %">
                          <el-input-number v-model="selectedElement.w" :min="4" :max="100" />
                        </el-form-item>
                        <el-form-item label="Высота, %">
                          <el-input-number v-model="selectedElement.h" :min="3" :max="40" />
                        </el-form-item>
                      </div>
                      <el-form-item label="Размер текста">
                        <el-slider v-model="selectedElement.fontSize" :min="10" :max="52" />
                      </el-form-item>
                      <el-form-item label="Выравнивание">
                        <el-radio-group v-model="selectedElement.align">
                          <el-radio-button label="left">Слева</el-radio-button>
                          <el-radio-button label="center">Центр</el-radio-button>
                          <el-radio-button label="right">Справа</el-radio-button>
                        </el-radio-group>
                      </el-form-item>
                      <el-form-item label="Автоперенос">
                        <el-switch v-model="selectedElement.wrap" active-text="Включен" />
                      </el-form-item>
                    </el-form>
                  </template>
                  <el-empty v-else description="Выберите слой на макете" />

                  <div class="layer-list">
                    <p class="document-details-eyebrow">Слои</p>
                    <button
                      v-for="element in sortedDesignerElements"
                      :key="element.id"
                      class="layer-list__item"
                      :class="{ 'layer-list__item--active': selectedElementId === element.id }"
                      @click="selectedElementId = element.id"
                    >
                      {{ element.label }}
                    </button>
                  </div>
                </aside>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="Документы" name="documents">
          <div class="grid-two">
            <el-card v-if="canIssueDocuments">
              <template #header>Мастер выпуска</template>
              <el-steps :active="issueStep" finish-status="success" class="issue-steps">
                <el-step title="Импорт" />
                <el-step title="Поля" />
                <el-step title="Предпросмотр" />
                <el-step title="Выпуск" />
              </el-steps>

              <div class="wizard-panel">
                <div v-if="issueStep === 0">
                  <el-form :model="issueForm" label-position="top">
                    <el-form-item label="Мероприятие">
                      <el-select v-model="issueForm.event_id" class="w-full" @change="syncIssueEvent">
                        <el-option v-for="event in events" :key="event.id" :label="event.title" :value="event.id" />
                      </el-select>
                    </el-form-item>
                  </el-form>
                  <div class="verify-grid">
                    <div class="verify-item">
                      <span>Участников выбрано</span>
                      <strong>{{ participants.length }}</strong>
                    </div>
                    <div class="verify-item">
                      <span>Импорт</span>
                      <strong>{{ importPreview ? 'Проверен' : 'Не выбран' }}</strong>
                    </div>
                  </div>
                  <input class="file-input top-gap" type="file" accept=".csv,.xlsx" @change="handleIssueImportFileChange" />
                  <div v-if="importPreview" class="helper-text">
                    Валидных строк: {{ importPreview.rows_valid }}, ошибок: {{ importPreview.rows_failed }}
                  </div>
                </div>

                <div v-else-if="issueStep === 1">
                  <el-form :model="issueForm" label-position="top">
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
                  </el-form>
                </div>

                <div v-else-if="issueStep === 2">
                  <el-button type="primary" @click="loadIssuePreview">Сформировать предпросмотр</el-button>
                  <div v-if="issuePreview" class="document-preview">
                    <p class="document-card__number">{{ issuePreview.number }}</p>
                    <h3>{{ issuePreview.template_name }}</h3>
                    <p>{{ issuePreview.full_name }}</p>
                    <p>{{ issuePreview.event_title }}</p>
                    <p class="helper-text">{{ issuePreview.signature_status }}</p>
                  </div>
                </div>

                <div v-else>
                  <el-result
                    icon="success"
                    title="Готово к выпуску"
                    :sub-title="`Мероприятие: ${selectedIssueEvent?.title || '-'}, шаблон: ${selectedIssueTemplate?.name || '-'}`"
                  />
                </div>

                <div class="document-actions">
                  <el-button :disabled="issueStep === 0" @click="issueStep -= 1">Назад</el-button>
                  <el-button v-if="issueStep < 3" type="primary" @click="nextIssueStep">Далее</el-button>
                  <el-button v-else type="primary" @click="issueDocuments">Выпустить пакет</el-button>
                </div>
              </div>
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
              <template v-if="recipientDocuments.length">
                <div class="recipient-docs-grid">
                  <article v-for="doc in paginatedRecipientDocuments" :key="doc.id" class="recipient-doc-card">
                    <p class="recipient-doc-card__event">{{ doc.event_title }}</p>
                    <p class="recipient-doc-card__number">{{ doc.number }}</p>
                    <p class="recipient-doc-card__status">{{ doc.signature_status }}</p>
                    <p class="recipient-doc-card__date">Выдан: {{ formatDocumentDate(doc.issued_at) }}</p>
                    <el-link :href="doc.qr_link" target="_blank" type="primary">Открыть проверку</el-link>
                    <el-link :href="normalizeFileUrl(doc.pdf_url)" target="_blank" type="primary">Скачать PDF</el-link>
                  </article>
                </div>
                <div class="recipient-pagination">
                  <el-pagination
                    v-model:current-page="recipientPage"
                    :page-size="recipientPageSize"
                    layout="prev, pager, next"
                    :total="recipientDocuments.length"
                    background
                    hide-on-single-page
                  />
                </div>
              </template>
              <el-empty v-else description="Документов пока нет" />
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


        <el-tab-pane v-if="canManageSettings" label="Администрирование" name="admin">
          <el-card>
            <template #header>Роли пользователей</template>
            <el-table :data="adminUsers" empty-text="Нет пользователей">
              <el-table-column prop="full_name" label="ФИО" min-width="200" />
              <el-table-column prop="email" label="Email" min-width="220" />
              <el-table-column prop="role_label" label="Текущая роль" width="180" />
              <el-table-column label="Новая роль" min-width="220">
                <template #default="{ row }">
                  <el-select v-model="roleDrafts[row.id]" class="w-full" filterable>
                    <el-option v-for="role in adminRoles" :key="role.value" :label="role.label" :value="role.value" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="Действие" width="160">
                <template #default="{ row }">
                  <el-button
                    type="primary"
                    size="small"
                    :loading="Boolean(roleUpdateLoadingByUser[row.id])"
                    @click="updateUserRole(row)"
                  >
                    Сохранить
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/axios'
import { mockDocuments, mockRecipientDocuments, mockTemplates, mockUsers } from '../data/mockTextData'

const loading = ref(false)
const activeTab = ref('overview')
const summary = ref(null)
const events = ref([])
const participants = ref([])
const templates = ref([])
const documents = ref([])
const recipientDocuments = ref([])
const recipientPage = ref(1)
const recipientPageSize = 8
const auditLogs = ref([])
const awardCategories = ref([])
const recipientConsent = ref(true)
const selectedEventId = ref(null)
const registeredUsers = ref([])
const selectedUserIds = ref([])
const adminUsers = ref([])
const adminRoles = ref([])
const roleDrafts = ref({})
const roleUpdateLoadingByUser = reactive({})
const importPreview = ref(null)
const issuePreview = ref(null)
const issueStep = ref(0)
const selectedTemplateId = ref(null)
const selectedElementId = ref(null)
const newElementField = ref('full_name')
const dragState = ref(null)
const designer = reactive({
  orientation: 'landscape',
  elements: [],
})
const participantAssignForm = reactive({
  status: 'Подтвержден',
  achievement: '',
  hours: 0,
  award_category: '',
})

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

const defaultDesignerElements = () => [
  {
    id: `el-${Date.now()}-title`,
    type: 'text',
    field: 'document_title',
    label: 'Сертификат',
    x: 12,
    y: 24,
    w: 76,
    h: 10,
    fontSize: 34,
    align: 'center',
    wrap: true,
    z: 1,
  },
  {
    id: `el-${Date.now()}-name`,
    type: 'variable',
    field: 'full_name',
    label: '{{ full_name }}',
    x: 14,
    y: 42,
    w: 72,
    h: 9,
    fontSize: 28,
    align: 'center',
    wrap: true,
    z: 2,
  },
  {
    id: `el-${Date.now()}-qr`,
    type: 'qr',
    field: 'qr_link',
    label: 'QR',
    x: 82,
    y: 72,
    w: 11,
    h: 16,
    fontSize: 14,
    align: 'center',
    wrap: false,
    z: 3,
  },
]

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
const canManageSettings = computed(
  () => Boolean(summary.value?.capabilities?.can_manage_settings) && summary.value?.current_user?.role === 'superadmin',
)
const isRegularRecipient = computed(() => summary.value?.current_user?.role === 'recipient')
const paginatedRecipientDocuments = computed(() => {
  const startIndex = (recipientPage.value - 1) * recipientPageSize
  return recipientDocuments.value.slice(startIndex, startIndex + recipientPageSize)
})
const selectedTemplate = computed(() => templates.value.find((template) => template.id === selectedTemplateId.value))
const selectedElement = computed(() => designer.elements.find((element) => element.id === selectedElementId.value))
const sortedDesignerElements = computed(() => [...designer.elements].sort((a, b) => (a.z || 0) - (b.z || 0)))
const selectedIssueEvent = computed(() => events.value.find((event) => event.id === issueForm.event_id))
const selectedIssueTemplate = computed(() => templates.value.find((template) => template.id === issueForm.template_id))

const getErrorMessage = (error, fallback) => error?.response?.data?.detail || fallback
const withFallbackData = (data, fallback) => {
  if (!Array.isArray(data)) return fallback
  return data.length ? data : fallback
}
const normalizeFileUrl = (value) => {
  if (!value) return ''
  if (/^https?:\/\//i.test(value)) return value
  const base = (api.defaults.baseURL || '').replace(/\/$/, '')
  const path = String(value).startsWith('/') ? value : `/${value}`
  return `${base}${path}`
}

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
      summary.value.capabilities.can_manage_events ? api.get('/users/registered') : Promise.resolve({ data: [] }),
      summary.value.capabilities.can_manage_settings ? api.get('/auth/users') : Promise.resolve({ data: [] }),
      summary.value.capabilities.can_manage_settings ? api.get('/reference/roles') : Promise.resolve({ data: [] }),
    ])

    events.value = responses[0].data
    templates.value = withFallbackData(responses[1].data, mockTemplates)
    documents.value = withFallbackData(responses[2].data, mockDocuments)
    recipientDocuments.value = withFallbackData(responses[3].data.documents, mockRecipientDocuments)
    if (isRegularRecipient.value) {
      activeTab.value = 'recipient'
    }
    recipientConsent.value = responses[3].data.consent_to_processing
    awardCategories.value = responses[4].data
    if (!participantAssignForm.award_category && awardCategories.value.length) {
      participantAssignForm.award_category = awardCategories.value[0]
    }
    auditLogs.value = responses[5].data || []
    registeredUsers.value = withFallbackData(responses[6].data, mockUsers)
    if (canManageSettings.value) {
      adminUsers.value = withFallbackData(responses[7].data, mockUsers)
      adminRoles.value = responses[8].data || []
      roleDrafts.value = Object.fromEntries(adminUsers.value.map((user) => [user.id, user.role]))
    } else {
      adminUsers.value = []
      adminRoles.value = []
      roleDrafts.value = {}
      if (activeTab.value === 'admin') {
        activeTab.value = 'overview'
      }
    }

    if (!selectedEventId.value && events.value.length) {
      selectedEventId.value = events.value[0].id
    }
    if (!issueForm.event_id && events.value.length) {
      issueForm.event_id = events.value[0].id
    }
    if (!issueForm.template_id && templates.value.length) {
      issueForm.template_id = templates.value[0].id
    }
    if (!selectedTemplateId.value && templates.value.length) {
      selectTemplate(templates.value[0])
    }
  } catch (error) {
    templates.value = [...mockTemplates]
    documents.value = [...mockDocuments]
    recipientDocuments.value = [...mockRecipientDocuments]
    registeredUsers.value = [...mockUsers]
    if (canManageSettings.value) {
      adminUsers.value = [...mockUsers]
      roleDrafts.value = Object.fromEntries(adminUsers.value.map((user) => [user.id, user.role]))
    }
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



const addRegisteredUsersToEvent = async () => {
  if (!selectedEventId.value) {
    ElMessage.warning('Сначала выберите мероприятие')
    return
  }

  if (!selectedUserIds.value.length) {
    ElMessage.warning('Выберите хотя бы одного зарегистрированного пользователя')
    return
  }
  if (!awardCategories.value.length) {
    ElMessage.warning('Категории наград пока не загружены')
    return
  }

  try {
    const { data } = await api.post(`/events/${selectedEventId.value}/participants/add-users`, {
      user_ids: selectedUserIds.value,
      status: participantAssignForm.status,
      achievement: participantAssignForm.achievement,
      hours: participantAssignForm.hours,
      award_category: participantAssignForm.award_category || awardCategories.value[0],
    })
    ElMessage.success(`Добавлено: ${data.inserted}, уже в мероприятии: ${data.skipped_existing}`)
    selectedUserIds.value = []
    await loadDashboard()
    await loadParticipants()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, 'Не удалось добавить зарегистрированных пользователей'))
  }
}

const handleImportFileChange = async (event) => {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (!selectedEventId.value) {
    ElMessage.warning('Сначала выберите мероприятие')
    return
  }

  const payload = new FormData()
  payload.append('file', file)
  try {
    const { data } = await api.post(`/events/${selectedEventId.value}/participants/import/preview`, payload, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    importPreview.value = data
    ElMessage.success(`Файл проверен: валидных строк ${data.rows_valid}`)
  } catch (error) {
    importPreview.value = null
    ElMessage.error(getErrorMessage(error, 'Не удалось разобрать файл импорта'))
  }
}

const commitParticipantImport = async () => {
  if (!selectedEventId.value || !importPreview.value?.batch_id) return
  try {
    const { data } = await api.post(`/events/${selectedEventId.value}/participants/import/${importPreview.value.batch_id}/commit`)
    ElMessage.success(`Импортировано участников: ${data.imported}`)
    importPreview.value = null
    await loadDashboard()
    await loadParticipants()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, 'Не удалось завершить импорт'))
  }
}

const syncIssueEvent = async () => {
  if (issueForm.event_id) {
    selectedEventId.value = issueForm.event_id
    await loadParticipants()
  }
}

const handleIssueImportFileChange = async (event) => {
  if (issueForm.event_id) {
    selectedEventId.value = issueForm.event_id
  }
  await handleImportFileChange(event)
}

const nextIssueStep = async () => {
  if (issueStep.value === 0) {
    if (!issueForm.event_id) {
      ElMessage.warning('Выберите мероприятие')
      return
    }
    if (importPreview.value?.batch_id) {
      await commitParticipantImport()
    } else {
      await syncIssueEvent()
    }
    if (!participants.value.length) {
      ElMessage.warning('Для выпуска нужны участники')
      return
    }
  }
  if (issueStep.value === 1 && !issueForm.template_id) {
    ElMessage.warning('Выберите шаблон')
    return
  }
  if (issueStep.value === 2 && !issuePreview.value) {
    await loadIssuePreview()
    if (!issuePreview.value) return
  }
  issueStep.value += 1
}



const updateUserRole = async (user) => {
  if (!canManageSettings.value) {
    ElMessage.error('Требуются права администратора')
    return
  }

  const selectedRole = roleDrafts.value[user.id]
  if (!selectedRole) {
    ElMessage.warning('Выберите роль')
    return
  }
  if (selectedRole === user.role) {
    ElMessage.info('Роль уже установлена')
    return
  }

  try {
    roleUpdateLoadingByUser[user.id] = true
    await api.patch(`/auth/users/${user.id}/role`, { role: selectedRole })
    ElMessage.success('Роль обновлена')
    await loadDashboard()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, 'Не удалось обновить роль пользователя'))
  } finally {
    roleUpdateLoadingByUser[user.id] = false
  }
}

const createTemplate = async () => {
  try {
    const { data } = await api.post('/templates', {
      ...templateForm,
      layout_config: buildDesignerLayout(),
    })
    ElMessage.success('Шаблон сохранен')
    await loadDashboard()
    selectTemplate(data)
  } catch (error) {
    ElMessage.error(getErrorMessage(error, 'Не удалось создать шаблон'))
  }
}

const normalizeTemplateLayout = (template) => {
  let layout = template?.layout_config || {}
  if (typeof layout === 'string') {
    try {
      layout = JSON.parse(layout)
    } catch {
      layout = {}
    }
  }
  designer.orientation = template?.orientation || layout.orientation || 'landscape'
  designer.elements = Array.isArray(layout.elements) && layout.elements.length
    ? layout.elements.map((element, index) => ({
        id: element.id || `el-${Date.now()}-${index}`,
        type: element.type || 'variable',
        field: element.field || '',
        label: element.label || element.field || 'Слой',
        x: Number(element.x ?? 10),
        y: Number(element.y ?? 10),
        w: Number(element.w ?? 30),
        h: Number(element.h ?? 8),
        fontSize: Number(element.fontSize ?? 18),
        align: element.align || 'left',
        wrap: Boolean(element.wrap ?? true),
        z: Number(element.z ?? index + 1),
      }))
    : defaultDesignerElements()
  selectedElementId.value = designer.elements[0]?.id || null
}

const selectTemplate = (template) => {
  if (!template) return
  selectedTemplateId.value = template.id
  templateForm.name = template.name
  templateForm.orientation = template.orientation
  templateForm.description = template.description || ''
  templateForm.allowed_fields = Array.isArray(template.allowed_fields) ? template.allowed_fields : [...templateFields]
  normalizeTemplateLayout(template)
}

const buildDesignerLayout = () => ({
  orientation: designer.orientation,
  elements: designer.elements,
  fonts_locked: true,
  colors_locked: true,
  logos_locked: true,
  grid_locked: true,
  margins_locked: true,
  page: 'A4',
})

const saveTemplateLayout = async () => {
  if (!selectedTemplateId.value) {
    ElMessage.warning('Выберите шаблон')
    return
  }
  try {
    const { data } = await api.patch(`/templates/${selectedTemplateId.value}/layout`, {
      layout_config: buildDesignerLayout(),
    })
    ElMessage.success('Макет шаблона сохранен')
    const index = templates.value.findIndex((template) => template.id === data.id)
    if (index >= 0) {
      templates.value[index] = data
    }
    selectTemplate(data)
  } catch (error) {
    ElMessage.error(getErrorMessage(error, 'Не удалось сохранить макет'))
  }
}

const addDesignerElement = (type) => {
  const z = designer.elements.length + 1
  const field = type === 'variable' ? newElementField.value : type
  const label = type === 'variable' ? `{{ ${field} }}` : type === 'qr' ? 'QR' : 'Подпись'
  designer.elements.push({
    id: `el-${Date.now()}-${z}`,
    type,
    field,
    label,
    x: type === 'qr' ? 80 : 16,
    y: 16 + z * 6,
    w: type === 'qr' ? 12 : 54,
    h: type === 'qr' ? 16 : 8,
    fontSize: type === 'qr' ? 14 : 18,
    align: type === 'qr' ? 'center' : 'left',
    wrap: type !== 'qr',
    z,
  })
  selectedElementId.value = designer.elements.at(-1).id
}

const duplicateDesignerElement = () => {
  if (!selectedElement.value) return
  const copy = {
    ...selectedElement.value,
    id: `el-${Date.now()}-copy`,
    label: `${selectedElement.value.label} копия`,
    x: Math.min(96, selectedElement.value.x + 3),
    y: Math.min(96, selectedElement.value.y + 3),
    z: designer.elements.length + 1,
  }
  designer.elements.push(copy)
  selectedElementId.value = copy.id
}

const removeDesignerElement = () => {
  if (!selectedElementId.value) return
  designer.elements = designer.elements.filter((element) => element.id !== selectedElementId.value)
  selectedElementId.value = designer.elements[0]?.id || null
}

const designerElementStyle = (element) => ({
  left: `${element.x}%`,
  top: `${element.y}%`,
  width: `${element.w}%`,
  height: `${element.h}%`,
  fontSize: `${element.fontSize}px`,
  textAlign: element.align,
  zIndex: element.z,
  whiteSpace: element.wrap ? 'normal' : 'nowrap',
})

const startDesignerDrag = (event, element) => {
  selectedElementId.value = element.id
  dragState.value = {
    id: element.id,
    startX: event.clientX,
    startY: event.clientY,
    originX: element.x,
    originY: element.y,
  }
}

const moveDesignerElement = (event) => {
  if (!dragState.value) return
  const element = designer.elements.find((item) => item.id === dragState.value.id)
  if (!element) return
  const page = event.currentTarget.querySelector('.designer-page')
  const rect = page.getBoundingClientRect()
  const dx = ((event.clientX - dragState.value.startX) / rect.width) * 100
  const dy = ((event.clientY - dragState.value.startY) / rect.height) * 100
  element.x = Math.max(0, Math.min(100 - element.w, Number((dragState.value.originX + dx).toFixed(1))))
  element.y = Math.max(0, Math.min(100 - element.h, Number((dragState.value.originY + dy).toFixed(1))))
}

const finishDesignerDrag = () => {
  dragState.value = null
}

const issueDocuments = async () => {
  try {
    const { data } = await api.post('/documents/issue', issueForm)
    ElMessage.success(`Выпущено документов: ${data.issued}`)
    issuePreview.value = null
    issueStep.value = 4
    await loadDashboard()
    await loadParticipants()
    await loadAudit()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, 'Не удалось выпустить документы'))
  }
}

const loadIssuePreview = async () => {
  if (!issueForm.event_id || !issueForm.template_id) {
    ElMessage.warning('Выберите мероприятие и шаблон')
    return
  }
  try {
    issueStep.value = 2
    const { data } = await api.get('/documents/preview', {
      params: {
        event_id: issueForm.event_id,
        template_id: issueForm.template_id,
      },
    })
    issuePreview.value = data
  } catch (error) {
    issuePreview.value = null
    ElMessage.error(getErrorMessage(error, 'Не удалось сформировать предпросмотр'))
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
const formatDocumentDate = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleDateString('ru-RU')
}

watch(selectedEventId, loadParticipants)
watch(recipientDocuments, () => {
  const maxPage = Math.max(1, Math.ceil(recipientDocuments.value.length / recipientPageSize))
  if (recipientPage.value > maxPage) {
    recipientPage.value = maxPage
    return
  }
  recipientPage.value = 1
})

const handleAuthChanged = async () => {
  await loadDashboard()
  await loadParticipants()
}

onMounted(async () => {
  await handleAuthChanged()
  window.addEventListener('auth-changed', handleAuthChanged)
})

onUnmounted(() => {
  window.removeEventListener('auth-changed', handleAuthChanged)
})
</script>
