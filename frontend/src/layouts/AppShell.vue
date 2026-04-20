<template>
  <div class="shell">
    <header class="shell-header">
      <div class="shell-brand" @click="goHome">
        <div class="brand-mark">TO</div>
        <div>
          <strong>Документы ТОГУ</strong>
          <p>Выпуск и верификация документов мероприятий</p>
        </div>
      </div>

      <div class="shell-actions">
        <template v-if="user">
          <div class="user-chip">
            <span>{{ user.full_name }}</span>
            <small v-if="isSuperadmin">{{ user.role_label }}</small>
          </div>
          <el-button type="danger" plain @click="logout">Выйти</el-button>
        </template>
        <template v-else>
          <el-button text @click="router.push('/login')">Войти</el-button>
          <el-button type="primary" @click="router.push('/register')">Регистрация</el-button>
        </template>
      </div>
    </header>

    <main class="shell-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api/axios'
import { clearAuthSession, getAccessToken } from '../utils/authToken'

const router = useRouter()
const user = ref(null)
const isSuperadmin = computed(() => user.value?.role === 'superadmin')

const refreshUser = async () => {
  const token = getAccessToken()
  if (!token) {
    user.value = null
    return
  }

  try {
    const { data } = await api.get('/auth/me')
    user.value = data
    localStorage.setItem('user_email', data.email)
  } catch (error) {
    const status = error?.response?.status
    if (status === 401 || status === 403) {
      clearAuthSession()
      user.value = null
      return
    }
    // Keep token on transient backend/network issues to avoid forced logout loops.
    user.value = null
  }
}

const goHome = () => {
  router.push('/')
}

const logout = () => {
  clearAuthSession()
  user.value = null
  ElMessage.success('Сессия завершена')
  router.push('/login')
}

const handleAuthChanged = () => {
  refreshUser()
}

onMounted(() => {
  refreshUser()
  window.addEventListener('auth-changed', handleAuthChanged)
})

onUnmounted(() => {
  window.removeEventListener('auth-changed', handleAuthChanged)
})
</script>
