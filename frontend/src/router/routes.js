import Dashboard from '../views/Dashboard.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import VerifyDocument from '../views/VerifyDocument.vue'

export const routes = [
  { path: '/login', name: 'Login', component: Login, meta: { guest: true } },
  { path: '/register', name: 'Register', component: Register, meta: { guest: true } },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/verify/:code', name: 'VerifyDocument', component: VerifyDocument },
  { path: '/', redirect: '/dashboard' },
]
