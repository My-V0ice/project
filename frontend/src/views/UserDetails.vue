<template>
  <section class="dashboard-page">
    <el-card v-if="user">
      <template #header>Информация о пользователе</template>
      <div class="detail-grid">
        <div><strong>ФИО:</strong> {{ user.full_name }}</div>
        <div><strong>Email:</strong> {{ user.email }}</div>
        <div><strong>Роль:</strong> {{ user.role_label || user.role }}</div>
        <div><strong>Бренд:</strong> {{ user.brand_name }}</div>
        <div><strong>Подразделение:</strong> {{ user.division_name }}</div>
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
import { textUsers } from '../data/textData'

const route = useRoute()
const router = useRouter()
const user = ref(null)

const loadUser = async () => {
  try {
    const { data } = await api.get(`/auth/users/${route.params.id}`)
    user.value = data
  } catch (error) {
    user.value = textUsers.find((item) => String(item.id) === String(route.params.id)) || null
    if (!user.value) {
      ElMessage.error(error?.response?.data?.detail || 'Пользователь не найден')
    } else {
      ElMessage.warning('Используются локальные текстовые данные этого пользователя')
    }
  }
}

onMounted(loadUser)
</script>
