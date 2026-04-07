import { createRouter, createWebHistory } from 'vue-router'

import { routes } from './routes'


const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !token) {
    return '/login'
  }

  if (to.meta.guest && token) {
    return '/dashboard'
  }

  return true
})

export default router
