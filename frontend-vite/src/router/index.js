import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '经营驾驶舱', requiresAuth: true }
      },
      {
        path: 'project-board',
        name: 'ProjectBoard',
        component: () => import('@/views/ProjectBoard.vue'),
        meta: { title: '项目核算看板', requiresAuth: true }
      },
      {
        path: 'project-board/detail/:id',
        name: 'ProjectBoardDetail',
        component: () => import('@/views/ProjectBoardDetail.vue'),
        meta: { title: '项目详情', requiresAuth: true }
      },
      {
        path: 'affiliated-tax',
        name: 'AffiliatedTax',
        component: () => import('@/views/AffiliatedTaxCalc.vue'),
        meta: { title: '挂靠税费计算器', requiresAuth: true }
      },
      {
        path: 'tax-burden',
        name: 'TaxBurden',
        component: () => import('@/views/TaxBurdenAnalysis.vue'),
        meta: { title: '税负率与缺票分析', requiresAuth: true }
      },
      {
        path: 'lmr-reference',
        name: 'LmrReference',
        component: () => import('@/views/LmrReference.vue'),
        meta: { title: '人材机参考库', requiresAuth: true }
      },
      {
        path: 'project-profit',
        name: 'ProjectProfit',
        component: () => import('@/views/ProjectProfit.vue'),
        meta: { title: '项目利润表', requiresAuth: true }
      },
      {
        path: 'fund-daily',
        name: 'FundDaily',
        component: () => import('@/views/FundDaily.vue'),
        meta: { title: '资金日报', requiresAuth: true }
      },
      {
        path: 'aging-receivable',
        name: 'AgingReceivable',
        component: () => import('@/views/AgingReceivable.vue'),
        meta: { title: '应收账龄', requiresAuth: true }
      },
      {
        path: 'import-balance',
        name: 'ImportBalance',
        component: () => import('@/views/ImportBalance.vue'),
        meta: { title: '科目余额表导入', requiresAuth: true }
      },
      {
        path: 'import-voucher',
        name: 'ImportVoucher',
        component: () => import('@/views/ImportVoucher.vue'),
        meta: { title: '凭证/序时账导入', requiresAuth: true }
      },
      {
        path: 'subject-mapping',
        name: 'SubjectMapping',
        component: () => import('@/views/SubjectMapping.vue'),
        meta: { title: '科目映射配置', requiresAuth: true }
      },
      {
        path: 'project-list',
        name: 'ProjectList',
        component: () => import('@/views/ProjectList.vue'),
        meta: { title: '项目档案', requiresAuth: true }
      },
      {
        path: 'bank-account',
        name: 'BankAccount',
        component: () => import('@/views/BankAccount.vue'),
        meta: { title: '银行账户', requiresAuth: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.token) {
    next('/login')
  } else if (to.path === '/login' && userStore.token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
