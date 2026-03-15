import { createRouter, createWebHistory } from 'vue-router'
import { useAdminStore } from '@/stores/admin'

const routes = [
  { path: '/', redirect: '/apply' },
  { path: '/apply', component: () => import('@/views/student/ApplyView.vue') },
  { path: '/application/:id/upload', component: () => import('@/views/student/UploadView.vue') },
  { path: '/application/:id/interview', component: () => import('@/views/student/InterviewView.vue') },
  { path: '/application/:id/status', component: () => import('@/views/student/StatusView.vue') },
  { path: '/admin/login', component: () => import('@/views/admin/AdminLoginView.vue') },
  {
    path: '/admin',
    redirect: '/admin/dashboard',
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/dashboard',
    component: () => import('@/views/admin/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/applications',
    component: () => import('@/views/admin/ApplicationsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/applications/:id',
    component: () => import('@/views/admin/ApplicationDetailView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const adminStore = useAdminStore()
    if (!adminStore.isAuthenticated) {
      next('/admin/login')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
