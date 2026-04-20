<template>
  <section class="dashboard-page">
    <el-card v-if="document" class="document-details-card">
      <template #header>
        <div class="document-details-header">
          <div>
            <p class="document-details-eyebrow">Документ</p>
            <h2>{{ document.number }}</h2>
          </div>
          <el-tag type="success">{{ document.signature_status || 'Подписан' }}</el-tag>
        </div>
      </template>

      <div class="document-details-grid">
        <div class="verify-item">
          <span>Получатель</span>
          <strong>{{ document.full_name || '-' }}</strong>
        </div>
        <div class="verify-item">
          <span>Мероприятие</span>
          <strong>{{ document.event_title || '-' }}</strong>
        </div>
        <div class="verify-item">
          <span>Статус документа</span>
          <strong>{{ document.status || '-' }}</strong>
        </div>
        <div class="verify-item">
          <span>Дата выдачи</span>
          <strong>{{ formatDate(document.issued_at) }}</strong>
        </div>
      </div>

      <div class="document-actions">
        <el-button type="primary" @click="generateQrCode">Сгенерировать QR-код</el-button>
        <el-button :disabled="!pdfUrl" @click="downloadByLink(pdfUrl, `${document.number}.pdf`)">Скачать PDF</el-button>
        <el-button :disabled="!archiveUrl" @click="downloadByLink(archiveUrl, `${document.number}.pdfa`)">Скачать PDF/A</el-button>
        <el-button :disabled="!imageUrl" @click="downloadByLink(imageUrl, `${document.number}.png`)">Скачать PNG</el-button>
      </div>

      <div v-if="qrCodeUrl" class="document-qr-block">
        <img :src="qrCodeUrl" :alt="`QR документа ${document.number}`" class="document-qr-image" />
        <div>
          <p class="helper-text">QR-код ссылается на страницу проверки документа.</p>
          <el-link :href="verificationUrl" target="_blank" type="primary">{{ verificationUrl }}</el-link>
        </div>
      </div>

      <div class="detail-links">
        <el-button type="primary" text :disabled="!document.template_id" @click="openTemplate">Открыть страницу шаблона</el-button>
        <el-button type="primary" text :disabled="!document.issued_by" @click="openUser">Открыть страницу пользователя</el-button>
      </div>
    </el-card>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api/axios'
import { textDocuments } from '../data/textData'

const route = useRoute()
const router = useRouter()

const document = ref(null)
const qrCodeUrl = ref('')

const normalizeFileUrl = (value) => {
  if (!value) return ''
  if (/^https?:\/\//i.test(value)) return value
  const base = (api.defaults.baseURL || '').replace(/\/$/, '')
  const path = String(value).startsWith('/') ? value : `/${value}`
  return `${base}${path}`
}

const pdfUrl = computed(() => normalizeFileUrl(document.value?.pdf_url))
const archiveUrl = computed(() => normalizeFileUrl(document.value?.archive_url))
const imageUrl = computed(() => normalizeFileUrl(document.value?.image_url))
const verificationUrl = computed(() => document.value?.qr_link || '')

const generateQrCode = () => {
  if (!verificationUrl.value) {
    ElMessage.warning('Ссылка для проверки документа недоступна')
    return
  }
  const encoded = encodeURIComponent(verificationUrl.value)
  qrCodeUrl.value = `https://api.qrserver.com/v1/create-qr-code/?size=260x260&data=${encoded}`
}

const downloadByLink = (url, fallbackName) => {
  if (!url) return
  const link = window.document.createElement('a')
  link.href = url
  link.download = fallbackName
  link.target = '_blank'
  link.rel = 'noopener'
  window.document.body.appendChild(link)
  link.click()
  window.document.body.removeChild(link)
}

const formatDate = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('ru-RU')
}

const loadDocument = async () => {
  try {
    const { data } = await api.get(`/documents/id/${route.params.id}`)
    document.value = data
  } catch (error) {
    document.value = textDocuments.find((item) => String(item.id) === String(route.params.id)) || null
    if (!document.value) {
      ElMessage.error(error?.response?.data?.detail || 'Документ не найден')
    } else {
      ElMessage.warning('Используются локальные текстовые данные этого документа')
    }
  }
}

const openTemplate = () => {
  if (document.value?.template_id) {
    router.push(`/templates/${document.value.template_id}`)
  }
}

const openUser = () => {
  if (document.value?.issued_by) {
    router.push(`/users/${document.value.issued_by}`)
  }
}

onMounted(loadDocument)
</script>

