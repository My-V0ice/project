import { createRouter, createWebHistory } from 'vue-router'
import { getAccessToken } from '../utils/authToken'

import { routes } from './routes'


const router = createRouter({
  history: createWebHistory(),
  routes,
})

const getRoleFromToken = (token) => {
  if (!token) return null

  try {
    const payload = token.split('.')[1]
    if (!payload) return null
    const decoded = JSON.parse(atob(payload))
    return decoded?.role || null
  } catch {
    return null
  }
}

router.beforeEach((to) => {
  const token = getAccessToken()
  const role = getRoleFromToken(token)

  if (to.meta.requiresAdmin && role !== 'superadmin') {
    return '/dashboard'
  }

  if (to.meta.guest && token) {
    return '/dashboard'
  }

  return true
})

export default router
