<template>
  <section class="dashboard-page">
    <div class="section-heading">
      <span class="eyebrow">Документы</span>
      <h1>Реестр документов</h1>
      <p>На главной странице отображаются только документы. Откройте карточку для просмотра полной информации.</p>
    </div>

    <div v-loading="loading">
      <div class="documents-grid">
        <el-card v-for="doc in pagedDocuments" :key="doc.id" class="document-card">
          <p class="document-card__number">{{ doc.number }}</p>
          <p>{{ doc.full_name }}</p>
          <p>{{ doc.event_title }}</p>
          <p>{{ doc.signature_status }}</p>
          <el-button type="primary" text @click="router.push(`/documents/${doc.id}`)">Открыть детали</el-button>
        </el-card>
      </div>

      <div class="recipient-pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          layout="prev, pager, next"
          :total="documents.length"
          background
          hide-on-single-page
        />
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api/axios'
import { textDocuments } from '../data/textData'

const router = useRouter()
const loading = ref(false)
const documents = ref([])
const page = ref(1)
const pageSize = 8

const pagedDocuments = computed(() => {
  const start = (page.value - 1) * pageSize
  return documents.value.slice(start, start + pageSize)
})

const loadDocuments = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/documents')
    documents.value = Array.isArray(data) && data.length ? data : textDocuments
  } catch (error) {
    documents.value = textDocuments
    ElMessage.warning(error?.response?.data?.detail || 'Используются локальные текстовые данные документов')
  } finally {
    loading.value = false
  }
}

onMounted(loadDocuments)
</script>
