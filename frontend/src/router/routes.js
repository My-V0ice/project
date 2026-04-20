import Dashboard from '../views/Dashboard.vue'
import DocumentDetails from '../views/DocumentDetails.vue'
import DocumentsHome from '../views/DocumentsHome.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import TemplateDetails from '../views/TemplateDetails.vue'
import UserDetails from '../views/UserDetails.vue'
import VerifyDocument from '../views/VerifyDocument.vue'

export const routes = [
  { path: '/', name: 'DocumentsHome', component: DocumentsHome },
  { path: '/login', name: 'Login', component: Login, meta: { guest: true } },
  { path: '/register', name: 'Register', component: Register, meta: { guest: true } },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/documents/:id', name: 'DocumentDetails', component: DocumentDetails },
  { path: '/templates/:id', name: 'TemplateDetails', component: TemplateDetails },
  { path: '/users/:id', name: 'UserDetails', component: UserDetails },
  { path: '/verify/:code', name: 'VerifyDocument', component: VerifyDocument },
]
