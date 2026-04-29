<template>
  <section class="auth-page">
    <el-card class="auth-card auth-card-wide">
      <div class="section-heading">
        <span class="eyebrow">Регистрация</span>
        <h1>Создание аккаунта</h1>
        <p>Для получателей, организаторов и администраторов платформы документов ТОГУ.</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="grid-two">
          <el-form-item label="ФИО" prop="full_name">
            <el-input v-model="form.full_name" placeholder="Иванов Иван Иванович" />
          </el-form-item>

          <el-form-item label="Email" prop="email">
            <el-input v-model="form.email" placeholder="name@togu.example" />
          </el-form-item>

          <el-form-item label="Бренд" prop="brand_name">
            <el-input v-model="form.brand_name" />
          </el-form-item>

          <el-form-item label="Подразделение" prop="division_name">
            <el-input v-model="form.division_name" />
          </el-form-item>

          <el-form-item label="Пароль" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="Минимум 6 символов" />
          </el-form-item>

          <el-form-item label="Подтверждение пароля" prop="confirmPassword">
            <el-input v-model="form.confirmPassword" type="password" show-password @keyup.enter="handleRegister" />
          </el-form-item>
        </div>

        <el-button type="primary" class="w-full" :loading="loading" @click="handleRegister">Создать аккаунт</el-button>
      </el-form>

      <div class="auth-links">
        <span>Уже зарегистрированы?</span>
        <el-link type="primary" @click="router.push('/login')">Войти</el-link>
      </div>
    </el-card>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api/axios'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  full_name: '',
  email: '',
  brand_name: 'ТОГУ',
  division_name: 'Цифровая кафедра',
  password: '',
  confirmPassword: '',
})

const validateConfirmPassword = (_, value, callback) => {
  if (!value) {
    callback(new Error('Подтвердите пароль'))
    return
  }
  if (value !== form.password) {
    callback(new Error('Пароли не совпадают'))
    return
  }
  callback()
}

const rules = {
  full_name: [{ required: true, message: 'Введите ФИО', trigger: 'blur' }],
  email: [
    { required: true, message: 'Введите email', trigger: 'blur' },
    { type: 'email', message: 'Укажите корректный email', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Введите пароль', trigger: 'blur' },
    { min: 6, message: 'Минимум 6 символов', trigger: 'blur' },
  ],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }],
}

const handleRegister = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true
    await api.post('/auth/register', {
      full_name: form.full_name,
      email: form.email,
      brand_name: form.brand_name,
      division_name: form.division_name,
      password: form.password,
    })
    ElMessage.success('Аккаунт создан, теперь можно войти')
    router.push('/login')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Не удалось создать аккаунт')
  } finally {
    loading.value = false
  }
}

</script>
