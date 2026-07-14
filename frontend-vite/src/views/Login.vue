<template>
  <div class="login-page">
    <div class="login-box">
      <div class="login-logo">
        <div class="login-logo-icon">建</div>
      </div>
      <div class="login-title">建税盾</div>
      <div class="login-subtitle">建筑经营管理报表系统</div>
      <el-form :model="loginForm" label-position="top" @submit.prevent="handleLogin">
        <el-form-item label="用户名">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" size="large" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width: 100%" :loading="loginLoading" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div style="text-align: center; color: #909399; font-size: 12px">演示账号：boss / 123456</div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const loginForm = reactive({
  username: 'boss',
  password: '123456'
})
const loginLoading = ref(false)

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loginLoading.value = true
  try {
    const success = await userStore.login(loginForm.username, loginForm.password)
    if (success) {
      ElMessage.success('登录成功')
      router.push('/dashboard')
    } else {
      ElMessage.error('用户名或密码错误')
    }
  } catch (e) {
    console.error('Login error:', e)
    ElMessage.error('登录失败，请稍后重试')
  } finally {
    loginLoading.value = false
  }
}
</script>
