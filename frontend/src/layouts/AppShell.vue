<template>
  <div class="shell">
    <div class="shell-backdrop" aria-hidden="true">
      <div class="shell-backdrop__plane shell-backdrop__plane--red"></div>
      <div class="shell-backdrop__plane shell-backdrop__plane--gold"></div>
      <div class="shell-backdrop__grid"></div>
    </div>

    <header class="shell-header">
      <div class="shell-brand" @click="goHome">
        <div class="brand-logo" aria-label="Тихоокеанский государственный университет">
          <svg class="brand-logo__svg" viewBox="0 0 456 120" role="img" aria-hidden="true">
            <image :href="toguMark" x="8" y="15" width="116" height="88" preserveAspectRatio="xMidYMid meet" />
            <g fill="#9b2242" font-family="Arial, Helvetica, sans-serif" font-size="29" font-weight="700">
              <text x="136" y="39">Тихоокеанский</text>
              <text x="136" y="68">государственный</text>
              <text x="136" y="97">университет</text>
            </g>
          </svg>
        </div>
        <div class="shell-brand-copy">
          <span class="shell-brand-copy__label">Цифровая платформа</span>
          <strong>Документы ТОГУ</strong>
          <p>Единая среда выпуска и проверки документов университета</p>
        </div>
      </div>

      <div class="shell-actions">
        <div class="shell-status">
          <span class="shell-status__dot"></span>
          <span>Бренд-система ТОГУ</span>
        </div>
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

    <main class="shell-main shell-main--framed">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api/axios'
import toguMark from '../assets/togu-mark.jpg'
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
