import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getCurrentUser } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  // state
  const token = ref(localStorage.getItem('jianzao_token') || '')
  const userInfo = ref({})

  // getters
  const isLoggedIn = computed(() => !!token.value)
  const userName = computed(() => userInfo.value.real_name || userInfo.value.username || '')
  const avatarText = computed(() => userInfo.value.real_name ? userInfo.value.real_name[0] : 'U')

  // actions
  async function login(username, password) {
    const data = await loginApi(username, password)
    if (data?.access_token) {
      token.value = data.access_token
      localStorage.setItem('jianzao_token', data.access_token)
      await fetchUserInfo()
      return true
    }
    return false
  }

  async function fetchUserInfo() {
    const data = await getCurrentUser()
    if (data) {
      userInfo.value = data
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = {}
    localStorage.removeItem('jianzao_token')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    userName,
    avatarText,
    login,
    fetchUserInfo,
    logout
  }
})
