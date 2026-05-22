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
    path: '/persons',
    name: 'persons',
    component: () => import('@/views/Persons.vue'),
  },
  {
    path: '/messages',
    name: 'messages',
    component: () => import('@/views/Messages.vue'),
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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
