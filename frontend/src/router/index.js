import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'overview',
    component: () => import('@/views/Overview.vue'),
  },
  {
    path: '/groups',
    name: 'groups',
    component: () => import('@/views/Groups.vue'),
  },
  {
    path: '/groups/:roomId',
    name: 'groupDetail',
    component: () => import('@/views/GroupDetail.vue'),
    props: true,
  },
  {
    path: '/operations',
    name: 'operations',
    component: () => import('@/views/OperationsDashboard.vue'),
  },
  {
    path: '/group-manager',
    name: 'groupManager',
    component: () => import('@/views/GroupManager.vue'),
  },
  {
    path: '/daily-board',
    name: 'dailyBoard',
    component: () => import('@/views/DailyBoard.vue'),
  },
  {
    path: '/ai-analyze',
    name: 'aiAnalyze',
    component: () => import('@/views/AIAnalyze.vue'),
  },
  {
    path: '/external-board',
    name: 'externalBoard',
    component: () => import('@/views/ExternalBoard.vue'),
  },
  {
    path: '/person-board',
    name: 'personBoard',
    component: () => import('@/views/PersonBoard.vue'),
  },
  {
    path: '/impact-board',
    name: 'impactBoard',
    component: () => import('@/views/ImpactBoard.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
