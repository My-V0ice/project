<template>
  <section class="verify-page">
    <el-card class="verify-card" v-loading="loading">
      <div class="section-heading">
        <span class="eyebrow">Проверка подлинности</span>
        <h1>Страница документа по QR-коду</h1>
        <p>Публичная верификация номера, статуса подписи и связи с мероприятием без входа в систему.</p>
      </div>

      <el-result v-if="error" icon="error" title="Документ не найден" :sub-title="error" />

      <template v-else-if="document">
        <div class="verify-grid">
          <div class="verify-item">
            <span>Номер документа</span>
            <strong>{{ document.number }}</strong>
          </div>
          <div class="verify-item">
            <span>Статус</span>
            <strong>{{ document.status }}</strong>
          </div>
          <div class="verify-item">
            <span>Подписант</span>
            <strong>{{ document.signatory_name }}</strong>
          </div>
          <div class="verify-item">
            <span>Тип подписи</span>
            <strong>{{ document.signature_type }}</strong>
          </div>
          <div class="verify-item">
            <span>Получатель</span>
            <strong>{{ document.full_name }}</strong>
          </div>
          <div class="verify-item">
            <span>Мероприятие</span>
            <strong>{{ document.event_title }}</strong>
          </div>
        </div>

        <el-descriptions :column="1" border>
          <el-descriptions-item label="Категория">{{ document.award_category }}</el-descriptions-item>
          <el-descriptions-item label="Статус участника">{{ document.participant_status }}</el-descriptions-item>
          <el-descriptions-item label="Часы">{{ document.hours }}</el-descriptions-item>
          <el-descriptions-item label="Подпись">{{ document.signature_status }}</el-descriptions-item>
          <el-descriptions-item label="Шаблон">{{ document.template_name }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-card>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api/axios'

const route = useRoute()
const loading = ref(false)
const document = ref(null)
const error = ref('')

const loadDocument = async () => {
  loading.value = true
  try {
    const { data } = await api.get(`/documents/${route.params.code}/verify`)
    document.value = data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Проверка не удалась'
  } finally {
    loading.value = false
  }
}

onMounted(loadDocument)
</script>
