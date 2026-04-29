<template>
  <section class="auth-page">
    <el-card class="auth-card">
      <div class="section-heading">
        <span class="eyebrow">Авторизация</span>
        <h1>Вход в систему выпуска документов</h1>
        <p>Личный кабинет получателя, реестр проверки и рабочее место администратора в одном приложении.</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="Email" prop="email">
          <el-input v-model="form.email" placeholder="name@togu.example" />
        </el-form-item>

        <el-form-item label="Пароль" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="Введите пароль" @keyup.enter="handleLogin" />
        </el-form-item>

        <el-button type="primary" class="w-full" :loading="loading" @click="handleLogin">Войти</el-button>
      </el-form>

      <div class="auth-links">
        <span>Нет аккаунта?</span>
        <el-link type="primary" @click="router.push('/register')">Создать</el-link>
      </div>
    </el-card>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api/axios'
import { clearAuthSession, setAccessToken } from '../utils/authToken'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  email: '',
  password: '',
})

const rules = {
  email: [
    { required: true, message: 'Введите email', trigger: 'blur' },
    { type: 'email', message: 'Укажите корректный email', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Введите пароль', trigger: 'blur' },
    { min: 6, message: 'Минимум 6 символов', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    const payload = new URLSearchParams()
    payload.append('username', form.email)
    payload.append('password', form.password)

    const response = await api.post('/auth/login', payload, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

    const token = setAccessToken(response.data.access_token)
    if (!token) {
      clearAuthSession()
      throw new Error('Missing access token')
    }
    localStorage.setItem('user_email', form.email)
    window.dispatchEvent(new Event('auth-changed'))
    ElMessage.success('Вход выполнен')
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Не удалось выполнить вход')
  } finally {
    loading.value = false
  }
}
</script>
