<template>
  <div class="main-layout">
    <!-- 顶部 -->
    <div class="main-header">
      <div class="header-left">
        <div style="font-size: 22px">
          <span
            style="background: linear-gradient(135deg, #409eff, #67c23a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: bold"
            >建</span
          >
        </div>
        <span class="logo-text">建税盾 <span class="logo-badge">建筑版</span></span>
      </div>
      <div class="header-right">
        <el-dropdown @command="handleCommand">
          <div class="user-info">
            <div class="user-avatar">{{ userStore.avatarText }}</div>
            <span>{{ userStore.userName || '用户' }}</span>
            <el-icon><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人信息</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="main-body">
      <!-- 侧边栏 -->
      <div class="sidebar">
        <el-menu
          :default-active="activeMenu"
          @select="handleMenuSelect"
          style="border-right: none"
        >
          <el-menu-item index="dashboard">
            <el-icon><DataAnalysis /></el-icon>
            <span>经营驾驶舱</span>
          </el-menu-item>
          <el-menu-item index="project-board">
            <el-icon><TrendCharts /></el-icon>
            <span>项目核算看板</span>
          </el-menu-item>
          <el-menu-item index="affiliated-tax">
            <el-icon><Calculator /></el-icon>
            <span>挂靠税费计算器</span>
          </el-menu-item>
          <el-menu-item index="tax-burden">
            <el-icon><TrendCharts /></el-icon>
            <span>税负率与缺票分析</span>
          </el-menu-item>
          <el-menu-item index="lmr-reference">
            <el-icon><Histogram /></el-icon>
            <span>人材机参考库</span>
          </el-menu-item>
          <el-menu-item index="project-profit">
            <el-icon><PieChart /></el-icon>
            <span>项目利润表</span>
          </el-menu-item>
          <el-menu-item index="fund-daily">
            <el-icon><Wallet /></el-icon>
            <span>资金日报</span>
          </el-menu-item>
          <el-menu-item index="aging-receivable">
            <el-icon><Histogram /></el-icon>
            <span>应收账龄</span>
          </el-menu-item>
          <el-sub-menu index="data">
            <template #title>
              <el-icon><Upload /></el-icon>
              <span>数据导入</span>
            </template>
            <el-menu-item index="import-balance">科目余额表导入</el-menu-item>
            <el-menu-item index="import-voucher">凭证/序时账导入</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="config">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统配置</span>
            </template>
            <el-menu-item index="subject-mapping">科目映射配置</el-menu-item>
            <el-menu-item index="project-list">项目档案</el-menu-item>
            <el-menu-item index="bank-account">银行账户</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </div>

      <!-- 内容区 -->
      <div class="content-area">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = ref('dashboard')

// 同步当前路由到菜单激活状态
watch(
  () => route.path,
  (path) => {
    const pathMap = {
      '/dashboard': 'dashboard',
      '/project-board': 'project-board',
      '/affiliated-tax': 'affiliated-tax',
      '/lmr-reference': 'lmr-reference',
      '/project-profit': 'project-profit',
      '/fund-daily': 'fund-daily',
      '/aging-receivable': 'aging-receivable',
      '/import-balance': 'import-balance',
      '/import-voucher': 'import-voucher',
      '/subject-mapping': 'subject-mapping',
      '/project-list': 'project-list',
      '/bank-account': 'bank-account'
    }
    activeMenu.value = pathMap[path] || 'dashboard'
  },
  { immediate: true }
)

function handleMenuSelect(index) {
  const routeMap = {
    dashboard: '/dashboard',
    'project-board': '/project-board',
    'affiliated-tax': '/affiliated-tax',
    'lmr-reference': '/lmr-reference',
    'project-profit': '/project-profit',
    'fund-daily': '/fund-daily',
    'aging-receivable': '/aging-receivable',
    'import-balance': '/import-balance',
    'import-voucher': '/import-voucher',
    'subject-mapping': '/subject-mapping',
    'project-list': '/project-list',
    'bank-account': '/bank-account'
  }
  if (routeMap[index]) {
    router.push(routeMap[index])
  }
}

function handleCommand(cmd) {
  if (cmd === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
      .then(() => {
        userStore.logout()
        router.push('/login')
        ElMessage.success('已退出登录')
      })
      .catch(() => {})
  } else if (cmd === 'profile') {
    ElMessage.info('个人信息功能开发中')
  }
}

onMounted(() => {
  // 加载用户信息
  if (userStore.token && !userStore.userInfo.username) {
    userStore.fetchUserInfo().catch(() => {
      // 获取失败不阻断
    })
  }
})
</script>
