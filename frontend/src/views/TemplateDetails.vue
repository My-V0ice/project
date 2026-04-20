<template>
  <section class="dashboard-page">
    <el-card v-if="templateData">
      <template #header>Информация о шаблоне</template>
      <div class="detail-grid">
        <div><strong>Название:</strong> {{ templateData.name }}</div>
        <div><strong>Ориентация:</strong> {{ templateData.orientation }}</div>
        <div><strong>Бренд:</strong> {{ templateData.brand_name }}</div>
        <div><strong>Сформировано документов:</strong> {{ templateData.documents_generated || 0 }}</div>
        <div><strong>Описание:</strong> {{ templateData.description || '-' }}</div>
      </div>
      <el-button type="primary" text @click="router.push('/')">Назад к документам</el-button>
    </el-card>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api/axios'
import { textTemplates } from '../data/textData'

const route = useRoute()
const router = useRouter()
const templateData = ref(null)

const loadTemplate = async () => {
  try {
    const { data } = await api.get(`/templates/${route.params.id}`)
    templateData.value = data
  } catch (error) {
    templateData.value = textTemplates.find((item) => String(item.id) === String(route.params.id)) || null
    if (!templateData.value) {
      ElMessage.error(error?.response?.data?.detail || 'Шаблон не найден')
    } else {
      ElMessage.warning('Используются локальные текстовые данные этого шаблона')
    }
  }
}

onMounted(loadTemplate)
</script>
